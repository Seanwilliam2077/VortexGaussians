const $ = id => document.getElementById(id);
const origin = performance.now();
const state = { phase: 'loading', door: 'authored_closed_from_inside', viewpoint: 'room',
  authoredDeliveryClaim: 'undelivered', errors: [], events: [] };
let resolveReady, rejectReady;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
ready.catch(() => {});
const clone = value => JSON.parse(JSON.stringify(value));
function record(action) {
  state.events.push({ action, phase: state.phase, elapsedSeconds: (performance.now() - origin) / 1000 });
}
function snapshot() {
  return clone({ ...state, interiorVisible: state.phase === 'room' || state.phase === 'threshold',
    outerShellVisible: state.phase === 'threshold' || state.phase === 'ended',
    staging: 'Authored SVG room and discrete viewpoint/door states. The room remains on the giver side; closure is not receipt.',
    elapsedSeconds: (performance.now() - origin) / 1000 });
}
function fail(error) {
  const message = error instanceof Error ? error.message : String(error);
  state.errors.push(message); state.phase = 'error'; record('error');
  $('error').textContent = '作品在这里停止：' + message + '。本次不自动重试。';
  $('error').hidden = false; $('loading').hidden = true;
  $('to-threshold').disabled = true; $('close-door').disabled = true; $('leave').disabled = false;
  rejectReady(error);
}
function toThreshold() {
  if (state.phase !== 'room') return;
  state.phase = 'threshold'; state.viewpoint = 'outside_threshold';
  state.door = 'authored_open_inward'; record('withdrew_to_threshold');
  $('room').setAttribute('hidden', ''); $('outside').removeAttribute('hidden');
  $('to-threshold').hidden = true; $('close-door').hidden = false;
  $('position').textContent = '门槛之外'; $('room-note').textContent = '这间房尚未送出。';
}
function closeDoor() {
  if (state.phase !== 'threshold') return;
  state.phase = 'ended'; state.door = 'authored_closed_from_inside'; record('door_closed_by_authored_staging');
  $('open-room').setAttribute('hidden', ''); $('closed-door').removeAttribute('hidden');
  $('close-door').hidden = true; $('ended-note').hidden = false;
  $('position').textContent = '门外 · 尚未送出'; $('room-note').textContent = '房间仍在这里。';
  $('leave').textContent = '结束观看';
}
function leave() {
  if (state.phase === 'loading' || state.phase === 'left') return;
  state.phase = 'left'; state.viewpoint = 'no_view'; record('viewer_left');
  $('room').setAttribute('hidden', ''); $('outside').setAttribute('hidden', ''); $('left-place').hidden = false;
  for (const id of ['to-threshold', 'close-door', 'ended-note', 'leave']) $(id).hidden = true;
  $('position').textContent = '观看已结束'; $('room-note').textContent = '';
}
Object.defineProperty(window, '__a22', { value: Object.freeze({ ready, snapshot }), writable: false });
try {
  $('to-threshold').addEventListener('click', toThreshold);
  $('close-door').addEventListener('click', closeDoor);
  $('leave').addEventListener('click', leave);
  state.phase = 'room'; record('room_ready');
  $('loading').hidden = true; $('to-threshold').disabled = false; $('leave').disabled = false;
  resolveReady(snapshot());
} catch (error) { fail(error); }
