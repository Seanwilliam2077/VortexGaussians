import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3G, p3gConfig, qualityCasesP3g, timingCasesP3g, parseP3gArgs } from './p3g-design.mjs';
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
import { validateSelectionSummary, summarizeMemorySelection, summarizeMemoryEvents, selectionBudgetLock, memoryGate, memoryDecision, cacheHash } from './lib/p3g-metrics.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export const timingKeys = ['simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'affineGroupingMs', 'affineModelBuildMs', 'correctionSelectionMs', 'correctionQueryMs', 'memoryModelMs', 'affineLookupMs', 'tracerAdvectionMs', 'memoryFinalizeMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
export function validateP3gSnapshot(s) {
  validateP3Snapshot(s, s.field.mode === 'tree');
  if (!s.field.correction) validateAffineLedger(s);
  else {
    const c = s.counters;
    for (const key of ['correctionFrames', 'correctionGroupsScored', 'correctionScoreMemberEvaluations', 'correctionSelectedGroups', 'correctionSelectedMembers', 'correctionDirectQueries', 'correctionDirectNoThermalSupportQueries']) if (!Number.isSafeInteger(c[key]) || c[key] < 0) throw new Error(`Invalid correction counter ${key}`);
    if (c.affineStencilQueries !== 7 * c.affineGroups || c.fullFieldQueries !== c.affineStencilQueries + c.correctionDirectQueries || c.fieldQueries !== c.fullFieldQueries || c.tracerFieldQueries !== c.affineReconstructions + c.correctionDirectQueries) throw new Error('Corrected affine query ledger failed');
    if (c.correctionFrames !== s.frame || c.correctionGroupsScored !== c.affineGroups || c.correctionScoreMemberEvaluations !== c.tracerFieldQueries || c.correctionSelectedMembers !== c.correctionDirectQueries || c.correctionDirectNoThermalSupportQueries > c.correctionDirectQueries) throw new Error('Correction selection accounting failed');
    for (const key of ['velocityOnlyFieldQueries', 'thermalOnlyFieldQueries', 'componentDirectQueries', 'cacheNodeQueries', 'cacheFallbacks']) if (c[key] !== 0) throw new Error(`Unexpected corrected route ${key}`);
    if (s.frame > 0) validateSelectionSummary(s.field.lastCorrection, s.field.correction, s.field.affine);
    if (s.field.correction.memory) {
      for (const key of ['memoryFrames', 'memoryModelEvaluations', 'memorySavedMembers', 'memoryReusedMembers', 'memoryPreviousMembers', 'memoryPreviousLiveMembers', 'memoryOverlappingMembers', 'memoryExpiredMissingMembers']) if (!Number.isSafeInteger(c[key]) || c[key] < 0) throw new Error(`Invalid memory counter ${key}`);
      if (c.memoryFrames !== s.frame || c.memoryModelEvaluations !== c.correctionDirectQueries || c.memorySavedMembers !== c.correctionDirectQueries || c.memoryPreviousMembers !== c.memoryReusedMembers + c.memoryOverlappingMembers + c.memoryExpiredMissingMembers || c.memoryPreviousLiveMembers !== c.memoryReusedMembers + c.memoryOverlappingMembers || typeof s.memoryStateHash !== 'string') throw new Error('Memory accounting failed');
      if (s.frame > 0 && (s.field.lastMemory.savedMembers !== s.field.lastCorrection.selectedMemberCount || s.field.lastMemory.savedIDHash !== s.field.lastCorrection.selectionIDHash)) throw new Error('Memory creation differs from actual selected identities');
    }
  }
  if (Math.abs(s.field.time - Math.max(0, s.time - P3G.dt)) > 1e-8) throw new Error('Frozen physical field time differs');
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
export async function loadP3gBaseline(directory, archive) {
  const pinBytes = await fs.readFile(new URL('./lib/p3g-baseline.json', import.meta.url)), pin = JSON.parse(pinBytes), checked = {};
  if (Object.keys(pin.files).length !== 3) throw new Error('P3g baseline requires three authenticated JSON records');
  for (const [file, expected] of Object.entries(pin.files)) { if (path.basename(file) !== file) throw new Error('Invalid baseline path'); checked[file] = requireFrozenChecksum(await fs.readFile(path.join(directory, file)), expected, file); }
  const m = JSON.parse(await fs.readFile(path.join(directory, 'manifest.json')));
  if (m.phase !== 'P3f' || m.status !== 'passed' || !m.quality?.complete || !m.protocolComplete || !m.sourceFreeze?.matched) throw new Error('Invalid archived P3f evidence');
  const archiveHash = archive ? requireFrozenChecksum(await fs.readFile(archive), pin.archiveSha256, 'P3f ZIP') : null;
  return { manifest: m, metadata: { directory, manifestSha256: checked['manifest.json'], sourceHashes: m.metadata.sourceHashes,
    authenticatedJsonFiles: checked, frozenChecksumListSha256: sha(pinBytes), expectedArchiveSha256: pin.archiveSha256,
    archive: archive ? { path: archive, sha256: archiveHash } : null } };
}
export async function runP3gQualityCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl), corrected = definition.method !== 'DD', memory = definition.method === 'memory';
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], tracerTrace: [], checkpoints: [], captures: [], selectionTrace: [], selections: [], memoryTrace: [], memoryEvents: [], browserErrors: errors };
  let previousCache = [];
  async function checkpoint(snapshot, captured) {
    validateP3gSnapshot(snapshot); const points = snapshot.renderParticles;
    delete snapshot.renderParticles; delete snapshot.physicsParticles; result.snapshots.push(snapshot);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles: await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points) });
    if (captured) {
      const record = { frame: snapshot.frame, time: snapshot.time, fieldTime: captured.fieldTime, inputPhase: captured.inputPhase, params: snapshot.params, inputs: captured.inputs, selection: captured.correctionSelection };
      if (memory) record.memoryFile = `memory/${definition.id}-f${snapshot.frame}.json`;
      const summary = summarizeMemorySelection(record, points, P3G, captured.memoryEvents), bytes = Buffer.from(JSON.stringify(record)), file = `selections/${definition.id}-f${snapshot.frame}.json`;
      await fs.mkdir(path.join(out, 'selections'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes);
      result.selections.push({ frame: snapshot.frame, time: snapshot.time, file, sha256: sha(bytes), bytes: bytes.length, summary });
    }
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3gConfig(definition) });
    result.trace.push(traceRow(initial)); result.tracerTrace.push({ frame: 0, tracerHash: initial.tracerHash }); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const sampled = frame % P3G.sampleEvery === 0;
      const state = await page.evaluate(({ dt, sample, observe, memory }) => {
        const r = window.__demo.researchP3, captured = observe || memory ? r.stepWithInputs(dt, { stride: sample ? 1 : 1000000, correctionDetails: observe, memoryDetails: memory }) : (r.step(1, dt), null);
        return { snapshot: r.snapshot({ detail: sample }), captured };
      }, { dt: P3G.dt, sample: sampled, observe: sampled && corrected, memory });
      validateP3gSnapshot(state.snapshot); result.trace.push(traceRow(state.snapshot)); result.tracerTrace.push({ frame, tracerHash: state.snapshot.tracerHash });
      if (corrected) result.selectionTrace.push(state.snapshot.field.lastCorrection);
      if (memory) {
        const events = state.captured.memoryEvents, record = { frame, time: state.snapshot.time, fieldTime: state.captured.fieldTime, params: state.snapshot.params, events };
        if (JSON.stringify(events.summary) !== JSON.stringify(state.snapshot.field.lastMemory)) throw new Error('Observed memory summary differs from actual production');
        const summary = summarizeMemoryEvents(record, previousCache, P3G, sampled ? state.snapshot.renderParticles : null); previousCache = events.cacheAfter;
        if (summary.afterHash !== state.snapshot.memoryStateHash) throw new Error('Observed cache differs from production memory hash');
        const bytes = Buffer.from(JSON.stringify(record)), file = `memory/${definition.id}-f${frame}.json`; await fs.mkdir(path.join(out, 'memory'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes);
        result.memoryEvents.push({ frame, time: state.snapshot.time, file, sha256: sha(bytes), bytes: bytes.length, summary });
        result.memoryTrace.push({ frame, memoryStateHash: state.snapshot.memoryStateHash, summary: state.snapshot.field.lastMemory });
      }
      if (sampled) await checkpoint(state.snapshot, state.captured);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3G.views) {
        const data = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'), image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash || before.memoryStateHash !== after.memoryStateHash) throw new Error('Capture changed production state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (definition.method === 'DD' && (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0)) throw new Error('Empty DD reference');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64')); result.captures.push({ frame, time: frame * P3G.dt, view, image, preview });
      }
    }
    requireCompleteP3dCase(result);
    if (corrected && (result.selectionTrace.length !== definition.frames || result.selections.length !== definition.frames / P3G.sampleEvery)) throw new Error('Incomplete production selection evidence');
    if (memory && (result.memoryEvents.length !== definition.frames || result.memoryTrace.length !== definition.frames)) throw new Error('Incomplete full-frame memory provenance');
    if (memory) {
      const counters = result.snapshots.at(-1).counters;
      for (const [key, counter] of [['createdCount', 'memorySavedMembers'], ['usedCount', 'memoryReusedMembers'], ['overlappingCount', 'memoryOverlappingMembers'], ['expiredMissingCount', 'memoryExpiredMissingMembers'], ['beforeCount', 'memoryPreviousMembers'], ['previousLiveCount', 'memoryPreviousLiveMembers']]) if (result.memoryEvents.reduce((sum, m) => sum + m.summary[key], 0) !== counters[counter]) throw new Error(`Memory event totals differ: ${counter}`);
    }
    if (corrected) {
      const c = result.snapshots.at(-1).counters;
      for (const [key, counter] of [['inputCount', 'correctionScoreMemberEvaluations'], ['groupCount', 'correctionGroupsScored'], ['selectedGroupCount', 'correctionSelectedGroups'], ['selectedMemberCount', 'correctionSelectedMembers'], ['stencilQueries', 'affineStencilQueries'], ['correctionQueries', 'correctionDirectQueries']]) if (result.selectionTrace.reduce((sum, s) => sum + s[key], 0) !== c[counter]) throw new Error(`Cumulative selection trace differs from ${counter}`);
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); } return result;
}

export async function compareP3g(out, results, baseline) {
  const answer = { comparisons: [], masks: [], selectionDetails: [], memoryDetails: [], exposure: [], budgetLocks: [], legacyRegression: [], failures: [], complete: false, gate: { passed: false } };
  try {
    const quality = results.filter(r => r.definition.family === 'quality');
    if (quality.length !== 6 || results.length !== 6 || results.some(r => r.status !== 'passed')) throw new Error('All six complete quality trajectories are required');
    for (const r of results) { requireCompleteP3dCase(r); await verifyRaw(out, r); }
    for (const current of quality.filter(r => r.definition.seed === 11 && ['DD', 'curvature'].includes(r.definition.method))) {
      const entry = baseline.manifest.results.find(r => r.id === current.definition.id); if (!entry) throw new Error('Missing archived case');
      const bytes = await fs.readFile(path.join(baseline.metadata.directory, entry.rawFile)), old = JSON.parse(bytes), binary = await verifyRaw(baseline.metadata.directory, old, true);
      requirePairedTrace(old.trace.slice(0, current.trace.length), current.trace); exactTracerReplay(old.tracerTrace.slice(0, current.tracerTrace.length), current.tracerTrace);
      for (const s of current.snapshots) requireOldFields(old.snapshots.find(p => p.frame === s.frame), s);
      answer.legacyRegression.push({ candidate: current.definition.id, referenceRawFile: entry.rawFile, referenceRawSha256: sha(bytes), referenceBinaryValidation: binary,
        exactPhysicalBirthTrace: true, exactTracerTrace: true, oldSnapshotFieldsExact: true, ...compareRecordedHashes(old, current, { partial: current.definition.frames !== 180 }) });
    }
    for (const pair of P3G.pairs) {
      const own = quality.filter(r => r.definition.seed === pair.seed && r.definition.renderSeed === pair.renderSeed), direct = own.find(r => r.definition.method === 'DD');
      if (own.length !== 3 || !direct) throw new Error('Missing predeclared quality arm');
      const memory = own.find(r => r.definition.method === 'memory');
      answer.budgetLocks.push({ ...pair, ...selectionBudgetLock(memory, own.find(r => r.definition.method === 'curvature'), direct, direct.definition.frames) });
      let previousCache = []; const eventRecords = new Map(), totals = { ...pair, inputCount: 0, unselectedCount: 0, createdCount: 0, usedCount: 0, overlappingCount: 0, expiredMissingCount: 0, previousLiveCount: 0 };
      if (memory.memoryEvents.length !== memory.definition.frames) throw new Error('Missing full-frame memory records');
      for (let i = 0; i < memory.memoryEvents.length; i++) {
        const item = memory.memoryEvents[i]; if (item.frame !== i + 1) throw new Error('Memory frame sequence incomplete');
        const bytes = await fs.readFile(path.join(out, item.file)); requireFrozenChecksum(bytes, item.sha256, item.file); const record = JSON.parse(bytes), checkpoint = memory.checkpoints.find(p => p.frame === item.frame);
        const points = checkpoint ? await readParticles(out, checkpoint.particles) : null, summary = summarizeMemoryEvents(record, previousCache, P3G, points); previousCache = record.events.cacheAfter;
        if (JSON.stringify(summary) !== JSON.stringify(item.summary) || memory.memoryTrace[i].memoryStateHash !== summary.afterHash) throw new Error('Memory provenance summary/hash differs from raw');
        if (JSON.stringify(record.events.summary) !== JSON.stringify(memory.memoryTrace[i].summary) || record.events.summary.savedMembers !== memory.selectionTrace[i].selectedMemberCount || record.events.summary.savedIDHash !== memory.selectionTrace[i].selectionIDHash) throw new Error('Memory raw provenance does not match the actual selection trace');
        for (const k of ['inputCount', 'unselectedCount', 'createdCount', 'usedCount', 'overlappingCount', 'expiredMissingCount', 'previousLiveCount']) totals[k] += summary[k];
        if (checkpoint) eventRecords.set(item.frame, record.events);
        answer.memoryDetails.push({ candidate: memory.definition.id, ...item });
      }
      totals.reuseFractionOfPreviousLive = totals.previousLiveCount ? totals.usedCount / totals.previousLiveCount : null;
      totals.reuseFractionOfInputs = totals.inputCount ? totals.usedCount / totals.inputCount : null; totals.reuseFractionOfUnselected = totals.unselectedCount ? totals.usedCount / totals.unselectedCount : null; answer.exposure.push(totals);
      const masks = new Map();
      for (const ref of direct.captures) {
        const roi = referenceMasks([await readImage(out, ref.image)], P3G.image), id = `${direct.definition.id}-f${ref.frame}-${ref.view.id}`;
        const record = { id, width: roi.width, height: roi.height, orientation: roi.orientation, reference: ref.image.file, masks: {} };
        for (const name of ['foregroundMask', 'holeMask']) { const bytes = Buffer.from(roi[name]), file = `images/roi-${id}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes); record.masks[name] = { file, sha256: sha(bytes), count: bytes.reduce((a, b) => a + b, 0) }; }
        masks.set(`${ref.frame}-${ref.view.id}`, roi); answer.masks.push(record);
      }
      for (const candidate of own.filter(r => r.definition.method !== 'DD')) {
        const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, direct.trace), paths = [], images = [];
        for (const c of candidate.checkpoints) { const ref = direct.checkpoints.find(p => p.frame === c.frame); paths.push({ frame: c.frame, time: c.time, ...pathsWithOpticalWeights(await readParticles(out, c.particles), await readParticles(out, ref.particles), P3G) }); }
        for (const c of candidate.captures) { const ref = direct.captures.find(p => p.frame === c.frame && p.view.id === c.view.id); images.push({ frame: c.frame, view: c.view, ...pairedImageError(await readImage(out, c.image), await readImage(out, ref.image), masks.get(`${c.frame}-${c.view.id}`), P3G.image) }); }
        for (const item of candidate.selections) {
          const bytes = await fs.readFile(path.join(out, item.file)); requireFrozenChecksum(bytes, item.sha256, item.file);
          const points = await readParticles(out, candidate.checkpoints.find(c => c.frame === item.frame).particles), summary = summarizeMemorySelection(JSON.parse(bytes), points, P3G, candidate.definition.method === 'memory' ? eventRecords.get(item.frame) : null);
          if (JSON.stringify(summary) !== JSON.stringify(item.summary)) throw new Error('Production selection summary differs from raw data');
          answer.selectionDetails.push({ candidate: candidate.definition.id, ...item });
        }
        const c = candidate.snapshots.at(-1).counters, comparison = { candidate: candidate.definition.id, reference: direct.definition.id, scenario: 'stationary', ...pair, method: candidate.definition.method,
          paths, images, pooled: poolPairedImages(images), physicsAndBirthRngMatched, cacheFallbacks: c.cacheFallbacks,
          capacityBlocks: c.physicsFullSteps + c.physicsCapacityLimitedSteps + c.physicsSuppressedEmissionCredit + c.tracerCapacityDropped };
        comparison.accuracyCheck = deployedQualityGate(comparison, P3G.accuracy); answer.comparisons.push(comparison);
      }
    }
    answer.gate = memoryGate(answer.comparisons, answer.budgetLocks, P3G.pairs, answer.exposure); answer.complete = true;
  } catch (e) { answer.failures.push({ reason: e.stack || String(e) }); } return answer;
}

export async function runP3gTimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl), result = { definition, status: 'running', graphics, trace: [], timings: [], selectionTrace: [], memorySummaries: [], browserErrors: errors };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3; r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0); const trace = [r.trace()], timings = [], selectionTrace = [], memorySummaries = [];
      for (let frame = 1; frame <= 180; frame++) { const sample = frame >= 60 && frame % 3 === 0, data = r.frame(spec.dt, { sync: sample ? 'finish' : 'none' }); trace.push(data.trace); if (data.correctionSummary) selectionTrace.push(data.correctionSummary); if (data.memorySummary) memorySummaries.push(data.memorySummary); if (sample) timings.push({ frame, time: data.time, ...data.timing, counts: data.counts }); }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), trace, timings, selectionTrace, memorySummaries };
    }, { seed: definition.seed, config: p3gConfig(definition), spec: P3G });
    validateP3gSnapshot(data.initial); validateP3gSnapshot(data.final); Object.assign(result, data);
    if (data.timings.length !== 41 || data.trace.length !== 181) throw new Error('Incomplete timing evidence');
    result.distributions = Object.fromEntries(timingKeys.map(k => [k, distribution(data.timings.map(t => t[k] ?? 0))]));
    for (const t of data.timings) {
      if (!String(t.synchronization).includes('finish')) throw new Error('Unsynchronized timing sample');
      for (const k of timingKeys) if (!(definition.method === 'DD' && ['correctionSelectionMs', 'correctionQueryMs', 'memoryModelMs', 'memoryFinalizeMs'].includes(k)) && (!Number.isFinite(t[k]) || t[k] < 0)) throw new Error(`Missing/nonfinite timing ${k}`);
      const sum = ['tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'affineGroupingMs', 'affineModelBuildMs', 'correctionSelectionMs', 'correctionQueryMs', 'memoryModelMs', 'affineLookupMs', 'tracerAdvectionMs', 'memoryFinalizeMs'].reduce((s, k) => s + (t[k] ?? 0), 0); if (sum > t.tracerMs + .01) throw new Error('Tracer substages exceed total');
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); } return result;
}

export async function main() {
  const args = parseP3gArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3g-run.mjs --suite all|quick [--out DIR] [--baseline P3F_DIR] [--baseline-archive ZIP] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3g-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const baseline = await loadP3gBaseline(path.resolve(args.baseline || path.join(researchRoot, 'runs', 'p3f-full')), args.baselineArchive ? path.resolve(args.baselineArchive) : null);
  const manifest = { phase: 'P3g', status: 'running', stageStatus: 'quality_running', exploratory: true, protocolComplete: false, args, specification: P3G,
    metadata: hostMetadata(), baseline: baseline.metadata, plannedQuality: qualityCasesP3g(args.suite), plannedTiming: timingCasesP3g(), results: [], physicsAndBirthLocks: [], timingProductionLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); let server, launched; const quality = [], timing = []; await save();
  async function record(d, run) {
    const started = Date.now(); console.log(`[${manifest.results.length + 1}] ${d.id}`); const r = await run(); r.hostElapsedMs = Date.now() - started;
    if (r.status === 'passed') {
      const ref = quality.find(q => q.definition.method === 'DD' && q.definition.seed === d.seed && q.definition.renderSeed === d.renderSeed);
      try {
        if (ref) requirePairedTrace(ref.trace, r.trace); manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: ref?.definition.id || d.id, steps: r.trace.length, passed: true });
        if (d.family === 'timing') {
          const same = quality.find(q => q.definition.method === d.method && q.definition.seed === d.seed), lock = requireTimingProductionMatch(same, r);
          if (JSON.stringify(same.selectionTrace) !== JSON.stringify(r.selectionTrace) || JSON.stringify(same.memoryTrace.map(t => t.summary)) !== JSON.stringify(r.memorySummaries)) throw new Error('Quality/timing selection or memory trace differs');
          if (d.method === 'memory' && (same.snapshots[0].memoryStateHash !== r.initial.memoryStateHash || same.snapshots.at(-1).memoryStateHash !== r.final.memoryStateHash)) throw new Error('Quality/timing endpoint cache differs');
          manifest.timingProductionLocks.push({ candidate: d.id, reference: same.definition.id, ...lock, exactSelectionTrace: true, exactMemorySummaries: true, endpointMemoryStateHashExact: d.method === 'memory' });
        }
      } catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
    }
    const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r));
    if (d.family !== 'timing') quality.push(r); else { timing.push(r); const columns = ['frame', 'time', ...timingKeys]; await fs.writeFile(path.join(out, `${d.id}.csv`), `${columns.join(',')}\n${r.timings.map(t => columns.map(k => t[k] ?? '').join(',')).join('\n')}\n`); }
    manifest.results.push({ id: d.id, family: d.family, status: r.status, rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null }); console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
  }
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable); manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (const d of manifest.plannedQuality) await record(d, () => runP3gQualityCase(launched.browser, server.url, d, out));
    manifest.quality = await compareP3g(out, quality, baseline);
    const permission = timingPermission({ suite: args.suite, executionValid: manifest.quality.complete, qualityGate: manifest.quality.gate }); manifest.stageStatus = permission.stageStatus;
    if (permission.run) {
      console.log('BOTH SEED GATES PASSED: starting ten independent synchronized timing runs'); manifest.stageStatus = 'timing_running'; await save();
      for (const d of manifest.plannedTiming) await record(d, () => runP3gTimingCase(launched.browser, server.url, d));
      manifest.stageStatus = timing.every(r => r.status === 'passed') ? 'timing_complete' : 'execution_failed';
    } else { manifest.timingSkipped = { reason: permission.reason, selectionGate: manifest.quality.gate, plannedRuns: 10 }; console.log(`TIMING SKIPPED: ${permission.reason}`); }
    manifest.timing = aggregateTiming(timing, P3G.scenarios, P3G.methods.filter(m => m.id !== 'curvature'), 5);
    const executionValid = manifest.quality.complete && manifest.results.every(r => r.status === 'passed'); manifest.protocolComplete = args.suite === 'all' && executionValid && (!permission.run || timing.length === 10);
    manifest.decision = memoryDecision(manifest.timing, manifest.quality.gate, manifest.protocolComplete, P3G.decision); manifest.status = executionValid ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.stageStatus = 'execution_failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try { manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes); const after = await loadP3gBaseline(baseline.metadata.directory, baseline.metadata.archive?.path); if (JSON.stringify(after.metadata) !== JSON.stringify(baseline.metadata)) throw new Error('Baseline changed'); manifest.baselineUnchanged = true; }
    catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; manifest.status = 'failed'; manifest.protocolComplete = false; }
    if (manifest.decision) manifest.decision.engineeringGo &&= manifest.status === 'passed'; manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3g results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
