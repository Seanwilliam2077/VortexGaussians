import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
if (!process.argv.includes('--execute')) {
  console.log('A42: one 3+1.5+1.5s material qualification, one handover, <=120s, <=5 PNG/8MiB; no retry.');
  process.exit(0);
}
const out = path.join(here, 'inspection-01');
await fs.mkdir(out, { recursive: false });
const started = performance.now();
const elapsed = () => (performance.now() - started) / 1000;
const sha = b => createHash('sha256').update(b).digest('hex');
const sourceFiles = [
  'BRIEF.md', 'WORK_SPEC.md', 'index.html', 'sample.mjs', 'bridge.js',
  'assemble.mjs', 'assembly.json', 'renderer.generated.html', 'inspect.mjs'
].map(f => path.join(here, f)).concat([
  path.join(repoRoot, 'demo/index.html'), path.join(repoRoot, 'research/lib/runtime.mjs'),
  path.join(repoRoot, 'tracks/art/studies/a39-handover-clock-maintenance/work.css'),
  path.join(repoRoot, 'tracks/art/studies/a41-inherited-apology-material/BRIEF.md'),
  path.join(repoRoot, 'tracks/art/studies/a40-material-handover-choice/CREATOR_CHOICE.md')
]);
const result = {
  schema: 'a42-inherited-apology-material-1', createdUTC: new Date().toISOString(),
  status: 'started', scope: 'One fixed material instrument sequence; not a completed artwork, participant, continuous viewing or artistic score.',
  sources: {}, images: [], actions: [], checks: {}, pageErrors: [], console: [],
  externalRequests: [], imageBytes: 0, closed: {}
};
let server, browser, context, page, deadline = false;
const timer = setTimeout(() => { deadline = true; context?.close().catch(() => {}); }, 120000);
const hard = setTimeout(() => process.exit(124), 140000);
const save = () => fs.writeFile(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n');
const read = () => page.evaluate(() => window.__a42.snapshot());
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const group = (s, name) => s.material.points.filter(p => p.group === name);
const sum = (pts, key) => pts.reduce((n, p) => n + p[key], 0);
const identity = s => ({ phase: s.phase, frame: s.frame, hash: s.hash,
  stepCalls: s.stepCalls, ignitionCalls: s.ignitionCalls,
  snapshotSHA256: sha(JSON.stringify(s)), snapshotError: s.snapshotError });
async function shot(label) {
  if (result.images.length >= 5) throw Error('Image-count budget exhausted');
  const before = await read(), file = label + '.png';
  await page.screenshot({ path: path.join(out, file), fullPage: true });
  const bytes = await fs.readFile(path.join(out, file));
  result.imageBytes += bytes.length;
  const after = await read();
  result.images.push({ file, bytes: bytes.length, sha256: sha(bytes),
    before: identity(before), after: identity(after), completeSnapshotEqual: equal(before, after),
    inspectionElapsedSeconds: elapsed() });
  await save();
  if (result.imageBytes > 8 * 1024 * 1024) throw Error('Image-byte budget exhausted');
}
async function act(button, expectedPhase, expectedFrame) {
  const before = await read();
  result.actions.push({ button, beforePhase: before.phase, beforeFrame: before.frame });
  await page.locator('#' + button).click();
  await page.waitForFunction(phase => ['error', phase].includes(window.__a42.snapshot().phase), expectedPhase, { timeout: 40000 });
  const after = await read();
  if (after.phase === 'error') throw Error('Instrument failed: ' + JSON.stringify(after.errors));
  if (after.phase !== expectedPhase || after.frame !== expectedFrame) throw Error('Unexpected stage/frame after ' + button);
  result.actions.at(-1).afterPhase = after.phase;
  result.actions.at(-1).afterFrame = after.frame;
  return after;
}
try {
  for (const file of sourceFiles) {
    const bytes = await fs.readFile(file);
    result.sources[path.relative(repoRoot, file).replaceAll('\\', '/')] = { bytes: bytes.length, sha256: sha(bytes) };
  }
  server = await startServer();
  const launched = await launchBrowser(); browser = launched.browser;
  result.browser = { module: launched.module, launchOptions: launched.launchOptions, version: browser.version() };
  context = await browser.newContext({ viewport: { width: 1360, height: 1100 } });
  await context.route('**/*', async route => {
    const u = route.request().url();
    if (u.startsWith(server.url + '/') || u.startsWith('data:') || u.startsWith('blob:')) await route.continue();
    else { result.externalRequests.push(u); await route.abort(); }
  });
  page = await context.newPage(); page.setDefaultTimeout(25000);
  page.on('pageerror', e => result.pageErrors.push(e.stack || String(e)));
  page.on('console', m => { if (['error', 'warning'].includes(m.type()) && result.console.length < 100) result.console.push({ type: m.type(), text: m.text() }); });
  await page.goto(server.url + '/tracks/art/studies/a42-inherited-apology-local-build/', { waitUntil: 'load' });
  await page.waitForFunction(() => ['ready', 'error'].includes(window.__a42?.snapshot().phase));
  result.initial = await read();
  if (result.initial.phase !== 'ready' || result.initial.frame !== 0) throw Error('Initial instrument not ready');
  await shot('01-ready');
  result.first = await act('first', 'first-held', 180);
  await shot('02-first-three-seconds');
  result.handed = await act('handover', 'handed', 180);
  await shot('03-handed-three-seconds');
  result.later = await act('later', 'later-held', 270);
  await shot('04-later-four-point-five');
  result.final = await act('finish', 'ended', 360);
  await shot('05-final-six-seconds');
  const stages = [result.initial, result.first, result.handed, result.later, result.final];
  const oldBefore = group(result.first, 'apology'), oldAfter = group(result.handed, 'apology');
  const introduced = group(result.handed, 'request');
  result.materialObservations = stages.map(s => ({
    phase: s.phase, frame: s.frame,
    groups: Object.fromEntries([...new Set(s.material.points.map(p => p.group))].map(name => {
      const pts = group(s, name);
      return [name, { count: pts.length, fuelSum: sum(pts, 'fuel'), charSum: sum(pts, 'char'), glowSum: sum(pts, 'glow'),
        burning: pts.filter(p => p.state === 1).length, fuelDepleted: pts.filter(p => p.state === 2).length }];
    }))
  }));
  result.checks.exactFrames = equal(stages.map(s => s.frame), [0, 180, 180, 270, 360]);
  result.checks.oneReset = stages.every(s => s.resetCalls === 1);
  result.checks.twoIgnitions = equal(stages.map(s => s.ignitionCalls), [0, 1, 1, 2, 2]);
  result.checks.exactStepCalls = equal(stages.map(s => s.stepCalls), [0, 180, 180, 270, 360]);
  result.checks.oneHandover = equal(stages.map(s => s.handoverCalls), [0, 0, 1, 1, 1]);
  result.checks.oldMaterialPreserved = oldBefore.length > 0 && equal(oldBefore, oldAfter);
  result.checks.newRequestUnburned = introduced.length > 0 && introduced.every(p => p.state === 0 && p.heat === 0 && p.glow === 0 && p.char === 0 && p.fuel === 1 && p.fuelInitial === 1);
  result.checks.replacedOnlyLowerGroup = equal([...new Set(result.first.material.points.map(p => p.group))].sort(), ['apology', 'release'])
    && equal([...new Set(result.handed.material.points.map(p => p.group))].sort(), ['apology', 'request']);
  result.checks.handoverKeepsTimeAndParticles = result.first.material.time === result.handed.material.time
    && result.first.material.frame === result.handed.material.frame
    && result.first.material.seed === result.handed.material.seed
    && result.first.material.randomDraws === result.handed.material.randomDraws
    && result.first.material.particleStateHash === result.handed.material.particleStateHash;
  result.checks.handoverKeepsCounters = equal(result.first.material.counters, result.handed.material.counters);
  result.checks.noScreenshotAdvance = result.images.every(x => x.completeSnapshotEqual && !x.before.snapshotError && !x.after.snapshotError
    && x.before.frame === x.after.frame && x.before.hash === x.after.hash
    && x.before.stepCalls === x.after.stepCalls && x.before.ignitionCalls === x.after.ignitionCalls);
  result.checks.handoverAssertions = result.handed.handover?.passed === true
    && Object.values(result.handed.handover.assertions).every(v => v === true);
  result.checks.correctDirectIgnitions = result.final.ignitions.length === 2
    && result.final.ignitions.every(x => x.passed && x.called && x.newlyLit > 0)
    && result.final.ignitions[1].intendedGroup === 'request'
    && result.final.ignitions[1].directlyTouchedApology === false;
  result.checks.noErrors = stages.every(s => Array.isArray(s.errors) && s.errors.length === 0)
    && result.pageErrors.length === 0 && result.console.length === 0 && result.externalRequests.length === 0;
  result.checks.sourcesUnchanged = true;
  for (const file of sourceFiles) {
    const key = path.relative(repoRoot, file).replaceAll('\\', '/');
    if (sha(await fs.readFile(file)) !== result.sources[key].sha256) result.checks.sourcesUnchanged = false;
  }
  result.checks.withinDeadline = !deadline;
  if (!Object.values(result.checks).every(v => v === true)) throw Error('A predeclared behavior/source check failed');
  // Store common geometry and the verbose transfer proof once. Stage material
  // points, counters, input records and costs remain complete; no arrays are
  // compressed, discarded or changed to improve a material outcome.
  result.sharedGeometry = result.initial.geometry;
  result.handoverReport = result.handed.handover;
  result.recordStorage = 'Stage geometry and handover proofs use explicit shared references. pointGroups are derivable from each full material.points array. Screenshot records retain exact full-snapshot equality and SHA256 rather than duplicate payloads.';
  for (const s of stages) {
    if (equal(s.geometry, result.sharedGeometry)) {
      delete s.geometry; s.geometryReference = 'sharedGeometry';
    }
    if (s.handover && equal(s.handover, result.handoverReport)) {
      delete s.handover; s.handoverReference = 'handoverReport';
    }
    if (s.evidence?.handoverReport && equal(s.evidence.handoverReport, result.handoverReport)) {
      delete s.evidence.handoverReport; s.evidence.handoverReportReference = 'handoverReport';
    }
    delete s.pointGroups;
  }
  result.status = 'completed_single_inherited_apology_material';
} catch (e) {
  result.status = 'failed'; result.error = { message: e.message, stack: e.stack };
  if (page) try { result.atFailure = await read(); } catch {}
  process.exitCode = 1;
} finally {
  clearTimeout(timer);
  if (context) await context.close().then(() => result.closed.context = true, e => result.closed.context = e.message);
  if (browser) await browser.close().then(() => result.closed.browser = true, e => result.closed.browser = e.message);
  if (server) await server.close().then(() => result.closed.server = true, e => result.closed.server = e.message);
  result.wallSeconds = elapsed(); await save(); clearTimeout(hard);
  console.log(JSON.stringify({ status: result.status, wallSeconds: result.wallSeconds, images: result.images.length, imageBytes: result.imageBytes, checks: result.checks, error: result.error }));
}
