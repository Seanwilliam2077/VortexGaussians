import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3F, p3fConfig, qualityCasesP3f, regressionCasesP3f, timingCasesP3f, parseP3fArgs } from './p3f-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3Snapshot } from './p3-run.mjs';
import { traceRow, requirePairedTrace } from './p3b-run.mjs';
import { requireCompleteP3dCase } from './p3d-run.mjs';
import { validateAffineLedger } from './p3e-run.mjs';
import { requireFrozenChecksum, requireOldFields, exactTracerReplay, compareRecordedHashes } from './lib/p3d-metrics.mjs';
import { encodeParticles, decodeParticles, pairedImageError, poolPairedImages, aggregateTiming } from './lib/p3b-metrics.mjs';
import { decodeFloat32, referenceMasks, distribution } from './lib/p3-metrics.mjs';
import { pathsWithOpticalWeights, deployedQualityGate, timingPermission, requireTimingProductionMatch } from './lib/p3e-metrics.mjs';
import { validateSelectionSummary, summarizeCorrectionSelection, selectionBudgetLock, correctionGate, correctionDecision } from './lib/p3f-metrics.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const timingKeys = ['simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'affineGroupingMs', 'affineModelBuildMs', 'correctionSelectionMs', 'correctionQueryMs', 'affineLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
export function validateP3fSnapshot(s) {
  validateP3Snapshot(s, s.field.mode === 'tree');
  if (!s.field.correction) validateAffineLedger(s);
  else {
    const c = s.counters;
    for (const key of ['correctionFrames', 'correctionGroupsScored', 'correctionScoreMemberEvaluations', 'correctionSelectedGroups', 'correctionSelectedMembers', 'correctionDirectQueries', 'correctionDirectNoThermalSupportQueries']) if (!Number.isSafeInteger(c[key]) || c[key] < 0) throw new Error(`Invalid correction counter ${key}`);
    if (c.affineStencilQueries !== 7 * c.affineGroups || c.fullFieldQueries !== c.affineStencilQueries + c.correctionDirectQueries || c.fieldQueries !== c.fullFieldQueries || c.tracerFieldQueries !== c.affineReconstructions + c.correctionDirectQueries) throw new Error('Corrected affine query ledger failed');
    if (c.correctionFrames !== s.frame || c.correctionGroupsScored !== c.affineGroups || c.correctionScoreMemberEvaluations !== c.tracerFieldQueries || c.correctionSelectedMembers !== c.correctionDirectQueries || c.correctionDirectNoThermalSupportQueries > c.correctionDirectQueries) throw new Error('Correction selection accounting failed');
    for (const key of ['velocityOnlyFieldQueries', 'thermalOnlyFieldQueries', 'componentDirectQueries', 'cacheNodeQueries', 'cacheFallbacks']) if (c[key] !== 0) throw new Error(`Unexpected corrected route ${key}`);
    if (s.frame > 0) validateSelectionSummary(s.field.lastCorrection, s.field.correction, s.field.affine);
  }
  if (Math.abs(s.field.time - Math.max(0, s.time - P3F.dt)) > 1e-8) throw new Error('Frozen physical field time differs');
  return s;
}
async function saveParticles(out, stem, points) {
  const { bytes, ...record } = encodeParticles(points), file = `particles/${stem}.f64`; await fs.mkdir(path.join(out, 'particles'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes); return { ...record, file };
}
async function readParticles(out, record) { return decodeParticles(await fs.readFile(path.join(out, record.file)), record); }
async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }
async function verifyRaw(out, r, optional = false) {
  let verified = 0, absent = 0;
  for (const item of [...r.checkpoints.map(c => c.particles), ...r.captures.map(c => c.image)]) {
    let bytes; try { bytes = await fs.readFile(path.join(out, item.file)); } catch (e) { if (optional && e.code === 'ENOENT') { absent++; continue; } throw e; }
    requireFrozenChecksum(bytes, item.sha256, item.file); verified++;
  }
  return { verified, absent, referenceFromAuthenticatedJson: optional };
}
export async function loadP3fBaseline(directory, archive) {
  const pinBytes = await fs.readFile(new URL('./lib/p3f-baseline.json', import.meta.url)), pin = JSON.parse(pinBytes), checked = {};
  if (Object.keys(pin.files).length !== 3) throw new Error('P3f baseline requires three authenticated JSON records');
  for (const [file, expected] of Object.entries(pin.files)) { if (path.basename(file) !== file) throw new Error('Invalid baseline path'); checked[file] = requireFrozenChecksum(await fs.readFile(path.join(directory, file)), expected, file); }
  const m = JSON.parse(await fs.readFile(path.join(directory, 'manifest.json')));
  if (m.phase !== 'P3e' || m.status !== 'passed' || !m.quality?.complete || !m.protocolComplete || !m.sourceFreeze?.matched) throw new Error('Invalid archived P3e evidence');
  const archiveHash = archive ? requireFrozenChecksum(await fs.readFile(archive), pin.archiveSha256, 'P3e ZIP') : null;
  return { manifest: m, metadata: { directory, manifestSha256: checked['manifest.json'], sourceHashes: m.metadata.sourceHashes,
    authenticatedJsonFiles: checked, frozenChecksumListSha256: sha(pinBytes), expectedArchiveSha256: pin.archiveSha256,
    archive: archive ? { path: archive, sha256: archiveHash } : null } };
}
export async function runP3fQualityCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl), corrected = ['curvature', 'hash'].includes(definition.method);
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], tracerTrace: [], checkpoints: [], captures: [], selectionTrace: [], selections: [], browserErrors: errors };
  async function checkpoint(snapshot, captured) {
    validateP3fSnapshot(snapshot); const points = snapshot.renderParticles;
    delete snapshot.renderParticles; delete snapshot.physicsParticles; result.snapshots.push(snapshot);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles: await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points) });
    if (captured) {
      const record = { frame: snapshot.frame, time: snapshot.time, fieldTime: captured.fieldTime, inputPhase: captured.inputPhase, params: snapshot.params, inputs: captured.inputs, selection: captured.correctionSelection };
      const summary = summarizeCorrectionSelection(record, points, P3F), bytes = Buffer.from(JSON.stringify(record)), file = `selections/${definition.id}-f${snapshot.frame}.json`;
      await fs.mkdir(path.join(out, 'selections'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes);
      result.selections.push({ frame: snapshot.frame, time: snapshot.time, file, sha256: sha(bytes), bytes: bytes.length, summary });
    }
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3fConfig(definition) });
    result.trace.push(traceRow(initial)); result.tracerTrace.push({ frame: 0, tracerHash: initial.tracerHash }); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const sampled = frame % P3F.sampleEvery === 0;
      const state = await page.evaluate(({ dt, sample, observe }) => {
        const r = window.__demo.researchP3, captured = observe ? r.stepWithInputs(dt, { stride: 1, correctionDetails: true }) : (r.step(1, dt), null);
        return { snapshot: r.snapshot({ detail: sample }), captured };
      }, { dt: P3F.dt, sample: sampled, observe: sampled && corrected });
      validateP3fSnapshot(state.snapshot); result.trace.push(traceRow(state.snapshot)); result.tracerTrace.push({ frame, tracerHash: state.snapshot.tracerHash });
      if (corrected) result.selectionTrace.push(state.snapshot.field.lastCorrection);
      if (sampled) await checkpoint(state.snapshot, state.captured);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3F.views) {
        const data = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'), image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Capture changed production state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (definition.method === 'DD' && (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0)) throw new Error('Empty DD reference');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64')); result.captures.push({ frame, time: frame * P3F.dt, view, image, preview });
      }
    }
    requireCompleteP3dCase(result);
    if (corrected && (result.selectionTrace.length !== definition.frames || result.selections.length !== definition.frames / P3F.sampleEvery)) throw new Error('Incomplete production selection evidence');
    if (corrected) {
      const c = result.snapshots.at(-1).counters;
      for (const [key, counter] of [['inputCount', 'correctionScoreMemberEvaluations'], ['groupCount', 'correctionGroupsScored'], ['selectedGroupCount', 'correctionSelectedGroups'], ['selectedMemberCount', 'correctionSelectedMembers'], ['stencilQueries', 'affineStencilQueries'], ['correctionQueries', 'correctionDirectQueries']]) if (result.selectionTrace.reduce((sum, s) => sum + s[key], 0) !== c[counter]) throw new Error(`Cumulative selection trace differs from ${counter}`);
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); } return result;
}

export async function compareP3f(out, results, baseline) {
  const answer = { comparisons: [], masks: [], selectionDetails: [], budgetLocks: [], legacyRegression: [], failures: [], complete: false, gate: { passed: false } };
  try {
    const quality = results.filter(r => r.definition.family === 'quality'), regression = results.filter(r => r.definition.family === 'regression');
    if (quality.length !== 6 || regression.length !== 1 || results.some(r => r.status !== 'passed')) throw new Error('All six quality trajectories and the old affine regression are required');
    for (const r of results) { requireCompleteP3dCase(r); await verifyRaw(out, r); }
    for (const current of [quality.find(r => r.definition.method === 'DD' && r.definition.seed === 11), regression[0]]) {
      const entry = baseline.manifest.results.find(r => r.id === current.definition.id); if (!entry) throw new Error('Missing archived case');
      const bytes = await fs.readFile(path.join(baseline.metadata.directory, entry.rawFile)), old = JSON.parse(bytes), binary = await verifyRaw(baseline.metadata.directory, old, true);
      requirePairedTrace(old.trace.slice(0, current.trace.length), current.trace); exactTracerReplay(old.tracerTrace.slice(0, current.tracerTrace.length), current.tracerTrace);
      for (const s of current.snapshots) requireOldFields(old.snapshots.find(p => p.frame === s.frame), s);
      answer.legacyRegression.push({ candidate: current.definition.id, referenceRawFile: entry.rawFile, referenceRawSha256: sha(bytes), referenceBinaryValidation: binary,
        exactPhysicalBirthTrace: true, exactTracerTrace: true, oldSnapshotFieldsExact: true, ...compareRecordedHashes(old, current, { partial: current.definition.frames !== 180 }) });
    }
    for (const pair of P3F.pairs) {
      const own = quality.filter(r => r.definition.seed === pair.seed && r.definition.renderSeed === pair.renderSeed), direct = own.find(r => r.definition.method === 'DD');
      if (own.length !== 3 || !direct) throw new Error('Missing predeclared quality arm');
      answer.budgetLocks.push({ ...pair, ...selectionBudgetLock(own.find(r => r.definition.method === 'curvature'), own.find(r => r.definition.method === 'hash'), direct, direct.definition.frames) });
      const masks = new Map();
      for (const ref of direct.captures) {
        const roi = referenceMasks([await readImage(out, ref.image)], P3F.image), id = `${direct.definition.id}-f${ref.frame}-${ref.view.id}`;
        const record = { id, width: roi.width, height: roi.height, orientation: roi.orientation, reference: ref.image.file, masks: {} };
        for (const name of ['foregroundMask', 'holeMask']) { const bytes = Buffer.from(roi[name]), file = `images/roi-${id}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes); record.masks[name] = { file, sha256: sha(bytes), count: bytes.reduce((a, b) => a + b, 0) }; }
        masks.set(`${ref.frame}-${ref.view.id}`, roi); answer.masks.push(record);
      }
      for (const candidate of own.filter(r => r.definition.method !== 'DD')) {
        const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, direct.trace), paths = [], images = [];
        for (const c of candidate.checkpoints) { const ref = direct.checkpoints.find(p => p.frame === c.frame); paths.push({ frame: c.frame, time: c.time, ...pathsWithOpticalWeights(await readParticles(out, c.particles), await readParticles(out, ref.particles), P3F) }); }
        for (const c of candidate.captures) { const ref = direct.captures.find(p => p.frame === c.frame && p.view.id === c.view.id); images.push({ frame: c.frame, view: c.view, ...pairedImageError(await readImage(out, c.image), await readImage(out, ref.image), masks.get(`${c.frame}-${c.view.id}`), P3F.image) }); }
        for (const item of candidate.selections) {
          const bytes = await fs.readFile(path.join(out, item.file)); requireFrozenChecksum(bytes, item.sha256, item.file);
          const points = await readParticles(out, candidate.checkpoints.find(c => c.frame === item.frame).particles), summary = summarizeCorrectionSelection(JSON.parse(bytes), points, P3F);
          if (JSON.stringify(summary) !== JSON.stringify(item.summary)) throw new Error('Production selection summary differs from raw data');
          answer.selectionDetails.push({ candidate: candidate.definition.id, ...item });
        }
        const c = candidate.snapshots.at(-1).counters, comparison = { candidate: candidate.definition.id, reference: direct.definition.id, scenario: 'stationary', ...pair, method: candidate.definition.method,
          paths, images, pooled: poolPairedImages(images), physicsAndBirthRngMatched, cacheFallbacks: c.cacheFallbacks,
          capacityBlocks: c.physicsFullSteps + c.physicsCapacityLimitedSteps + c.physicsSuppressedEmissionCredit + c.tracerCapacityDropped };
        comparison.accuracyCheck = deployedQualityGate(comparison, P3F.accuracy); answer.comparisons.push(comparison);
      }
    }
    answer.gate = correctionGate(answer.comparisons, answer.budgetLocks, P3F.pairs); answer.complete = true;
  } catch (e) { answer.failures.push({ reason: e.stack || String(e) }); } return answer;
}

export async function runP3fTimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl), result = { definition, status: 'running', graphics, trace: [], timings: [], selectionTrace: [], browserErrors: errors };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3; r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0); const trace = [r.trace()], timings = [], selectionTrace = [];
      for (let frame = 1; frame <= 180; frame++) { const sample = frame >= 60 && frame % 3 === 0, data = r.frame(spec.dt, { sync: sample ? 'finish' : 'none' }); trace.push(data.trace); if (data.correctionSummary) selectionTrace.push(data.correctionSummary); if (sample) timings.push({ frame, time: data.time, ...data.timing, counts: data.counts }); }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), trace, timings, selectionTrace };
    }, { seed: definition.seed, config: p3fConfig(definition), spec: P3F });
    validateP3fSnapshot(data.initial); validateP3fSnapshot(data.final); Object.assign(result, data);
    if (data.timings.length !== 41 || data.trace.length !== 181) throw new Error('Incomplete timing evidence');
    result.distributions = Object.fromEntries(timingKeys.map(k => [k, distribution(data.timings.map(t => t[k] ?? 0))]));
    for (const t of data.timings) {
      if (!String(t.synchronization).includes('finish')) throw new Error('Unsynchronized timing sample');
      for (const k of timingKeys) if (!(definition.method === 'DD' && ['correctionSelectionMs', 'correctionQueryMs'].includes(k)) && (!Number.isFinite(t[k]) || t[k] < 0)) throw new Error(`Missing/nonfinite timing ${k}`);
      const sum = ['tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'affineGroupingMs', 'affineModelBuildMs', 'correctionSelectionMs', 'correctionQueryMs', 'affineLookupMs', 'tracerAdvectionMs'].reduce((s, k) => s + (t[k] ?? 0), 0); if (sum > t.tracerMs + .01) throw new Error('Tracer substages exceed total');
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); } return result;
}

export async function main() {
  const args = parseP3fArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3f-run.mjs --suite all|quick [--out DIR] [--baseline P3E_DIR] [--baseline-archive ZIP] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3f-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const baseline = await loadP3fBaseline(path.resolve(args.baseline || path.join(researchRoot, 'runs', 'p3e-full')), args.baselineArchive ? path.resolve(args.baselineArchive) : null);
  const manifest = { phase: 'P3f', status: 'running', stageStatus: 'quality_running', exploratory: true, protocolComplete: false, args, specification: P3F,
    metadata: hostMetadata(), baseline: baseline.metadata, plannedQuality: qualityCasesP3f(args.suite), plannedRegression: regressionCasesP3f(args.suite), plannedTiming: timingCasesP3f(), results: [], physicsAndBirthLocks: [], timingProductionLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); let server, launched; const quality = [], timing = []; await save();
  async function record(d, run) {
    const started = Date.now(); console.log(`[${manifest.results.length + 1}] ${d.id}`); const r = await run(); r.hostElapsedMs = Date.now() - started;
    if (r.status === 'passed') {
      const ref = quality.find(q => q.definition.method === 'DD' && q.definition.seed === d.seed && q.definition.renderSeed === d.renderSeed);
      try {
        if (ref) requirePairedTrace(ref.trace, r.trace); manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: ref?.definition.id || d.id, steps: r.trace.length, passed: true });
        if (d.family === 'timing') { const same = quality.find(q => q.definition.method === d.method && q.definition.seed === d.seed); const lock = requireTimingProductionMatch(same, r); if (JSON.stringify(same.selectionTrace) !== JSON.stringify(r.selectionTrace)) throw new Error('Quality/timing selection trace differs'); manifest.timingProductionLocks.push({ candidate: d.id, reference: same.definition.id, ...lock, exactSelectionTrace: true }); }
      } catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
    }
    const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r));
    if (d.family !== 'timing') quality.push(r); else { timing.push(r); const columns = ['frame', 'time', ...timingKeys]; await fs.writeFile(path.join(out, `${d.id}.csv`), `${columns.join(',')}\n${r.timings.map(t => columns.map(k => t[k] ?? '').join(',')).join('\n')}\n`); }
    manifest.results.push({ id: d.id, family: d.family, status: r.status, rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null }); console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
  }
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable); manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (const d of [...manifest.plannedQuality, ...manifest.plannedRegression]) await record(d, () => runP3fQualityCase(launched.browser, server.url, d, out));
    manifest.quality = await compareP3f(out, quality, baseline);
    const permission = timingPermission({ suite: args.suite, executionValid: manifest.quality.complete, qualityGate: manifest.quality.gate }); manifest.stageStatus = permission.stageStatus;
    if (permission.run) {
      console.log('BOTH SEED GATES PASSED: starting ten independent synchronized timing runs'); manifest.stageStatus = 'timing_running'; await save();
      for (const d of manifest.plannedTiming) await record(d, () => runP3fTimingCase(launched.browser, server.url, d));
      manifest.stageStatus = timing.every(r => r.status === 'passed') ? 'timing_complete' : 'execution_failed';
    } else { manifest.timingSkipped = { reason: permission.reason, selectionGate: manifest.quality.gate, plannedRuns: 10 }; console.log(`TIMING SKIPPED: ${permission.reason}`); }
    manifest.timing = aggregateTiming(timing, P3F.scenarios, P3F.methods.filter(m => m.id !== 'hash'), 5);
    const executionValid = manifest.quality.complete && manifest.results.every(r => r.status === 'passed'); manifest.protocolComplete = args.suite === 'all' && executionValid && (!permission.run || timing.length === 10);
    manifest.decision = correctionDecision(manifest.timing, manifest.quality.gate, manifest.protocolComplete, P3F.decision); manifest.status = executionValid ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.stageStatus = 'execution_failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try { manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes); const after = await loadP3fBaseline(baseline.metadata.directory, baseline.metadata.archive?.path); if (JSON.stringify(after.metadata) !== JSON.stringify(baseline.metadata)) throw new Error('Baseline changed'); manifest.baselineUnchanged = true; }
    catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; manifest.status = 'failed'; manifest.protocolComplete = false; }
    if (manifest.decision) manifest.decision.engineeringGo &&= manifest.status === 'passed'; manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3f results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
