const $ = id => document.getElementById(id);
const DT = 1 / 60, MAX_STEPS = 360, SEED = 20261031, IGNITION_RADIUS = .12;
const VIEW = Object.freeze({ width: 1200, height: 600 });
const CAMERA = Object.freeze({ yaw: 0, elevation: 0, distance: 3.4, fov: .85, targetY: 1.05 });
const FONT_SOURCE = 'local("Microsoft YaHei")';
const FONT = '400 32px "A36Raster"';
const WORLD_PER_PIXEL = 2 * CAMERA.distance * Math.tan(CAMERA.fov / 2) / VIEW.height;
const RASTER = Object.freeze({ width: 1200, height: 96, anchorX: 280, anchorY: 48,
  stride: 2, alphaThreshold: 128, worldPerPixel: WORLD_PER_PIXEL, z: 0,
  gaussianScale: WORLD_PER_PIXEL, opacity: .94, color: [.82, .78, .67], fuel: 1 });
const LINES = Object.freeze([
  { id: 'line1', label: '第一行', text: '末班车九点十二分开走。', sourceY: 204 },
  { id: 'line2', label: '第二行', text: '请把长凳推到门边，留出一人睡觉的地方。', sourceY: 252 },
  { id: 'line3', label: '第三行', text: '时刻表不要摘，明早第一班仍是六点四十。', sourceY: 300 },
  { id: 'line4', label: '第四行', text: '若有人问今晚还能不能走，先把今晚那一行念完，再把门打开。', sourceY: 348 },
  { id: 'line5', label: '第五行', text: '暖水瓶里剩的水不够两杯，留给最后进来的人。', sourceY: 396 },
  { id: 'line6', label: '第六行', text: '我把钥匙压在纸下；你离开时，把这张纸放回钥匙上。', sourceY: 444 }
]);
const TARGET = Object.freeze({ id: 'do-not-remove', label: '不要摘', line: 'line3', startIndex: 3, endIndexExclusive: 6 });
const PARAMS = Object.freeze({ solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
  paused: true, orbit: false, yaw: CAMERA.yaw, camElev: CAMERA.elevation, camDist: CAMERA.distance, fov: CAMERA.fov,
  sliceMode: 'world', emitterOn: false, spreadOn: false,
  spreadFlameHeat: true, spreadSceneFeed: true, spreadClockMode: 'elapsed',
  spreadParticlePolicy: 'block', spreadMeasureMode: 'legacy',
  spreadFrontierCap: 1400, spreadSampleCap: 160, spreadFeedCap: 48,
  sceneOn: true, sceneMax: 16000, sceneScale: 1, sceneSH: 0,
  sceneYaw: 0, scenePitch: 0, sceneLift: 0, sceneOffX: 0, sceneOffZ: 0, box: false });
const BUDGET_KEYS = ['frontierDeferred', 'frontierProcessed', 'clockProcessed', 'clockFuelConsumed',
  'flameSampleCapHits', 'sceneFeedAttempts', 'sceneFeedCapacityBlocked'];
const state = { phase: 'loading', frame: 0, run: 0, resetCalls: 0, ignitionCalls: 0,
  totalStepCalls: 0, totalIgnitionHits: 0, runIgnitionCalls: 0, runIgnitionHits: 0,
  pointCount: 0, geometry: null, latestHeldFrame: null, holds: [], events: [],
  completedRuns: [], errors: [] };
const targetPointIds = new Set();
const canvas = $('view');
let demo, research, sourceCanvas, initialized = false, raf = 0, activeHold = null;
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
const wallStart = performance.now();
const clone = value => JSON.parse(JSON.stringify(value));
const wallSeconds = () => (performance.now() - wallStart) / 1000;
function record(action, extra = {}) { state.events.push({ action, run: state.run, frame: state.frame, elapsedSeconds: wallSeconds(), ...extra }); }
function finite(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error('原平台返回非有限状态');
  if (value && typeof value === 'object') for (const v of Object.values(value)) finite(v);
}
function metric(values) {
  const sum = values.reduce((a, b) => a + b, 0);
  return { sum, mean: values.length ? sum / values.length : 0,
    min: values.length ? Math.min(...values) : 0, max: values.length ? Math.max(...values) : 0,
    nonzeroCount: values.filter(v => v !== 0).length };
}
function summarizePoints(points) {
  return { count: points.length, heat: metric(points.map(p => p.heat)),
    fuel: metric(points.map(p => p.fuel)), fuelInitial: metric(points.map(p => p.fuelInitial)),
    char: metric(points.map(p => p.char)), glow: metric(points.map(p => p.glow)),
    stateCounts: { unburned: points.filter(p => p.state === 0).length,
      burning: points.filter(p => p.state === 1).length,
      fuelDepleted: points.filter(p => p.state === 2).length,
      other: points.filter(p => ![0, 1, 2].includes(p.state)).length } };
}
function readMaterial() {
  if (!research || !state.resetCalls) return null;
  const raw = research.snapshot({ detail: true });
  finite(raw);
  return { frame: raw.frame, time: raw.time, seed: raw.seed, hash: raw.hash,
    particleStateHash: raw.particleStateHash, scene: raw.scene, total: summarizePoints(raw.points),
    groups: Object.fromEntries(LINES.map(line => [line.id, { label: line.label,
      ...summarizePoints(raw.points.filter(p => p.group === line.id)) }])),
    subgroups: { [TARGET.id]: { label: TARGET.label, parentGroup: TARGET.line, overlapsParent: true,
      ...summarizePoints(raw.points.filter(p => targetPointIds.has(p.id))) } },
    particles: raw.particles, counters: raw.counters, countersByGroup: raw.countersByGroup,
    params: raw.params, randomDraws: raw.randomDraws,
    capDelayObserved: raw.counters.frontierDeferred > 0 };
}
function cumulativeBudgets(material) {
  const currentAlreadyArchived = state.completedRuns.some(run => run.run === state.run);
  return Object.fromEntries(BUDGET_KEYS.map(key => [key,
    state.completedRuns.reduce((sum, run) => sum + (run.counters[key] ?? 0), 0)
      + (currentAlreadyArchived ? 0 : material?.counters[key] ?? 0)]));
}
function snapshot() {
  let material = null, snapshotError = null;
  try { material = readMaterial(); } catch (error) { snapshotError = String(error.message || error); }
  return clone({ ...state, time: material?.time ?? state.frame * DT, simSeconds: material?.time ?? state.frame * DT,
    dt: DT, maxSteps: MAX_STEPS, seed: SEED, ignitionRadius: IGNITION_RADIUS,
    running: state.phase === 'running' && activeHold !== null, activeHold: activeHold ? { ...activeHold } : null,
    groups: material?.groups ?? null, subgroups: material?.subgroups ?? null, total: material?.total ?? null,
    counters: material?.counters ?? null, cumulativeBudgets: cumulativeBudgets(material),
    hash: material?.hash ?? null, material, snapshotError,
    canvasVisible: !$('canvas-frame').hidden, sourceCanvasSize: [sourceCanvas?.width ?? null, sourceCanvas?.height ?? null],
    elapsedSeconds: wallSeconds() });
}
function stopRAF() { if (raf) cancelAnimationFrame(raf); raf = 0; }
function updateUI() {
  const messages = { loading: '正在准备字面。', ready: '可以先读完，再按住字面划行。',
    running: '按住时，画面向前。', held: '画面停在这里。可以继续读，也可以再按住。',
    ended: '六模拟秒已到。字面留在这里。', left: '这次观看已结束。', error: '本次观看停止，状态保留。' };
  if ($('status').textContent !== messages[state.phase]) $('status').textContent = messages[state.phase];
  $('time-readout').textContent = `${(state.frame * DT).toFixed(2)} / 6.00 模拟秒`;
  $('leave').disabled = ['loading', 'left', 'error'].includes(state.phase);
  $('leave').hidden = state.phase === 'left';
  $('restart').hidden = state.phase !== 'left';
  canvas.dataset.disabled = String(!['ready', 'held', 'running'].includes(state.phase));
  if (state.phase === 'running') $('stats-caption').textContent = `推进中；下表保留最近停留点 ${(state.latestHeldFrame * DT).toFixed(2)} 秒的状态。`;
}
function showHeldStats() {
  const material = readMaterial();
  state.latestHeldFrame = state.frame;
  $('stats-caption').textContent = `第${state.run}遍 · ${(state.frame * DT).toFixed(2)}模拟秒 · ${state.pointCount.toLocaleString()}个材料点`;
  const fragment = document.createDocumentFragment();
  for (const line of LINES) {
    const g = material.groups[line.id], row = document.createElement('tr');
    const percent = g.fuelInitial.sum ? 100 * g.fuel.sum / g.fuelInitial.sum : 0;
    for (const text of [line.label, String(g.count), g.heat.mean.toFixed(3), `${percent.toFixed(1)}%`,
      `${g.stateCounts.burning} / ${g.stateCounts.fuelDepleted}`]) {
      const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
    }
    fragment.appendChild(row);
  }
  $('group-rows').replaceChildren(fragment);
  const total = cumulativeBudgets(material);
  $('counter-readout').textContent = `本遍 frontierDeferred ${material.counters.frontierDeferred}，clockProcessed ${material.counters.clockProcessed}；`
    + `跨遍累计 ${total.frontierDeferred} / ${total.clockProcessed}。点火调用累计 ${state.ignitionCalls} 次，推进调用累计 ${state.totalStepCalls} 次。`;
}
function renderMaterial() {
  demo.render(); demo.gl.finish();
  if (sourceCanvas.width !== VIEW.width || sourceCanvas.height !== VIEW.height) throw new Error('源画布尺寸不是固定1200×600');
  canvas.getContext('2d', { alpha: false }).drawImage(sourceCanvas, 0, 0, VIEW.width, VIEW.height, 0, 0, VIEW.width, VIEW.height);
}
function eventPoint(event) {
  const bounds = canvas.getBoundingClientRect();
  if (bounds.width <= 0 || bounds.height <= 0) throw new Error('字面没有有效输入范围');
  const sx = (event.clientX - bounds.left) / bounds.width * VIEW.width;
  const sy = (event.clientY - bounds.top) / bounds.height * VIEW.height;
  if (![sx, sy].every(Number.isFinite)) throw new Error('触点坐标不是有限值');
  return { source: { x: sx, y: sy }, world: { x: (sx - 600) * WORLD_PER_PIXEL,
    y: CAMERA.targetY + (300 - sy) * WORLD_PER_PIXEL, z: 0 },
    inside: sx >= 0 && sx < VIEW.width && sy >= 0 && sy < VIEW.height,
    bounds: { x: bounds.left, y: bounds.top, width: bounds.width, height: bounds.height } };
}
function logInput(hold, event, point = null) {
  hold.events.push({ type: event.type, frame: state.frame, elapsedSeconds: wallSeconds(),
    pointerId: event.pointerId ?? null, pointerType: event.pointerType ?? null,
    buttons: event.buttons ?? null, clientX: event.clientX ?? null, clientY: event.clientY ?? null,
    point: point ? clone(point) : null });
}
function endHold(reason) {
  if (!activeHold) return;
  stopRAF();
  const hold = state.holds[activeHold.index], pointerId = activeHold.pointerId;
  hold.endFrame = state.frame; hold.stopReason = reason; hold.endElapsedSeconds = wallSeconds();
  activeHold = null;
  state.phase = state.frame >= MAX_STEPS ? 'ended' : 'held';
  record('hold_stopped', { holdId: hold.id, reason });
  if (canvas.hasPointerCapture(pointerId)) canvas.releasePointerCapture(pointerId);
  showHeldStats(); updateUI();
}
function fail(error) {
  stopRAF();
  const message = String(error.message || error);
  if (!state.errors.includes(message)) state.errors.push(message);
  if (activeHold) {
    const hold = state.holds[activeHold.index], pointerId = activeHold.pointerId;
    hold.endFrame = state.frame; hold.stopReason = 'error'; hold.endElapsedSeconds = wallSeconds(); activeHold = null;
    try { if (canvas.hasPointerCapture(pointerId)) canvas.releasePointerCapture(pointerId); }
    catch (captureError) { state.errors.push(String(captureError.message || captureError)); }
  }
  state.phase = 'error'; record('error', { message });
  $('loading').hidden = true; $('error').hidden = false;
  $('error').textContent = '本次观看停止：' + message + '。状态保留，不自动重试。';
  updateUI(); rejectReady(error);
}
const guarded = fn => event => { try { fn(event); } catch (error) { fail(error); } };
function igniteAtCurrent(trigger) {
  const hold = state.holds[activeHold.index], point = activeHold.point;
  state.ignitionCalls++; state.runIgnitionCalls++;
  const entry = { call: state.ignitionCalls, trigger, frameBefore: state.frame, frameAfter: state.frame,
    source: { ...point.source }, world: { ...point.world }, radius: IGNITION_RADIUS, newlyLit: null };
  hold.ignitions.push(entry);
  entry.newlyLit = demo.ignite(point.world.x, point.world.y, 0, IGNITION_RADIUS);
  if (!Number.isInteger(entry.newlyLit) || entry.newlyLit < 0 || entry.newlyLit > state.pointCount)
    throw new Error('点火返回无效命中数');
  state.totalIgnitionHits += entry.newlyLit; state.runIgnitionHits += entry.newlyLit;
  hold.ignitionCalls++; hold.newlyLit += entry.newlyLit;
  return entry;
}
function advanceHeldFrame() {
  raf = 0;
  if (!activeHold || state.phase !== 'running') return;
  try {
    const entry = igniteAtCurrent('before-step'), expectedFrame = state.frame + 1;
    state.totalStepCalls++; entry.stepCall = state.totalStepCalls;
    const raw = research.step(1, DT);
    finite(raw);
    if (raw.frame !== expectedFrame || Math.abs(raw.time - expectedFrame * DT) > 1e-8)
      throw new Error('本页与原平台的步数或模拟时间不一致');
    state.frame = raw.frame; entry.frameAfter = raw.frame;
    renderMaterial();
    if (state.frame >= MAX_STEPS) endHold('360_step_limit');
    else { updateUI(); raf = requestAnimationFrame(advanceHeldFrame); }
  } catch (error) { fail(error); }
}
canvas.addEventListener('pointerdown', guarded(event => {
  if (!['ready', 'held'].includes(state.phase) || activeHold || state.frame >= MAX_STEPS
    || event.isPrimary === false || event.button !== 0) return;
  const point = eventPoint(event);
  if (!point.inside) return;
  event.preventDefault();
  const hold = { id: state.holds.length + 1, run: state.run, pointerId: event.pointerId,
    pointerType: event.pointerType, startFrame: state.frame, startElapsedSeconds: wallSeconds(),
    endFrame: null, stopReason: null, releaseObserved: false, events: [], ignitions: [], ignitionCalls: 0, newlyLit: 0 };
  state.holds.push(hold);
  activeHold = { index: state.holds.length - 1, pointerId: event.pointerId, point };
  logInput(hold, event, point); record('hold_started', { holdId: hold.id });
  canvas.setPointerCapture(event.pointerId);
  hold.events.push({ type: 'capture-requested', frame: state.frame, elapsedSeconds: wallSeconds(), pointerId: event.pointerId });
  igniteAtCurrent('pointerdown');
  if (state.runIgnitionCalls === 1) research.setParams({ spreadOn: true });
  state.phase = 'running'; renderMaterial(); updateUI();
  raf = requestAnimationFrame(advanceHeldFrame);
}));
canvas.addEventListener('pointermove', guarded(event => {
  if (!activeHold || activeHold.pointerId !== event.pointerId) return;
  const point = eventPoint(event), hold = state.holds[activeHold.index];
  logInput(hold, event, point);
  if (!point.inside) { endHold('pointermove_outside'); return; }
  if (event.pointerType === 'mouse' && event.buttons === 0) { endHold('buttons_released'); return; }
  event.preventDefault(); activeHold.point = point;
}));
canvas.addEventListener('pointerleave', guarded(event => {
  if (!activeHold || activeHold.pointerId !== event.pointerId) return;
  logInput(state.holds[activeHold.index], event, eventPoint(event)); endHold('pointerleave');
}));
for (const type of ['pointerup', 'pointercancel']) window.addEventListener(type, guarded(event => {
  const hold = state.holds.findLast(h => h.pointerId === event.pointerId && !h.releaseObserved);
  if (!hold) return;
  logInput(hold, event, $('canvas-frame').hidden ? null : eventPoint(event));
  hold.releaseObserved = true;
  if (activeHold?.pointerId === event.pointerId) endHold(type);
}));
for (const type of ['gotpointercapture', 'lostpointercapture']) canvas.addEventListener(type, guarded(event => {
  const hold = state.holds.findLast(h => h.pointerId === event.pointerId);
  if (hold) logInput(hold, event);
  if (type === 'lostpointercapture' && activeHold?.pointerId === event.pointerId) endHold('lostpointercapture');
}));
window.addEventListener('blur', guarded(() => { if (activeHold) endHold('window_blur'); }));
document.addEventListener('visibilitychange', guarded(() => { if (document.hidden && activeHold) endHold('page_hidden'); }));
window.addEventListener('pagehide', guarded(() => { if (activeHold) endHold('page_hidden'); }));
$('leave').addEventListener('click', guarded(() => {
  if (['loading', 'left', 'error'].includes(state.phase)) return;
  if (activeHold) endHold('viewer_end');
  stopRAF(); state.phase = 'left'; record('viewer_end');
  $('canvas-frame').hidden = true; $('end-card').hidden = false;
  showHeldStats(); updateUI(); $('restart').focus({ preventScroll: true });
}));
function resetRun() {
  state.resetCalls++; research.reset(SEED, PARAMS); state.run++;
  state.frame = 0; state.runIgnitionCalls = 0; state.runIgnitionHits = 0;
  demo.forceSize(VIEW.width, VIEW.height); research.camera(CAMERA.yaw);
  renderMaterial();
  const material = readMaterial();
  if (material.frame !== 0 || material.time !== 0 || material.total.stateCounts.unburned !== state.pointCount
    || material.total.fuel.sum !== material.total.fuelInitial.sum) throw new Error('重置后不是完整未点火初态');
  state.phase = 'ready'; record('original_restored');
  $('canvas-frame').hidden = false; $('end-card').hidden = true;
  showHeldStats(); updateUI();
}
$('restart').addEventListener('click', guarded(() => {
  if (state.phase !== 'left') return;
  const material = readMaterial();
  state.completedRuns.push({ run: state.run, frame: state.frame, hash: material.hash,
    ignitionCalls: state.runIgnitionCalls, ignitionHits: state.runIgnitionHits,
    counters: clone(material.counters), groups: clone(material.groups), total: clone(material.total) });
  record('restart_requested'); resetRun();
}));
/* The following glyph construction is copied from A37; only the point limit is 16000. */
function fnvBytes(bytes) {
  let h = 2166136261;
  for (const byte of bytes) { h ^= byte; h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(16).padStart(8, '0');
}
async function makeScene() {
  const font = new FontFace('A36Raster', FONT_SOURCE, { weight: '400', style: 'normal' });
  await font.load(); document.fonts.add(font);
  await document.fonts.load(FONT, LINES.map(line => line.text).join(''));
  const points = [], groups = [];
  let targetBounds = null;
  for (const line of LINES) {
    const canvas = document.createElement('canvas');
    canvas.width = RASTER.width; canvas.height = RASTER.height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.font = FONT; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#ffffff';
    const measured = ctx.measureText(line.text);
    const inkBounds = { left: RASTER.anchorX - measured.actualBoundingBoxLeft,
      right: RASTER.anchorX + measured.actualBoundingBoxRight,
      top: RASTER.anchorY - measured.actualBoundingBoxAscent,
      bottom: RASTER.anchorY + measured.actualBoundingBoxDescent };
    if (![measured.width, ...Object.values(inkBounds)].every(Number.isFinite))
      throw new Error(`${line.label}字形测量不可用`);
    if (RASTER.anchorX + measured.width > RASTER.width || inkBounds.left < 0 || inkBounds.right > RASTER.width
      || inkBounds.top < 0 || inkBounds.bottom > RASTER.height)
      throw new Error(`${line.label}超出预定栅格，不自动缩字或移位`);
    if (line.id === TARGET.line) {
      if (line.text.slice(TARGET.startIndex, TARGET.endIndexExclusive) !== TARGET.label) throw new Error('子组字符索引不符');
      targetBounds = { startX: RASTER.anchorX + ctx.measureText(line.text.slice(0, TARGET.startIndex)).width,
        endXExclusive: RASTER.anchorX + ctx.measureText(line.text.slice(0, TARGET.endIndexExclusive)).width };
    }
    ctx.fillText(line.text, RASTER.anchorX, RASTER.anchorY);
    const pixels = ctx.getImageData(0, 0, RASTER.width, RASTER.height).data;
    const before = points.length;
    const bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
    for (let y = 1; y < RASTER.height; y += RASTER.stride) {
      for (let x = 1; x < RASTER.width; x += RASTER.stride) {
        if (pixels[4 * (y * RASTER.width + x) + 3] < RASTER.alphaThreshold) continue;
        bounds.minX = Math.min(bounds.minX, x); bounds.maxX = Math.max(bounds.maxX, x);
        bounds.minY = Math.min(bounds.minY, y); bounds.maxY = Math.max(bounds.maxY, y);
        const id = `${line.id}:${y}:${x}`;
        const sourceX = x + .5, sourceY = line.sourceY + y + .5 - RASTER.anchorY;
        points.push({ id, group: line.id,
          position: [(sourceX - VIEW.width / 2) * WORLD_PER_PIXEL,
            CAMERA.targetY + (VIEW.height / 2 - sourceY) * WORLD_PER_PIXEL, RASTER.z],
          color: [...RASTER.color], scale: RASTER.gaussianScale, opacity: RASTER.opacity, fuel: RASTER.fuel });
        if (line.id === TARGET.line && sourceX >= targetBounds.startX && sourceX < targetBounds.endXExclusive) targetPointIds.add(id);
      }
    }
    const count = points.length - before;
    if (!count) throw new Error(`${line.label}没有生成字形点`);
    groups.push({ ...line, pointCount: count, requestedCanvasFont: FONT, canvasFont: ctx.font,
      measuredTextWidth: measured.width, measuredInkBounds: inkBounds,
      sampledPixelBounds: bounds, rgbaFNV1a32: fnvBytes(pixels) });
  }
  if (points.length > 16000) throw new Error(`字形点数${points.length}超过16000，不自动抽稀`);
  if (!targetPointIds.size) throw new Error('固定字符区间“不要摘”没有生成字形点');
  return { points, metadata: { fontSource: FONT_SOURCE, fontStatus: font.status,
    requestedFont: FONT, raster: RASTER, camera: CAMERA, groups, pointCount: points.length,
    target: { ...TARGET, ...targetBounds, pointCount: targetPointIds.size, attribution: 'sample centers in fixed character-prefix bounds; subset of line3' },
    sourceCanvasSize: [VIEW.width, VIEW.height], sourcePixelLineSpacing: 48,
    outsideFluidXCount: points.filter(p => Math.abs(p.position[0]) > 1).length,
    stableOnlyForSameLocalFontAndRasterizer: true } };
}

Object.defineProperty(window, '__a39', { value: Object.freeze({ ready, snapshot }), writable: false, configurable: false });
const initializationTimeout = setTimeout(() => fail(new Error('原平台或本地字体在20秒内未就绪')), 20000);
async function initialize() {
  if (initialized || state.phase !== 'loading') return;
  initialized = true;
  try {
    demo = $('source').contentWindow.__demo;
    if (!demo?.research) throw new Error('原平台接口不可用，请从仓库HTTP服务打开');
    research = demo.research; sourceCanvas = $('source').contentDocument.querySelector('#cv');
    if (!sourceCanvas) throw new Error('原平台画布缺失');
    const scene = await makeScene();
    if (state.phase !== 'loading') return;
    const loaded = research.setScene(scene.points);
    if (loaded.count !== scene.points.length) throw new Error('原平台载入字形点数不一致');
    state.pointCount = loaded.count; state.geometry = scene.metadata;
    resetRun(); $('loading').hidden = true; clearTimeout(initializationTimeout); resolveReady(snapshot());
  } catch (error) { clearTimeout(initializationTimeout); fail(error); }
}
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) initialize();
