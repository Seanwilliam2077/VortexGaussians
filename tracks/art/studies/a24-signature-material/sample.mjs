const $ = id => document.getElementById(id);
const DT = 1 / 60, SEGMENT_STEPS = 120, MAX_STEPS = 360, SEED = 20261031;
const FONT_SOURCE = 'local("Microsoft YaHei")';
const FONT = '400 64px "A24Raster"';
const RASTER = Object.freeze({ width: 144, height: 80, stride: 2, alphaThreshold: 128,
  worldPerPixel: .008, centerY: .75, z: 0, gaussianScale: .0102, opacity: .94,
  color: [.82, .78, .67], fuel: 1 });
const NAMES = Object.freeze([
  { id: 'ning-lan', name: '宁岚', centerX: -1.4 },
  { id: 'ye-qing', name: '叶青', centerX: 0 },
  { id: 'shen-zhou', name: '沈舟', centerX: 1.4 }
]);
const IGNITION = Object.freeze({ x: 0, y: .75, z: 0, radius: .40 });
const PARAMS = Object.freeze({ solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
  paused: true, orbit: false, yaw: 0, camElev: 0, camDist: 3.4, fov: .85,
  sliceMode: 'world', emitterOn: false, spreadOn: false,
  spreadFlameHeat: true, spreadSceneFeed: true, spreadClockMode: 'legacy',
  spreadParticlePolicy: 'block', spreadMeasureMode: 'legacy',
  sceneOn: true, sceneMax: 8000, sceneScale: 1, sceneSH: 0,
  sceneYaw: 0, scenePitch: 0, sceneLift: 0, sceneOffX: 0, sceneOffZ: 0, box: false });
const state = { phase: 'loading', frame: 0, segmentEnd: 0, segmentsCompleted: 0,
  resetCalls: 0, ignitionCalls: 0, initialLit: null, pointCount: 0, geometry: null,
  latestHeldFrame: null, heldGroups: null, errors: [], events: [], endedBecause: null };
let demo, research, sourceCanvas, raf = 0, initialized = false;
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
const wallStart = performance.now();
const clone = value => JSON.parse(JSON.stringify(value));
function record(action) {
  state.events.push({ action, phase: state.phase, frame: state.frame,
    elapsedSeconds: (performance.now() - wallStart) / 1000 });
}
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
      burnedOut: points.filter(p => p.state === 2).length,
      other: points.filter(p => ![0, 1, 2].includes(p.state)).length } };
}
function readMaterial() {
  if (!research) return null;
  const raw = research.snapshot({ detail: true });
  finite(raw);
  if (raw.frame !== state.frame || Math.abs(raw.time - state.frame * DT) > 1e-8)
    throw new Error('本页与原平台的步数或模拟时间不一致');
  const groups = Object.fromEntries(NAMES.map(n => [n.id, { name: n.name,
    ...summarizePoints(raw.points.filter(p => p.group === n.id)) }]));
  return { frame: raw.frame, time: raw.time, seed: raw.seed, hash: raw.hash,
    particleStateHash: raw.particleStateHash, scene: raw.scene, total: summarizePoints(raw.points),
    groups, particles: raw.particles, counters: raw.counters, countersByGroup: raw.countersByGroup,
    params: raw.params, randomDraws: raw.randomDraws };
}
function snapshot() {
  const material = readMaterial();
  return clone({ ...state, simSeconds: state.frame * DT, maxSteps: MAX_STEPS,
    segmentSteps: SEGMENT_STEPS, dt: DT, seed: SEED, ignition: IGNITION,
    groups: material?.groups ?? null, total: material?.total ?? null, hash: material?.hash ?? null,
    material, elapsedSeconds: (performance.now() - wallStart) / 1000,
    scope: 'Gaussian signatures only; statement and request are static HTML, not simulated.' });
}
function stopRAF() { cancelAnimationFrame(raf); raf = 0; }
function fail(error) {
  stopRAF();
  const message = error instanceof Error ? error.message : String(error);
  if (!state.errors.includes(message)) state.errors.push(message);
  state.phase = 'error'; state.endedBecause = 'error'; record('error');
  $('loading').hidden = true; $('error').hidden = false;
  $('error').textContent = '本次小样停止：' + message + '。状态保留，不自动重试。';
  updateUI(); rejectReady(error);
}
function updateUI() {
  $('sim-time').textContent = (state.frame * DT).toFixed(2);
  const descriptions = { loading: '准备中', ready: '初始署名', ignited: '已点燃 · 尚未推进',
    running: '正在推进', paused: '段内暂停', held: '本段结束 · 停留',
    ended: '六秒结束 · 状态保留', left: '已停止 · 状态保留', error: '执行停止' };
  $('phase-text').textContent = descriptions[state.phase] ?? state.phase;
  $('ignite').disabled = state.phase !== 'ready';
  $('advance').disabled = !['ignited', 'held'].includes(state.phase) || state.frame >= MAX_STEPS;
  $('pause').disabled = !['running', 'paused'].includes(state.phase);
  $('pause').textContent = state.phase === 'paused' ? '继续本段' : '暂停';
  $('leave').disabled = ['loading', 'left', 'error'].includes(state.phase);
  if (state.heldGroups) $('stats-caption').textContent = state.phase === 'running'
    ? `推进中；下表保留最近停留点 ${(state.latestHeldFrame * DT).toFixed(2)} 秒的状态。`
    : `当前停留点 ${(state.latestHeldFrame * DT).toFixed(2)} 秒 · 共 ${state.pointCount.toLocaleString()} 个字形点。`;
}
function updateHeldStats() {
  const material = readMaterial();
  state.heldGroups = material.groups; state.latestHeldFrame = state.frame;
  const fragment = document.createDocumentFragment();
  for (const n of NAMES) {
    const g = material.groups[n.id], row = document.createElement('tr');
    const percent = g.fuelInitial.sum ? 100 * g.fuel.sum / g.fuelInitial.sum : 0;
    for (const text of [n.name, g.heat.mean.toFixed(3), `${percent.toFixed(1)}%`,
      g.char.mean.toFixed(3), `${g.stateCounts.burning} / ${g.stateCounts.burnedOut}`]) {
      const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
    }
    fragment.appendChild(row);
  }
  $('group-rows').replaceChildren(fragment); updateUI();
}
function renderMaterial() {
  demo.render(); demo.gl.finish();
  const canvas = $('view'), ctx = canvas.getContext('2d', { alpha: false });
  ctx.drawImage(sourceCanvas, 0, 0, sourceCanvas.width, sourceCanvas.height, 0, 0, canvas.width, canvas.height);
}
function fnvBytes(bytes) {
  let h = 2166136261;
  for (const byte of bytes) { h ^= byte; h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(16).padStart(8, '0');
}
async function makeScene() {
  const font = new FontFace('A24Raster', FONT_SOURCE, { weight: '400', style: 'normal' });
  await font.load(); document.fonts.add(font);
  await document.fonts.load(FONT, '宁岚叶青沈舟');
  const points = [], groups = [];
  for (const n of NAMES) {
    const canvas = document.createElement('canvas');
    canvas.width = RASTER.width; canvas.height = RASTER.height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.font = FONT; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#ffffff';
    ctx.fillText(n.name, RASTER.width / 2, RASTER.height / 2);
    const pixels = ctx.getImageData(0, 0, RASTER.width, RASTER.height).data;
    const before = points.length, bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
    for (let y = 1; y < RASTER.height; y += RASTER.stride) {
      for (let x = 1; x < RASTER.width; x += RASTER.stride) {
        if (pixels[4 * (y * RASTER.width + x) + 3] < RASTER.alphaThreshold) continue;
        bounds.minX = Math.min(bounds.minX, x); bounds.maxX = Math.max(bounds.maxX, x);
        bounds.minY = Math.min(bounds.minY, y); bounds.maxY = Math.max(bounds.maxY, y);
        points.push({ id: `${n.id}:${y}:${x}`, group: n.id,
          position: [n.centerX + (x + .5 - RASTER.width / 2) * RASTER.worldPerPixel,
            RASTER.centerY + (RASTER.height / 2 - y - .5) * RASTER.worldPerPixel, RASTER.z],
          color: [...RASTER.color], scale: RASTER.gaussianScale, opacity: RASTER.opacity, fuel: RASTER.fuel });
      }
    }
    const count = points.length - before;
    if (!count) throw new Error(`${n.name}没有生成字形点`);
    const width = ctx.measureText(n.name).width;
    if (width > RASTER.width - 8) throw new Error(`${n.name}字宽超过预定栅格，不自动缩字`);
    groups.push({ ...n, pointCount: count, requestedCanvasFont: FONT, canvasFont: ctx.font,
      measuredTextWidth: width, sampledPixelBounds: bounds, rgbaFNV1a32: fnvBytes(pixels) });
  }
  if (points.length > 8000) throw new Error(`字形点数${points.length}超过8000，不自动抽稀`);
  return { points, metadata: { fontSource: FONT_SOURCE, fontStatus: font.status,
    requestedFont: FONT, raster: RASTER, groups, pointCount: points.length,
    sourceCanvasSize: [1200, 600], stableOnlyForSameLocalFontAndRasterizer: true } };
}
function ignite() {
  if (state.phase !== 'ready' || state.ignitionCalls !== 0) return;
  try {
    state.ignitionCalls++;
    state.initialLit = demo.ignite(IGNITION.x, IGNITION.y, IGNITION.z, IGNITION.radius);
    record('ignite_called');
    if (!Number.isInteger(state.initialLit) || state.initialLit < 1 || state.initialLit > 1400)
      throw new Error(`初始点火数为${state.initialLit}，不在1..1400；停止且不改点火位置`);
    research.setParams({ spreadOn: true }); state.phase = 'ignited';
    renderMaterial(); updateHeldStats(); record('ignited_without_advance');
  } catch (error) { fail(error); }
}
function advanceOneFrame() {
  raf = 0;
  if (state.phase !== 'running') return;
  try {
    const raw = research.step(1, DT); state.frame++;
    finite(raw);
    if (raw.frame !== state.frame || Math.abs(raw.time - state.frame * DT) > 1e-8)
      throw new Error('原平台推进步数或模拟时间不一致');
    renderMaterial();
    if (state.frame === state.segmentEnd) {
      state.segmentsCompleted++;
      state.phase = state.frame === MAX_STEPS ? 'ended' : 'held';
      if (state.phase === 'ended') state.endedBecause = 'fixed_360_step_limit';
      updateHeldStats(); record('segment_endpoint');
    } else { updateUI(); raf = requestAnimationFrame(advanceOneFrame); }
  } catch (error) { fail(error); }
}
function advanceSegment() {
  if (!['ignited', 'held'].includes(state.phase) || state.frame >= MAX_STEPS) return;
  state.segmentEnd = state.frame + SEGMENT_STEPS;
  state.phase = 'running'; record('segment_started'); updateUI();
  raf = requestAnimationFrame(advanceOneFrame);
}
function pause() {
  try {
    if (state.phase === 'running') {
      stopRAF(); state.phase = 'paused'; updateHeldStats(); record('paused');
    } else if (state.phase === 'paused') {
      state.phase = 'running'; record('resumed'); updateUI(); raf = requestAnimationFrame(advanceOneFrame);
    }
  } catch (error) { fail(error); }
}
function leave() {
  if (['loading', 'left', 'error'].includes(state.phase)) return;
  try {
    stopRAF(); state.phase = 'left'; state.endedBecause ??= 'viewer_stopped';
    updateHeldStats(); record('viewer_stopped');
  } catch (error) { fail(error); }
}
$('ignite').addEventListener('click', ignite);
$('advance').addEventListener('click', advanceSegment);
$('pause').addEventListener('click', pause);
$('leave').addEventListener('click', leave);
Object.defineProperty(window, '__a24', { value: Object.freeze({ ready, snapshot }), writable: false });
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
    research.reset(SEED, PARAMS); state.resetCalls++;
    demo.forceSize(1200, 600); research.camera(0);
    renderMaterial(); state.phase = 'ready'; updateHeldStats(); record('ready');
    $('loading').hidden = true; clearTimeout(initializationTimeout); resolveReady(snapshot());
  } catch (error) { clearTimeout(initializationTimeout); fail(error); }
}
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) initialize();
window.addEventListener('pagehide', () => {
  stopRAF();
  if (!['ended', 'left', 'error', 'loading'].includes(state.phase)) {
    state.phase = 'left'; state.endedBecause = 'page_hidden'; record('page_hidden');
  }
});
