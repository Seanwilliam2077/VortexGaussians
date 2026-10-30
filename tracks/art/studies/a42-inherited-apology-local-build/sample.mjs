const $ = id => document.getElementById(id);
const DT = 1 / 60, SEED = 20261031, MAX_STEPS = 360, RADIUS = .12;
const VIEW = Object.freeze({ width: 1200, height: 600 });
const CAMERA = Object.freeze({ yaw: 0, elevation: 0, distance: 3.4, fov: .85, targetY: 1.05 });
const FONT_SOURCE = 'local("Microsoft YaHei")', FONT = '400 32px "A36Raster"';
const Q = 2 * CAMERA.distance * Math.tan(CAMERA.fov / 2) / VIEW.height;
const RASTER = Object.freeze({ width: 1200, height: 96, anchorX: 400, anchorY: 48,
  stride: 2, alphaThreshold: 128, worldPerPixel: Q, z: 0, gaussianScale: Q,
  opacity: .94, color: [.82, .78, .67], fuel: 1 });
const LINES = Object.freeze([
  { id: 'apology', text: '我来迟了。', sourceY: 276 },
  { id: 'release', text: '你先回去，不必等我。', sourceY: 324 },
  { id: 'request', text: '你再等一会，我就到了。', sourceY: 324 }
]);
// Complete RESEARCH_DEFAULTS values plus exactly the A39 parameter overrides.
// This is explicit inheritance, not a parameter search or a new look preset.
const PARAMS = Object.freeze({
  mode: 'fire', simLayers: 9, riseV: 1.15, sway: .9, rate: 1500, coolP: .8, spread: .7,
  buoy: .9, baro: 1.4, eps: .07, cool: 1.2, gam: 1, turb: .55, couple: .5, interZ: 0,
  solver: 'vpm', theta: .9, vpmVisc: 0, vpmNaive: false, showTiming: false,
  layers: 9, yaw: 0, rad: 42, ppl: 160, wind: 0,
  camDist: 3.4, camElev: 0, fov: .85, sliceMode: 'world', sliceDepth: .7,
  covStretch: 1.3, covMax: 3.6, covRelax: 1, dimMode: 'layer', vol3DTurb: .6,
  vol3DScale: 2.4, stretch3: 1, filament: false, filLen: .5, filGain: 3,
  exposure: 1, emis: 2.2, bloom: 1, thresh: .40, blurIters: 5, look: 'cinematic',
  box: false, boxLight: .10, embers: true, reflect: .05, haze: .05, emberRate: 16, emberMax: 160,
  sceneOn: true, sceneMax: 16000, sceneScale: 1, sceneYaw: 0, scenePitch: 0, sceneLift: 0,
  sceneOffX: 0, sceneOffZ: 0, faithful: false, scenePreComp: false, sceneSH: 0, sceneLight: 1,
  sceneSorted: true, sceneBackdrop: false, sceneDepthTest: false, depthTestAlpha: .5,
  spreadOn: false, spreadIgnR: .14, spreadHeat: 2.2, spreadIgnH: 1,
  spreadR: .11, spreadRate: 3, spreadBurnT: 6, spreadFeed: 5,
  spreadFlameHeat: true, spreadSceneFeed: true, emitterOn: false,
  spreadFrontierCap: 1400, spreadSampleCap: 160, spreadFeedCap: 48,
  spreadClockMode: 'elapsed', spreadParticlePolicy: 'block', spreadRecycleMinAge: .5,
  spreadMeasureMode: 'legacy', spreadReferenceArea: .0016, spreadAreaFeedRate: 30,
  charDesat: .85, charDim: .12, charSootMix: 0, charOpa: 0,
  charSootR: .0495, charSootG: .0459, charSootB: .0428,
  orbit: false, stretch: true, flicker: true, paused: true
});
const clone = value => JSON.parse(JSON.stringify(value));
const freeze = value => {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
};
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const same = (a, b) => {
  if (typeof a !== typeof b) return false;
  if (a === null || b === null || typeof a !== 'object') return Object.is(a, b);
  const keys = Object.keys(a);
  return Array.isArray(a) === Array.isArray(b) && keys.length === Object.keys(b).length
    && keys.every(key => Object.hasOwn(b, key) && same(a[key], b[key]));
};
const finite = value => {
  if (typeof value === 'number') assert(Number.isFinite(value), '原平台返回非有限状态');
  else if (value && typeof value === 'object') Object.values(value).forEach(finite);
};
const startedAt = performance.now();
const state = { phase: 'loading', frame: 0, resetCalls: 0, ignitionCalls: 0, stepCalls: 0,
  handoverCalls: 0, buttonCalls: { first: 0, handover: 0, later: 0, finish: 0 },
  geometry: null, initial: null, handover: null, ignitions: [], events: [], holds: [], errors: [],
  costs: { initializationMs: null, handoverMs: null, stepMs: 0, renderMs: 0,
    explicitRenderCalls: 0, steps: [], lastRecordedElapsedMs: 0 } };
let demo, research, bridge, sourceCanvas, scene, initialized = false, raf = 0, active = null;
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
function record(action, details = {}) {
  const elapsedMs = performance.now() - startedAt;
  state.costs.lastRecordedElapsedMs = elapsedMs;
  state.events.push({ action, phase: state.phase, frame: state.frame, elapsedMs, ...details });
}
function summarize(points) {
  const sum = key => points.reduce((s, p) => s + p[key], 0);
  return { count: points.length, heatSum: sum('heat'), fuelSum: sum('fuel'), fuelInitialSum: sum('fuelInitial'),
    charSum: sum('char'), glowSum: sum('glow'), stateCounts: { unburned: points.filter(p => p.state === 0).length,
      burning: points.filter(p => p.state === 1).length, fuelDepleted: points.filter(p => p.state === 2).length } };
}
function read() {
  if (!bridge || !state.resetCalls) return { material: null, evidence: null };
  const result = bridge.inspect(); finite(result); return result;
}
function snapshot() {
  let material = null, evidence = null, snapshotError = null;
  try { ({ material, evidence } = read()); } catch (error) { snapshotError = String(error.message || error); }
  // No wall-clock reads, UI updates, rendering or mutation in this read-only path.
  // Frozen copied snapshots are stable while held, including across screenshots.
  return freeze(clone({ ...state,
    hash: material?.hash ?? null, material, evidence, snapshotError,
    time: material?.time ?? state.frame * DT, seed: SEED, dt: DT, maxSteps: MAX_STEPS,
    ignitionRadius: RADIUS, running: active !== null,
    active: active ? { ...active } : null,
    pointGroups: material ? Object.fromEntries(LINES.map(line => [line.id,
      material.points.filter(p => p.group === line.id)])) : null,
    groups: material ? Object.fromEntries(LINES.map(line => [line.id,
      summarize(material.points.filter(p => p.group === line.id))])) : null,
    originalMaterialHash: state.initial?.materialValuesHash ?? null,
    materialHash: evidence?.materialValuesHash ?? null,
    particleStateHash: material?.particleStateHash ?? null,
    counters: material?.counters ?? null,
    countersAllGroups: evidence?.countersAllGroups ?? null,
    sourceCanvasSize: [sourceCanvas?.width ?? null, sourceCanvas?.height ?? null]
  }));
}
function updateUI() {
  const messages = { loading: '正在准备固定材料。', ready: '初态。先阅读两行，再开始固定检查。',
    running: '固定步数推进中。', 'first-held': '首段停在3秒；下一步只更换下行。',
    handed: '换行完成，仍为3秒；旧句保留先前材料。',
    'later-held': '后段停在4.5秒；下一步继续到6秒。',
    ended: '6秒已到。本次材料检查结束。', error: '本次检查停止，保留失败记录。' };
  $('status').textContent = messages[state.phase];
  $('time-readout').textContent = `${(state.frame * DT).toFixed(2)} / 6.00 模拟秒 · frame ${state.frame}`;
  const enabled = { ready: 'first', 'first-held': 'handover', handed: 'later', 'later-held': 'finish' }[state.phase];
  for (const id of ['first', 'handover', 'later', 'finish']) $(id).disabled = id !== enabled || state.buttonCalls[id] !== 0;
  $('counter-readout').textContent = `reset ${state.resetCalls} · ignite ${state.ignitionCalls} · steps ${state.stepCalls} · handover ${state.handoverCalls}`;
}
function renderMaterial() {
  const begin = performance.now();
  demo.render(); demo.gl.finish();
  assert(sourceCanvas.width === VIEW.width && sourceCanvas.height === VIEW.height, '源画布尺寸不是固定1200×600');
  $('view').getContext('2d', { alpha: false }).drawImage(sourceCanvas, 0, 0, VIEW.width, VIEW.height,
    0, 0, VIEW.width, VIEW.height);
  const ms = performance.now() - begin;
  state.costs.explicitRenderCalls++; state.costs.renderMs += ms; return ms;
}
function hold(phase) {
  state.phase = phase; active = null;
  const { material, evidence } = read();
  assert(material.frame === state.frame && Math.abs(material.time - state.frame * DT) < 1e-8,
    '本页与原平台的步数或时间不一致');
  state.holds.push({ phase, frame: state.frame, time: material.time, hash: material.hash,
    materialValuesHash: evidence.materialValuesHash, particleStateHash: material.particleStateHash,
    apologyMaterialHash: evidence.apologyMaterialHash, counters: clone(material.counters),
    countersAllGroups: clone(evidence.countersAllGroups) });
  record('held', { phase }); updateUI();
}
function fail(error) {
  if (raf) cancelAnimationFrame(raf); raf = 0; active = null;
  const message = String(error.message || error);
  if (!state.errors.includes(message)) state.errors.push(message);
  state.phase = 'error';
  try { if (bridge && state.handoverCalls) state.handover = clone(bridge.inspect().evidence.handoverReport); }
  catch (readError) { state.errors.push('失败记录读取：' + String(readError.message || readError)); }
  record('error', { message });
  $('loading').hidden = true; $('error').hidden = false;
  $('error').textContent = `本次检查停止：${message}。不移动点位、不重置、不重试。`;
  updateUI(); rejectReady(error);
}
const guard = fn => event => { try { fn(event); } catch (error) { fail(error); } };
function visibleAndFocused() {
  assert(!document.hidden && document.hasFocus(), '检查期间页面隐藏或窗口失焦');
}
function claimButton(id, phase, frame) {
  assert(state.phase === phase && state.frame === frame && !active, '动作顺序或固定帧不符');
  assert(state.buttonCalls[id] === 0, '固定按钮不可重复');
  visibleAndFocused(); state.buttonCalls[id]++; record('button', { id });
}
function ignite(source, group) {
  const world = { x: (source.x - VIEW.width / 2) * Q,
    y: CAMERA.targetY + (VIEW.height / 2 - source.y) * Q, z: 0 };
  const before = research.snapshot({ detail: true });
  const candidates = before.points.filter(p => Math.hypot(p.position[0] - world.x,
    p.position[1] - world.y, p.position[2] - world.z) <= RADIUS);
  const entry = { source, world, radius: RADIUS, intendedGroup: group,
    frameBefore: before.frame, timeBefore: before.time, frameAfter: null, timeAfter: null,
    directCandidateIds: candidates.map(p => p.id), directCandidateGroups: [...new Set(candidates.map(p => p.group))],
    directlyTouchedApology: candidates.some(p => p.group === 'apology'),
    called: false, call: null, newlyLit: null, changedIds: [], passed: false };
  state.ignitions.push(entry);
  assert(candidates.length > 0 && candidates.every(p => p.group === group), '固定点位未命中目标组或误中另一行');
  if (group === 'request') assert(!entry.directlyTouchedApology, '新下行点火半径直接命中旧apology');
  state.ignitionCalls++; entry.call = state.ignitionCalls; entry.called = true;
  entry.newlyLit = demo.ignite(world.x, world.y, world.z, RADIUS);
  const after = research.snapshot({ detail: true }), prior = new Map(before.points.map(p => [p.id, p]));
  entry.changedIds = after.points.filter(p => p.state !== prior.get(p.id).state).map(p => p.id);
  entry.frameAfter = after.frame; entry.timeAfter = after.time;
  assert(Number.isInteger(entry.newlyLit) && entry.newlyLit > 0 && entry.newlyLit === entry.changedIds.length,
    '固定点火没有新增燃烧点或命中记录不一致');
  assert(after.points.every(p => p.state === prior.get(p.id).state || p.group === group), '点火改变了目标组外状态');
  assert(before.frame === after.frame && before.time === after.time
    && before.particleStateHash === after.particleStateHash && before.randomDraws === after.randomDraws
    && same(before.counters, after.counters), '点火意外推进时间、粒子、随机数或累计计数');
  entry.passed = true; record('ignite', { call: entry.call, group, newlyLit: entry.newlyLit });
}
function beginAdvance(target, destination) {
  assert(target <= MAX_STEPS && target > state.frame, '固定步数预算无效');
  active = { from: state.frame, target, destination }; state.phase = 'running'; updateUI();
  raf = requestAnimationFrame(advance);
}
function advance() {
  raf = 0;
  if (!active || state.phase !== 'running') return;
  try {
    visibleAndFocused();
    assert(state.stepCalls < MAX_STEPS && state.frame < active.target, '超出固定步数');
    const expected = state.frame + 1, begin = performance.now();
    state.stepCalls++;
    const raw = research.step(1, DT), simulationMs = performance.now() - begin;
    finite(raw);
    assert(raw.frame === expected && Math.abs(raw.time - expected * DT) < 1e-8, '单步时间或帧不符');
    state.frame = raw.frame; state.costs.stepMs += simulationMs;
    const renderMs = renderMaterial();
    state.costs.steps.push({ frame: state.frame, simulationMs, renderMs,
      particleCount: raw.particles.count, hash: raw.hash, particleStateHash: raw.particleStateHash });
    if (state.frame === active.target) {
      const destination = active.destination;
      if (destination === 'ended') assert(state.resetCalls === 1 && state.ignitionCalls === 2
        && state.stepCalls === 360 && state.handoverCalls === 1
        && Object.values(state.buttonCalls).every(n => n === 1), '终态调用预算不符');
      hold(destination);
    } else { updateUI(); raf = requestAnimationFrame(advance); }
  } catch (error) { fail(error); }
}
$('first').addEventListener('click', guard(() => {
  claimButton('first', 'ready', 0); ignite({ x: 480, y: 276 }, 'apology');
  research.setParams({ spreadOn: true }); beginAdvance(180, 'first-held');
}));
$('handover').addEventListener('click', guard(() => {
  claimButton('handover', 'first-held', 180);
  assert(scene.first.filter(p => p.group === 'apology').every((p, i) => p === scene.apology[i])
    && scene.second.filter(p => p.group === 'apology').every((p, i) => p === scene.apology[i]),
  'apology原始几何对象未复用');
  state.handoverCalls++; const begin = performance.now();
  try { state.handover = clone(bridge.handover(scene.second)); }
  finally { state.costs.handoverMs = performance.now() - begin; }
  assert(state.handover.passed, '继承逐值核对未通过');
  renderMaterial(); hold('handed');
}));
$('later').addEventListener('click', guard(() => {
  claimButton('later', 'handed', 180); ignite({ x: 480, y: 324 }, 'request');
  beginAdvance(270, 'later-held');
}));
$('finish').addEventListener('click', guard(() => {
  claimButton('finish', 'later-held', 270); beginAdvance(360, 'ended');
}));
for (const type of ['blur', 'pagehide']) window.addEventListener(type, () => {
  if (active) fail(new Error(type === 'blur' ? '推进期间窗口失焦，固定检查未完成' : '推进期间离开页面，固定检查未完成'));
});
document.addEventListener('visibilitychange', () => {
  if (active && document.hidden) fail(new Error('推进期间页面隐藏，固定检查未完成'));
});

function fnvBytes(bytes) {
  let h = 2166136261;
  for (const byte of bytes) { h ^= byte; h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(16).padStart(8, '0');
}
async function makeScene() {
  const font = new FontFace('A36Raster', FONT_SOURCE, { weight: '400', style: 'normal' });
  await font.load(); document.fonts.add(font);
  await document.fonts.load(FONT, LINES.map(line => line.text).join(''));
  const byGroup = {}, groups = [];
  for (const line of LINES) {
    const raster = document.createElement('canvas'); raster.width = RASTER.width; raster.height = RASTER.height;
    const ctx = raster.getContext('2d', { willReadFrequently: true });
    ctx.font = FONT; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#ffffff';
    const measured = ctx.measureText(line.text);
    const ink = { left: RASTER.anchorX - measured.actualBoundingBoxLeft,
      right: RASTER.anchorX + measured.actualBoundingBoxRight,
      top: RASTER.anchorY - measured.actualBoundingBoxAscent,
      bottom: RASTER.anchorY + measured.actualBoundingBoxDescent };
    assert([measured.width, ...Object.values(ink)].every(Number.isFinite), line.id + '字形测量不可用');
    assert(RASTER.anchorX + measured.width <= RASTER.width && ink.left >= 0 && ink.right <= RASTER.width
      && ink.top >= 0 && ink.bottom <= RASTER.height, line.id + '超出固定栅格');
    ctx.fillText(line.text, RASTER.anchorX, RASTER.anchorY);
    const pixels = ctx.getImageData(0, 0, RASTER.width, RASTER.height).data, points = [];
    const bounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
    for (let y = 1; y < RASTER.height; y += RASTER.stride) for (let x = 1; x < RASTER.width; x += RASTER.stride) {
      if (pixels[4 * (y * RASTER.width + x) + 3] < RASTER.alphaThreshold) continue;
      bounds.minX = Math.min(bounds.minX, x); bounds.maxX = Math.max(bounds.maxX, x);
      bounds.minY = Math.min(bounds.minY, y); bounds.maxY = Math.max(bounds.maxY, y);
      const sourceX = x + .5, sourceY = line.sourceY + y + .5 - RASTER.anchorY;
      points.push(freeze({ id: `${line.id}:${y}:${x}`, group: line.id,
        position: [(sourceX - VIEW.width / 2) * Q, CAMERA.targetY + (VIEW.height / 2 - sourceY) * Q, RASTER.z],
        fuel: RASTER.fuel, opacity: RASTER.opacity, scale: RASTER.gaussianScale,
        color: [...RASTER.color], areaWeight: null }));
    }
    assert(points.length > 0, line.id + '没有生成材料点');
    byGroup[line.id] = Object.freeze(points);
    groups.push({ ...line, pointCount: points.length, generationCount: 1,
      requestedCanvasFont: FONT, canvasFont: ctx.font, measuredTextWidth: measured.width,
      measuredInkBounds: ink, sampledPixelBounds: bounds, rgbaFNV1a32: fnvBytes(pixels) });
  }
  const first = Object.freeze([...byGroup.apology, ...byGroup.release]);
  const second = Object.freeze([...byGroup.apology, ...byGroup.request]);
  assert(first.length <= 16000 && second.length <= 16000, '固定材料超过16000点，不自动抽稀');
  return { apology: byGroup.apology, first, second, metadata: {
    fontSource: FONT_SOURCE, fontStatus: font.status, requestedFont: FONT, raster: RASTER, camera: CAMERA,
    groups, authoredGroups: byGroup, firstPointCount: first.length, secondPointCount: second.length,
    apologyGeneratedOnce: true, apologyObjectReferencesReused: true,
    sourceCanvasSize: [VIEW.width, VIEW.height], sourcePixelLineSpacing: 48,
    stableOnlyForSameLocalFontAndRasterizer: true,
    outsideFluidXCount: Object.fromEntries(Object.entries(byGroup).map(([g, ps]) => [g, ps.filter(p => Math.abs(p.position[0]) > 1).length]))
  } };
}
Object.defineProperty(window, '__a42', { value: Object.freeze({ ready, snapshot }), writable: false, configurable: false });
const timeout = setTimeout(() => fail(new Error('派生页面或本地字体在20秒内未就绪')), 20000);
async function initialize() {
  if (initialized || state.phase !== 'loading') return;
  initialized = true;
  try {
    const sourceWindow = $('source').contentWindow;
    demo = sourceWindow.__demo; bridge = sourceWindow.__a42LocalBridge;
    assert(demo?.research && bridge?.handover && bridge?.inspect, '本地派生页面或显式桥接接口不可用');
    research = demo.research; sourceCanvas = $('source').contentDocument.querySelector('#cv');
    assert(sourceCanvas, '原渲染器画布缺失');
    scene = await makeScene();
    if (state.phase !== 'loading') return;
    state.geometry = scene.metadata;
    const loaded = research.setScene(scene.first);
    assert(loaded.count === scene.first.length, '初次几何载入点数不符');
    state.resetCalls++; research.reset(SEED, PARAMS);
    demo.forceSize(VIEW.width, VIEW.height); research.camera(CAMERA.yaw);
    const { material, evidence } = read();
    assert(material.frame === 0 && material.time === 0 && same(material.params, PARAMS), '初态时间或完整参数不符');
    assert(material.points.every(p => p.state === 0 && p.heat === 0 && p.glow === 0 && p.char === 0
      && p.fuel === 1 && p.fuelInitial === 1), '初态材料不是完整未燃状态');
    state.initial = { hash: material.hash, particleStateHash: material.particleStateHash,
      materialValuesHash: evidence.materialValuesHash, metadataHash: evidence.metadataHash,
      completeGeometryHash: evidence.completeGeometryHash, apologyMetadataHash: evidence.apologyMetadataHash,
      apologyMaterialHash: evidence.apologyMaterialHash, pointCount: material.points.length };
    renderMaterial(); state.costs.initializationMs = performance.now() - startedAt;
    hold('ready'); $('loading').hidden = true; clearTimeout(timeout); resolveReady(snapshot());
  } catch (error) { clearTimeout(timeout); fail(error); }
}
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) initialize();
