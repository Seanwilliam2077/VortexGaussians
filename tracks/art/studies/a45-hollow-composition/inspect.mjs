import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
if (!process.argv.includes('--execute')) {
  console.log('A45: one prepared 150-step source and one normal 22s presentation; <=150s total, <=6 PNG/8MiB, one optional WebM/16MiB. No retry.');
  process.exit(0);
}
const out = path.join(here, 'inspection-01');
await fs.mkdir(out, { recursive: false });
const started = performance.now(), elapsed = () => (performance.now() - started) / 1000;
const sha = b => createHash('sha256').update(b).digest('hex');
const sourceFiles = ['BRIEF.md', 'AUTHOR_SPEC.md', 'WORK_SPEC.md', 'index.html', 'work.css', 'work.mjs', 'inspect.mjs']
  .map(f => path.join(here, f)).concat(['demo/index.html', 'research/lib/runtime.mjs',
    'tracks/art/studies/a44-form-selection/CREATOR_CHOICE.md',
    'tracks/art/studies/a20-room-gift/room.mjs', 'tracks/art/studies/a20-room-gift/WORK_SPEC.md']
    .map(f => path.join(repoRoot, f)));
const result = { schema: 'a45-hollow-composition-1', createdUTC: new Date().toISOString(), status: 'started',
  scope: 'One ordinary source preparation and actual playback. Saved images and execution records do not establish continuous human viewing, artistic contribution, or a score.',
  sources: {}, images: [], video: null, checks: {}, pageErrors: [], console: [], externalRequests: [], closed: {} };
let server, browser, context, page, expired = false;
const save = () => fs.writeFile(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n');
const timer = setTimeout(() => { expired = true; context?.close().catch(() => {}); }, 150000);
const hard = setTimeout(() => process.exit(124), 165000);
const read = () => page.evaluate(() => window.__a45.snapshot());
async function exportExistingArtifacts() {
  const artifacts = await page.evaluate(() => window.__a45.artifacts());
  result.imageBytes ??= 0;
  for (const item of artifacts.images) {
    if (result.images.some(i => i.file === item.file)) continue;
    if (result.images.length >= 6) throw Error('Image count exceeded');
    if (!/^[a-zA-Z0-9._-]+\.png$/.test(item.file) || !item.dataURL.startsWith('data:image/png;base64,')) throw Error('Unexpected image artifact');
    const bytes = Buffer.from(item.dataURL.slice('data:image/png;base64,'.length), 'base64');
    const identityMatches = bytes.length === item.bytes && sha(bytes) === item.sha256;
    const dimensionsMatch = bytes.subarray(0, 8).equals(Buffer.from([137,80,78,71,13,10,26,10]))
      && bytes.readUInt32BE(16) === 720 && bytes.readUInt32BE(20) === 720;
    await fs.writeFile(path.join(out, item.file), bytes, { flag: 'wx' });
    const { dataURL, ...metadata } = item;
    result.images.push({ ...metadata, bytes: bytes.length, sha256: sha(bytes), identityMatches, dimensionsMatch });
    result.imageBytes += bytes.length;
  }
  if (artifacts.video && !result.video) {
    const { base64, ...metadata } = artifacts.video;
    if (!/^[a-zA-Z0-9._-]+\.webm$/.test(metadata.file)) throw Error('Unexpected video artifact');
    const bytes = Buffer.from(base64, 'base64');
    await fs.writeFile(path.join(out, metadata.file), bytes, { flag: 'wx' });
    result.video = { ...metadata, bytes: bytes.length, sha256: sha(bytes),
      identityMatches: bytes.length === metadata.bytes && sha(bytes) === metadata.sha256,
      validation: 'Recorded browser artifact; no external encoding or continuous human viewing.' };
  }
}
try {
  for (const file of sourceFiles) {
    const b = await fs.readFile(file);
    result.sources[path.relative(repoRoot, file).replaceAll('\\', '/')] = { bytes: b.length, sha256: sha(b) };
  }
  server = await startServer();
  const launched = await launchBrowser(); browser = launched.browser;
  result.browser = { module: launched.module, launchOptions: launched.launchOptions, version: browser.version() };
  context = await browser.newContext({ viewport: { width: 1100, height: 1080 }, deviceScaleFactor: 1 });
  await context.route('**/*', async route => {
    const u = route.request().url();
    if (u.startsWith(server.url + '/') || u.startsWith('data:') || u.startsWith('blob:')) await route.continue();
    else { result.externalRequests.push(u); await route.abort(); }
  });
  page = await context.newPage(); page.setDefaultTimeout(100000);
  page.on('pageerror', e => result.pageErrors.push(e.stack || String(e)));
  page.on('console', m => { if (['error', 'warning'].includes(m.type()) && result.console.length < 100) result.console.push({ type: m.type(), text: m.text() }); });
  await page.goto(server.url + '/tracks/art/studies/a45-hollow-composition/', { waitUntil: 'load' });
  await page.waitForFunction(() => ['ready', 'error'].includes(window.__a45?.snapshot().phase), undefined, { polling: 250 });
  result.ready = await read();
  if (result.ready.phase !== 'ready') throw Error('Preparation failed: ' + JSON.stringify(result.ready.errors));
  result.playClickElapsedSeconds = elapsed();
  await page.locator('#play').click();
  await page.waitForFunction(() => {
    const s = window.__a45.snapshot();
    return s.phase === 'error' || (s.phase === 'ended' && s.artifactsReady === true);
  }, undefined, { timeout: 45000, polling: 250 });
  result.final = await read();
  if (result.final.phase !== 'ended') throw Error('Presentation failed: ' + JSON.stringify(result.final.errors));
  await exportExistingArtifacts();
  result.afterArtifactRead = await read();
  const s = result.final, equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  result.checks.completed = result.final.phase === 'ended';
  result.checks.noPageErrorsOrExternalRequests = result.pageErrors.length === 0 && result.externalRequests.length === 0;
  result.checks.noWorkErrors = s.errors.length === 0 && s.snapshotError === null;
  result.checks.oneSource = s.preparationCalls === 1 && s.resetCalls === 1 && s.stepCalls === 150
    && s.renderCalls === 150 && s.bitmapCalls === 150 && s.ignitionCalls === 0;
  result.checks.preparationComplete = s.preparation.complete && s.preparation.steps.length === 150
    && s.sourceInitial.frame === 0 && s.sourceAfterPreparation.frame === 150 && Math.abs(s.sourceAfterPreparation.time-5) < 1e-8;
  result.checks.oneNormalPresentation = s.presentationCalls === 1 && s.playCalls === 1 && s.pauseCalls === 0 && s.leaveCalls === 0
    && s.playback.terminalActualSeconds >= 22 && s.playback.pausedWallMs === 0;
  result.checks.physicsUnchangedInPresentation = s.sourceUnchangedDuringPresentation === true
    && equal(s.sourceAfterPreparation, s.sourceAfterPresentation) && equal(s.material, s.sourceAfterPresentation);
  result.checks.readOnlyArtifactExport = equal(result.final, result.afterArtifactRead);
  result.checks.centerBlack = s.center.allPureBlack && s.center.nonBlackPixels === 0 && s.center.checks === s.compositeCalls && s.compositeCalls > 0;
  result.checks.fourFixedFreezes = s.freezes.length === 4 && s.freezes.every((f,i) => f.observed
    && f.side === ['top','right','bottom','left'][i] && f.sourceFrame === [60,90,120,150][i] && f.actualSeconds >= [4,6,8,10][i]);
  result.checks.allDisplayedFramesFollowClock = s.displayLog.every(d => {
    const n = Math.min(150, 1 + Math.floor(15*Math.max(0,d.actualSeconds)));
    return equal(d.sourceFrames, {top:d.actualSeconds>=4?60:n, right:d.actualSeconds>=6?90:n,
      bottom:d.actualSeconds>=8?120:n, left:d.actualSeconds>=10?150:n});
  });
  result.checks.cleanupComplete = s.cleanup.complete && s.cleanup.bitmapsCreated === 150 && s.cleanup.bitmapsClosed === 150
    && s.cleanup.bitmapLiveCount === 0 && !s.preparation.bitmapInFlight && !s.cleanup.ownRAFOutstanding
    && s.cleanup.sourceDetached && s.cleanup.stagingReleased && s.cleanup.streamTracksStopped;
  result.checks.artifactIdentity = result.images.every(i => i.identityMatches && i.dimensionsMatch) && (!result.video || result.video.identityMatches);
  result.checks.oneRecordingAttempt = s.recording.attempts === 1 && s.recording.audioTracks === 0;
  result.checks.imageBudget = result.images.length <= 6 && result.imageBytes <= 8 * 1024 * 1024;
  result.checks.videoBudget = !result.video || result.video.bytes <= 16 * 1024 * 1024;
  result.checks.sourcesUnchanged = true;
  for (const file of sourceFiles) {
    const k = path.relative(repoRoot, file).replaceAll('\\', '/');
    if (sha(await fs.readFile(file)) !== result.sources[k].sha256) result.checks.sourcesUnchanged = false;
  }
  result.checks.withinDeadline = !expired;
  if (!Object.values(result.checks).every(Boolean)) throw Error('A behavior or source check failed');
  result.status = 'completed_single_hollow_presentation';
} catch (e) {
  result.status = 'failed'; result.error = { message: e.message, stack: e.stack }; process.exitCode = 1;
  if (page) try { result.atFailure = await read(); } catch {}
  if (page) try { await exportExistingArtifacts(); } catch (artifactError) { result.partialArtifactExportError = artifactError.message; }
} finally {
  clearTimeout(timer);
  if (context) await context.close().then(() => result.closed.context = true, e => result.closed.context = e.message);
  if (browser) await browser.close().then(() => result.closed.browser = true, e => result.closed.browser = e.message);
  if (server) await server.close().then(() => result.closed.server = true, e => result.closed.server = e.message);
  result.wallSeconds = elapsed(); await save(); clearTimeout(hard);
  console.log(JSON.stringify({ status: result.status, wallSeconds: result.wallSeconds, images: result.images.length, imageBytes: result.imageBytes, videoBytes: result.video?.bytes, checks: result.checks, error: result.error }));
}
