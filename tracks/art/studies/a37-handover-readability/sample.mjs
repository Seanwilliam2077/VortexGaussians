const $ = id => document.getElementById(id);
const SEED = 20261031;
const VIEW = Object.freeze({ width: 1200, height: 600 });
const CAMERA = Object.freeze({ yaw: 0, elevation: 0, distance: 3.4, fov: .85, targetY: 1.05 });
const FONT_SOURCE = 'local("Microsoft YaHei")';
// Keep A36's font alias and raster construction unchanged for direct comparison.
const FONT = '400 32px "A36Raster"';
const WORLD_PER_PIXEL = 2 * CAMERA.distance * Math.tan(CAMERA.fov / 2) / VIEW.height;
const RASTER = Object.freeze({ width: 1200, height: 96, anchorX: 280, anchorY: 48,
  stride: 2, alphaThreshold: 128, worldPerPixel: WORLD_PER_PIXEL, z: 0,
  gaussianScale: WORLD_PER_PIXEL, opacity: .94, color: [.82, .78, .67], fuel: 1 });
const LINES = Object.freeze([
  { id: 'line3', label: '第三行', text: '时刻表不要摘，明早第一班仍是六点四十。', sourceY: 300 },
  { id: 'line4', label: '第四行', text: '若有人问今晚还能不能走，先把今晚那一行念完，再把门打开。', sourceY: 348 }
]);
const TARGET = Object.freeze({ id: 'do-not-remove', label: '不要摘', line: 'line3', startIndex: 3, endIndexExclusive: 6 });
const PARAMS = Object.freeze({ solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
  paused: true, orbit: false, yaw: CAMERA.yaw, camElev: CAMERA.elevation, camDist: CAMERA.distance, fov: CAMERA.fov,
  sliceMode: 'world', emitterOn: false, spreadOn: false,
  spreadFlameHeat: true, spreadSceneFeed: true, spreadClockMode: 'legacy',
  spreadParticlePolicy: 'block', spreadMeasureMode: 'legacy',
  spreadFrontierCap: 1400, spreadSampleCap: 160, spreadFeedCap: 48,
  sceneOn: true, sceneMax: 8000, sceneScale: 1, sceneSH: 0,
  sceneYaw: 0, scenePitch: 0, sceneLift: 0, sceneOffX: 0, sceneOffZ: 0, box: false });
const state = { phase: 'loading', resetCalls: 0, ignitionCalls: 0, stepCalls: 0,
  pointCount: 0, geometry: null, errors: [], events: [] };
const targetPointIds = new Set();
let demo, research, sourceCanvas, initialized = false;
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
const wallStart = performance.now();
const clone = value => JSON.parse(JSON.stringify(value));
function record(action) {
  state.events.push({ action, phase: state.phase, elapsedSeconds: (performance.now() - wallStart) / 1000 });
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
      fuelDepleted: points.filter(p => p.state === 2).length,
      other: points.filter(p => ![0, 1, 2].includes(p.state)).length } };
}
function readMaterial() {
  if (!research || !state.resetCalls) return null;
  const raw = research.snapshot({ detail: true });
  finite(raw);
  const groups = Object.fromEntries(LINES.map(line => [line.id, { label: line.label,
    ...summarizePoints(raw.points.filter(p => p.group === line.id)) }]));
  const subgroups = { [TARGET.id]: { label: TARGET.label, parentGroup: TARGET.line,
    overlapsParent: true, ...summarizePoints(raw.points.filter(p => targetPointIds.has(p.id))) } };
  const total = summarizePoints(raw.points);
  const initialState = { frameZero: raw.frame === 0, timeZero: raw.time === 0,
    zeroBurning: total.stateCounts.burning === 0,
    fuelLoss: raw.points.reduce((sum, p) => sum + p.fuelInitial - p.fuel, 0),
    unchangedFuelCount: raw.points.filter(p => p.fuel === p.fuelInitial).length,
    allUnburned: total.stateCounts.unburned === raw.points.length };
  return { frame: raw.frame, time: raw.time, seed: raw.seed, hash: raw.hash,
    particleStateHash: raw.particleStateHash, scene: raw.scene, total, groups, subgroups, initialState,
    particles: raw.particles, counters: raw.counters, countersByGroup: raw.countersByGroup,
    params: raw.params, randomDraws: raw.randomDraws };
}
function snapshot() {
  const material = readMaterial();
  return clone({ ...state, frame: material?.frame ?? null, simSeconds: material?.time ?? null, seed: SEED,
    groups: material?.groups ?? null, subgroups: material?.subgroups ?? null,
    total: material?.total ?? null, counters: material?.counters ?? null,
    initialState: material?.initialState ?? null, hash: material?.hash ?? null,
    material, elapsedSeconds: (performance.now() - wallStart) / 1000,
    sourceCanvasSize: [sourceCanvas?.width ?? null, sourceCanvas?.height ?? null],
    materialDifference: { base: 'A36', property: 'Gaussian scale', previous: .0102, current: WORLD_PER_PIXEL,
      pointConstruction: 'same IDs, order and positions; compare raster metadata on the same font/rasterizer' },
    scope: 'Initial state only. Two material-text lines; subgroup overlaps line3 and is never added to total.' });
}
function fail(error) {
  const message = error instanceof Error ? error.message : String(error);
  if (!state.errors.includes(message)) state.errors.push(message);
  state.phase = 'error'; record('error');
  $('loading').hidden = true; $('error').hidden = false;
  $('error').textContent = '本次初态检查停止：' + message + '。不自动重试。';
  $('phase-text').textContent = '执行停止';
  rejectReady(error);
}
function showStats(material) {
  $('phase-text').textContent = '初始材料字 · 停留';
  $('time-readout').textContent = `${material.frame} 步 / ${material.time.toFixed(2)} 模拟秒`;
  $('stats-caption').textContent = `共 ${state.pointCount.toLocaleString()} 个字形点；Gaussian scale = ${WORLD_PER_PIXEL.toPrecision(10)}。`;
  const fragment = document.createDocumentFragment();
  for (const g of [...LINES.map(line => material.groups[line.id]), material.subgroups[TARGET.id]]) {
    const row = document.createElement('tr');
    const percent = g.fuelInitial.sum ? 100 * g.fuel.sum / g.fuelInitial.sum : 0;
    for (const text of [g.label + (g.overlapsParent ? '（子组）' : ''), String(g.count),
      g.heat.mean.toFixed(3), `${percent.toFixed(1)}%`, `${g.stateCounts.burning} / ${g.stateCounts.fuelDepleted}`]) {
      const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
    }
    fragment.appendChild(row);
  }
  $('group-rows').replaceChildren(fragment);
  $('initial-readout').textContent = `reset ${state.resetCalls} 次；点火 ${state.ignitionCalls} 次；推进 ${state.stepCalls} 次；燃料减少量 ${material.initialState.fuelLoss}。`;
}
function renderMaterial() {
  demo.render(); demo.gl.finish();
  if (sourceCanvas.width !== VIEW.width || sourceCanvas.height !== VIEW.height)
    throw new Error('源画布尺寸不是固定1200×600');
  const canvas = $('view'), ctx = canvas.getContext('2d', { alpha: false });
  ctx.drawImage(sourceCanvas, 0, 0, sourceCanvas.width, sourceCanvas.height, 0, 0, canvas.width, canvas.height);
}
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
  if (points.length > 8000) throw new Error(`字形点数${points.length}超过8000，不自动抽稀`);
  if (!targetPointIds.size) throw new Error('固定字符区间“不要摘”没有生成字形点');
  return { points, metadata: { fontSource: FONT_SOURCE, fontStatus: font.status,
    requestedFont: FONT, raster: RASTER, camera: CAMERA, groups, pointCount: points.length,
    target: { ...TARGET, ...targetBounds, pointCount: targetPointIds.size, attribution: 'sample centers in fixed character-prefix bounds; subset of line3' },
    sourceCanvasSize: [VIEW.width, VIEW.height], sourcePixelLineSpacing: 48,
    outsideFluidXCount: points.filter(p => Math.abs(p.position[0]) > 1).length,
    stableOnlyForSameLocalFontAndRasterizer: true } };
}
Object.defineProperty(window, '__a37', { value: Object.freeze({ ready, snapshot }), writable: false, configurable: false });
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
    demo.forceSize(VIEW.width, VIEW.height); research.camera(CAMERA.yaw);
    renderMaterial();
    const material = readMaterial(), initial = material.initialState;
    if (!initial.frameZero || !initial.timeZero || !initial.zeroBurning || !initial.allUnburned
      || initial.fuelLoss !== 0 || initial.unchangedFuelCount !== state.pointCount)
      throw new Error('原平台状态不是未点火、零推进、零燃料损失的初态');
    state.phase = 'ready'; showStats(material); record('ready');
    $('loading').hidden = true; clearTimeout(initializationTimeout); resolveReady(snapshot());
  } catch (error) { clearTimeout(initializationTimeout); fail(error); }
}
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) initialize();
