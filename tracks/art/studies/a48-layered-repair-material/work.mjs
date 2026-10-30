const started = performance.now();
const canvas = document.querySelector('#work'), ctx = canvas.getContext('2d', { alpha: false });
const cover = document.querySelector('#cover'), stageElement = document.querySelector('#stage');
const restoreButton = document.querySelector('#restore'), leaveButton = document.querySelector('#leave');
const sourceHost = document.querySelector('#source-host');
const sourceSHA = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
const require = (ok, message) => { if (!ok) throw Error('A48 page: ' + message); };
const elapsed = () => performance.now() - started;
const records = { version: 1, phase: 'loading', artifactsReady: false, errors: [], source: null, identity: null,
  draws: [], pngAttempts: [], images: [], costs: { sourceLoadMs: null, preparedAtMs: null, endedAtMs: null,
    inspection: { calls: 0, totalMs: 0 }, imageReads: { calls: 0, totalMs: 0 },
    nominalRGBABytes: { mainCanvas: 720 * 720 * 4, paperCanvases: 2 * 300 * 400 * 4, paperImageData: 2 * 300 * 400 * 4 },
    note: 'CPU wall times include ordinary initialization and idle embed RAF lifetime; no automatic source render/step.' },
  cleanup: { complete: false, reason: null, iframeRemoved: false, paperCachesReleased: false,
    hostRAFUsed: false, pendingPNGCancelled: false, leaveCalls: 0 } };
const storedImages = [];
const paperColor = [228, 221, 204], lineColor = [76, 81, 75], lineCenters = [34, 162, 234];
let active = true, frame = null, restoreHandler = null, cancelPNG = null;
const controller = new AbortController();
const papers = ['B', 'F'].map(group => {
  const surface = document.createElement('canvas'); surface.width = 300; surface.height = 400;
  const context = surface.getContext('2d'), pixels = context.createImageData(300, 400);
  return { group, surface, context, pixels };
});
const sha256 = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(n => n.toString(16).padStart(2, '0')).join('');
const ensureActive = () => require(active, 'page has stopped');

function cleanup(reason) {
  if (records.cleanup.complete) return;
  active = false; controller.abort(); clearTimeout(preparationTimer);
  window.removeEventListener('a48-source-connect', connectSource);
  if (restoreHandler) restoreButton.removeEventListener('click', restoreHandler);
  restoreHandler = null; restoreButton.disabled = true;
  if (cancelPNG) { records.cleanup.pendingPNGCancelled = true; cancelPNG(); cancelPNG = null; }
  for (const attempt of records.pngAttempts) if (attempt.status === 'encoding') {
    attempt.status = 'cancelled'; attempt.error = 'Page left or stopped during PNG work';
  }
  if (frame) { frame.remove(); frame = null; }
  sourceHost.replaceChildren();
  for (const paper of papers) { paper.surface.width = 0; paper.surface.height = 0; paper.pixels = null; paper.context = null; }
  canvas.width = 0; canvas.height = 0;
  records.cleanup = { ...records.cleanup, complete: true, reason, iframeRemoved: true, paperCachesReleased: true,
    mainCanvasReleased: true, completedAtMs: elapsed(), sourceIdleRAFLifetimeEnded: true };
}
function fail(error) {
  if (records.phase === 'left') return;
  records.errors.push(String(error.message || error)); records.phase = 'error';
  cover.hidden = false; cover.textContent = '此次准备已停止'; stageElement.setAttribute('aria-busy', 'false');
  cleanup('error');
}
function setPhase(phase) {
  ensureActive(); records.phase = phase;
  if (phase === 'prepared') {
    require(storedImages.length === 2, 'prepared image is incomplete');
    clearTimeout(preparationTimer); records.costs.preparedAtMs = elapsed();
    cover.hidden = true; stageElement.setAttribute('aria-busy', 'false'); restoreButton.disabled = false;
  }
  if (phase === 'ended') {
    require(storedImages.length === 3, 'third image is incomplete');
    records.artifactsReady = true; records.costs.endedAtMs = elapsed(); restoreButton.disabled = true;
  }
}
function draw(name, chars) {
  ensureActive(); require(ctx && chars.length === 15000, 'invalid presentation input');
  require(!records.draws.some(d => d.stage === name) && records.draws.length < 3, 'a stage may be drawn only once');
  const t0 = performance.now();
  for (const paper of papers) {
    const bytes = paper.pixels.data, offset = paper.group === 'F' ? 0 : 7500;
    for (let y = 0; y < 400; y++) for (let x = 0; x < 300; x++) {
      const char = chars[offset + Math.floor(y / 4) * 75 + Math.floor(x / 4)];
      require(Number.isFinite(char), 'nonfinite material char');
      const line = y >= 20 && y < 380 && lineCenters.some(center => x >= center - 1 && x < center + 1);
      const color = line ? lineColor : paperColor, k = (y * 300 + x) * 4;
      bytes[k] = color[0]; bytes[k + 1] = color[1]; bytes[k + 2] = color[2];
      bytes[k + 3] = Math.round(255 * (1 - Math.max(0, Math.min(1, char))));
    }
    paper.context.putImageData(paper.pixels, 0, 0);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#1D2320'; ctx.fillRect(0, 0, 720, 720);
  // Each combined paper-and-line surface is composited exactly once.
  ctx.save(); ctx.translate(300, 390); ctx.rotate(-12 * Math.PI / 180);
  ctx.drawImage(papers[0].surface, -150, -200); ctx.restore();
  ctx.drawImage(papers[1].surface, 280, 80);
  records.draws.push({ stage: name, width: 720, height: 720, sourceField: 'char_',
    paperDrawImageCalls: 2, elapsedMs: performance.now() - t0, completedAtMs: elapsed() });
}
function pngBlob() {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (error, blob) => {
      if (settled) return; settled = true; clearTimeout(timer); cancelPNG = null;
      if (error) reject(error); else resolve(blob);
    };
    const timer = setTimeout(() => finish(Error('PNG encoding exceeded 15 seconds')), 15000);
    cancelPNG = () => finish(Error('PNG capture cancelled on leave/stop'));
    canvas.toBlob(blob => finish(blob ? null : Error('PNG encoding returned null'), blob), 'image/png');
  });
}
async function capture(name, chars) {
  ensureActive();
  const order = ['initial', 'prepared', 'swapped'];
  require(name === order[storedImages.length] && records.pngAttempts.length === storedImages.length, 'PNG order/budget differs');
  draw(name, chars);
  const attempt = { stage: name, status: 'encoding', startedAtMs: elapsed() };
  records.pngAttempts.push(attempt);
  try {
    const blob = await pngBlob(); ensureActive();
    require(blob.type === 'image/png', 'encoder did not return PNG');
    const bytes = new Uint8Array(await blob.arrayBuffer()); ensureActive();
    require(storedImages.reduce((n, image) => n + image.bytes, 0) + bytes.length <= 8 * 1024 * 1024, 'PNG total exceeds 8 MiB');
    const digest = await sha256(bytes); ensureActive();
    let binary = '';
    for (let i = 0; i < bytes.length; i += 32768) binary += String.fromCharCode(...bytes.subarray(i, i + 32768));
    const metadata = { file: `${storedImages.length + 1}-${name}.png`, stage: name, width: 720, height: 720,
      bytes: bytes.length, sha256: digest, completedAtMs: elapsed() };
    storedImages.push({ ...metadata, dataURL: 'data:image/png;base64,' + btoa(binary) });
    records.images.push(metadata); attempt.status = 'cached'; attempt.elapsedMs = elapsed() - attempt.startedAtMs;
  } catch (error) { if (active) { attempt.status = 'failed'; attempt.error = error.message; } throw error; }
}
function connectSource(event) {
  if (!active || !frame || event.detail?.sourceWindow !== frame.contentWindow) return;
  window.removeEventListener('a48-source-connect', connectSource);
  records.costs.sourceLoadMs = elapsed();
  try {
    event.detail.connect({ active: () => active, phase: setPhase, fail, capture,
      publish: report => { records.source = report; },
      disableRestore: () => { restoreButton.disabled = true; },
      bindRestore: action => {
        require(!restoreHandler, 'restore handler already installed');
        restoreHandler = () => { if (records.phase === 'prepared' && active) void action(); };
        restoreButton.addEventListener('click', restoreHandler, { once: true });
      } });
  } catch (error) { fail(error); }
}
function leave() {
  if (records.phase === 'left') return;
  records.cleanup.leaveCalls++; records.phaseBeforeLeave = records.phase; records.phase = 'left';
  cover.hidden = false; cover.textContent = '已离开'; stageElement.setAttribute('aria-busy', 'false');
  cleanup('leave'); leaveButton.disabled = true;
}
leaveButton.addEventListener('click', leave, { once: true });
window.addEventListener('pagehide', () => cleanup('pagehide'), { once: true });
const preparationTimer = setTimeout(() => fail(Error('Ordinary page preparation exceeded 110 seconds')), 110000);

function inspect(options = {}) {
  const t0 = performance.now();
  const value = options.summary ? { version: records.version, phase: records.phase, artifactsReady: records.artifactsReady,
    errors: records.errors, calls: records.source?.calls ?? null, imageCount: storedImages.length, cleanup: records.cleanup } : records;
  const result = structuredClone(value);
  records.costs.inspection.calls++; records.costs.inspection.totalMs += performance.now() - t0;
  if (!options.summary) result.costs.inspection = { ...records.costs.inspection };
  return result;
}
function images() {
  const t0 = performance.now();
  const value = structuredClone({ images: storedImages, totalBytes: storedImages.reduce((n, image) => n + image.bytes, 0),
    complete: storedImages.length === 3, sourceIdentity: records.identity?.source ?? null });
  records.costs.imageReads.calls++; records.costs.imageReads.totalMs += performance.now() - t0;
  return value;
}
Object.defineProperty(window, '__a48', { value: Object.freeze({ inspect, images }), writable: false, configurable: false });

async function start() {
  try {
    require(ctx, '2D canvas is unavailable');
    const response = await fetch('./assembly.json', { signal: controller.signal, cache: 'no-store' });
    require(response.ok, 'assemble the reviewed local source before loading');
    const manifest = await response.json(); ensureActive();
    require(manifest.source.bytes === 314044 && manifest.source.sha256 === sourceSHA
      && manifest.insertion.insertionOnly && manifest.insertion.originalBytesReconstructExactly, 'assembly manifest identity differs');
    records.identity = manifest;
    window.addEventListener('a48-source-connect', connectSource);
    frame = document.createElement('iframe'); frame.title = '原材料时钟'; frame.tabIndex = -1;
    frame.src = './renderer.generated.html?embed=1&orbit=0';
    frame.addEventListener('error', () => fail(Error('Source iframe failed to load')), { once: true });
    sourceHost.append(frame);
  } catch (error) { if (active) fail(error); }
}
void start();
