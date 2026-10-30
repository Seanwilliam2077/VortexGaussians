// A16: one reception-timed normal playback record. A15 remains unchanged and failed.
import fs from 'node:fs/promises';
import { openSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const monotonic = () => process.hrtime.bigint(), beganNs = monotonic();
const wall = (time = monotonic()) => Number(time - beganNs) / 1e9;
const stamp = (time = monotonic()) => ({ receivedMonotonicNs: time.toString(), receivedWallSeconds: wall(time), hostEpochSeconds: Date.now() / 1000 });
const absBig = value => value < 0n ? -value : value;
const secondsText = us => `${us / 1000000n}.${(us % 1000000n).toString().padStart(6, '0')}`;
const here = path.dirname(fileURLToPath(import.meta.url)), out = path.join(here, 'run-01');
const ffmpeg = 'C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe';
const ffprobe = path.join(path.dirname(ffmpeg), 'ffprobe.exe');
const artifact = 'tracks/art/studies/a14-view-authored-object/index.html';
const frozenSHA256 = '3cbdaf8703bfa88c01e60d57bdf8c6b25c560cc2528fa03649ea5520cbdce6d5';
const plan = { attempts: 1, viewport: { width: 1440, height: 1100 }, initialHoldSeconds: 2,
  finalHoldSeconds: 3, browserLimitSeconds: 150, workerLimitSeconds: 270, supervisorLimitSeconds: 300,
  maximumJPEGFrames: 2000, maximumJPEGBytes: 200 * 1024 * 1024, maximumVideoBytes: 20 * 1024 * 1024,
  capture: 'CDP Page.startScreencast JPEG quality 85, everyNthFrame=1; no native-full-frame-rate claim',
  timingBasis: 'process.hrtime.bigint() receipt time; absolute offsets rounded once to microseconds',
  output: out, frozenSHA256, ffmpeg, ffprobe };
if (!process.argv.includes('--execute')) { console.log(JSON.stringify(plan, null, 2)); process.exit(0); }
if (!process.env.PLAYWRIGHT_MODULE || !process.env.BROWSER_EXECUTABLE) throw new Error('Explicit existing runtime paths are required');
await fs.mkdir(out, { recursive: false }); await fs.mkdir(path.join(out, 'raw'));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const r = { schema: 'a16-reception-timing-record-v1', createdUTC: new Date().toISOString(), plan,
  status: 'started', errors: [], console: [], external: [], events: [], observations: [],
  commands: [], resourcesClosed: { context: true, browser: true, server: true },
  recordingCompleted: false, mediaValidated: false,
  inputSource: { tool: 'tracks/art/studies/a16-reception-timing-record/record.mjs', supervisor: 'tracks/art/studies/a16-reception-timing-record/execute.py', protocol: 'tracks/art/studies/a16-reception-timing-record/PROTOCOL.md', artwork: artifact, frozenArtworkSHA256: frozenSHA256 },
  interpretation: 'Reception-time presentation of the image stream actually received. Not exact compositor presentation order, a benchmark, an audience test, or evidence of artistic success. A15 remains failed.',
  costScope: 'This complete recording/media worker is separate from the historical TOG subprocess subtotal; neither is total project cost.',
  runtime: { node: process.version, playwright: process.env.PLAYWRIGHT_MODULE, browserExecutable: process.env.BROWSER_EXECUTABLE } };
const publish = async () => {
  const pending = path.join(out, 'result.pending.json');
  await fs.writeFile(pending, JSON.stringify(r, null, 2) + '\n'); await fs.rename(pending, path.join(out, 'result.json'));
};
const names = [artifact, 'demo/index.html', 'research/lib/runtime.mjs',
  'tracks/art/studies/a14-view-authored-object/WORK_SPEC.md',
  ...['PROTOCOL.md', 'record.mjs', 'execute.py', 'PREPARATION.md'].map(n => 'tracks/art/studies/a16-reception-timing-record/' + n)];
const sources = async () => Object.fromEntries(await Promise.all(names.map(async name => {
  const data = await fs.readFile(path.join(repoRoot, name)); return [name, { bytes: data.length, sha256: hash(data) }];
})));
let server, browser, context, page, cdp, watchdog, browserStarted, captureStarted = false, captureStopped = false;
let captureFailure, chain = Promise.resolve(), firstResolve, firstReject, jpegBytes = 0, receivedCount = 0;
const firstFrame = new Promise((resolve, reject) => { firstResolve = resolve; firstReject = reject; }); firstFrame.catch(() => {});
const frames = [], ackTasks = new Set(), overflow = [], cdpTimestampAnomalies = [];
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
  const receivedNs = monotonic();
  receivedCount++;
  const receivedWallSeconds = wall(receivedNs), receivedMonotonicNs = receivedNs.toString(), receivedHostEpochSeconds = Date.now() / 1000;
  const ack = cdp.send('Page.screencastFrameAck', { sessionId: event.sessionId })
    .catch(error => captureFail(new Error('Frame acknowledgement failed: ' + error.message)))
    .finally(() => ackTasks.delete(ack));
  ackTasks.add(ack);
  const bytes = Buffer.from(event.data, 'base64');
  if (frames.length >= plan.maximumJPEGFrames || jpegBytes + bytes.length > plan.maximumJPEGBytes) {
    overflow.push({ arrivalIndex: receivedCount - 1, receivedMonotonicNs, receivedWallSeconds, receivedHostEpochSeconds, metadata: event.metadata, bytes: bytes.length, sessionId: event.sessionId });
    captureFail(new Error('JPEG limit reached; excess event metadata retained without exceeding raw byte/frame budget'));
    return;
  }
  const index = frames.length, file = `raw/frame-${String(index).padStart(5, '0')}.jpg`;
  const row = { index, arrivalIndex: receivedCount - 1, file, bytes: bytes.length, sha256: hash(bytes), metadata: event.metadata,
    sessionId: event.sessionId, receivedMonotonicNs, receivedWallSeconds, receivedHostEpochSeconds,
    timestamp: event.metadata?.timestamp };
  frames.push(row); jpegBytes += bytes.length;
  chain = chain.then(async () => {
    await fs.writeFile(path.join(out, file), bytes, { flag: 'wx' });
    await fs.appendFile(path.join(out, 'raw/frames.ndjson'), JSON.stringify(row) + '\n');
  }).catch(error => captureFail(new Error('Raw frame persistence failed: ' + error.message)));
  if (!Number.isFinite(row.timestamp) || row.timestamp <= 0) captureFail(new Error('CDP frame has no valid timestamp'));
  else if (index && row.timestamp <= frames[index - 1].timestamp) {
    const previous = frames[index - 1];
    cdpTimestampAnomalies.push({ previousArrivalIndex: previous.arrivalIndex, arrivalIndex: row.arrivalIndex,
      previousTimestamp: previous.timestamp, timestamp: row.timestamp, deltaSeconds: row.timestamp - previous.timestamp,
      previousReceivedMonotonicNs: previous.receivedMonotonicNs, receivedMonotonicNs,
      receiptDeltaNs: (receivedNs - BigInt(previous.receivedMonotonicNs)).toString(), sameJPEG: row.sha256 === previous.sha256 });
  }
  if (index && receivedNs <= BigInt(frames[index - 1].receivedMonotonicNs)) captureFail(new Error('Non-increasing monotonic receipt time; no timestamp repair'));
  if (index === 0 && !captureFailure) firstResolve(row);
  if (frames.length === plan.maximumJPEGFrames || jpegBytes === plan.maximumJPEGBytes)
    captureFail(new Error('JPEG capture budget exhausted; no retry or reduced-quality fallback'));
}
const read = async full => {
  const requestedMonotonicNs = monotonic().toString();
  const observation = await page.evaluate(full => {
    const s = window.__a14.snapshot();
    return { browserEpochSeconds: Date.now() / 1000, snapshot: full ? s : {
      phase: s.phase, frame: s.frame, simSeconds: s.simSeconds, driver: s.driver, driverYaw: s.driverYaw,
      displayDistance: s.displayDistance, wallSeconds: s.wallSeconds, ignitionCalls: s.ignitionCalls,
      resetCalls: s.resetCalls, errors: s.errors } };
  }, full);
  return { ...observation, requestedMonotonicNs, ...stamp() };
};
const event = async (name, full = false) => {
  const item = { name, ...await read(full) }; r.events.push(item); await publish(); return item;
};
async function stopCapture() {
  if (!cdp || !captureStarted || captureStopped) return;
  await cdp.send('Page.stopScreencast'); captureStopped = true;
  // This actual receipt-domain boundary is sampled immediately after the stop acknowledgement.
  r.captureStop = stamp();
  r.captureStop.browserEpochSecondsDiagnostic = await page.evaluate(() => Date.now() / 1000);
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
  r.captureRequested = { browserEpochSecondsDiagnostic: await page.evaluate(() => Date.now() / 1000), ...stamp() };
  captureStarted = true;
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1440, maxHeight: 1100, everyNthFrame: 1 });
  let firstTimer;
  try { await Promise.race([firstFrame, new Promise((_, reject) => { firstTimer = setTimeout(() => reject(new Error('No CDP frame within 8 seconds')), 8000); })]); }
  finally { clearTimeout(firstTimer); }
  r.captureStart = { receivedMonotonicNs: frames[0].receivedMonotonicNs, receivedWallSeconds: frames[0].receivedWallSeconds,
    sourceCDPTimestampDiagnostic: frames[0].timestamp,
    definition: 'First actual JPEG arrival in the Node monotonic receipt domain; no pre-arrival interval is encoded.' };
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
    budgetDiscardedEvents: overflow, cdpTimestampAnomalies, stopped: captureStopped, frameIndex: 'raw/frames.ndjson',
    limitations: 'Arrival order and Node receipt timing are retained. Transport jitter, queues, receipt workload and capture overhead can alter this rhythm; it is not exact browser presentation timing. CDP may coalesce or omit repaints. Every arrival is acknowledged; native missed frames cannot be counted. Static holds are not assumed dropped frames.' };
  if (frames.length) {
    const gaps = frames.slice(1).map((f, i) => Number(BigInt(f.receivedMonotonicNs) - BigInt(frames[i].receivedMonotonicNs)) / 1e9), sorted = [...gaps].sort((a, b) => a - b);
    r.capture.timing = { basis: 'Node monotonic receipt intervals', firstReceivedMonotonicNs: frames[0].receivedMonotonicNs, lastReceivedMonotonicNs: frames.at(-1).receivedMonotonicNs,
      minIntervalSeconds: sorted[0] ?? null, medianIntervalSeconds: sorted[Math.floor(sorted.length * .5)] ?? null,
      p95IntervalSeconds: sorted[Math.floor(sorted.length * .95)] ?? null, maxIntervalSeconds: sorted.at(-1) ?? null,
      intervalsOver100ms: gaps.filter(v => v > .1).length, intervalsOver500ms: gaps.filter(v => v > .5).length,
      identicalJPEGAdjacentPairs: frames.slice(1).filter((f, i) => f.sha256 === frames[i].sha256).length,
      nonIncreasingIntervals: gaps.filter(v => v <= 0).length,
      firstHostEpochMinusCDPTimestampSecondsDiagnostic: frames[0].receivedHostEpochSeconds - frames[0].timestamp };
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
function increasing(values) { return values.every((value, i) => i === 0 || value > values[i - 1]); }
function timestampUS(value) {
  const match = /^(-?)(\d+)(?:\.(\d{1,6}))?$/.exec(String(value));
  if (!match) throw new Error('Missing or invalid microsecond media timestamp: ' + value);
  const us = BigInt(match[2]) * 1000000n + BigInt((match[3] || '').padEnd(6, '0'));
  return match[1] ? -us : us;
}
if (r.recordingCompleted) {
  try {
    const first = BigInt(frames[0].receivedMonotonicNs), stop = BigInt(r.captureStop.receivedMonotonicNs);
    const offsetsNS = [...frames.map(f => BigInt(f.receivedMonotonicNs) - first), stop - first];
    if (receivedCount !== frames.length || !increasing(offsetsNS) || offsetsNS[0] !== 0n || stop - first <= 5000000000n)
      throw new Error('Invalid complete reception boundaries or missing frame');
    // Subtract in BigInt first. Round absolute offsets once; difference only these rounded values.
    const expectedUS = offsetsNS.map(ns => (ns + 500n) / 1000n);
    if (!increasing(expectedUS)) throw new Error('Microsecond quantization collision or reversal; no PTS repair');
    const beforeClick = BigInt(r.events.find(e => e.name === 'ui-click-before').receivedMonotonicNs);
    const ended = BigInt(r.ended.receivedMonotonicNs), duration = Number(stop - first) / 1e9;
    if (beforeClick - first < 2000000000n || stop - ended < 3000000000n) throw new Error('Opening/final real hold was shortened');
    const lines = ['ffconcat version 1.0'];
    for (let i = 0; i < frames.length; i++) {
      lines.push(`file '../${frames[i].file}'`, 'option framerate 1000000', `duration ${secondsText(expectedUS[i + 1] - expectedUS[i])}`);
    }
    lines.push(`file '../${frames.at(-1).file}'`, 'option framerate 1000000');
    await fs.writeFile(path.join(out, 'raw/timeline.ffconcat'), lines.join('\n') + '\n', { flag: 'wx' });
    r.timeline = { firstReceivedMonotonicNs: first.toString(), stopReceivedMonotonicNs: stop.toString(), durationSeconds: duration,
      expectedPTSUS: expectedUS.map(us => us.toString()),
      maximumRoundingErrorNs: offsetsNS.reduce((max, ns, i) => { const error = absBig(expectedUS[i] * 1000n - ns); return error > max ? error : max; }, 0n).toString(),
      lastImageHoldSeconds: Number(stop - BigInt(frames.at(-1).receivedMonotonicNs)) / 1e9,
      openingToClickSeconds: Number(beforeClick - first) / 1e9, endedToStopSeconds: Number(stop - ended) / 1e9,
      clockMapping: 'All receipt, UI brackets, read-only observations and actual stop acknowledgement use process.hrtime.bigint(). Original CDP and epoch values remain diagnostics; phase transitions have read-only polling resolution, not exact transition times.',
      quantization: 'Each BigInt absolute receipt offset from the first arrival is rounded once to microseconds, then differenced for concat duration. JPEG demux, encoder and MP4 track use microsecond time bases. Output -r 60 is nominal only; VFR passthrough and every measured PTS are checked. One repeated terminal image marks real stop, not another captured event. Its packet may extend the file by at most 20ms, with no shortening beyond 2us.',
      noInterpolationOrTrim: true };
    await publish();
    command('encode', ffmpeg, ['-hide_banner', '-nostdin', '-n', '-f', 'concat', '-safe', '0', '-i', 'raw/timeline.ffconcat',
      '-an', '-r', '60', '-fps_mode', 'passthrough', '-enc_time_base', '1:1000000', '-c:v', 'libx264', '-preset', 'medium',
      '-crf', '20', '-pix_fmt', 'yuv420p', '-threads', '2', '-video_track_timescale', '1000000', '-movflags', '+faststart', 'study.mp4'], 90);
    const video = await fs.readFile(path.join(out, 'study.mp4'));
    r.video = { file: 'study.mp4', bytes: video.length, sha256: hash(video), commitEligible: video.length <= plan.maximumVideoBytes };
    command('probe', ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_streams', '-show_format', '-show_frames', '-show_packets',
      '-show_entries', 'stream=codec_name,width,height,time_base,nb_frames,duration,start_time:format=duration,size:frame=best_effort_timestamp_time,pkt_duration_time,duration_time,width,height:packet=pts_time,duration_time', '-of', 'json', 'study.mp4'], 20);
    const probe = JSON.parse(await fs.readFile(path.join(out, 'probe.stdout.log'), 'utf8'));
    const encodedFrames = probe.frames || probe.packets_and_frames?.filter(row => row.type === 'frame') || [];
    const packets = probe.packets || probe.packets_and_frames?.filter(row => row.type === 'packet') || [];
    const stream = probe.streams?.[0], ptsUS = encodedFrames.map(f => timestampUS(f.best_effort_timestamp_time));
    if (stream?.codec_name !== 'h264' || stream.width !== 1440 || stream.height !== 1100 || stream.time_base !== '1/1000000' ||
        ptsUS.length !== expectedUS.length || ptsUS[0] !== 0n || !increasing(ptsUS))
      throw new Error('Encoded frame count, dimensions, codec, or PTS order mismatch');
    const maximumPTSErrorUS = ptsUS.reduce((max, value, i) => { const error = absBig(value - expectedUS[i]); return error > max ? error : max; }, 0n);
    const mediaDurationUS = timestampUS(probe.format?.duration), mediaDuration = Number(mediaDurationUS) / 1e6;
    const signedTailNS = mediaDurationUS * 1000n - (stop - first);
    const terminalPacket = packets.find(packet => timestampUS(packet.pts_time) === ptsUS.at(-1));
    r.video.probe = { stream, durationSeconds: mediaDuration, frameCount: ptsUS.length, maximumPTSErrorUS: maximumPTSErrorUS.toString(),
      signedDurationMinusStopNs: signedTailNS.toString(), signedDurationMinusStopSeconds: Number(signedTailNS) / 1e9, terminalPacket: terminalPacket || null,
      lastFramePacketDurationTime: encodedFrames.at(-1)?.pkt_duration_time ?? null, lastFrameDurationTime: encodedFrames.at(-1)?.duration_time ?? null };
    if (!terminalPacket || !Number.isFinite(Number(terminalPacket.duration_time)) || maximumPTSErrorUS > 2n ||
        signedTailNS < -2000n || signedTailNS > 20000000n)
      throw new Error('Encoded timing or terminal packet exceeds the fixed microsecond/hold contract');
    // A real raw-frame hash muxer with an explicit time base avoids null-muxer DTS rescaling traps.
    command('decode', ffmpeg, ['-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-n', '-copyts', '-i', 'study.mp4',
      '-map', '0:v:0', '-an', '-fps_mode', 'passthrough', '-enc_time_base', '1:1000000', '-f', 'framemd5', 'raw/decode.framemd5'], 45);
    const decoded = await fs.readFile(path.join(out, 'raw/decode.framemd5'), 'utf8');
    const tb = decoded.match(/^#tb\s+0:\s*(\d+)\/(\d+)/m);
    if (!tb || BigInt(tb[1]) * 1000000n !== BigInt(tb[2])) throw new Error('Decode microsecond time base not reported');
    const decodedPTS = decoded.split(/\r?\n/).filter(line => line && !line.startsWith('#')).map(line => BigInt(line.split(',')[2].trim()));
    if (decodedPTS.length !== ptsUS.length || !increasing(decodedPTS) || decodedPTS.some((v, i) => absBig(v - ptsUS[i]) > 2n))
      throw new Error('Full decode did not preserve every validated timestamp');
    r.video.fullDecode = { passed: true, frames: decodedPTS.length, manifest: 'raw/decode.framemd5', sha256: hash(decoded), timeBase: [Number(tb[1]), Number(tb[2])] };
    await fs.mkdir(path.join(out, 'review'));
    command('review-frames', ffmpeg, ['-hide_banner', '-nostdin', '-v', 'error', '-xerror', '-n', '-i', 'study.mp4',
      '-vf', 'fps=1:start_time=0:round=near:eof_action=pass,scale=960:-2', '-fps_mode', 'passthrough', '-q:v', '3', '-start_number', '0', 'review/second-%03d.jpg'], 40);
    const files = (await fs.readdir(path.join(out, 'review'))).filter(f => /^second-\d+\.jpg$/.test(f)).sort();
    r.review = { periodWallSeconds: 1, width: 960, sourceVideo: { file: r.video.file, sha256: r.video.sha256 }, captureStopOffsetSeconds: duration,
      method: 'FFmpeg fps=1, start_time=0, round=near, eof_action=pass; input PTS are rounded to a one-second output grid with drops/repeats. videoSecond is output PTS, not an exact instantaneous source screenshot or nearest-source-frame selection. Any output PTS beyond actual stop is labeled boundaryHoldBeyondCapture and is not new capture.',
      limitation: 'Ordered still-image reading is not continuous video understanding and cannot settle all movement or rhythm experience.', frames: [] };
    for (const [i, file] of files.entries()) { const bytes = await fs.readFile(path.join(out, 'review', file)); r.review.frames.push({ videoSecond: i, boundaryHoldBeyondCapture: i > duration, file: 'review/' + file, bytes: bytes.length, sha256: hash(bytes) }); }
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
r.noRetry = true; r.stopRecordingLoopAfterFailure = true;
r.timingLimit = 'Node total ends before final receipt/stdout write; supervisor measures the entire child lifetime.';
await publish();
console.log(JSON.stringify({ status: r.status, secondsBeforeReceipt: r.totalWallSecondsBeforeFinalReceipt,
  savedFrames: frames.length, video: r.video, reviewFrames: r.review?.frames.length, failure: r.failure || null, out }));
process.exitCode = r.status === 'completed_recording_and_media' ? 0 : 1;
