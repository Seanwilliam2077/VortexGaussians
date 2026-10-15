import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3D, p3dConfig, qualityCasesP3d, timingCasesP3d, parseP3dArgs } from './p3d-design.mjs';
import { P3B } from './p3b-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3cSnapshot } from './p3c-run.mjs';
import { traceRow, requirePairedTrace } from './p3b-run.mjs';
import { decodeFloat32, referenceMasks, distribution } from './lib/p3-metrics.mjs';
import { encodeParticles, decodeParticles, pairedParticles, pairedImageError, poolPairedImages, approximationGate, aggregateTiming } from './lib/p3b-metrics.mjs';
import { requireFrozenChecksum, requireOldFields, exactTracerReplay, compareRecordedHashes, costDecision } from './lib/p3d-metrics.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
export function validateQueryLedger(s) {
  const c = s.counters, fields = ['fullFieldQueries', 'velocityOnlyFieldQueries', 'thermalOnlyFieldQueries', 'fullNoThermalSupportQueries', 'thermalOnlyNoThermalSupportQueries'];
  if (fields.some(k => !Number.isInteger(c[k]) || c[k] < 0)) throw new Error('Missing or invalid specialized query counters');
  if (c.fieldQueries !== c.fullFieldQueries + c.velocityOnlyFieldQueries + c.thermalOnlyFieldQueries ||
      c.noThermalSupportQueries !== c.fullNoThermalSupportQueries + c.thermalOnlyNoThermalSupportQueries ||
      c.fullNoThermalSupportQueries > c.fullFieldQueries || c.thermalOnlyNoThermalSupportQueries > c.thermalOnlyFieldQueries) throw new Error('Specialized query accounting failed');
  if (s.field.evaluation === 'specialized') {
    if (s.field.mode !== 'grid' || s.field.components !== 'temperature' || c.fullFieldQueries !== 0 ||
        c.velocityOnlyFieldQueries !== c.componentDirectQueries || c.velocityOnlyFieldQueries !== c.tracerFieldQueries ||
        c.thermalOnlyFieldQueries !== c.cacheNodeQueries || c.componentDirectNoThermalSupportQueries !== 0) throw new Error('Specialized method performed redundant or missing component work');
  } else if (s.field.evaluation !== 'combined' || c.velocityOnlyFieldQueries !== 0 || c.thermalOnlyFieldQueries !== 0) throw new Error('Combined legacy route performed specialized queries');
  return true;
}
export function validateP3dSnapshot(s) { validateP3cSnapshot(s); validateQueryLedger(s); return s; }
export function requireCompleteP3dCase(r) {
  const d = r.definition, frames = [0, ...Array.from({ length: d.frames / 15 }, (_, i) => (i + 1) * 15)];
  if (r.trace.length !== d.frames + 1 || r.trace.some((t, i) => t.frame !== i) || r.tracerTrace.length !== d.frames + 1) throw new Error('Incomplete quality trace');
  exactTracerReplay(r.tracerTrace, r.tracerTrace);
  if (JSON.stringify(r.checkpoints.map(c => c.frame)) !== JSON.stringify(frames)) throw new Error('Incomplete quality particle checkpoints');
  if (JSON.stringify(r.captures.map(c => `${c.frame}-${c.view.id}`)) !== JSON.stringify(d.captures.flatMap(f => P3D.views.map(v => `${f}-${v.id}`)))) throw new Error('Incomplete quality images');
  return true;
}
async function saveParticles(out, stem, points) {
  const { bytes, ...record } = encodeParticles(points), file = `particles/${stem}.f64`;
  await fs.mkdir(path.join(out, 'particles'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes); return { ...record, file };
}
async function readParticles(out, record) { return decodeParticles(await fs.readFile(path.join(out, record.file)), record); }
async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }
async function verifyRawBytes(out, r, optional = false) {
  let verified = 0, absent = 0;
  for (const record of [...r.checkpoints.map(c => c.particles), ...r.captures.map(c => c.image)]) {
    let bytes;
    try { bytes = await fs.readFile(path.join(out, record.file)); }
    catch (e) { if (optional && e.code === 'ENOENT') { absent++; continue; } throw e; }
    if (sha(bytes) !== record.sha256) throw new Error(`Raw file checksum mismatch: ${record.file}`); verified++;
  }
  return { verified, absent, referenceFromAuthenticatedJson: optional };
}
export async function runP3dQualityCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], tracerTrace: [], checkpoints: [], captures: [], browserErrors: errors };
  async function checkpoint(snapshot) {
    validateP3dSnapshot(snapshot); const points = snapshot.renderParticles;
    delete snapshot.renderParticles; delete snapshot.physicsParticles; result.snapshots.push(snapshot);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles: await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points) });
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3dConfig(definition) });
    result.trace.push(traceRow(initial)); result.tracerTrace.push({ frame: 0, tracerHash: initial.tracerHash }); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      // Quality-only dense snapshot computes the requested tracer hash; timing runs never use this path.
      const state = await page.evaluate(({ dt, sample }) => { const r = window.__demo.researchP3; r.step(1, dt); return r.snapshot({ detail: sample }); }, { dt: P3D.dt, sample: frame % 15 === 0 });
      validateP3dSnapshot(state); result.trace.push(traceRow(state)); result.tracerTrace.push({ frame, tracerHash: state.tracerHash });
      if (state.renderParticles) await checkpoint(state);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3D.views) {
        const data = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'), image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Camera/capture changed production state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0) throw new Error('Empty optical image');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64'));
        result.captures.push({ frame, time: frame * P3D.dt, view, image, preview });
      }
    }
    requireCompleteP3dCase(result); if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}
export async function runP3dTimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, timings: [], trace: [], browserErrors: errors };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3; r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0);
      const timings = [], trace = [r.trace()];
      for (let frame = 1; frame <= spec.timing.lastFrame; frame++) {
        const sample = frame >= spec.timing.firstFrame && frame % spec.timing.sampleEvery === 0;
        const data = r.frame(spec.dt, { sync: sample ? 'finish' : 'none' });
        if (!data.trace) throw new Error('Missing lightweight frame trace'); trace.push(data.trace);
        if (sample) timings.push({ frame, time: data.time, ...data.timing, counts: data.counts });
      }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), timings, trace };
    }, { seed: definition.seed, config: p3dConfig(definition), spec: P3D });
    validateP3dSnapshot(data.initial); validateP3dSnapshot(data.final); Object.assign(result, data);
    const keys = ['simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
    result.distributions = Object.fromEntries(keys.map(k => [k, distribution(data.timings.map(t => t[k]))]));
    if (data.timings.length !== 41 || data.trace.length !== 181) throw new Error('Incomplete timing run');
    for (const t of data.timings) {
      assertFiniteTree(t); if (!String(t.synchronization).includes('finish')) throw new Error('Unsynchronized timing sample');
      if (t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.tracerAdvectionMs > t.tracerMs + .01) throw new Error('Tracer stages exceed total');
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

export async function loadBaseline(directory, archive) {
  const pinBytes = await fs.readFile(new URL('./lib/p3d-baseline.json', import.meta.url)), pin = JSON.parse(pinBytes);
  if (Object.keys(pin.files).length !== 19) throw new Error('Frozen baseline must include manifest and eighteen raw JSON records');
  const checked = {};
  for (const [file, expected] of Object.entries(pin.files)) {
    if (path.basename(file) !== file) throw new Error('Unexpected baseline path');
    checked[file] = requireFrozenChecksum(await fs.readFile(path.join(directory, file)), expected, file);
  }
  const bytes = await fs.readFile(path.join(directory, 'manifest.json')), m = JSON.parse(bytes);
  if (m.phase !== 'P3c' || m.status !== 'passed' || !m.analysis?.complete || !m.sourceFreeze?.matched || m.results.length !== 36) throw new Error('P3c baseline is incomplete or failed');
  const archiveHash = archive ? sha(await fs.readFile(archive)) : null;
  if (archive && archiveHash !== pin.archiveSha256) throw new Error('Supplied archive is not the frozen P3c ZIP');
  const metadata = { directory, manifestSha256: sha(bytes), sourceHashes: m.metadata.sourceHashes, sourceFreeze: m.sourceFreeze,
    authenticatedJsonFiles: checked, frozenChecksumListSha256: sha(pinBytes), expectedArchiveSha256: pin.archiveSha256,
    archive: archive ? { path: archive, sha256: archiveHash } : null };
  return { manifest: m, metadata };
}
async function legacyRegression(out, candidate, baselineDirectory, baselineManifest) {
  const d = candidate.definition, id = `${d.scenario}-${d.baselineArm}-s${d.seed}-r${d.renderSeed}`;
  const entry = baselineManifest.results.find(r => r.id === id); if (entry?.status !== 'passed') throw new Error(`Missing immutable baseline ${id}`);
  const bytes = await fs.readFile(path.join(baselineDirectory, entry.rawFile)), reference = JSON.parse(bytes);
  const referenceBinaryValidation = await verifyRawBytes(baselineDirectory, reference, true); await verifyRawBytes(out, candidate);
  requirePairedTrace(reference.trace.slice(0, candidate.trace.length), candidate.trace);
  for (const s of candidate.snapshots) { const old = reference.snapshots.find(r => r.frame === s.frame); if (!old) throw new Error('Missing legacy snapshot'); requireOldFields(old, s); }
  return { candidate: d.id, reference: id, referenceRawFile: entry.rawFile, referenceRawSha256: sha(bytes), referenceBinaryValidation, oldSnapshotFieldsExact: true, physicalAndBirthTraceExact: true,
    ...compareRecordedHashes(reference, candidate, { partial: d.frames !== 180 }) };
}
export async function compareP3d(out, results, planned, baseline) {
  const comparisons = [], masks = [], equivalence = [], legacy = [], failures = [];
  for (const d of planned) {
    const candidate = results.find(r => r.definition.id === d.id);
    if (candidate?.status !== 'passed') { failures.push({ candidate: d.id, reason: 'Required quality case missing/failed' }); continue; }
    try {
      requireCompleteP3dCase(candidate); await verifyRawBytes(out, candidate);
      if (d.baselineArm) legacy.push(await legacyRegression(out, candidate, baseline.metadata.directory, baseline.manifest));
      if (d.method === 'DD') continue;
      const samePair = r => r.definition.scenario === d.scenario && r.definition.seed === d.seed && r.definition.renderSeed === d.renderSeed;
      const direct = results.find(r => r.definition.method === 'DD' && samePair(r));
      if (direct?.status !== 'passed') throw new Error('Paired DD missing/failed');
      requireCompleteP3dCase(direct); const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, direct.trace), paths = [], images = [];
      for (const c of candidate.checkpoints) {
        const ref = direct.checkpoints.find(r => r.frame === c.frame);
        paths.push({ frame: c.frame, time: c.time, ...pairedParticles(await readParticles(out, c.particles), await readParticles(out, ref.particles)) });
      }
      for (const c of candidate.captures) {
        const ref = direct.captures.find(r => r.frame === c.frame && r.view.id === c.view.id), image = await readImage(out, ref.image), roi = referenceMasks([image], P3D.image);
        const id = `${direct.definition.id}-f${c.frame}-${c.view.id}`;
        if (!masks.some(m => m.id === id)) {
          const record = { id, width: roi.width, height: roi.height, orientation: roi.orientation, reference: ref.image.file, masks: {} };
          for (const name of ['foregroundMask', 'holeMask']) {
            const bytes = Buffer.from(roi[name]), file = `images/roi-${id}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes);
            record.masks[name] = { file, sha256: sha(bytes), count: bytes.reduce((a, b) => a + b, 0) };
          } masks.push(record);
        }
        images.push({ frame: c.frame, view: c.view, ...pairedImageError(await readImage(out, c.image), image, roi, P3D.image) });
      }
      const last = candidate.snapshots.at(-1).counters, comparison = { candidate: d.id, reference: direct.definition.id, scenario: d.scenario, seed: d.seed, renderSeed: d.renderSeed, method: d.method,
        paths, images, pooled: poolPairedImages(images), physicsAndBirthRngMatched, cacheFallbacks: last.cacheFallbacks,
        capacityBlocks: last.physicsFullSteps + last.physicsCapacityLimitedSteps + last.physicsSuppressedEmissionCredit + last.tracerCapacityDropped };
      comparison.accuracyCheck = approximationGate(comparison, P3B.selection); comparisons.push(comparison);
      if (paths.some(p => p.visualStateMismatchIds.length)) throw new Error('Matched visual state changed');
      if (d.method === 'DG-specialized') {
        const original = results.find(r => r.definition.method === 'DG-original' && samePair(r));
        if (original?.status !== 'passed') throw new Error('Original DG missing/failed');
        requirePairedTrace(original.trace, candidate.trace); exactTracerReplay(original.tracerTrace, candidate.tracerTrace);
        equivalence.push({ candidate: d.id, reference: original.definition.id, steps: candidate.tracerTrace.length, exactTracerHashes: true,
          ...compareRecordedHashes(original, candidate, { partial: d.frames !== 180 }) });
      }
    } catch (e) { failures.push({ candidate: d.id, reason: e.stack || String(e) }); }
  }
  return { comparisons, masks, equivalence, legacyRegression: legacy, failures,
    complete: results.length === planned.length && results.every(r => r.status === 'passed') && planned.length > 0 && comparisons.length === planned.length * 2 / 3 && equivalence.length === planned.length / 3 && legacy.length === planned.length * 2 / 3 && failures.length === 0 };
}
function timingCsv(rows) {
  const names = ['frame', 'time', 'simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
  return `${names.join(',')}\n${rows.map(r => names.map(k => r[k] ?? '').join(',')).join('\n')}\n`;
}
export async function main() {
  const args = parseP3dArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3d-run.mjs --suite all|quality|timing|quick [--out DIR] [--baseline P3C_DIR] [--baseline-archive ZIP] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3d-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true });
  const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const baseline = await loadBaseline(path.resolve(args.baseline || path.join(researchRoot, 'runs', 'p3c-full')), args.baselineArchive ? path.resolve(args.baselineArchive) : null);
  const manifest = { phase: 'P3d', status: 'running', exploratory: true, protocolComplete: args.suite === 'all', args, specification: P3D, metadata: hostMetadata(), baseline: baseline.metadata,
    plannedQuality: qualityCasesP3d(args.suite), plannedTiming: timingCasesP3d(args.suite), results: [], physicsAndBirthLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); const quality = [], timing = [], traces = new Map(); let server, launched; await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    const cases = [...manifest.plannedQuality, ...manifest.plannedTiming];
    for (let i = 0; i < cases.length; i++) {
      const d = cases[i], started = Date.now(); console.log(`[${i + 1}/${cases.length}] ${d.id}`);
      const r = d.family === 'quality' ? await runP3dQualityCase(launched.browser, server.url, d, out) : await runP3dTimingCase(launched.browser, server.url, d);
      r.hostElapsedMs = Date.now() - started;
      if (r.status === 'passed') {
        const key = `${d.scenario}-${d.seed}-${d.renderSeed}`, old = traces.get(key);
        try {
          if (old) requirePairedTrace(old.trace, r.trace); else traces.set(key, { id: d.id, trace: r.trace });
          manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: old?.id || d.id, steps: r.trace.length, passed: true });
        } catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
      }
      const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r));
      if (d.family === 'quality') quality.push(r); else { timing.push(r); await fs.writeFile(path.join(out, `${d.id}.csv`), timingCsv(r.timings)); }
      manifest.results.push({ id: d.id, status: r.status, family: d.family, rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null });
      console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
    }
    if (quality.length) manifest.quality = await compareP3d(out, quality, manifest.plannedQuality, baseline);
    manifest.timing = aggregateTiming(timing, P3D.scenarios, P3D.methods, P3D.timing.repeats);
    const evidenceComplete = quality.length === 27 && timing.length === 45 && manifest.quality?.complete === true && timing.every(r => r.status === 'passed');
    const accuracyPassed = manifest.quality?.comparisons.length === 18 && manifest.quality.comparisons.every(c => c.accuracyCheck.passed);
    manifest.decision = costDecision(manifest.timing, P3D.decision, P3D.scenarios, evidenceComplete, accuracyPassed);
    manifest.status = manifest.results.length > 0 && manifest.results.every(r => r.status === 'passed') && (!quality.length || manifest.quality.complete) ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try {
      manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes);
      const baselineAfter = await loadBaseline(baseline.metadata.directory, baseline.metadata.archive?.path);
      if (JSON.stringify(baseline.metadata) !== JSON.stringify(baselineAfter.metadata)) throw new Error('Baseline provenance changed during run');
      manifest.baselineUnchanged = true;
    } catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; manifest.status = 'failed'; }
    if (manifest.decision) manifest.decision.engineeringGo &&= manifest.status === 'passed';
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3d results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
