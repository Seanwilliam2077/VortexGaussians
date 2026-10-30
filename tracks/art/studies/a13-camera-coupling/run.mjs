// One fixed A13 five-arm attempt. Preparation is inert without --execute.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { isDeepStrictEqual } from 'node:util';
import { gzipSync } from 'node:zlib';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const began = performance.now(), wall = () => (performance.now() - began) / 1000;
const here = path.dirname(fileURLToPath(import.meta.url)), out = path.join(here, 'run-01');
const arms = [
  { id: 'view-yaw0', sliceMode: 'view', yaw: 0 },
  { id: 'view-yaw05', sliceMode: 'view', yaw: .5 },
  { id: 'world-yaw0', sliceMode: 'world', yaw: 0 },
  { id: 'world-yaw05', sliceMode: 'world', yaw: .5 },
  { id: 'view-yaw0-repeat', sliceMode: 'view', yaw: 0 },
];
const plan = { attemptCount: 1, loads: 1, resets: 5, arms, seed: 20261027,
  asset: 'static/test_scene.ply', expectedPoints: 45808, sceneMax: 800000,
  ignition: { x: 0, y: .65, z: 0, radius: .30 }, steps: 360, dt: 1 / 60,
  sampleEverySteps: 30, samplesPerArm: 13, explicitRendersPerArm: 2,
  viewport: { width: 640, height: 480 }, browserLimitSeconds: 240,
  workerLimitSeconds: 270, supervisorLimitSeconds: 300, out };
if (!process.argv.includes('--execute')) { console.log(JSON.stringify(plan, null, 2)); process.exit(0); }
if (!process.env.PLAYWRIGHT_MODULE || !process.env.BROWSER_EXECUTABLE)
  throw new Error('Explicit existing Playwright and browser paths are required');
await fs.mkdir(out, { recursive: false });
await fs.mkdir(path.join(out, 'raw'));

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
// Preserve nonfinite exports as explicit markers in failure evidence, never silent JSON nulls.
const json = value => JSON.stringify(value, (_, v) => typeof v === 'number' && !Number.isFinite(v)
  ? { nonFiniteNumber: String(v) } : v, 2) + '\n';
const sourceNames = ['demo/index.html', 'research/lib/runtime.mjs', 'static/test_scene.ply',
  ...['PROTOCOL.md', 'run.mjs', 'execute.py'].map(n => 'tracks/art/studies/a13-camera-coupling/' + n)];
const sourceHashes = async () => Object.fromEntries(await Promise.all(sourceNames.map(async name => {
  const data = await fs.readFile(path.join(repoRoot, name));
  return [name, { bytes: data.length, sha256: sha256(data) }];
})));
const result = { schema: 'a13-camera-coupling-v1', createdUTC: new Date().toISOString(), plan,
  status: 'running', arms: [], errors: [], console: [], blockedExternal: [], requestFailures: [],
  resourcesAcquired: { context: false, browser: false, server: false },
  resourcesClosed: { context: true, browser: true, server: true }, workflowCompleted: false,
  runtime: { node: process.version, playwrightModule: process.env.PLAYWRIGHT_MODULE,
    browserExecutable: process.env.BROWSER_EXECUTABLE },
  scope: 'One fixed synthetic art-material experiment; no artistic, physical, audience, or TOG claim.',
  exportedStateLimit: 'Equality covers public exported fields only, not all hidden internal state.',
  costScope: 'This art-material worker cost is separate from the specified TOG subprocess subtotal of 2017.6732525997795 seconds; neither is total project cost. Preparation and reading are excluded.' };
const publish = async () => {
  const pending = path.join(out, 'result.pending.json');
  await fs.writeFile(pending, json(result));
  await fs.rename(pending, path.join(out, 'result.json'));
};
const summary = ({ points, ...rest }) => rest;
function comparable(snapshot, excluded = ['yaw', 'sliceMode']) {
  const copy = { ...snapshot, params: { ...snapshot.params } };
  for (const key of excluded) delete copy.params[key];
  return copy;
}
function differencePaths(a, b, prefix = '', found = [], limit = 20) {
  if (isDeepStrictEqual(a, b) || found.length >= limit) return found;
  if (!a || !b || typeof a !== 'object' || typeof b !== 'object') {
    found.push(prefix || '(root)'); return found;
  }
  for (const key of new Set([...Object.keys(a), ...Object.keys(b)])) {
    differencePaths(a[key], b[key], prefix ? `${prefix}.${key}` : key, found, limit);
    if (found.length >= limit) break;
  }
  return found;
}
function finiteExport(value, where = 'snapshot') {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error(`Nonfinite export: ${where}`);
  if (value && typeof value === 'object')
    for (const [key, child] of Object.entries(value)) finiteExport(child, `${where}.${key}`);
}
function validate(snapshot, detail = false) {
  finiteExport(snapshot);
  if (snapshot.scene.count !== plan.expectedPoints) throw new Error('Unexpected scene point count');
  if (detail) {
    if (snapshot.points.length !== plan.expectedPoints) throw new Error('Missing detail points');
    const ids = new Set();
    for (const point of snapshot.points) {
      if (typeof point.id !== 'string' || ids.has(point.id)) throw new Error('Missing or duplicate point id');
      ids.add(point.id);
      if (!Array.isArray(point.position) || point.position.length !== 3 || point.position.some(v => !Number.isFinite(v)))
        throw new Error(`Invalid point position: ${point.id}`);
      for (const field of ['heat', 'fuel', 'char', 'glow', 'fuelInitial', 'state'])
        if (!Number.isFinite(point[field])) throw new Error(`Invalid ${field}: ${point.id}`);
    }
  }
}
async function raw(arm, phase, snapshot) {
  const text = json(snapshot), bytes = gzipSync(text), file = `raw/${arm.id}-${phase}.json.gz`;
  await fs.writeFile(path.join(out, file), bytes, { flag: 'wx' });
  const identity = { file, gzipBytes: bytes.length, gzipSHA256: sha256(bytes),
    jsonBytes: Buffer.byteLength(text), jsonSHA256: sha256(text), pointCount: snapshot.points.length };
  arm.raw[phase] = identity;
  await publish();
  validate(snapshot, true);
  return identity;
}
function comparePoints(a, b) {
  const fields = ['heat', 'fuel', 'char', 'glow'];
  const report = { comparedPoints: Math.min(a.length, b.length), samePointSetAndOrder: a.length === b.length,
    samePositions: a.length === b.length, allExportedFieldsEqual: a.length === b.length,
    differingPointCount: 0, burnValueDifferingPointCount: 0, stateDifferingPointCount: 0,
    maxAbsDifference: Object.fromEntries(fields.map(k => [k, 0])), stateTransitions: {}, firstDifferentIds: [] };
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const p = a[i], q = b[i];
    if (p.id !== q.id) report.samePointSetAndOrder = false;
    if (!isDeepStrictEqual(p.position, q.position)) report.samePositions = false;
    if (!isDeepStrictEqual(p, q)) {
      report.allExportedFieldsEqual = false; report.differingPointCount++;
      if (report.firstDifferentIds.length < 12) report.firstDifferentIds.push([p.id, q.id]);
    }
    if (fields.some(k => p[k] !== q[k])) report.burnValueDifferingPointCount++;
    if (p.state !== q.state) {
      report.stateDifferingPointCount++;
      const transition = `${p.state}->${q.state}`;
      report.stateTransitions[transition] = (report.stateTransitions[transition] || 0) + 1;
    }
    for (const field of fields) report.maxAbsDifference[field] = Math.max(report.maxAbsDifference[field], Math.abs(p[field] - q[field]));
  }
  return report;
}
function compareTrace(a, b) {
  const samples = a.map((sample, i) => ({ frame: sample.frame, time: sample.time,
    equal: isDeepStrictEqual(comparable(sample), comparable(b[i])),
    randomDraws: [sample.randomDraws, b[i]?.randomDraws],
    differencePaths: differencePaths(comparable(sample), b[i] ? comparable(b[i]) : undefined) }));
  const firstDifference = samples.find(s => !s.equal) || null;
  const firstRandomDivergence = samples.find(s => s.randomDraws[0] !== s.randomDraws[1]) || null;
  return { equal: a.length === b.length && samples.every(s => s.equal),
    excludedFields: ['params.yaw', 'params.sliceMode'], firstDifferentSample: firstDifference,
    firstRandomDrawDivergenceSample: firstRandomDivergence, samples,
    interpretation: firstRandomDivergence
      ? 'Random-call counts diverged: subsequent differences describe the whole causal chain with random feedback, not an isolated direct geometric effect.'
      : 'No random-call-count divergence at sampled times; this does not prove identical hidden event correspondence.',
    temporalResolution: 'First divergence is localized only to the saved 30-step samples, not an exact first divergent step.' };
}
function observerCheck(before, after, excluded) {
  const a = comparable(before, excluded), b = comparable(after, excluded);
  return { equal: isDeepStrictEqual(a, b), excludedFields: excluded.map(k => 'params.' + k),
    differencePaths: differencePaths(a, b), afterSummary: summary(after) };
}

let server, browser, context, page, watchdog, browserStart;
let baselineInitial, baselineIgnited, baselineIgnitionIds;
const finals = [];
const healthy = () => {
  if (result.watchdogFired || (browserStart !== undefined && wall() - browserStart >= plan.browserLimitSeconds))
    throw new Error('Browser phase deadline reached; no retry');
  if (result.errors.length || result.blockedExternal.length) throw new Error('Browser error or blocked external request; see retained diagnostics');
};
async function closeResource(key, handle, close) {
  if (!handle) return;
  let timer;
  try {
    await Promise.race([close(), new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('cleanup timeout')), 6000); })]);
    result.resourcesClosed[key] = true;
  } catch (e) { result.resourcesClosed[key] = false; result.errors.push({ source: 'cleanup', resource: key, message: e.message }); }
  finally { clearTimeout(timer); }
}
try {
  result.sourceHashesBefore = await sourceHashes(); await publish();
  browserStart = wall(); result.browserStartedWallSeconds = browserStart;
  watchdog = setTimeout(() => {
    result.watchdogFired = true;
    result.errors.push({ source: 'watchdog', wallSeconds: wall(), message: '240-second browser limit reached' });
    if (browser) void browser.close().catch(e => result.errors.push({ source: 'watchdog-close', message: e.message }));
  }, plan.browserLimitSeconds * 1000);
  server = await startServer(); result.resourcesAcquired.server = true; result.resourcesClosed.server = false;
  result.server = { url: server.url, scope: 'fresh ephemeral loopback server' };
  const launch = await launchBrowser(process.env.BROWSER_EXECUTABLE);
  browser = launch.browser; result.resourcesAcquired.browser = true; result.resourcesClosed.browser = false;
  result.runtime.browserVersion = browser.version(); result.runtime.launchOptions = launch.launchOptions;
  if (launch.module !== process.env.PLAYWRIGHT_MODULE) throw new Error('Unexpected Playwright module fallback');
  healthy();
  context = await browser.newContext({ viewport: plan.viewport, deviceScaleFactor: 1, serviceWorkers: 'block' });
  result.resourcesAcquired.context = true; result.resourcesClosed.context = false;
  result.context = { persistent: false, storageStateProvided: false, serviceWorkers: 'block', deviceScaleFactor: 1 };
  await context.route('**/*', async route => {
    const url = route.request().url(), parsed = new URL(url);
    if (parsed.origin === server.url || ['data:', 'blob:', 'about:'].includes(parsed.protocol)) await route.continue();
    else { result.blockedExternal.push({ wallSeconds: wall(), url }); await route.abort('blockedbyclient'); }
  });
  page = await context.newPage(); page.setDefaultTimeout(12000);
  page.on('pageerror', e => result.errors.push({ source: 'pageerror', wallSeconds: wall(), message: e.message, stack: e.stack }));
  page.on('console', message => {
    if (['warning', 'error'].includes(message.type())) {
      const item = { wallSeconds: wall(), type: message.type(), text: message.text(), location: message.location() };
      result.console.push(item);
      if (message.type() === 'error') result.errors.push({ source: 'console', ...item });
    }
  });
  page.on('requestfailed', request => result.requestFailures.push({ wallSeconds: wall(), url: request.url(), failure: request.failure() }));
  await page.goto(server.url + '/demo/?embed=1&solver=vpm&orbit=0', { waitUntil: 'load', timeout: 12000 });
  await page.waitForFunction(() => window.__demo?.research?.snapshot);
  result.asset = await page.evaluate(async asset => {
    const d = window.__demo;
    d.forceSize(640, 480);
    const response = await fetch('/' + asset);
    if (!response.ok) throw new Error('PLY fetch failed: ' + response.status);
    const loaded = d.loadPLY(await response.arrayBuffer());
    const canvas = document.querySelector('#cv'), bounds = canvas.getBoundingClientRect();
    return { loaded, sceneScale: d.P.sceneScale, sceneSH: d.P.sceneSH, sceneMax: d.P.sceneMax,
      sceneCount: d.sceneN, canvas: { width: canvas.width, height: canvas.height, cssWidth: bounds.width, cssHeight: bounds.height } };
  }, plan.asset);
  if (result.asset.loaded.kept !== plan.expectedPoints || result.asset.sceneCount !== plan.expectedPoints || result.asset.sceneMax !== plan.sceneMax)
    throw new Error('PLY point count or default maximum changed; stop without alternate asset');
  if (Object.entries(result.asset.canvas).some(([k, v]) => v !== (k.toLowerCase().includes('width') ? 640 : 480)))
    throw new Error('Canvas size is not 640x480');
  result.fixedParams = { solver: 'vpm', dimMode: 'layer', layers: 9, simLayers: 9, ppl: 600,
    paused: true, orbit: false, emitterOn: false, spreadOn: false, spreadFlameHeat: true, spreadSceneFeed: true,
    spreadClockMode: 'legacy', spreadParticlePolicy: 'block', spreadMeasureMode: 'legacy',
    sceneOn: true, box: false, sceneMax: plan.sceneMax, sceneScale: result.asset.sceneScale,
    sceneSH: result.asset.sceneSH, sceneLift: .6, sceneYaw: 0, scenePitch: 0, sceneOffX: 0, sceneOffZ: 0 };
  await publish(); healthy();
  for (const definition of arms) {
    healthy();
    const arm = { ...definition, startedWallSeconds: wall(), raw: {}, snapshots: [], completed: false, explicitRenders: 0 };
    result.arms.push(arm); await publish();
    try {
      const initial = await page.evaluate(({ seed, params, yaw }) => {
        const r = window.__demo.research; r.reset(seed, params); r.camera(yaw);
        return r.snapshot({ detail: true });
      }, { seed: plan.seed, params: { ...result.fixedParams, sliceMode: arm.sliceMode, yaw: arm.yaw }, yaw: arm.yaw });
      await raw(arm, 'initial', initial); arm.initialSummary = summary(initial);
      if (!baselineInitial) baselineInitial = initial;
      arm.initialVsFirst = comparePoints(baselineInitial.points, initial.points);
      const renderedInitial = await page.evaluate(() => {
        const d = window.__demo; d.render(); d.gl.finish(); return d.research.snapshot({ detail: true });
      });
      arm.explicitRenders++;
      arm.initialRender = observerCheck(initial, renderedInitial, []);
      if (!arm.initialRender.equal) await raw(arm, 'initial-after-render-mismatch', renderedInitial);
      validate(renderedInitial, true);
      const ignition = await page.evaluate(p => {
        const d = window.__demo, lit = d.ignite(p.x, p.y, p.z, p.radius);
        d.research.setParams({ spreadOn: true });
        return { lit, snapshot: d.research.snapshot({ detail: true }) };
      }, plan.ignition);
      await raw(arm, 'ignited', ignition.snapshot);
      arm.ignitionCount = ignition.lit;
      const ignitionIds = ignition.snapshot.points.filter((p, i) => p.state !== initial.points[i].state).map(p => p.id);
      if (!baselineIgnited) { baselineIgnited = ignition.snapshot; baselineIgnitionIds = ignitionIds; }
      arm.ignitionSet = { count: ignitionIds.length, sha256: sha256(JSON.stringify(ignitionIds)),
        equalsFirstByDirectComparison: isDeepStrictEqual(ignitionIds, baselineIgnitionIds),
        countMatchesReturn: ignitionIds.length === ignition.lit, nonempty: ignition.lit > 0 };
      arm.ignitedVsFirst = comparePoints(baselineIgnited.points, ignition.snapshot.points);
      arm.snapshots.push(summary(ignition.snapshot)); await publish();
      for (let step = 30; step <= 360; step += 30) {
        healthy();
        const snapshot = await page.evaluate(({ n, dt }) => window.__demo.research.step(n, dt), { n: 30, dt: plan.dt });
        arm.snapshots.push(snapshot); await publish(); validate(snapshot);
        if (snapshot.frame !== step) throw new Error('Unexpected sampled frame');
      }
      const final = await page.evaluate(() => window.__demo.research.snapshot({ detail: true }));
      await raw(arm, 'final', final);
      arm.finalSummaryMatchesLastSample = isDeepStrictEqual(summary(final), arm.snapshots.at(-1));
      arm.finalVsInitialIdentity = { samePointSetAndOrder: initial.points.every((p, i) => p.id === final.points[i].id),
        samePositions: initial.points.every((p, i) => isDeepStrictEqual(p.position, final.points[i].position)) };
      finals.push(final);
      const observed = await page.evaluate(() => {
        const d = window.__demo; d.research.camera(0);
        const beforeRender = d.research.snapshot({ detail: true });
        d.render(); d.gl.finish();
        return { beforeRender, afterRender: d.research.snapshot({ detail: true }) };
      });
      arm.explicitRenders++;
      arm.finalCameraChange = observerCheck(final, observed.beforeRender, ['yaw']);
      arm.finalRender = observerCheck(observed.beforeRender, observed.afterRender, []);
      if (!arm.finalCameraChange.equal) await raw(arm, 'final-after-camera-mismatch', observed.beforeRender);
      if (!arm.finalRender.equal) await raw(arm, 'final-after-render-mismatch', observed.afterRender);
      validate(observed.beforeRender, true); validate(observed.afterRender, true);
      const file = `${arm.id}.png`, image = await page.locator('#cv').screenshot({ path: path.join(out, file), type: 'png', timeout: 10000 });
      arm.screenshot = { file, bytes: image.length, sha256: sha256(image), yaw: 0,
        width: image.readUInt32BE(16), height: image.readUInt32BE(20) };
      if (arm.screenshot.width !== 640 || arm.screenshot.height !== 480) throw new Error('Screenshot is not 640x480');
      healthy(); arm.completed = true;
    } finally { arm.endedWallSeconds = wall(); arm.wallSeconds = arm.endedWallSeconds - arm.startedWallSeconds; await publish(); }
  }
  result.comparisons = {};
  for (const [name, a, b] of [['viewYaw', 0, 1], ['worldYawControl', 2, 3], ['viewRepeatControl', 0, 4]])
    result.comparisons[name] = { arms: [arms[a].id, arms[b].id], points: comparePoints(finals[a].points, finals[b].points),
      trace: compareTrace(result.arms[a].snapshots, result.arms[b].snapshots) };
  result.workflowCompleted = true;
} catch (e) { result.failure = { wallSeconds: wall(), message: e.message, stack: e.stack }; }
finally {
  clearTimeout(watchdog);
  await closeResource('context', context, () => context.close());
  await closeResource('browser', browser, () => browser.close());
  await closeResource('server', server, () => server.close());
  result.browserPhaseWallSeconds = browserStart === undefined ? 0 : wall() - browserStart;
  try {
    result.sourceHashesAfter = await sourceHashes();
    result.sourcesUnchanged = isDeepStrictEqual(result.sourceHashesBefore, result.sourceHashesAfter);
  } catch (e) { result.sourcesUnchanged = false; result.errors.push({ source: 'source-hash', message: e.message }); }
  const c = result.comparisons;
  result.qualification = {
    fiveArmsCompleted: result.workflowCompleted && result.arms.length === 5 && result.arms.every(a => a.completed),
    allSamplesAndRenders: result.arms.length === 5 && result.arms.every(a => a.snapshots.length === 13 && a.snapshots[0].frame === 0 && a.snapshots.at(-1).frame === 360 && a.explicitRenders === 2),
    sameInitialPointsAndIgnition: result.arms.length === 5 && result.arms.every(a => a.initialVsFirst?.allExportedFieldsEqual && a.ignitedVsFirst?.allExportedFieldsEqual && a.ignitionSet?.equalsFirstByDirectComparison && a.ignitionSet.countMatchesReturn && a.ignitionSet.nonempty),
    unchangedPointIdentity: result.arms.length === 5 && result.arms.every(a => a.finalVsInitialIdentity?.samePointSetAndOrder && a.finalVsInitialIdentity?.samePositions),
    observersPure: result.arms.length === 5 && result.arms.every(a => a.initialRender?.equal && a.finalCameraChange?.equal && a.finalRender?.equal && a.finalSummaryMatchesLastSample),
    repeatControl: !!(c?.viewRepeatControl?.points?.allExportedFieldsEqual && c.viewRepeatControl.trace.equal),
    worldControl: !!(c?.worldYawControl?.points?.allExportedFieldsEqual && c.worldYawControl.trace.equal),
    noExecutionFailure: !result.failure && !result.errors.length && !result.blockedExternal.length && !result.watchdogFired,
    browserWithinBudget: result.browserPhaseWallSeconds <= plan.browserLimitSeconds,
    workerWithinBudget: wall() <= plan.workerLimitSeconds,
    sourcesUnchanged: result.sourcesUnchanged, resourcesClosed: Object.values(result.resourcesClosed).every(v => v === true),
  };
  result.qualified = Object.values(result.qualification).every(v => v === true);
  result.status = result.qualified ? 'completed_qualified' : 'not_attributable';
  result.materialConclusion = !result.qualified ? 'Not attributable under the fixed protocol; preserve this attempt and do not rerun or tune.'
    : c.viewYaw.points.differingPointCount === 0 ? 'No exported per-point difference in this fixed six-second configuration; this does not establish absence across the whole model.'
      : 'View yaw changed exported per-point material state in this fixed configuration; consult direct differences and random-call divergence before interpreting the causal chain. Artistic value is unassessed.';
  result.totalWallSecondsBeforeFinalReceipt = wall();
  result.noFurtherAttempts = true;
  result.timingLimit = 'Node wall time ends before final receipt/stdout writing; supervisor records the entire child lifetime.';
  await publish();
}
console.log(JSON.stringify({ status: result.status, qualified: result.qualified,
  workerSecondsBeforeReceipt: result.totalWallSecondsBeforeFinalReceipt, out,
  failure: result.failure?.message || null, diagnosticCounts: { errors: result.errors.length,
    consoleWarningsAndErrors: result.console.length, externalBlocks: result.blockedExternal.length } }));
process.exitCode = result.qualified ? 0 : 1;
