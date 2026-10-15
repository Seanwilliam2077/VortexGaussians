import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3E, p3eConfig, qualityCasesP3e, timingCasesP3e, parseP3eArgs } from './p3e-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3Snapshot } from './p3-run.mjs';
import { traceRow, requirePairedTrace } from './p3b-run.mjs';
import { requireCompleteP3dCase } from './p3d-run.mjs';
import { requireFrozenChecksum, requireOldFields, exactTracerReplay, compareRecordedHashes } from './lib/p3d-metrics.mjs';
import { encodeParticles, decodeParticles, pairedImageError, poolPairedImages, aggregateTiming } from './lib/p3b-metrics.mjs';
import { decodeFloat32, referenceMasks, distribution } from './lib/p3-metrics.mjs';
import { pathsWithOpticalWeights, deployedQualityGate, timingPermission, affineDecision, summarizeAffineDiagnostic, requireTimingProductionMatch } from './lib/p3e-metrics.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const timingKeys = ['simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'affineGroupingMs', 'affineModelBuildMs', 'affineLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
export function validateAffineLedger(s) {
  const c = s.counters;
  for (const k of ['affineGroups', 'affineStencilQueries', 'affineReconstructions', 'affineGroupSortCalls', 'affineSortedPointCount', 'affineTbClippedLow', 'affineTbClippedHigh']) if (!Number.isSafeInteger(c[k]) || c[k] < 0) throw new Error(`Invalid affine counter ${k}`);
  if (s.field.mode === 'affine') {
    if (c.affineStencilQueries !== 7 * c.affineGroups || c.fieldQueries !== c.affineStencilQueries || c.fullFieldQueries !== c.affineStencilQueries || c.tracerFieldQueries !== c.affineReconstructions) throw new Error('Affine query accounting failed');
    for (const k of ['velocityOnlyFieldQueries', 'thermalOnlyFieldQueries', 'componentDirectQueries', 'cacheNodeQueries', 'cacheFallbacks']) if (c[k] !== 0) throw new Error(`Affine route performed unexpected ${k}`);
  } else if (s.field.mode !== 'tree' || c.affineGroups !== 0 || c.affineStencilQueries !== 0 || c.affineReconstructions !== 0) throw new Error('DD affine accounting failed');
  return true;
}
export function validateP3eSnapshot(s) {
  // Approximation-induced retirement is allowed; missing IDs belong to the scientific quality gate.
  validateP3Snapshot(s, s.field.mode === 'tree'); validateAffineLedger(s);
  if (Math.abs(s.field.time - Math.max(0, s.time - P3E.dt)) > 1e-8) throw new Error('Physical field time mismatch'); return s;
}
async function saveParticles(out, stem, points) {
  const { bytes, ...record } = encodeParticles(points), file = `particles/${stem}.f64`;
  await fs.mkdir(path.join(out, 'particles'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes); return { ...record, file };
}
async function readParticles(out, record) { return decodeParticles(await fs.readFile(path.join(out, record.file)), record); }
async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }
async function verifyRaw(out, r, optional = false) {
  let verified = 0, absent = 0;
  for (const item of [...r.checkpoints.map(c => c.particles), ...r.captures.map(c => c.image)]) {
    let bytes; try { bytes = await fs.readFile(path.join(out, item.file)); } catch (e) { if (optional && e.code === 'ENOENT') { absent++; continue; } throw e; }
    requireFrozenChecksum(bytes, item.sha256, item.file); verified++;
  } return { verified, absent, referenceFromAuthenticatedJson: optional };
}
export async function loadP3eBaseline(directory, archive) {
  const pinBytes = await fs.readFile(new URL('./lib/p3e-baseline.json', import.meta.url)), pin = JSON.parse(pinBytes), checked = {};
  if (Object.keys(pin.files).length !== 2) throw new Error('Baseline requires two pinned JSON files');
  for (const [file, expected] of Object.entries(pin.files)) { if (path.basename(file) !== file) throw new Error('Invalid baseline path'); checked[file] = requireFrozenChecksum(await fs.readFile(path.join(directory, file)), expected, file); }
  const m = JSON.parse(await fs.readFile(path.join(directory, 'manifest.json')));
  if (m.phase !== 'P3d' || m.status !== 'passed' || !m.quality?.complete || !m.sourceFreeze?.matched) throw new Error('Invalid P3d baseline');
  const archiveHash = archive ? requireFrozenChecksum(await fs.readFile(archive), pin.archiveSha256, 'P3d ZIP') : null;
  return { manifest: m, metadata: { directory, manifestSha256: checked['manifest.json'], sourceHashes: m.metadata.sourceHashes,
    authenticatedJsonFiles: checked, frozenChecksumListSha256: sha(pinBytes), expectedArchiveSha256: pin.archiveSha256,
    archive: archive ? { path: archive, sha256: archiveHash } : null } };
}
export async function runP3eQualityCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], tracerTrace: [], checkpoints: [], captures: [], diagnostics: [], browserErrors: errors };
  async function checkpoint(snapshot, captured, diagnostic) {
    validateP3eSnapshot(snapshot); const points = snapshot.renderParticles;
    if (captured && JSON.stringify(captured.inputs.map(p => p.id).sort((a, b) => a - b)) !== JSON.stringify(points.map(p => p.id).sort((a, b) => a - b))) throw new Error('DD all-points observer omitted or duplicated live inputs');
    delete snapshot.renderParticles; delete snapshot.physicsParticles; result.snapshots.push(snapshot);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles: await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points) });
    if (captured) {
      const record = { frame: snapshot.frame, time: snapshot.time, inputPhase: captured.inputPhase, fieldTime: captured.fieldTime, inputs: captured.inputs, diagnostic };
      const summary = summarizeAffineDiagnostic(record, P3E), file = `diagnostics/${definition.id}-f${snapshot.frame}.json`, bytes = Buffer.from(JSON.stringify(record));
      await fs.mkdir(path.join(out, 'diagnostics'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes);
      result.diagnostics.push({ frame: snapshot.frame, time: snapshot.time, file, sha256: sha(bytes), bytes: bytes.length, summary });
    }
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3eConfig(definition) });
    result.trace.push(traceRow(initial)); result.tracerTrace.push({ frame: 0, tracerHash: initial.tracerHash }); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const sampled = frame % P3E.sampleEvery === 0;
      const state = await page.evaluate(({ dt, sample, observe, affine }) => {
        const r = window.__demo.researchP3, captured = observe ? r.stepWithInputs(dt, { stride: 1 }) : (r.step(1, dt), null);
        const snapshot = r.snapshot({ detail: sample }); let diagnostic = null;
        if (captured) {
          diagnostic = r.affineDiagnostics(captured.inputs, affine);
          if (JSON.stringify(snapshot) !== JSON.stringify(r.snapshot({ detail: true }))) throw new Error('DD diagnostic changed full production state');
          if (diagnostic.fieldTime !== captured.fieldTime) throw new Error('Diagnostic sampled a different frozen physical time');
        }
        return { snapshot, captured, diagnostic };
      }, { dt: P3E.dt, sample: sampled, observe: sampled && definition.method === 'DD', affine: P3E.affine });
      validateP3eSnapshot(state.snapshot); result.trace.push(traceRow(state.snapshot)); result.tracerTrace.push({ frame, tracerHash: state.snapshot.tracerHash });
      if (sampled) await checkpoint(state.snapshot, state.captured, state.diagnostic);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3E.views) {
        const data = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'), image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Image capture changed production state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (definition.method === 'DD' && (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0)) throw new Error('Empty DD reference image');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64'));
        result.captures.push({ frame, time: frame * P3E.dt, view, image, preview });
      }
    }
    requireCompleteP3dCase(result);
    if (definition.method === 'DD' && result.diagnostics.length !== definition.frames / P3E.sampleEvery) throw new Error('Incomplete DD diagnostics');
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}
export async function compareP3e(out, results, baseline) {
  const failures = [], masks = [], direct = results.find(r => r.definition.method === 'DD'), candidate = results.find(r => r.definition.method === 'affine');
  const answer = { comparisons: [], masks, diagnostics: direct?.diagnostics || [], legacyRegression: [], failures, complete: false, gate: { passed: false } };
  try {
    if (results.length !== 2 || results.some(r => r.status !== 'passed')) throw new Error('Both complete quality trajectories are required');
    for (const r of results) { requireCompleteP3dCase(r); await verifyRaw(out, r); }
    const entry = baseline.manifest.results.find(r => r.id === direct.definition.id), oldBytes = await fs.readFile(path.join(baseline.metadata.directory, entry.rawFile)), old = JSON.parse(oldBytes);
    const referenceBinaryValidation = await verifyRaw(baseline.metadata.directory, old, true);
    requirePairedTrace(old.trace.slice(0, direct.trace.length), direct.trace); exactTracerReplay(old.tracerTrace.slice(0, direct.tracerTrace.length), direct.tracerTrace);
    for (const s of direct.snapshots) requireOldFields(old.snapshots.find(p => p.frame === s.frame), s);
    answer.legacyRegression.push({ candidate: direct.definition.id, reference: old.definition.id, referenceRawFile: entry.rawFile,
      referenceRawSha256: sha(oldBytes), referenceBinaryValidation, exactPhysicalBirthTrace: true, exactTracerTrace: true, oldSnapshotFieldsExact: true,
      ...compareRecordedHashes(old, direct, { partial: direct.definition.frames !== 180 }) });
    for (const d of answer.diagnostics) {
      const bytes = await fs.readFile(path.join(out, d.file)); requireFrozenChecksum(bytes, d.sha256, d.file);
      const summary = summarizeAffineDiagnostic(JSON.parse(bytes), P3E); if (JSON.stringify(summary) !== JSON.stringify(d.summary)) throw new Error('Diagnostic summary differs from raw data');
    }
    if (direct.definition.frames === 180) {
      const total = key => answer.diagnostics.reduce((sum, d) => sum + d.summary[key], 0);
      if (answer.diagnostics.length !== 12 || total('count') !== 56160 || total('groupCount') !== 3510 || total('modelQueries') !== 24570) throw new Error('Full DD diagnostic coverage differs from fixed protocol');
    }
    const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, direct.trace), paths = [], images = [];
    for (const c of candidate.checkpoints) { const ref = direct.checkpoints.find(p => p.frame === c.frame); paths.push({ frame: c.frame, time: c.time, ...pathsWithOpticalWeights(await readParticles(out, c.particles), await readParticles(out, ref.particles), P3E) }); }
    for (const c of candidate.captures) {
      const ref = direct.captures.find(p => p.frame === c.frame && p.view.id === c.view.id), image = await readImage(out, ref.image), roi = referenceMasks([image], P3E.image);
      const id = `${direct.definition.id}-f${c.frame}-${c.view.id}`, mask = { id, width: roi.width, height: roi.height, orientation: roi.orientation, reference: ref.image.file, masks: {} };
      for (const name of ['foregroundMask', 'holeMask']) { const bytes = Buffer.from(roi[name]), file = `images/roi-${id}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes); mask.masks[name] = { file, sha256: sha(bytes), count: bytes.reduce((a, b) => a + b, 0) }; }
      masks.push(mask); images.push({ frame: c.frame, view: c.view, ...pairedImageError(await readImage(out, c.image), image, roi, P3E.image) });
    }
    const c = candidate.snapshots.at(-1).counters, comparison = { candidate: candidate.definition.id, reference: direct.definition.id, method: 'affine', paths, images, pooled: poolPairedImages(images), physicsAndBirthRngMatched,
      cacheFallbacks: c.cacheFallbacks, capacityBlocks: c.physicsFullSteps + c.physicsCapacityLimitedSteps + c.physicsSuppressedEmissionCredit + c.tracerCapacityDropped };
    comparison.accuracyCheck = deployedQualityGate(comparison, P3E.accuracy); answer.comparisons.push(comparison); answer.gate = comparison.accuracyCheck;
    answer.complete = true;
  } catch (e) { failures.push({ reason: e.stack || String(e) }); }
  return answer;
}
export async function runP3eTimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl), result = { definition, status: 'running', graphics, trace: [], timings: [], browserErrors: errors };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3; r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0); const trace = [r.trace()], timings = [];
      for (let frame = 1; frame <= 180; frame++) { const sample = frame >= 60 && frame % 3 === 0, data = r.frame(spec.dt, { sync: sample ? 'finish' : 'none' }); trace.push(data.trace); if (sample) timings.push({ frame, time: data.time, ...data.timing, counts: data.counts }); }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), trace, timings };
    }, { seed: definition.seed, config: p3eConfig(definition), spec: P3E });
    validateP3eSnapshot(data.initial); validateP3eSnapshot(data.final); Object.assign(result, data);
    if (data.timings.length !== 41 || data.trace.length !== 181) throw new Error('Incomplete timing evidence');
    result.distributions = Object.fromEntries(timingKeys.map(k => [k, distribution(data.timings.map(t => t[k]))]));
    for (const t of data.timings) {
      if (!String(t.synchronization).includes('finish')) throw new Error('Unsynchronized timing sample');
      const sum = t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.affineGroupingMs + t.affineModelBuildMs + t.affineLookupMs + t.tracerAdvectionMs;
      if (sum > t.tracerMs + .01) throw new Error('Tracer substages exceed total');
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); } return result;
}
export async function main() {
  const args = parseP3eArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3e-run.mjs --suite all|quick [--out DIR] [--baseline P3D_DIR] [--baseline-archive ZIP] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3e-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const baseline = await loadP3eBaseline(path.resolve(args.baseline || path.join(researchRoot, 'runs', 'p3d-full')), args.baselineArchive ? path.resolve(args.baselineArchive) : null);
  const manifest = { phase: 'P3e', status: 'running', stageStatus: 'quality_running', exploratory: true, protocolComplete: false, args, specification: P3E,
    metadata: hostMetadata(), baseline: baseline.metadata, plannedQuality: qualityCasesP3e(args.suite), plannedTiming: timingCasesP3e(), results: [], physicsAndBirthLocks: [], timingProductionLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); let server, launched; const quality = [], timing = []; await save();
  async function record(d, run) {
    const started = Date.now(); console.log(`[${manifest.results.length + 1}] ${d.id}`); const r = await run(); r.hostElapsedMs = Date.now() - started;
    if (r.status === 'passed') {
      const ref = quality[0]; try {
        if (ref) requirePairedTrace(ref.trace, r.trace); manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: ref?.definition.id || d.id, steps: r.trace.length, passed: true });
        if (d.family === 'timing') { const same = quality.find(q => q.definition.method === d.method); manifest.timingProductionLocks.push({ candidate: d.id, reference: same.definition.id, ...requireTimingProductionMatch(same, r) }); }
      }
      catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
    }
    const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r));
    if (d.family === 'quality') quality.push(r); else { timing.push(r); const columns = ['frame', 'time', ...timingKeys]; await fs.writeFile(path.join(out, `${d.id}.csv`), `${columns.join(',')}\n${r.timings.map(t => columns.map(k => t[k] ?? '').join(',')).join('\n')}\n`); }
    manifest.results.push({ id: d.id, family: d.family, status: r.status, rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null }); console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
  }
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable); manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (const d of manifest.plannedQuality) await record(d, () => runP3eQualityCase(launched.browser, server.url, d, out));
    manifest.quality = await compareP3e(out, quality, baseline);
    const permission = timingPermission({ suite: args.suite, executionValid: manifest.quality.complete, qualityGate: manifest.quality.gate }); manifest.stageStatus = permission.stageStatus;
    if (permission.run) {
      console.log('QUALITY GATE PASSED: starting ten independent synchronized timing runs'); manifest.stageStatus = 'timing_running'; await save();
      for (const d of manifest.plannedTiming) await record(d, () => runP3eTimingCase(launched.browser, server.url, d));
      manifest.stageStatus = timing.every(r => r.status === 'passed') ? 'timing_complete' : 'execution_failed';
    } else { manifest.timingSkipped = { reason: permission.reason, qualityGate: manifest.quality.gate, plannedRuns: 10 }; console.log(`TIMING SKIPPED: ${permission.reason}`); }
    manifest.timing = aggregateTiming(timing, P3E.scenarios, P3E.methods, 5);
    const executionValid = manifest.quality.complete && manifest.results.every(r => r.status === 'passed');
    manifest.protocolComplete = args.suite === 'all' && executionValid && (!permission.run || timing.length === 10);
    manifest.decision = affineDecision(manifest.timing, manifest.quality.gate, manifest.protocolComplete, P3E.decision);
    manifest.status = executionValid ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.stageStatus = 'execution_failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try {
      manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes);
      const after = await loadP3eBaseline(baseline.metadata.directory, baseline.metadata.archive?.path);
      if (JSON.stringify(after.metadata) !== JSON.stringify(baseline.metadata)) throw new Error('Baseline provenance changed during run'); manifest.baselineUnchanged = true;
    } catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; manifest.status = 'failed'; manifest.protocolComplete = false; }
    if (manifest.decision) manifest.decision.engineeringGo &&= manifest.status === 'passed'; manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3e results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
