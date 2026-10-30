const $ = id => document.getElementById(id);
const DT = 1 / 30, MAX_STEPS = 150, SEED = 20261030;
const state = { phase: 'loading', fireFrame: 0, resetCalls: 0, ignitionCalls: 0,
  emissionStartCalls: 0, door: 'closed_from_inside', viewpoint: 'bed_edge',
  errors: [], events: [], lastMaterialSummary: null, fireStoppedBecause: null };
let demo, research, sourceCanvas, raf = 0, nextDue = 0, initialized = false;
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
const origin = performance.now();
const clone = value => JSON.parse(JSON.stringify(value));
function record(action) { state.events.push({ action, phase: state.phase, fireFrame: state.fireFrame, elapsedSeconds: (performance.now() - origin) / 1000 }); }
function snapshot() {
  return clone({ ...state, fireSimSeconds: state.fireFrame * DT, maxFireSteps: MAX_STEPS,
    source: demo ? { frame: research.snapshot().frame, time: research.snapshot().time,
      parameters: { ...demo.P } } : null,
    staging: 'Authored SVG room and discrete viewpoint/door states; source fire is composited outside, not simulated paper combustion.',
    elapsedSeconds: (performance.now() - origin) / 1000 });
}
function stopFire(reason) { cancelAnimationFrame(raf); raf = 0; if (state.emissionStartCalls && state.fireStoppedBecause === null) state.fireStoppedBecause = reason; }
function fail(error) {
  const message = error instanceof Error ? error.message : String(error);
  stopFire('error'); state.errors.push(message); state.phase = 'error'; record('error');
  $('error').textContent = '作品在这里停止：' + message + '。本次不自动重试。';
  $('error').hidden = false; $('loading').hidden = true;
  for (const id of ['start-fire', 'to-threshold', 'close-door']) $(id).disabled = true;
  $('leave').disabled = false; rejectReady(error);
}
function finite(value) {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error('原平台返回非有限状态');
  if (value && typeof value === 'object') for (const child of Object.values(value)) finite(child);
}
function copyMaterial() {
  demo.render(); demo.gl.finish();
  for (const id of ['fire-inside', 'fire-outside']) {
    const canvas = $(id), ctx = canvas.getContext('2d', { alpha: false });
    ctx.drawImage(sourceCanvas, 0, 0, sourceCanvas.width, sourceCanvas.height, 0, 0, canvas.width, canvas.height);
  }
}
function advanceFire(now) {
  raf = 0;
  if (state.phase !== 'fire') return;
  try {
    if (now >= nextDue && state.fireFrame < MAX_STEPS) {
      state.lastMaterialSummary = research.step(1, DT); state.fireFrame++;
      finite(state.lastMaterialSummary);
      if (state.lastMaterialSummary.frame !== state.fireFrame) throw new Error('外火步数与原平台不一致');
      copyMaterial(); nextDue = performance.now() + 1000 / 30;
    }
    if (state.fireFrame < MAX_STEPS) raf = requestAnimationFrame(advanceFire);
    else { state.fireStoppedBecause = 'fixed_material_limit'; record('material_stopped_at_limit'); }
  } catch (error) { fail(error); }
}
function startFire() {
  if (state.phase !== 'room') return;
  try {
    const params = { solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
      paused: true, orbit: false, yaw: 0, sliceMode: 'world', emitterOn: true,
      spreadOn: false, spreadFlameHeat: false, spreadSceneFeed: false,
      sceneOn: false, box: false, camDist: 4.4, camElev: .12,
      mode: 'fire', exposure: 1, bloom: .65 };
    state.lastMaterialSummary = research.reset(SEED, params); state.resetCalls++;
    state.emissionStartCalls++; state.phase = 'fire'; record('external_fire_started');
    for (const item of document.querySelectorAll('.fire-image')) item.removeAttribute('hidden');
    $('warm-wall').setAttribute('opacity', '1');
    $('start-fire').hidden = true; $('to-threshold').hidden = false;
    $('position').textContent = '房内 · 外面的火'; $('room-note').textContent = '可以再停留一会儿。';
    nextDue = performance.now(); raf = requestAnimationFrame(advanceFire);
  } catch (error) { fail(error); }
}
function toThreshold() {
  if (state.phase !== 'fire') return;
  stopFire('viewer_left_room'); state.phase = 'threshold'; state.viewpoint = 'outside_threshold';
  state.door = 'authored_open_inward'; record('withdrew_to_threshold');
  $('room').setAttribute('hidden', ''); $('outside').removeAttribute('hidden');
  $('to-threshold').hidden = true; $('close-door').hidden = false;
  $('position').textContent = '门槛之外'; $('room-note').textContent = '房间仍在门里。';
}
function closeDoor() {
  if (state.phase !== 'threshold') return;
  state.phase = 'ended'; state.door = 'authored_closed_from_inside'; record('door_closed_by_authored_staging');
  $('open-room').setAttribute('hidden', ''); $('closed-door').removeAttribute('hidden');
  $('close-door').hidden = true; $('ended-note').hidden = false;
  $('position').textContent = '门外'; $('room-note').textContent = '';
  $('leave').textContent = '结束观看';
}
function leave() {
  if (state.phase === 'loading' || state.phase === 'left') return;
  stopFire('viewer_ended_viewing'); state.phase = 'left'; state.viewpoint = 'no_view'; record('viewer_left');
  $('room').setAttribute('hidden', ''); $('outside').setAttribute('hidden', ''); $('left-place').hidden = false;
  for (const id of ['start-fire', 'to-threshold', 'close-door', 'ended-note', 'leave']) $(id).hidden = true;
  $('position').textContent = '观看已结束'; $('room-note').textContent = '';
}
$('start-fire').addEventListener('click', startFire);
$('to-threshold').addEventListener('click', toThreshold);
$('close-door').addEventListener('click', closeDoor);
$('leave').addEventListener('click', leave);
Object.defineProperty(window, '__a20', { value: Object.freeze({ ready, snapshot }), writable: false });
const timeout = setTimeout(() => fail(new Error('本地外火渲染器在20秒内未就绪')), 20000);
function initialize() {
  if (initialized || state.phase !== 'loading') return;
  try {
    demo = $('source').contentWindow.__demo;
    if (!demo?.research) throw new Error('原平台渲染器不可用，请通过仓库HTTP服务打开');
    research = demo.research; sourceCanvas = $('source').contentDocument.querySelector('#cv');
    if (!sourceCanvas) throw new Error('原平台画布缺失');
    demo.P.paused = true; demo.forceSize(640, 480);
    initialized = true; state.phase = 'room'; record('room_ready');
    $('loading').hidden = true; $('start-fire').disabled = false; $('leave').disabled = false;
    clearTimeout(timeout); resolveReady(snapshot());
  } catch (error) { clearTimeout(timeout); fail(error); }
}
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) initialize();
window.addEventListener('pagehide', () => stopFire('page_hidden'));
