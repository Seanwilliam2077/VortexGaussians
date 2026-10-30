import fs from 'node:fs/promises';
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

if (!process.argv.includes('--execute')) {
  console.log('A48 is unexecuted. After review/assembly: one --execute, <=120s including cleanup, three original PNGs <=8MiB, no retry.');
  process.exit(0);
}
const started = performance.now(), elapsed = () => performance.now() - started;
const here = path.dirname(fileURLToPath(import.meta.url)), out = path.join(here, 'inspection-01');
await fs.mkdir(out, { recursive: false }); // An existing attempt is terminal, never reused.
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const require = (ok, message) => { if (!ok) throw Error('A48 inspection: ' + message); };
const fixedSHA = 'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0';
const files = ['BRIEF.md', 'AUTHOR_SPEC.md', 'STATIC_FEASIBILITY.md', 'IMPLEMENTATION_DECISION.md', 'WORK_SPEC.md',
  'index.html', 'work.css', 'work.mjs', 'bridge.js', 'assemble.mjs', '.gitignore', 'inspect.mjs',
  'renderer.generated.html', 'assembly.json'].map(f => path.join(here, f))
  .concat([path.join(repoRoot, 'demo/index.html'), path.join(repoRoot, 'research/lib/runtime.mjs')]);
const result = { version: 1, status: 'started', createdUTC: new Date().toISOString(), sources: {}, checks: {},
  images: [], imageBytes: 0, pageErrors: [], console: [], externalRequests: [], closed: {},
  scope: 'One ordinary A48 preparation and one real restore-button action. No artistic-success or paper claim.' };
let server, browser, context, page, lastSnapshot, expired = false, closing;
let readInFlight, exportPromise, failureEvidence, shutdown, evidenceClosed = false;
let snapshotWriteAttempted = false, resultWriteAttempted = false;
function persistSnapshotOnce() {
  if (!lastSnapshot || snapshotWriteAttempted) return;
  snapshotWriteAttempted = true;
  result.observedCalls = lastSnapshot.source?.calls ?? null;
  try {
    const bytes = Buffer.from(JSON.stringify(lastSnapshot) + '\n');
    writeFileSync(path.join(out, 'snapshot.json'), bytes, { flag: 'wx' });
    result.snapshot = { file: 'snapshot.json', bytes: bytes.length, sha256: sha(bytes), phase: lastSnapshot.phase };
  } catch (error) { result.snapshotWriteError = error.message; }
}
function persistResultOnce() {
  if (resultWriteAttempted) return;
  resultWriteAttempted = true;
  writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
}
async function closeResources() {
  if (closing) await closing;
  closing = (async () => {
    // A resource whose async creation finished during the deadline close still gets closed.
    for (const [name, resource] of [['context', context], ['browser', browser], ['server', server]]) if (resource && result.closed[name] !== true) {
      try { await resource.close(); result.closed[name] = true; }
      catch (error) { result.closed[name] = error.message; }
    }
  })();
  return closing;
}
const soft = setTimeout(() => {
  expired = true; result.deadline = '110s action stop; <=2s read-only evidence attempt, then resource closure before 120s';
  shutdown = (async () => {
    await collectFailureEvidence();
    persistSnapshotOnce();
    await closeResources();
  })();
}, Math.max(1, 110000 - elapsed()));
const hard = setTimeout(() => {
  evidenceClosed = true;
  result.status = 'failed'; result.error = '120s hard deadline'; result.wallMs = elapsed();
  persistSnapshotOnce();
  try { persistResultOnce(); } catch {}
  process.exit(124);
}, Math.max(1, 120000 - elapsed()));
const guard = () => require(!expired && elapsed() < 110000, 'work deadline exceeded');
function read() {
  require(!evidenceClosed, 'evidence read window closed');
  if (readInFlight) return readInFlight;
  const pending = page.evaluate(() => window.__a48.inspect()).then(s => {
    if (!evidenceClosed) lastSnapshot = s;
    return s;
  });
  readInFlight = pending;
  pending.finally(() => { if (readInFlight === pending) readInFlight = null; }).catch(() => {});
  return pending;
}
function collectFailureEvidence() {
  if (failureEvidence) return failureEvidence;
  failureEvidence = (async () => {
    const evidence = result.partialEvidence = { startedAtMs: elapsed(), budgetMs: 2000,
      snapshot: 'pending', images: 'pending', imageReadReused: !!exportPromise, completeEvidenceClaimed: false };
    if (!page || page.isClosed()) {
      evidence.snapshot = evidence.images = 'unavailable: page absent or closed'; evidenceClosed = true; return;
    }
    let accepting = true, timer;
    const settle = (key, operation) => operation.then(() => {
      if (accepting) evidence[key] = 'obtained';
    }, error => { if (accepting) evidence[key] = 'unavailable: ' + error.message; });
    // A pending ordinary read/export is joined, never issued a second time.
    await Promise.race([
      Promise.all([settle('snapshot', read()), settle('images', exportCachedImages())]),
      new Promise(resolve => { timer = setTimeout(resolve, Math.max(0, 2000 - (elapsed() - evidence.startedAtMs))); })
    ]);
    accepting = false; evidenceClosed = true; clearTimeout(timer);
    for (const key of ['snapshot', 'images']) if (evidence[key] === 'pending')
      evidence[key] = 'unavailable: total 2s read-only budget expired; late response ignored';
    evidence.finishedAtMs = elapsed();
    evidence.cachedSnapshotAvailable = !!lastSnapshot;
    evidence.savedImageCount = result.images.length;
  })();
  return failureEvidence;
}
async function verifyAssembly() {
  const [source, bridge, generated, manifestText] = await Promise.all([
    fs.readFile(path.join(repoRoot, 'demo/index.html')), fs.readFile(path.join(here, 'bridge.js')),
    fs.readFile(path.join(here, 'renderer.generated.html')), fs.readFile(path.join(here, 'assembly.json'), 'utf8')]);
  const m = JSON.parse(manifestText), insertion = m.insertion;
  require(source.length === 314044 && sha(source) === fixedSHA, 'original identity differs');
  require(m.source.sha256 === sha(source) && m.source.bytes === source.length, 'manifest source differs');
  require(m.bridge.sha256 === sha(bridge) && m.bridge.bytes === bridge.length, 'manifest bridge differs');
  require(m.output.sha256 === sha(generated) && m.output.bytes === generated.length, 'manifest output differs');
  const anchor = Buffer.from('window.__demo = {'), at = source.indexOf(anchor);
  require(at >= 0 && source.indexOf(anchor, at + anchor.length) === -1 && insertion.byteOffset === at, 'anchor differs');
  const added = Buffer.concat([Buffer.from(insertion.beginMarker), bridge, Buffer.from(insertion.endMarker)]);
  require(insertion.bytes === added.length && insertion.sha256 === sha(added), 'insertion identity differs');
  require(Buffer.concat([source.subarray(0, at), added, source.subarray(at)]).equals(generated), 'derived source has a non-insertion change');
  return m;
}
function exportCachedImages() {
  if (exportPromise) return exportPromise;
  exportPromise = exportImagesOnce();
  return exportPromise;
}
async function exportImagesOnce() {
  require(!evidenceClosed, 'image evidence window closed');
  const artifacts = await page.evaluate(() => window.__a48.images());
  require(!evidenceClosed, 'late image read ignored after evidence deadline');
  require(artifacts.images.length <= 3, 'too many cached images');
  for (let i = 0; i < artifacts.images.length; i++) {
    const image = artifacts.images[i], expectedStage = ['initial', 'prepared', 'swapped'][i];
    require(image.stage === expectedStage && image.file === `${i + 1}-${expectedStage}.png`, 'unexpected image identity');
    require(image.dataURL.startsWith('data:image/png;base64,'), 'artifact is not a PNG data URL');
    const bytes = Buffer.from(image.dataURL.slice('data:image/png;base64,'.length), 'base64');
    require(bytes.length >= 24 && bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])), 'bad PNG signature');
    require(bytes.readUInt32BE(16) === 720 && bytes.readUInt32BE(20) === 720 && image.width === 720 && image.height === 720, 'PNG dimensions differ');
    require(bytes.length === image.bytes && sha(bytes) === image.sha256, 'PNG identity differs');
    require(result.imageBytes + bytes.length <= 8 * 1024 * 1024, 'image byte budget exceeded');
    // One writer: no async disk write can race terminal evidence persistence.
    writeFileSync(path.join(out, image.file), bytes, { flag: 'wx' });
    const { dataURL, ...metadata } = image;
    result.images.push(metadata); result.imageBytes += bytes.length;
  }
  require(artifacts.totalBytes === result.imageBytes, 'image byte accounting differs');
}
function audit(s) {
  const r = s.source, a = r.stages, keys = ['h', 'fuel', 'glow', 'char_', 'state'], n = 7500;
  require(s.phase === 'ended' && s.artifactsReady && !s.errors.length && !r.errors.length, 'page did not end successfully');
  require(equal(r.calls, { setScene: 1, reset: 1, ignite: 1, stepAPI: 1, steps: 360, restore: 1 }), 'operation counts differ');
  require(Object.keys(a).length === 4 && ['initial', 'ignited', 'prepared', 'swapped'].every(k => a[k]), 'missing material stage');
  require(a.initial.material.frame === 0 && a.ignited.material.frame === 0 && a.prepared.material.frame === 360 && a.swapped.material.frame === 360, 'frame boundaries differ');
  require(Math.abs(a.prepared.material.time - 6) < 1e-8 && equal(a.prepared.material.params, a.swapped.material.params), 'time/parameters differ');
  const authored = r.geometry.value.authored;
  require(authored.length === 15000 && r.geometry.value.gaussians.length === 15000, 'missing original geometry');
  for (let i = 0; i < n; i++) {
    const id = `${i % 75}:${Math.floor(i / 75)}`;
    require(authored[i].id === 'F:' + id && authored[i + n].id === 'B:' + id, 'pairing/order differs');
  }
  for (const stage of Object.values(a)) {
    require(stage.material.points.length === 15000 && stage.geometryRef === r.geometry.id && stage.geometryEqual, 'incomplete raw material/geometry reference');
    const byId = new Map(stage.material.points.map(p => [p.id, p]));
    const fieldMap = { h: 'heat', fuel: 'fuel', glow: 'glow', char_: 'char', state: 'state' };
    for (const key of keys) {
      require(stage.arrays[key].length === 15000, 'material array length differs');
      for (let i = 0; i < 15000; i++) require(Object.is(stage.arrays[key][i], byId.get(authored[i].id)[fieldMap[key]]), 'array and raw snapshot disagree');
    }
  }
  const hits = new Set(r.ignition.actualIndices);
  require(hits.size > 0 && r.ignition.exactMatch && r.ignition.returnedLit === hits.size
    && equal([...hits].sort((x, y) => x - y), r.ignition.expectedIndices.slice().sort((x, y) => x - y)) && [...hits].every(i => i < n), 'hit set differs');
  for (let i = 0; i < 15000; i++) if (!hits.has(i)) for (const key of keys)
    require(Object.is(a.initial.arrays[key][i], a.ignited.arrays[key][i]) && Object.is(a.initial.arrays[key][i], a.prepared.arrays[key][i]), 'unhit material changed');
  for (let i = 0; i < n; i++) for (const key of keys)
    require(Object.is(a.prepared.arrays[key][i], a.swapped.arrays[key][i + n])
      && Object.is(a.prepared.arrays[key][i + n], a.swapped.arrays[key][i]), 'pair did not exchange exactly');
  require(equal(a.swapped.frontier.indices, a.prepared.frontier.indices.map(i => i < n ? i + n : i - n))
    && Object.is(a.prepared.frontier.emitCursor, a.swapped.frontier.emitCursor), 'frontier/cursor changed incorrectly');
  require(equal(r.physicalStates[a.prepared.physicalRef], r.physicalStates[a.swapped.physicalRef]), 'independent physical state changed');
  for (const key of ['counters', 'groups', 'areaFeedCredit']) require(equal(a.prepared[key], a.swapped[key]), 'full historical cost changed');
  require(a.prepared.material.particleStateHash === a.swapped.material.particleStateHash, 'particle hash changed');
  require(r.exchange.passed && Object.values(r.exchange.assertions).every(Boolean) && r.preparation.passed, 'internal audit failed');
  require(r.pngChecks.length === 3 && r.pngChecks.every(p => p.unchanged), 'PNG invariance audit missing');
  require(s.draws.length === 3 && s.pngAttempts.length === 3 && s.pngAttempts.every(p => p.status === 'cached'), 'drawing/export count differs');
  result.checks.materialPreparationAndExchange = true;
}
try {
  for (const file of files) {
    const bytes = await fs.readFile(file); guard();
    result.sources[path.relative(repoRoot, file).replaceAll('\\', '/')] = { bytes: bytes.length, sha256: sha(bytes) };
  }
  result.assembly = await verifyAssembly(); guard();
  server = await startServer(); guard();
  const launched = await launchBrowser(); browser = launched.browser;
  if (expired) { await browser.close(); throw Error('Browser launch completed after deadline'); }
  result.browser = { module: launched.module, launchOptions: launched.launchOptions, version: browser.version() };
  context = await browser.newContext({ viewport: { width: 1000, height: 900 }, deviceScaleFactor: 1 }); guard();
  await context.route('**/*', async route => {
    const url = route.request().url();
    if (url.startsWith(server.url + '/') || url.startsWith('data:') || url.startsWith('blob:')) await route.continue();
    else { result.externalRequests.push(url); await route.abort(); }
  });
  page = await context.newPage(); page.setDefaultTimeout(100000);
  page.on('pageerror', error => result.pageErrors.push(error.stack || String(error)));
  page.on('console', message => { if (['error', 'warning'].includes(message.type()) && result.console.length < 80)
    result.console.push({ type: message.type(), text: message.text() }); });
  await page.goto(server.url + '/tracks/art/studies/a48-layered-repair-material/', { waitUntil: 'load' }); guard();
  await page.waitForFunction(() => ['prepared', 'error', 'left'].includes(window.__a48?.inspect({ summary: true }).phase), undefined, { polling: 250 }); guard();
  const prepared = await read(); guard(); require(prepared.phase === 'prepared', 'automatic preparation failed');
  result.prepared = { atMs: elapsed(), hash: prepared.source.stages.prepared.material.hash };
  await page.locator('#restore').click(); guard();
  await page.waitForFunction(() => { const s = window.__a48.inspect({ summary: true });
    return s.phase === 'error' || s.phase === 'left' || (s.phase === 'ended' && s.artifactsReady);
  }, undefined, { polling: 250 }); guard();
  const ended = await read(); guard(); audit(ended); guard();
  await exportCachedImages(); guard();
  const afterRead = await read(); guard();
  require(equal(ended.source, afterRead.source) && equal(ended.images, afterRead.images)
    && equal(ended.draws, afterRead.draws) && equal(ended.pngAttempts, afterRead.pngAttempts), 'readback changed evidence');
  result.checks.readOnlyExports = true;
  require(result.images.length === 3 && !result.pageErrors.length && !result.externalRequests.length, 'image count/page/external request failure');
  await page.locator('#leave').click(); guard();
  const left = await read(); guard();
  require(left.phase === 'left' && left.phaseBeforeLeave === 'ended' && left.cleanup.complete
    && left.cleanup.iframeRemoved && left.cleanup.paperCachesReleased && left.cleanup.sourceIdleRAFLifetimeEnded
    && left.cleanup.leaveCalls === 1 && equal(left.source, ended.source), 'leave cleanup/evidence retention failed');
  result.checks.ordinaryLeave = true; result.status = 'completed_single_material_exchange';
} catch (error) {
  result.status = 'failed'; result.error = { message: error.message, stack: error.stack }; process.exitCode = 1;
  await collectFailureEvidence();
} finally {
  clearTimeout(soft);
  if (shutdown) await shutdown;
  evidenceClosed = true; persistSnapshotOnce();
  await closeResources();
  try {
    result.checks.sourcesUnchanged = true;
    for (const file of files) {
      const key = path.relative(repoRoot, file).replaceAll('\\', '/'), before = result.sources[key];
      if (!before || sha(await fs.readFile(file)) !== before.sha256) result.checks.sourcesUnchanged = false;
    }
    await verifyAssembly();
  } catch (error) { result.checks.sourcesUnchanged = false; result.identityError = error.message; }
  result.wallMs = elapsed(); result.checks.withinDeadline = !expired && result.wallMs < 120000;
  result.checks.resourcesClosed = ['context', 'browser', 'server'].every(k => result.closed[k] === true);
  if (!Object.values(result.checks).every(Boolean)) { result.status = 'failed'; process.exitCode = 1; }
  persistResultOnce();
  clearTimeout(hard);
  console.log(JSON.stringify({ status: result.status, wallMs: result.wallMs, images: result.images.length,
    imageBytes: result.imageBytes, checks: result.checks, error: result.error }));
}
