const $ = id => document.getElementById(id);
const SEED = 20261030, DT = 1 / 30, SOURCE_FRAMES = 150, DURATION = 22;
const SOURCE_SIZE = Object.freeze({ width: 640, height: 480 });
const VIEW_SIZE = Object.freeze({ width: 720, height: 720 });
const BITMAP_BYTES = 640 * 480 * 4, CACHE_LIMIT = 192 * 1024 * 1024;
const PNG_LIMIT = 8 * 1024 * 1024, VIDEO_LIMIT = 16 * 1024 * 1024;
const MIME = 'video/webm;codecs=vp9';
// Exactly A20 startFire's overrides; research.reset supplies its original defaults.
const PARAMS = Object.freeze({ solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 160,
  paused: true, orbit: false, yaw: 0, sliceMode: 'world', emitterOn: true,
  spreadOn: false, spreadFlameHeat: false, spreadSceneFeed: false,
  sceneOn: false, box: false, camDist: 4.4, camElev: .12,
  mode: 'fire', exposure: 1, bloom: .65 });
const TARGETS = [2, 4, 6, 8, 10, 22];
const FREEZES = Object.freeze([
  { side: 'top', threshold: 4, sourceFrame: 60 },
  { side: 'right', threshold: 6, sourceFrame: 90 },
  { side: 'bottom', threshold: 8, sourceFrame: 120 },
  { side: 'left', threshold: 10, sourceFrame: 150 }
]);
const SIDES = ['top', 'right', 'bottom', 'left'];
const ROTATIONS = Object.freeze([{ side: 'bottom', radians: 0 }, { side: 'left', radians: Math.PI / 2 },
  { side: 'top', radians: Math.PI }, { side: 'right', radians: 3 * Math.PI / 2 }]);
const copy = value => JSON.parse(JSON.stringify(value));
const freeze = value => {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
};
const assert = (ok, message) => { if (!ok) throw new Error(message); };
const same = (a, b) => {
  if (typeof a !== typeof b) return false;
  if (a === null || b === null || typeof a !== 'object') return Object.is(a, b);
  const keys = Object.keys(a);
  return Array.isArray(a) === Array.isArray(b) && keys.length === Object.keys(b).length
    && keys.every(k => Object.hasOwn(b, k) && same(a[k], b[k]));
};
function finite(value) {
  if (typeof value === 'number') assert(Number.isFinite(value), '原平台返回非有限值');
  else if (value && typeof value === 'object') Object.values(value).forEach(finite);
}
const origin = performance.now(), wall = () => performance.now() - origin;
const canvas = $('view'), ctx = canvas.getContext('2d', { alpha: false, willReadFrequently: true });
const state = {
  phase: 'loading', preparationCalls: 0, resetCalls: 0, stepCalls: 0, ignitionCalls: 0,
  renderCalls: 0, bitmapCalls: 0, playCalls: 0, pauseCalls: 0, leaveCalls: 0,
  presentationCalls: 0, compositeCalls: 0, captureCalls: 0, artifactsReady: false,
  seed: SEED, dt: DT, sourceFrameLimit: SOURCE_FRAMES, intendedDurationSeconds: DURATION,
  geometry: { source: SOURCE_SIZE, view: VIEW_SIZE, sourceScale: 1.125,
    baseImageRect: [0, 180, 720, 540], baseClip: [[0, 720], [720, 720], [480, 480], [240, 480]],
    rotationCenter: [360, 360], clockwiseDrawingOrder: ['bottom:0', 'left:90', 'top:180', 'right:270'],
    centerBlackRect: [240, 240, 240, 240] },
  requestedParams: PARAMS, sourceInitial: null, sourceAfterPreparation: null, sourceAfterPresentation: null,
  sourceParams: null, sourceUnchangedDuringPresentation: null,
  preparation: { startedWallMs: null, endedWallMs: null, wallMs: null, complete: false, aborted: false, stopReason: null,
    framesReady: 0, bitmapInFlight: false, steps: [], stepMs: 0, renderMs: 0, copyMs: 0, bitmapMs: 0, yieldMs: 0 },
  memory: { sourceBitmapSetNominalBytes: SOURCE_FRAMES * BITMAP_BYTES, stagingNominalBytes: BITMAP_BYTES,
    persistentCacheNominalBytes: (SOURCE_FRAMES + 1) * BITMAP_BYTES, cacheLimitBytes: CACHE_LIMIT,
    sourceCanvasNominalBytes: BITMAP_BYTES, outputCanvasNominalBytes: 720 * 720 * 4,
    maximumSinglePixelReadBytes: 720 * 720 * 4,
    note: 'Nominal RGBA surfaces only; not measured process/GPU/encoder peak memory. One reusable staging canvas, no second frame set.' },
  playback: { startedWallMs: null, firstCompositeWallMs: null, lastCompositeWallMs: null,
    endedWallMs: null, actualWallMs: null, activeWallMs: null, pausedWallMs: 0,
    currentSeconds: 0, terminalActualSeconds: null, terminalOverrunSeconds: null,
    sourceFrames: null, pauses: [], stopReason: null, continuousHumanViewingClaimed: false },
  displayLog: [], missedIntervals: [], freezes: FREEZES.map(f => ({ ...f, observed: false })),
  captures: TARGETS.map(t => ({ targetSeconds: t, status: 'pending' })),
  center: { rectangle: [240, 240, 240, 240], checks: 0, pixelsChecked: 0, nonBlackPixels: 0,
    allPureBlack: true, lastCheck: null },
  terminalPixels: { tenSeconds: null, twentyTwoSeconds: null, equal: null },
  costs: { compositeMs: 0, centerCheckMs: 0, pngEncodingWallMs: 0, pngBytes: 0, recordedChunkBytes: 0 },
  recording: { attempts: 0, requestedMime: MIME, supported: null, actualMime: null, status: 'not-attempted',
    requestedBitsPerSecond: 2000000, requestedCaptureFPS: 30, startedWallMs: null, stopRequestedWallMs: null,
    stoppedWallMs: null, recordWallMs: null, pausedWallMs: 0, chunks: [], bytes: 0, observedBytes: 0,
    encoded: false, recordedBlobReady: false, metadata: null, events: [], errors: [],
    audioTracks: 0, trackSettings: null, trackStatesAtClose: [], continuousPlaybackObserved: false },
  cleanup: { requested: false, reason: null, ownRAFOutstanding: false, bitmapsCreated: 0,
    bitmapsClosed: 0, bitmapLiveCount: 0, stagingReleased: false, sourceDetached: false,
    streamTracksStopped: false, recorderStateAtClose: null, complete: false },
  errors: [], events: [], terminalDestination: null
};
let demo = null, research = null, sourceCanvas = null, staging = null, stagingCtx = null;
let frames = [], raf = 0, initialized = false, cancelled = false, shutdownPromise = null;
let playStart = null, pauseStart = null, pausedTotal = 0;
let recorder = null, stream = null, chunks = [], recorderStopPromise = null, resolveRecorderStop = null;
let recordingFailure = null, recordingSettled = false, stopRequested = false;
let imageArtifacts = [], videoArtifact = null;
const capturePromises = [];
let resolveReady, rejectReady, resolvePreparationFinished;
const ready = new Promise((resolve, reject) => { resolveReady = resolve; rejectReady = reject; });
const preparationFinished = new Promise(resolve => { resolvePreparationFinished = resolve; });
ready.catch(() => {});
function record(action, extra = {}) { state.events.push({ action, wallMs: wall(), phase: state.phase, ...extra }); }
function mediaEvent(action, extra = {}) { state.recording.events.push({ action, wallMs: wall(), ...extra }); }
function addError(scope, error) {
  const message = `${scope}: ${String(error.message || error)}`;
  state.errors.push(message); record('error', { scope, message }); return message;
}
function materialNow() {
  return research ? research.snapshot({ detail: true }) : state.sourceAfterPresentation || state.sourceAfterPreparation || state.sourceInitial;
}
function snapshot() {
  let material = null, snapshotError = null;
  try { material = materialNow(); } catch (error) { snapshotError = String(error.message || error); }
  // Reads only. Wall-clock times are recorded by actual actions, not by inspection.
  return freeze(copy({ ...state, material, snapshotError,
    frame: material?.frame ?? 0, hash: material?.hash ?? null,
    particleStateHash: material?.particleStateHash ?? null,
    images: imageArtifacts.map(({ dataURL, ...identity }) => identity),
    video: videoArtifact ? (({ base64, ...identity }) => identity)(videoArtifact) : null }));
}
function artifacts() {
  // No draw, source access, encoding, recording, fetch or clock read here.
  return freeze(copy({ artifactsReady: state.artifactsReady, images: imageArtifacts,
    video: videoArtifact, captureRecords: state.captures, recordingStatus: state.recording.status }));
}
function updateUI() {
  const text = { loading: '正在准备影像。', preparing: '正在准备影像。', ready: '可以播放。',
    playing: '', paused: '已暂停。', finalizing: '呈示已停止。', ended: '呈示结束。',
    left: '观看到这里。', error: '本次呈示停止。' };
  $('status').textContent = text[state.phase] ?? '';
  $('play').textContent = state.phase === 'paused' ? '继续' : '播放';
  $('play').disabled = !['ready', 'paused'].includes(state.phase);
  $('pause').disabled = state.phase !== 'playing';
  $('leave').disabled = ['left', 'finalizing'].includes(state.phase);
  if (state.errors.length) { $('error').hidden = false; $('error').textContent = '本次呈示遇到错误，记录已经保留，不自动重试。'; }
}
function sourceFramesAt(t) {
  const current = Math.min(150, 1 + Math.floor(15 * Math.max(0, t)));
  return { top: t >= 4 ? 60 : current, right: t >= 6 ? 90 : current,
    bottom: t >= 8 ? 120 : current, left: t >= 10 ? 150 : current };
}
function contentSeconds(now = performance.now()) {
  if (playStart === null) return 0;
  return Math.max(0, ((pauseStart ?? now) - playStart - pausedTotal) / 1000);
}
function fnv(bytes) {
  let h = 2166136261;
  for (const b of bytes) { h ^= b; h = Math.imul(h, 16777619); }
  return (h >>> 0).toString(16).padStart(8, '0');
}
async function sha256(bytes) {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v => v.toString(16).padStart(2, '0')).join('');
}
function base64(bytes) {
  const parts = [];
  for (let i = 0; i < bytes.length; i += 32768) parts.push(String.fromCharCode(...bytes.subarray(i, i + 32768)));
  return btoa(parts.join(''));
}
function checkCenter(sequence, seconds) {
  const begin = performance.now(), pixels = ctx.getImageData(240, 240, 240, 240).data;
  let bad = 0;
  for (let i = 0; i < pixels.length; i += 4)
    if (pixels[i] !== 0 || pixels[i + 1] !== 0 || pixels[i + 2] !== 0 || pixels[i + 3] !== 255) bad++;
  const ms = performance.now() - begin;
  state.center.checks++; state.center.pixelsChecked += 240 * 240; state.center.nonBlackPixels += bad;
  state.center.allPureBlack &&= bad === 0;
  state.center.lastCheck = { sequence, actualSeconds: seconds, nonBlackPixels: bad, checkMs: ms };
  state.costs.centerCheckMs += ms;
  assert(bad === 0, '中央240×240区域不是纯黑不透明像素');
  return { nonBlackPixels: bad, checkMs: ms };
}
function logMissed(previous, current) {
  if (!previous) return;
  for (const side of SIDES) {
    const from = previous.sourceFrames[side], to = current.sourceFrames[side];
    if (to > from + 1) state.missedIntervals.push({ side, afterComposite: previous.sequence,
      beforeComposite: current.sequence, fromSourceFrame: from + 1, toSourceFrame: to - 1,
      count: to - from - 1, idealStartSeconds: from / 15, idealEndSeconds: (to - 1) / 15,
      previousActualSeconds: previous.actualSeconds, nextActualSeconds: current.actualSeconds,
      meaning: 'No normal canvas composite selected these source indices for this side.' });
  }
}
function captureCanvas(target, entry) {
  state.captureCalls++;
  const pixels = ctx.getImageData(0, 0, 720, 720).data, pixelHash = fnv(pixels);
  const file = `${String(TARGETS.indexOf(target.targetSeconds) + 1).padStart(2, '0')}-${target.targetSeconds}s.png`;
  Object.assign(target, { status: 'encoding', file, actualSeconds: entry.actualSeconds,
    lateBySeconds: entry.actualSeconds - target.targetSeconds, compositeSequence: entry.sequence,
    capturedWallMs: wall(), captureInvokedSeconds: contentSeconds(),
    drawCompletedSeconds: entry.drawCompletedSeconds, sourceFrames: { ...entry.sourceFrames }, pixelHash,
    width: 720, height: 720, encodingEndedWallMs: null });
  target.captureLateBySeconds = target.captureInvokedSeconds - target.targetSeconds;
  if (target.targetSeconds === 10) state.terminalPixels.tenSeconds = { pixelHash, compositeSequence: entry.sequence, actualSeconds: entry.actualSeconds };
  if (target.targetSeconds === 22) state.terminalPixels.twentyTwoSeconds = { pixelHash, compositeSequence: entry.sequence, actualSeconds: entry.actualSeconds };
  if (state.terminalPixels.tenSeconds && state.terminalPixels.twentyTwoSeconds)
    state.terminalPixels.equal = state.terminalPixels.tenSeconds.pixelHash === state.terminalPixels.twentyTwoSeconds.pixelHash;
  // toBlob snapshots this normal canvas now; callbacks never redraw a target state.
  const promise = new Promise((resolve, reject) => {
    canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('PNG编码返回空数据')), 'image/png');
  }).then(async blob => {
    assert(state.costs.pngBytes + blob.size <= PNG_LIMIT, '六图累计PNG超出8MiB，拒绝保存额外图');
    state.costs.pngBytes += blob.size;
    const bytes = new Uint8Array(await blob.arrayBuffer()), identity = await sha256(bytes);
    Object.assign(target, { status: 'saved', bytes: blob.size, sha256: identity, encodingEndedWallMs: wall() });
    state.costs.pngEncodingWallMs += target.encodingEndedWallMs - target.capturedWallMs;
    imageArtifacts.push({ file, targetSeconds: target.targetSeconds, actualSeconds: target.actualSeconds,
      lateBySeconds: target.lateBySeconds, sourceFrames: { ...target.sourceFrames },
      compositeSequence: entry.sequence, capturedWallMs: target.capturedWallMs,
      captureInvokedSeconds: target.captureInvokedSeconds, captureLateBySeconds: target.captureLateBySeconds,
      drawCompletedSeconds: entry.drawCompletedSeconds,
      width: 720, height: 720, bytes: blob.size, sha256: identity, pixelHash,
      mime: 'image/png', dataURL: 'data:image/png;base64,' + base64(bytes) });
    imageArtifacts.sort((a, b) => a.targetSeconds - b.targetSeconds);
  }).catch(error => { target.status = 'failed'; target.error = addError('PNG', error); target.encodingEndedWallMs = wall(); });
  capturePromises.push(promise);
}
function considerTargets(entry) {
  const reached = state.captures.filter(t => t.status === 'pending' && t.targetSeconds <= entry.actualSeconds);
  if (!reached.length) return;
  for (const target of reached.slice(0, -1)) Object.assign(target, { status: 'missing',
    reason: 'multiple-targets-crossed-in-one-normal-composite', detectedAtSeconds: entry.actualSeconds,
    compositeSequence: entry.sequence, sourceFrames: { ...entry.sourceFrames } });
  captureCanvas(reached.at(-1), entry);
}
function composite(now, rafTimestamp, trigger) {
  const begin = performance.now(), seconds = contentSeconds(now), selected = sourceFramesAt(seconds);
  assert(frames.length === SOURCE_FRAMES, '呈示时源帧集不完整');
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 720, 720);
  for (const region of ROTATIONS) {
    ctx.save(); ctx.translate(360, 360); ctx.rotate(region.radians); ctx.translate(-360, -360);
    ctx.beginPath(); ctx.moveTo(0, 720); ctx.lineTo(720, 720); ctx.lineTo(480, 480); ctx.lineTo(240, 480);
    ctx.closePath(); ctx.clip();
    ctx.drawImage(frames[selected[region.side] - 1], 0, 180, 720, 540); ctx.restore();
  }
  ctx.fillStyle = '#000'; ctx.fillRect(240, 240, 240, 240);
  const drawCompleted = performance.now();
  const sequence = ++state.compositeCalls;
  const center = checkCenter(sequence, seconds);
  const previous = state.displayLog.at(-1);
  const entry = { sequence, trigger, wallMs: now - origin, rafTimestampMs: rafTimestamp,
    actualSeconds: seconds, idealUnfrozenSourceFrame: Math.min(150, 1 + Math.floor(15 * seconds)),
    secondsSincePreviousComposite: previous ? seconds - previous.actualSeconds : null,
    sourceFrames: selected, center, drawCompletedWallMs: drawCompleted - origin,
    drawCompletedSeconds: contentSeconds(drawCompleted), compositeMs: performance.now() - begin,
    actualSecondsMeaning: 'Actual callback/composition selection time; not requested deadline or display scanout.',
    browserCallbackNotDisplayScanout: true };
  logMissed(previous, entry);
  for (const item of state.freezes) if (!item.observed && seconds >= item.threshold) {
    Object.assign(item, { observed: true, compositeSequence: sequence, actualSeconds: seconds,
      lateBySeconds: seconds - item.threshold, wallMs: entry.wallMs,
      previousDisplayedSourceFrame: previous?.sourceFrames[item.side] ?? null,
      requiredFramePreviouslyComposited: state.displayLog.some(e => e.sourceFrames[item.side] === item.sourceFrame) });
  }
  state.displayLog.push(entry); state.costs.compositeMs += entry.compositeMs;
  state.playback.firstCompositeWallMs ??= entry.wallMs;
  state.playback.lastCompositeWallMs = entry.wallMs;
  state.playback.currentSeconds = seconds; state.playback.sourceFrames = selected;
  considerTargets(entry);
  return seconds;
}
function nextRAF() {
  raf = requestAnimationFrame(tick); state.cleanup.ownRAFOutstanding = true;
}
function tick(timestamp) {
  raf = 0; state.cleanup.ownRAFOutstanding = false;
  if (state.phase !== 'playing' || cancelled) return;
  try {
    assert(!document.hidden && document.hasFocus(), '呈示期间页面隐藏或窗口失焦');
    const seconds = composite(performance.now(), timestamp, 'requestAnimationFrame');
    if (seconds >= DURATION) void terminate('fixed-22-second-end', 'ended');
    else nextRAF();
  } catch (error) { addError('presentation', error); void terminate('presentation-error', 'error'); }
}

function stopStream() {
  if (stream) {
    for (const track of stream.getTracks()) track.stop();
    state.recording.trackStatesAtClose = stream.getTracks().map(t => ({ kind: t.kind, readyState: t.readyState }));
  }
  state.cleanup.streamTracksStopped = !stream || stream.getTracks().every(t => t.readyState === 'ended');
}
function stopRecording(reason) {
  if (stopRequested) return;
  stopRequested = true;
  if (state.recording.attempts && recorder) {
    state.recording.stopRequestedWallMs = wall(); mediaEvent('stop-requested', { reason, recorderState: recorder.state });
    if (!recordingFailure) state.recording.status = 'stopping';
    try { if (recorder.state !== 'inactive') recorder.stop(); }
    catch (error) { state.recording.errors.push(String(error.message || error)); recordingFailure ??= 'stop-error'; resolveRecorderStop?.(); }
  }
  stopStream(); state.cleanup.recorderStateAtClose = recorder?.state ?? null;
}
function startRecording() {
  state.recording.attempts++;
  try {
    state.recording.supported = typeof MediaRecorder !== 'undefined'
      && typeof canvas.captureStream === 'function' && MediaRecorder.isTypeSupported(MIME);
    if (!state.recording.supported) { state.recording.status = 'unsupported'; mediaEvent('unsupported'); recordingSettled = true; return; }
    stream = canvas.captureStream(30);
    state.recording.audioTracks = stream.getAudioTracks().length;
    assert(state.recording.audioTracks === 0, '记录轨道必须静默');
    state.recording.trackSettings = stream.getVideoTracks().map(track => track.getSettings());
    recorder = new MediaRecorder(stream, { mimeType: MIME, videoBitsPerSecond: 2000000 });
    state.recording.actualMime = recorder.mimeType;
    recorderStopPromise = new Promise(resolve => { resolveRecorderStop = resolve; });
    recorder.addEventListener('start', () => { if (!recordingSettled) mediaEvent('start'); });
    recorder.addEventListener('pause', () => { if (!recordingSettled) mediaEvent('pause'); });
    recorder.addEventListener('resume', () => { if (!recordingSettled) mediaEvent('resume'); });
    recorder.addEventListener('dataavailable', event => {
      if (recordingSettled) return;
      const bytes = event.data.size; state.recording.observedBytes += bytes; state.costs.recordedChunkBytes += bytes;
      state.recording.chunks.push({ bytes, wallMs: wall(), timecode: Number.isFinite(event.timecode) ? event.timecode : null });
      if (state.recording.observedBytes > VIDEO_LIMIT) {
        recordingFailure = 'size-limit'; state.recording.errors.push('WebM超过16MiB；不导出超限或残缺替代品');
        chunks = []; stopRecording('video-size-limit');
      } else if (!recordingFailure && bytes > 0) chunks.push(event.data);
    });
    recorder.addEventListener('error', event => {
      if (recordingSettled) return;
      recordingFailure = 'encoder-error'; state.recording.errors.push(String(event.error?.message || 'MediaRecorder error'));
      mediaEvent('error'); stopRecording('encoder-error');
    });
    recorder.addEventListener('stop', () => {
      if (recordingSettled) return;
      state.recording.stoppedWallMs = wall(); mediaEvent('stop'); resolveRecorderStop?.();
    });
    state.recording.startedWallMs = wall(); state.recording.status = 'recording';
    recorder.start(1000); mediaEvent('start-requested', { recorderState: recorder.state });
  } catch (error) {
    state.recording.errors.push(String(error.message || error)); recordingFailure = 'start-error';
    state.recording.status = 'failed'; stopRecording('start-error'); recordingSettled = true;
  }
}
async function settleWithTimeout(promise, ms, message) {
  let timer;
  try { return await Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(message)), ms); })]); }
  finally { clearTimeout(timer); }
}
async function mediaMetadata(blob) {
  const video = document.createElement('video'), url = URL.createObjectURL(blob);
  let active = true;
  video.preload = 'auto'; video.muted = true; video.playsInline = true;
  const result = { status: 'waiting', width: null, height: null, durationSeconds: null,
    durationRaw: null, decodedFirstFrame: false, continuousViewing: false,
    note: 'Metadata/first-frame decode only. This element is never played.', playbackQuality: null, error: null };
  const read = () => {
    if (!active) return;
    result.width = video.videoWidth; result.height = video.videoHeight;
    result.durationSeconds = Number.isFinite(video.duration) ? video.duration : null;
    result.durationRaw = String(video.duration);
    if (typeof video.getVideoPlaybackQuality === 'function') {
      const q = video.getVideoPlaybackQuality();
      result.playbackQuality = { totalVideoFrames: q.totalVideoFrames, droppedVideoFrames: q.droppedVideoFrames,
        corruptedVideoFrames: q.corruptedVideoFrames ?? null,
        note: 'Read from an unplayed metadata probe; not a measurement of the live canvas presentation.' };
    }
  };
  try {
    const loaded = new Promise((resolve, reject) => {
      video.addEventListener('loadedmetadata', () => { if (active) { read(); result.status = 'metadata-loaded'; } }, { once: true });
      video.addEventListener('loadeddata', () => { if (active) { read(); result.status = 'first-frame-decoded'; result.decodedFirstFrame = true; resolve(); } }, { once: true });
      video.addEventListener('error', () => { if (active) reject(new Error(video.error?.message || 'WebM metadata/decode error')); }, { once: true });
    });
    video.src = url; video.load(); await settleWithTimeout(loaded, 3000, 'WebM metadata/decode timeout');
  } catch (error) { result.error = String(error.message || error); if (result.status === 'waiting') result.status = 'unavailable'; }
  finally { active = false; video.removeAttribute('src'); video.load(); URL.revokeObjectURL(url); }
  return result;
}
async function finishRecording() {
  if (!state.recording.attempts || recordingSettled) { chunks = []; recorder = null; stream = null; return; }
  try {
    await settleWithTimeout(recorderStopPromise, 6000, 'MediaRecorder stop timeout');
    state.recording.recordWallMs = (state.recording.stoppedWallMs ?? wall()) - state.recording.startedWallMs;
    if (recordingFailure) throw new Error(recordingFailure);
    const recordedBlob = new Blob(chunks, { type: state.recording.actualMime || MIME }); chunks = [];
    state.recording.recordedBlobReady = true; state.recording.status = 'blob-ready'; state.recording.bytes = recordedBlob.size;
    assert(recordedBlob.size > 0 && recordedBlob.size <= VIDEO_LIMIT, 'WebM为空或超过16MiB');
    state.recording.status = 'encoding-artifact';
    const bytes = new Uint8Array(await recordedBlob.arrayBuffer()), identity = await sha256(bytes);
    state.recording.encoded = true; state.recording.status = 'probing-metadata';
    state.recording.metadata = await mediaMetadata(recordedBlob);
    videoArtifact = { file: 'normal-presentation.webm', mime: recordedBlob.type,
      bytes: recordedBlob.size, sha256: identity, base64: base64(bytes), metadata: copy(state.recording.metadata),
      requestedWidth: 720, requestedHeight: 720, startedWallMs: state.recording.startedWallMs,
      stoppedWallMs: state.recording.stoppedWallMs, recordWallMs: state.recording.recordWallMs,
      pausedWallMs: state.recording.pausedWallMs, terminalContentSeconds: state.playback.terminalActualSeconds };
    state.recording.status = 'complete'; mediaEvent('artifact-ready', { bytes: recordedBlob.size, sha256: identity });
  } catch (error) {
    state.recording.errors.push(String(error.message || error)); state.recording.status = 'failed'; chunks = [];
  } finally {
    recordingSettled = true; stopStream(); state.cleanup.recorderStateAtClose = recorder?.state ?? null;
    recorder = null; stream = null; resolveRecorderStop = null;
  }
}

function releaseBitmaps() {
  for (const bitmap of frames) { bitmap.close(); state.cleanup.bitmapsClosed++; }
  frames = []; state.cleanup.bitmapLiveCount = 0;
  if (staging) { staging.width = 0; staging.height = 0; staging = null; stagingCtx = null; }
  state.cleanup.stagingReleased = true;
}
function terminate(reason, destination) {
  if (shutdownPromise) return shutdownPromise;
  cancelled = true;
  if (raf) cancelAnimationFrame(raf); raf = 0; state.cleanup.ownRAFOutstanding = false;
  state.cleanup.requested = true; state.cleanup.reason = reason;
  if (!state.preparation.complete) { state.preparation.aborted = true; state.preparation.stopReason = reason; }
  state.playback.stopReason = reason; state.terminalDestination = destination;
  const now = performance.now();
  if (playStart !== null) {
    state.playback.endedWallMs = now - origin; state.playback.actualWallMs = now - playStart;
    state.playback.terminalActualSeconds = contentSeconds(now);
    state.playback.terminalOverrunSeconds = Math.max(0, state.playback.terminalActualSeconds - DURATION);
    const allPause = pausedTotal + (pauseStart === null ? 0 : now - pauseStart);
    state.playback.pausedWallMs = allPause; state.playback.activeWallMs = now - playStart - allPause;
    state.recording.pausedWallMs = allPause;
    if (pauseStart !== null) Object.assign(state.playback.pauses.at(-1), {
      endedWallMs: now - origin, wallMs: now - pauseStart, endedBy: reason });
  }
  for (const target of state.captures) if (target.status === 'pending') Object.assign(target,
    { status: 'missing', reason, detectedAtSeconds: state.playback.terminalActualSeconds });
  try {
    state.sourceAfterPresentation = materialNow() ? copy(materialNow()) : null;
    if (state.sourceAfterPreparation) {
      state.sourceUnchangedDuringPresentation = same(state.sourceAfterPreparation, state.sourceAfterPresentation);
      assert(state.sourceUnchangedDuringPresentation, '呈示期间源物理状态或参数发生变化');
    }
  } catch (error) { addError('source-lock', error); state.terminalDestination = 'error'; }
  stopRecording(reason); releaseBitmaps();
  $('source')?.remove(); state.cleanup.sourceDetached = true;
  demo = null; research = null; sourceCanvas = null;
  if (!state.preparationCalls) resolvePreparationFinished();
  state.phase = 'finalizing'; record('presentation-stopped', { reason, destination }); updateUI();
  if (destination === 'left') document.body.dataset.left = 'true';
  rejectReady(new Error('准备未完成或观看已结束：' + reason));
  shutdownPromise = (async () => {
    await preparationFinished;
    await Promise.allSettled(capturePromises);
    await finishRecording();
    state.cleanup.complete = state.cleanup.bitmapLiveCount === 0
      && state.cleanup.bitmapsCreated === state.cleanup.bitmapsClosed && !state.preparation.bitmapInFlight
      && state.cleanup.stagingReleased && state.cleanup.sourceDetached && state.cleanup.streamTracksStopped
      && !state.cleanup.ownRAFOutstanding && [null, 'inactive'].includes(state.cleanup.recorderStateAtClose);
    state.artifactsReady = true; state.phase = state.terminalDestination;
    record('artifacts-settled', { cleanupComplete: state.cleanup.complete, recordingStatus: state.recording.status }); updateUI();
  })().catch(error => {
    addError('finalization', error); state.phase = 'error'; state.artifactsReady = true; updateUI();
  });
  return shutdownPromise;
}
function play() {
  if (!['ready', 'paused'].includes(state.phase) || cancelled) return;
  try {
    assert(!document.hidden && document.hasFocus(), '播放时页面不可见或窗口无焦点');
    state.playCalls++;
    if (state.phase === 'ready') {
      assert(state.presentationCalls === 0 && state.preparation.complete, '只能使用已完成源序列呈示一次');
      state.presentationCalls++; startRecording(); playStart = performance.now();
      state.playback.startedWallMs = playStart - origin; state.phase = 'playing'; record('play');
      composite(playStart, null, 'normal-play-button'); nextRAF();
    } else {
      const now = performance.now(), span = now - pauseStart; pausedTotal += span;
      Object.assign(state.playback.pauses.at(-1), { endedWallMs: now - origin, wallMs: span });
      state.playback.pausedWallMs = pausedTotal; pauseStart = null; state.phase = 'playing';
      if (recorder && recorder.state === 'paused') try { recorder.resume(); } catch (error) {
        recordingFailure = 'resume-error'; state.recording.errors.push(String(error.message || error)); stopRecording('resume-error');
      }
      record('resume'); nextRAF();
    }
    updateUI();
  } catch (error) { addError('play', error); void terminate('play-error', 'error'); }
}
function pause() {
  if (state.phase !== 'playing' || cancelled) return;
  const now = performance.now(); state.pauseCalls++; pauseStart = now;
  state.playback.currentSeconds = contentSeconds(now);
  state.playback.pauses.push({ startedWallMs: now - origin, contentSeconds: state.playback.currentSeconds,
    endedWallMs: null, wallMs: null, reason: 'normal-pause-button' });
  if (raf) cancelAnimationFrame(raf); raf = 0; state.cleanup.ownRAFOutstanding = false;
  state.phase = 'paused';
  if (recorder && recorder.state === 'recording') try { recorder.pause(); } catch (error) {
    recordingFailure = 'pause-error'; state.recording.errors.push(String(error.message || error)); stopRecording('pause-error');
  }
  record('pause'); updateUI();
}
$('play').addEventListener('click', play);
$('pause').addEventListener('click', pause);
$('leave').addEventListener('click', () => {
  if (state.phase === 'left') return;
  state.leaveCalls++; record('leave');
  if (state.phase === 'ended' || (state.artifactsReady && state.phase === 'error')) {
    state.phase = 'left'; document.body.dataset.left = 'true'; updateUI();
  } else void terminate('normal-leave-button', 'left');
});
function interrupt(reason) {
  if (['loading', 'preparing', 'playing', 'paused'].includes(state.phase) && !cancelled) {
    addError('interruption', reason); void terminate(reason, 'error');
  }
}
window.addEventListener('blur', () => interrupt('window-blur'));
document.addEventListener('visibilitychange', () => { if (document.hidden) interrupt('page-hidden'); });
window.addEventListener('pagehide', () => {
  if (!cancelled) void terminate('pagehide', state.phase === 'ended' ? 'ended' : 'left');
});

async function initialize() {
  if (initialized || cancelled) return;
  initialized = true;
  try {
    assert(ctx, '作品2D画布不可用');
    demo = $('source').contentWindow.__demo;
    assert(demo?.research, '原demo公开research接口不可用');
    research = demo.research; sourceCanvas = $('source').contentDocument.querySelector('#cv');
    assert(sourceCanvas, '源canvas缺失');
    assert((SOURCE_FRAMES + 1) * BITMAP_BYTES <= CACHE_LIMIT, '名义帧缓存超过192MiB');
    assert(!document.hidden && document.hasFocus(), '准备开始时页面隐藏或窗口无焦点');
    state.preparationCalls++; state.phase = 'preparing'; state.preparation.startedWallMs = wall(); record('preparation-started'); updateUI();
    demo.forceSize(640, 480);
    state.resetCalls++; research.reset(SEED, PARAMS);
    state.sourceInitial = copy(research.snapshot({ detail: true })); finite(state.sourceInitial);
    state.sourceParams = copy(state.sourceInitial.params);
    assert(state.sourceInitial.frame === 0 && state.sourceInitial.time === 0 && state.sourceInitial.scene.count === 0,
      '源初态必须为零帧、无文字或其他场景');
    assert(Object.entries(PARAMS).every(([k, v]) => same(state.sourceParams[k], v)), 'A20参数覆盖不一致');
    staging = document.createElement('canvas'); staging.width = 640; staging.height = 480;
    stagingCtx = staging.getContext('2d', { alpha: false });
    assert(stagingCtx, '源像素暂存2D画布不可用');
    for (let n = 1; n <= SOURCE_FRAMES; n++) {
      if (cancelled) return;
      assert(!document.hidden && document.hasFocus(), '准备期间页面隐藏或窗口失焦');
      const started = performance.now(); state.stepCalls++;
      const physical = research.step(1, DT), afterStep = performance.now(); finite(physical);
      assert(physical.frame === n && Math.abs(physical.time - n * DT) < 1e-8, '唯一源步数或时间不符');
      state.renderCalls++; demo.render(); demo.gl.finish();
      const afterRender = performance.now();
      assert(sourceCanvas.width === 640 && sourceCanvas.height === 480, '源画布不为640×480');
      // WebGL's default buffer may be discarded after this task. Copy synchronously
      // before any await; retain only this one reusable 2D staging surface.
      stagingCtx.drawImage(sourceCanvas, 0, 0, 640, 480);
      const afterCopy = performance.now(); state.bitmapCalls++; state.preparation.bitmapInFlight = true;
      const bitmap = await createImageBitmap(staging);
      state.preparation.bitmapInFlight = false; state.cleanup.bitmapsCreated++;
      if (cancelled) { bitmap.close(); state.cleanup.bitmapsClosed++; return; }
      if (bitmap.width !== 640 || bitmap.height !== 480) {
        bitmap.close(); state.cleanup.bitmapsClosed++; throw new Error('源ImageBitmap尺寸不符');
      }
      frames.push(bitmap); state.cleanup.bitmapLiveCount = frames.length; state.preparation.framesReady = frames.length;
      const afterBitmap = performance.now();
      const entry = { sourceFrame: n, time: physical.time, hash: physical.hash, particleStateHash: physical.particleStateHash,
        particleCount: physical.particles.count, stepMs: afterStep - started, renderMs: afterRender - afterStep,
        copyMs: afterCopy - afterRender, bitmapMs: afterBitmap - afterCopy, yieldMs: null, totalMs: null };
      state.preparation.stepMs += entry.stepMs; state.preparation.renderMs += entry.renderMs;
      state.preparation.copyMs += entry.copyMs; state.preparation.bitmapMs += entry.bitmapMs;
      state.preparation.steps.push(entry);
      const yieldStart = performance.now(); await new Promise(resolve => setTimeout(resolve, 0));
      entry.yieldMs = performance.now() - yieldStart; entry.totalMs = performance.now() - started;
      state.preparation.yieldMs += entry.yieldMs;
    }
    if (cancelled) return;
    assert(state.resetCalls === 1 && state.stepCalls === 150 && state.ignitionCalls === 0
      && state.renderCalls === 150 && state.bitmapCalls === 150 && frames.length === 150, '唯一源调用预算不符');
    state.sourceAfterPreparation = copy(research.snapshot({ detail: true })); finite(state.sourceAfterPreparation);
    state.preparation.endedWallMs = wall(); state.preparation.wallMs = state.preparation.endedWallMs - state.preparation.startedWallMs;
    state.preparation.complete = true; state.phase = 'ready'; record('source-ready'); updateUI(); resolveReady(snapshot());
  } catch (error) {
    state.preparation.bitmapInFlight = false; addError('preparation', error); void terminate('preparation-error', 'error'); rejectReady(error);
  } finally {
    if (state.preparation.startedWallMs !== null && state.preparation.endedWallMs === null) {
      state.preparation.endedWallMs = wall();
      state.preparation.wallMs = state.preparation.endedWallMs - state.preparation.startedWallMs;
    }
    resolvePreparationFinished();
  }
}
Object.defineProperty(window, '__a45', { value: Object.freeze({ ready, snapshot, artifacts }), writable: false, configurable: false });
$('source').addEventListener('load', initialize, { once: true });
if ($('source').contentWindow?.__demo?.research) void initialize();
