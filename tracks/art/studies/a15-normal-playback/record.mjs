// A15: one normal playback, one CDP frame stream, one untrimmed encode. Inert without --execute.
import fs from 'node:fs/promises';
import { openSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { spawnSync } from 'node:child_process';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const began = performance.now(), wall = () => (performance.now() - began) / 1000;
const here = path.dirname(fileURLToPath(import.meta.url)), out = path.join(here, 'run-01');
const ffmpeg = 'C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe';
const ffprobe = path.join(path.dirname(ffmpeg), 'ffprobe.exe');
const artifact = 'tracks/art/studies/a14-view-authored-object/index.html';
const frozenSHA256 = '3cbdaf8703bfa88c01e60d57bdf8c6b25c560cc2528fa03649ea5520cbdce6d5';
const plan = { attempts: 1, viewport: { width: 1440, height: 1100 }, initialHoldSeconds: 2,
  finalHoldSeconds: 3, browserLimitSeconds: 150, workerLimitSeconds: 270, supervisorLimitSeconds: 300,
  maximumJPEGFrames: 2000, maximumJPEGBytes: 200 * 1024 * 1024, maximumVideoBytes: 20 * 1024 * 1024,
  capture: 'CDP Page.startScreencast JPEG quality 85, everyNthFrame=1; no native-full-frame-rate claim',
  output: out, frozenSHA256, ffmpeg, ffprobe };
if (!process.argv.includes('--execute')) { console.log(JSON.stringify(plan, null, 2)); process.exit(0); }
if (!process.env.PLAYWRIGHT_MODULE || !process.env.BROWSER_EXECUTABLE) throw new Error('Explicit existing runtime paths are required');
await fs.mkdir(out, { recursive: false }); await fs.mkdir(path.join(out, 'raw'));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const r = { schema: 'a15-normal-playback-v1', createdUTC: new Date().toISOString(), plan,
  status: 'started', errors: [], console: [], external: [], events: [], observations: [],
  commands: [], resourcesClosed: { context: true, browser: true, server: true },
  recordingCompleted: false, mediaValidated: false,
  interpretation: 'Normal presentation record of a frozen artwork. Not a control experiment, benchmark, audience test, or evidence of artistic success.',
  costScope: 'This complete recording/media worker is separate from the historical TOG subprocess subtotal; neither is total project cost.',
  runtime: { node: process.version, playwright: process.env.PLAYWRIGHT_MODULE, browserExecutable: process.env.BROWSER_EXECUTABLE } };
const publish = async () => {
  const pending = path.join(out, 'result.pending.json');
  await fs.writeFile(pending, JSON.stringify(r, null, 2) + '\n'); await fs.rename(pending, path.join(out, 'result.json'));
};
const names = [artifact, 'demo/index.html', 'research/lib/runtime.mjs',
  'tracks/art/studies/a14-view-authored-object/WORK_SPEC.md',
  ...['PROTOCOL.md', 'record.mjs', 'execute.py', 'PREPARATION.md'].map(n => 'tracks/art/studies/a15-normal-playback/' + n)];
const sources = async () => Object.fromEntries(await Promise.all(names.map(async name => {
  const data = await fs.readFile(path.join(repoRoot, name)); return [name, { bytes: data.length, sha256: hash(data) }];
})));
let server, browser, context, page, cdp, watchdog, browserStarted, captureStarted = false, captureStopped = false;
let captureFailure, chain = Promise.resolve(), firstResolve, firstReject, jpegBytes = 0, receivedCount = 0;
const firstFrame = new Promise((resolve, reject) => { firstResolve = resolve; firstReject = reject; }); firstFrame.catch(() => {});
const frames = [], ackTasks = new Set(), overflow = [];
const healthy = () => {
  if (captureFailure) throw captureFailure;
  if (r.watchdogFired || (browserStarted !== undefined && wall() - browserStarted >= 150)) throw new Error('Browser deadline reached');
  if (r.errors.length || r.external.length) throw new Error('Browser diagnostics prevent a complete recording; see retained records');
};
function captureFail(error) {
  if (captureFailure) return;
  captureFailure = error; firstReject(error);
  r.captureFailure = { wallSeconds: wall(), message: error.message };
  if (cdp && captureStarted) void cdp.send('Page.stopScreencast').catch(() => {});
}
function onFrame(event) {
  receivedCount++;
  const receivedWallSeconds = wall(), receivedHostEpochSeconds = Date.now() / 1000;
  const ack = cdp.send('Page.screencastFrameAck', { sessionId: event.sessionId })
    .catch(error => captureFail(new Error('Frame acknowledgement failed: ' + error.message)))
    .finally(() => ackTasks.delete(ack));
  ackTasks.add(ack);
  const bytes = Buffer.from(event.data, 'base64');
  if (frames.length >= plan.maximumJPEGFrames || jpegBytes + bytes.length > plan.maximumJPEGBytes) {
    overflow.push({ receivedWallSeconds, metadata: event.metadata, bytes: bytes.length, sessionId: event.sessionId });
    captureFail(new Error('JPEG limit reached; excess event metadata retained without exceeding raw byte/frame budget'));
    return;
  }
  const index = frames.length, file = `raw/frame-${String(index).padStart(5, '0')}.jpg`;
  const row = { index, file, bytes: bytes.length, sha256: hash(bytes), metadata: event.metadata,
    sessionId: event.sessionId, receivedWallSeconds, receivedHostEpochSeconds,
    timestamp: event.metadata?.timestamp };
  frames.push(row); jpegBytes += bytes.length;
  chain = chain.then(async () => {
    await fs.writeFile(path.join(out, file), bytes, { flag: 'wx' });
    await fs.appendFile(path.join(out, 'raw/frames.ndjson'), JSON.stringify(row) + '\n');
  }).catch(error => captureFail(new Error('Raw frame persistence failed: ' + error.message)));
  if (!Number.isFinite(row.timestamp) || row.timestamp <= 0) captureFail(new Error('CDP frame has no valid timestamp'));
  else if (index && row.timestamp <= frames[index - 1].timestamp) captureFail(new Error('Non-increasing CDP frame timestamp; no temporal repair'));
  if (index === 0 && !captureFailure) firstResolve(row);
  if (frames.length === plan.maximumJPEGFrames || jpegBytes === plan.maximumJPEGBytes)
    captureFail(new Error('JPEG capture budget exhausted; no retry or reduced-quality fallback'));
}
const read = async full => {
  const observation = await page.evaluate(full => {
    const s = window.__a14.snapshot();
    return { browserEpochSeconds: Date.now() / 1000, snapshot: full ? s : {
      phase: s.phase, frame: s.frame, simSeconds: s.simSeconds, driver: s.driver, driverYaw: s.driverYaw,
      displayDistance: s.displayDistance, wallSeconds: s.wallSeconds, ignitionCalls: s.ignitionCalls,
      resetCalls: s.resetCalls, errors: s.errors } };
  }, full);
  return { ...observation, receivedWallSeconds: wall() };
};
const event = async (name, full = false) => {
  const item = { name, ...await read(full) }; r.events.push(item); await publish(); return item;
};
async function stopCapture() {
  if (!cdp || !captureStarted || captureStopped) return;
  await cdp.send('Page.stopScreencast'); captureStopped = true;
  // This boundary is after the stop acknowledgement, so a static final image is held through the real stop.
  r.captureStop = { browserEpochSeconds: await page.evaluate(() => Date.now() / 1000), receivedWallSeconds: wall() };
  await Promise.allSettled([...ackTasks]); await chain;
}
async function boundedClose(key, handle, action) {
  if (!handle) return;
  let timer;
  try { await Promise.race([action(), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('cleanup timeout')), 5000); })]); r.resourcesClosed[key] = true; }
  catch (error) { r.resourcesClosed[key] = false; r.errors.push({ source: 'cleanup', key, message: error.message }); }
  finally { clearTimeout(timer); }
}
try {
  r.sourceBefore = await sources();
  if (r.sourceBefore[artifact].sha256 !== frozenSHA256) throw new Error('Frozen A14 source identity does not match');
  await publish(); browserStarted = wall();
  watchdog = setTimeout(() => {
    r.watchdogFired = true; captureFail(new Error('150-second browser watchdog fired'));
    if (browser) void browser.close().catch(() => {});
  }, 150000);
  server = await startServer(); r.resourcesClosed.server = false;
  const launched = await launchBrowser(process.env.BROWSER_EXECUTABLE); browser = launched.browser; r.resourcesClosed.browser = false;
  if (launched.module !== process.env.PLAYWRIGHT_MODULE) throw new Error('Unexpected Playwright fallback');
  r.runtime.browser = browser.version(); r.runtime.launch = launched.launchOptions;
  context = await browser.newContext({ viewport: plan.viewport, deviceScaleFactor: 1, serviceWorkers: 'block' }); r.resourcesClosed.context = false;
  await context.route('**/*', async route => {
    const u = new URL(route.request().url());
    if (u.origin === server.url || ['data:', 'blob:', 'about:'].includes(u.protocol)) await route.continue();
    else { r.external.push({ url: u.href, wallSeconds: wall() }); await route.abort('blockedbyclient'); }
  });
  page = await context.newPage(); page.setDefaultTimeout(12000);
  page.on('pageerror', error => r.errors.push({ source: 'pageerror', wallSeconds: wall(), message: error.message }));
  page.on('console', message => { if (['error', 'warning'].includes(message.type())) r.console.push({ type: message.type(), text: message.text(), wallSeconds: wall() }); });
  await page.goto(server.url + '/tracks/art/studies/a14-view-authored-object/', { waitUntil: 'load', timeout: 20000 });
  await page.waitForFunction(() => !!window.__a14); await page.evaluate(() => window.__a14.ready);
  r.initial = await read(true);
  if (r.initial.snapshot.phase !== 'ready' || r.initial.snapshot.frame !== 0 || r.initial.snapshot.resetCalls || r.initial.snapshot.ignitionCalls || r.initial.snapshot.inspect)
    throw new Error('Initial page is not a fresh normal-playback state');
  healthy();
  cdp = await context.newCDPSession(page); cdp.on('Page.screencastFrame', onFrame);
  r.captureRequested = { browserEpochSeconds: await page.evaluate(() => Date.now() / 1000), receivedWallSeconds: wall() };
  captureStarted = true;
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1440, maxHeight: 1100, everyNthFrame: 1 });
  let firstTimer;
  try { await Promise.race([firstFrame, new Promise((_, reject) => { firstTimer = setTimeout(() => reject(new Error('No CDP frame within 8 seconds')), 8000); })]); }
  finally { clearTimeout(firstTimer); }
  r.captureStart = { browserEpochSeconds: frames[0].timestamp, receivedWallSeconds: frames[0].receivedWallSeconds,
    definition: 'First actually received compositor frame; no blank or invented pre-frame interval is encoded.' };
  await event('opening-hold-begins'); await page.waitForTimeout(2000); healthy();
  await event('ui-click-before'); await page.getByRole('button', { name: '开始观看', exact: true }).click();
  const clicked = await event('ui-click-after', true);
  if (clicked.snapshot.resetCalls !== 1 || clicked.snapshot.ignitionCalls !== 1 || clicked.snapshot.sequence !== 1)
    throw new Error('The single UI start did not establish exactly one reset and ignition');
  while (true) {
    healthy(); const observation = await read(false); r.observations.push(observation);
    if (observation.snapshot.errors.length || observation.snapshot.phase === 'error') throw new Error('A14 reported an error');
    if (observation.snapshot.phase === 'ended') break;
    if (observation.snapshot.frame > 360 || observation.snapshot.resetCalls !== 1 || observation.snapshot.ignitionCalls !== 1)
      throw new Error('Normal sequence exceeded fixed scope');
    await page.waitForTimeout(150);
  }
  r.ended = await event('ended-observed', true);
  if (r.ended.snapshot.frame !== 360 || r.ended.snapshot.simSeconds !== 12 || r.ended.snapshot.handoffEqualExceptYaw !== true)
    throw new Error('Sequence ended without the fixed 360-step handoff contract');
  await page.waitForTimeout(3000); healthy();
  await event('final-hold-complete', true); await stopCapture(); healthy();
  r.recordingCompleted = true;
} catch (error) { r.failure = { stage: 'browser', wallSeconds: wall(), message: error.message, stack: error.stack }; }
finally {
  try { await stopCapture(); } catch (error) { r.errors.push({ source: 'capture-stop', message: error.message }); }
  clearTimeout(watchdog);
  await boundedClose('context', context, () => context.close());
  await boundedClose('browser', browser, () => browser.close());
  await boundedClose('server', server, () => server.close());
  await Promise.allSettled([...ackTasks]); await chain;
  r.browserWallSeconds = browserStarted === undefined ? 0 : wall() - browserStarted;
  r.capture = { receivedEvents: receivedCount, savedFrames: frames.length, savedJPEGBytes: jpegBytes,
    budgetDiscardedEvents: overflow, stopped: captureStopped, frameIndex: 'raw/frames.ndjson',
    limitations: 'CDP emits compositor samples, often only on changes. Every arrival is acknowledged; native missed/repaint-coalesced frames cannot be counted. Long static holds are not assumed dropped frames. Recording/observation overhead may change wall time.' };
  if (frames.length) {
    const gaps = frames.slice(1).map((f, i) => f.timestamp - frames[i].timestamp), sorted = [...gaps].sort((a, b) => a - b);
    r.capture.timing = { firstTimestamp: frames[0].timestamp, lastTimestamp: frames.at(-1).timestamp,
      minIntervalSeconds: sorted[0] ?? null, medianIntervalSeconds: sorted[Math.floor(sorted.length * .5)] ?? null,
      p95IntervalSeconds: sorted[Math.floor(sorted.length * .95)] ?? null, maxIntervalSeconds: sorted.at(-1) ?? null,
      intervalsOver100ms: gaps.filter(v => v > .1).length, intervalsOver500ms: gaps.filter(v => v > .5).length,
      identicalJPEGAdjacentPairs: frames.slice(1).filter((f, i) => f.sha256 === frames[i].sha256).length,
      nonIncreasingIntervals: gaps.filter(v => v <= 0).length,
      firstReceiptDelaySeconds: frames[0].receivedHostEpochSeconds - frames[0].timestamp };
    const indexBytes = await fs.readFile(path.join(out, 'raw/frames.ndjson')).catch(() => null);
    if (indexBytes) r.capture.frameIndexSHA256 = hash(indexBytes);
  }
  if (captureFailure || r.errors.length || r.external.length || r.browserWallSeconds > 150) r.recordingCompleted = false;
  await publish();
}

function command(label, executable, args, maximumSeconds) {
  const available = Math.floor(Math.min(maximumSeconds, 270 - wall() - 3) * 1000);
  if (available <= 0) throw new Error('No remaining media budget for ' + label);
  const row = { label, executable, args, startedWallSeconds: wall(), timeoutMilliseconds: available }; r.commands.push(row);
  const stdout = openSync(path.join(out, label + '.stdout.log'), 'wx'), stderr = openSync(path.join(out, label + '.stderr.log'), 'wx');
  try {
    const child = spawnSync(executable, args, { cwd: out, timeout: available, windowsHide: true, stdio: ['ignore', stdout, stderr] });
    row.exitCode = child.status; row.signal = child.signal; row.error = child.error?.message || null;
    if (child.error || child.status !== 0) throw new Error(label + ': ' + (row.error || 'exit ' + child.status));
  } finally { closeSync(stdout); closeSync(stderr); row.endedWallSeconds = wall(); row.wallSeconds = row.endedWallSeconds - row.startedWallSeconds; }
}
function increasing(values) { return values.every((value, i) => Number.isFinite(value) && (i === 0 || value > values[i - 1])); }
if (r.recordingCompleted) {
  try {
    const first = frames[0].timestamp, stop = r.captureStop.browserEpochSeconds, duration = stop - first;
    if (!increasing(frames.map(f => f.timestamp)) || !(stop > frames.at(-1).timestamp) || !(duration > 5)) throw new Error('Invalid complete recording boundaries');
    const monotonicSpan = r.captureStop.receivedWallSeconds - r.captureStart.receivedWallSeconds;
    if (Math.abs(duration - monotonicSpan) > .5) throw new Error('Browser epoch and monotonic receipt span disagree by more than 0.5 seconds');
    const beforeClick = r.events.find(e => e.name === 'ui-click-before').browserEpochSeconds;
    if (beforeClick - first < 2 || stop - r.ended.browserEpochSeconds < 3) throw new Error('Opening/final real hold was shortened');
    const lines = ['ffconcat version 1.0'];
    for (let i = 0; i < frames.length; i++) {
      const next = i + 1 < frames.length ? frames[i + 1].timestamp : stop;
      lines.push(`file '../${frames[i].file}'`, 'option framerate 1000', `duration ${(next - frames[i].timestamp).toFixed(6)}`);
    }
    lines.push(`file '../${frames.at(-1).file}'`, 'option framerate 1000');
    await fs.writeFile(path.join(out, 'raw/timeline.ffconcat'), lines.join('\n') + '\n', { flag: 'wx' });
    r.timeline = { firstBrowserEpochSeconds: first, stopBrowserEpochSeconds: stop, durationSeconds: duration,
      monotonicReceiptSpanSeconds: monotonicSpan, epochMinusMonotonicSpanSeconds: duration - monotonicSpan,
      lastImageHoldSeconds: stop - frames.at(-1).timestamp, openingToClickSeconds: beforeClick - first,
      endedToStopSeconds: stop - r.ended.browserEpochSeconds,
      clockMapping: 'CDP metadata.timestamp and browser Date.now()/1000 share epoch seconds. Each event also retains host epoch and Node monotonic receipt time; UI click is bracketed, phase transitions are localized to 150ms polling intervals.',
      quantization: 'Original CDP timestamps are retained. Concat duration text has microsecond precision; JPEG demux/encoder time base is 1ms, MP4 track time base is 1us. Validation allows at most 3ms PTS error. One repeated terminal image marks the real stop boundary, not another observed frame.',
      noInterpolationOrTrim: true };
    await publish();
    command('encode', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-f', 'concat', '-safe', '0', '-i', 'raw/timeline.ffconcat',
      '-an', '-fps_mode', 'passthrough', '-enc_time_base', '1:1000', '-c:v', 'libx264', '-preset', 'medium',
      '-crf', '20', '-pix_fmt', 'yuv420p', '-threads', '2', '-video_track_timescale', '1000000', '-movflags', '+faststart', 'study.mp4'], 90);
    const video = await fs.readFile(path.join(out, 'study.mp4'));
    r.video = { file: 'study.mp4', bytes: video.length, sha256: hash(video), commitEligible: video.length <= plan.maximumVideoBytes };
    command('probe', ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_streams', '-show_format', '-show_frames',
      '-show_entries', 'stream=codec_name,width,height,time_base,nb_frames,duration,start_time:format=duration,size:frame=best_effort_timestamp_time,pkt_duration_time,width,height', '-of', 'json', 'study.mp4'], 20);
    const probe = JSON.parse(await fs.readFile(path.join(out, 'probe.stdout.log'), 'utf8'));
    const stream = probe.streams?.[0], pts = (probe.frames || []).map(f => Number(f.best_effort_timestamp_time));
    const expected = [...frames.map(f => f.timestamp - first), duration];
    if (stream?.codec_name !== 'h264' || stream.width !== 1440 || stream.height !== 1100 || pts.length !== expected.length || !increasing(pts))
      throw new Error('Encoded frame count, dimensions, codec, or PTS order mismatch');
    const maximumPTSError = Math.max(...pts.map((value, i) => Math.abs(value - expected[i])));
    if (maximumPTSError > .003 || Math.abs(Number(probe.format.duration) - duration) > .005) throw new Error('Encoded timing exceeds fixed quantization tolerance');
    r.video.probe = { stream, durationSeconds: Number(probe.format.duration), frameCount: pts.length, maximumPTSErrorSeconds: maximumPTSError };
    // A real raw-frame hash muxer with an explicit time base avoids null-muxer DTS rescaling traps.
    command('decode', ffmpeg, ['-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-n', '-copyts', '-i', 'study.mp4',
      '-map', '0:v:0', '-an', '-fps_mode', 'passthrough', '-enc_time_base', '1:1000000', '-f', 'framemd5', 'raw/decode.framemd5'], 45);
    const decoded = await fs.readFile(path.join(out, 'raw/decode.framemd5'), 'utf8');
    const tb = decoded.match(/^#tb\s+0:\s*(\d+)\/(\d+)/m);
    if (!tb) throw new Error('Decode time base not reported');
    const decodedPTS = decoded.split(/\r?\n/).filter(line => line && !line.startsWith('#')).map(line => Number(line.split(',')[2]) * Number(tb[1]) / Number(tb[2]));
    if (decodedPTS.length !== pts.length || !increasing(decodedPTS) || decodedPTS.some((v, i) => Math.abs(v - pts[i]) > .000002))
      throw new Error('Full decode did not preserve every validated timestamp');
    r.video.fullDecode = { passed: true, frames: decodedPTS.length, manifest: 'raw/decode.framemd5', sha256: hash(decoded), timeBase: [Number(tb[1]), Number(tb[2])] };
    await fs.mkdir(path.join(out, 'review'));
    command('review-frames', ffmpeg, ['-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-n', '-i', 'study.mp4',
      '-vf', 'fps=1:start_time=0:round=near:eof_action=pass,scale=960:-2', '-fps_mode', 'passthrough', '-q:v', '3', '-start_number', '0', 'review/second-%03d.jpg'], 40);
    const files = (await fs.readdir(path.join(out, 'review'))).filter(f => /^second-\d+\.jpg$/.test(f)).sort();
    r.review = { periodWallSeconds: 1, width: 960, method: 'FFmpeg fps=1, start_time=0, round=near, eof_action=pass; input PTS are rounded to a one-second output grid with drops/repeats. videoSecond is output PTS, not an exact instantaneous source screenshot or nearest-source-frame selection.',
      limitation: 'Ordered still-image reading is not continuous video understanding and cannot settle all movement or rhythm experience.', frames: [] };
    for (const [i, file] of files.entries()) { const bytes = await fs.readFile(path.join(out, 'review', file)); r.review.frames.push({ videoSecond: i, file: 'review/' + file, bytes: bytes.length, sha256: hash(bytes) }); }
    r.review.expectedFrames = Math.ceil(Number(probe.format.duration));
    if (!files.length || files.length > 151 || files.length !== r.review.expectedFrames) throw new Error('Unexpected fixed-second review frame count');
    r.mediaValidated = true;
  } catch (error) { r.failure = { stage: 'media', wallSeconds: wall(), message: error.message, stack: error.stack }; }
}
try { r.sourceAfter = await sources(); r.sourcesUnchanged = JSON.stringify(r.sourceBefore) === JSON.stringify(r.sourceAfter); }
catch (error) { r.sourcesUnchanged = false; r.errors.push({ source: 'source-hash', message: error.message }); }
r.totalWallSecondsBeforeFinalReceipt = wall();
r.status = r.recordingCompleted && r.mediaValidated && r.video?.commitEligible && r.sourcesUnchanged &&
  !r.errors.length && Object.values(r.resourcesClosed).every(v => v === true) && wall() <= 270 ? 'completed_recording_and_media' : 'failed';
r.noRetry = true; r.timingLimit = 'Node total ends before final receipt/stdout write; supervisor measures the entire child lifetime.';
await publish();
console.log(JSON.stringify({ status: r.status, secondsBeforeReceipt: r.totalWallSecondsBeforeFinalReceipt,
  savedFrames: frames.length, video: r.video, reviewFrames: r.review?.frames.length, failure: r.failure || null, out }));
process.exitCode = r.status === 'completed_recording_and_media' ? 0 : 1;
