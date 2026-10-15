import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3C, p3cConfig, casesP3c, parseP3cArgs } from './p3c-design.mjs';
import { P3B } from './p3b-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3Snapshot } from './p3-run.mjs';
import { traceRow, requirePairedTrace } from './p3b-run.mjs';
import { decodeFloat32, referenceMasks } from './lib/p3-metrics.mjs';
import { encodeParticles, decodeParticles, pairedImageError, poolPairedImages, approximationGate } from './lib/p3b-metrics.mjs';
import { directionalPaths, poolDirectional, interactionPaths, poolInteraction, summarizeInputs } from './lib/p3c-metrics.mjs';

export function validateComponentLedger(field, c) {
  if (!['both', 'velocity', 'temperature'].includes(field.components) || !Number.isFinite(c.componentDirectQueries)) throw new Error('Missing component field contract');
  if (field.mode === 'grid') {
    if (c.fieldQueries !== c.cacheNodeQueries + c.cacheFallbacks + c.componentDirectQueries ||
        c.cacheHits + c.cacheMisses !== c.cacheStencilLookups ||
        c.cacheStencilLookups !== 8 * (c.tracerFieldQueries - c.cacheOutsideQueries) ||
        c.cacheFallbacks !== c.cacheCapacityFallbacks + c.cacheOutsideQueries ||
        (c.cacheFallbacks === 0 && c.cacheNodeQueries !== c.cacheMisses)) throw new Error('Component cache accounting failed');
    if (field.components === 'both' && c.componentDirectQueries !== 0) throw new Error('GG performed unexpected direct component queries');
    if (field.components !== 'both' && c.componentDirectQueries !== c.tracerFieldQueries - c.cacheFallbacks) throw new Error('Hybrid direct component query count differs from successful interpolation queries');
  } else if (field.mode !== 'tree' || c.componentDirectQueries !== 0) throw new Error('DD component mode accounting failed');
}
export function validateP3cSnapshot(s) {
  validateP3Snapshot(s); validateComponentLedger(s.field, s.counters);
  const c = s.counters;
  if (c.cacheFallbacks !== 0) throw new Error('Primary component diagnostic requires zero cache fallback');
  if (!Number.isFinite(c.componentDirectNoThermalSupportQueries) || c.componentDirectNoThermalSupportQueries < 0 || c.componentDirectNoThermalSupportQueries > c.componentDirectQueries) throw new Error('Invalid component thermal support counters');
  const remaining = c.noThermalSupportQueries - c.componentDirectNoThermalSupportQueries;
  if (s.field.mode === 'grid' && (remaining < 0 || remaining > c.cacheNodeQueries)) throw new Error('Node thermal support accounting failed');
  if (Math.abs(s.field.time - Math.max(0, s.time - P3C.dt)) > 1e-8) throw new Error('Frozen physical field time mismatch');
  return s;
}
export function requireCompleteCase(r) {
  const d = r.definition, frames = [0, ...Array.from({ length: d.frames / P3C.sampleEvery }, (_, i) => (i + 1) * P3C.sampleEvery)];
  if (r.trace.length !== d.frames + 1 || r.trace.some((v, i) => v.frame !== i)) throw new Error('Incomplete per-step trace');
  if (JSON.stringify(r.checkpoints.map(c => c.frame)) !== JSON.stringify(frames)) throw new Error('Incomplete particle checkpoints');
  const expected = d.captures.flatMap(f => P3C.views.map(v => `${f}-${v.id}`));
  if (JSON.stringify(r.captures.map(c => `${c.frame}-${c.view.id}`)) !== JSON.stringify(expected)) throw new Error('Incomplete image captures');
  if (d.arm === 'DD' && r.checkpoints.slice(1).some(c => !Array.isArray(c.inputs) || !c.probe || c.inputs.length !== c.probe.samples.length)) throw new Error('Incomplete DD input probes');
  return true;
}
async function saveParticles(out, stem, points) {
  const { bytes, ...record } = encodeParticles(points), file = `particles/${stem}.f64`;
  await fs.mkdir(path.join(out, 'particles'), { recursive: true }); await fs.writeFile(path.join(out, file), bytes); return { ...record, file };
}
async function readParticles(out, record) { return decodeParticles(await fs.readFile(path.join(out, record.file)), record); }
async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }

export async function runP3cCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], checkpoints: [], captures: [], browserErrors: errors };
  async function checkpoint(snapshot, captured = null, probe = null) {
    validateP3cSnapshot(snapshot); const points = snapshot.renderParticles;
    delete snapshot.renderParticles; delete snapshot.physicsParticles; result.snapshots.push(snapshot);
    const particles = await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles,
      inputs: captured?.inputs ?? null, inputPhase: captured?.inputPhase ?? null, fieldTime: captured?.fieldTime ?? null, probe });
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3cConfig(definition) });
    result.trace.push(traceRow(initial)); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const sample = frame % P3C.sampleEvery === 0;
      const state = await page.evaluate(({ dt, sample, capture, stride, h, maxNodes }) => {
        const r = window.__demo.researchP3, captured = capture ? r.stepWithInputs(dt, { stride }) : (r.step(1, dt), null);
        const trace = r.trace(); if (!sample) return { trace };
        const snapshot = r.snapshot({ detail: true }); let probe = null;
        if (captured) {
          probe = r.fieldProbe(captured.inputs.map(p => p.position), { cellSize: h, maxNodes }); const after = r.snapshot({ detail: true });
          if (JSON.stringify(snapshot) !== JSON.stringify(after)) throw new Error('Read-only actual-input probe changed production state');
          if (probe.fieldTime !== captured.fieldTime) throw new Error('Probe sampled a different physical time than captured inputs');
        }
        return { trace, snapshot, captured, probe };
      }, { dt: P3C.dt, sample, capture: sample && definition.arm === 'DD', stride: P3C.inputStride, h: P3C.cellSize, maxNodes: P3C.maxNodes });
      result.trace.push(state.trace); if (sample) await checkpoint(state.snapshot, state.captured, state.probe);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3C.views) {
        const data = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'), image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Camera/capture changed production state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0) throw new Error('Empty optical image');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64'));
        result.captures.push({ frame, time: frame * P3C.dt, view, image, preview });
      }
    }
    requireCompleteCase(result); if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

export async function compareP3c(out, results, planned) {
  const comparisons = [], masks = [], groups = [], failures = [];
  const find = d => results.find(r => r.definition.id === d.id);
  for (const d of planned.filter(d => d.arm !== 'DD')) {
    const candidate = find(d), dd = planned.find(x => x.arm === 'DD' && x.scenario === d.scenario && x.seed === d.seed && x.renderSeed === d.renderSeed), direct = dd && find(dd);
    if (candidate?.status !== 'passed' || direct?.status !== 'passed') { failures.push({ candidate: d.id, reason: 'Candidate or DD trajectory missing/failed' }); continue; }
    try {
      requireCompleteCase(candidate); requireCompleteCase(direct);
      const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, direct.trace), paths = [], images = [];
      for (const c of candidate.checkpoints) {
        const ref = direct.checkpoints.find(r => r.frame === c.frame);
        paths.push({ frame: c.frame, time: c.time, ...directionalPaths(await readParticles(out, c.particles), await readParticles(out, ref.particles), P3C) });
      }
      for (const c of candidate.captures) {
        const ref = direct.captures.find(r => r.frame === c.frame && r.view.id === c.view.id), image = await readImage(out, ref.image);
        const roi = referenceMasks([image], P3C.image), id = `${dd.id}-f${c.frame}-${c.view.id}`;
        if (!masks.some(m => m.id === id)) {
          const record = { id, width: roi.width, height: roi.height, orientation: roi.orientation, reference: ref.image.file, masks: {} };
          for (const name of ['foregroundMask', 'holeMask']) {
            const bytes = Buffer.from(roi[name]), file = `images/roi-${id}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes);
            record.masks[name] = { file, sha256: createHash('sha256').update(bytes).digest('hex'), count: bytes.reduce((a, b) => a + b, 0) };
          }
          masks.push(record);
        }
        images.push({ frame: c.frame, view: c.view, ...pairedImageError(await readImage(out, c.image), image, roi, P3C.image) });
      }
      const c = candidate.snapshots.at(-1).counters;
      const comparison = { candidate: d.id, reference: dd.id, scenario: d.scenario, seed: d.seed, renderSeed: d.renderSeed, arm: d.arm,
        paths, pooledPaths: poolDirectional(paths.filter(p => p.frame > 0), P3C), images, pooled: poolPairedImages(images), physicsAndBirthRngMatched,
        cacheFallbacks: c.cacheFallbacks, capacityBlocks: c.physicsFullSteps + c.physicsCapacityLimitedSteps + c.physicsSuppressedEmissionCredit + c.tracerCapacityDropped };
      comparison.accuracyCheck = { ...approximationGate(comparison, P3B.selection), interpretation: 'Descriptive application of prior P3b accuracy thresholds only. No route-go or performance conclusion.' };
      comparisons.push(comparison);
      if (paths.some(p => p.visualStateMismatchIds.length)) throw new Error('Matched T/d/life changed');
    } catch (e) { failures.push({ candidate: d.id, reason: e.stack || String(e) }); }
  }
  for (const d of planned.filter(d => d.arm === 'DD')) {
    try {
      const quartet = Object.fromEntries(P3C.arms.map(a => [a.id, results.find(r => r.definition.scenario === d.scenario && r.definition.seed === d.seed && r.definition.renderSeed === d.renderSeed && r.definition.arm === a.id)]));
      for (const r of Object.values(quartet)) { if (r?.status !== 'passed') throw new Error('Incomplete four-arm group'); requireCompleteCase(r); }
      const checkpoints = [];
      for (const c of quartet.DD.checkpoints.filter(c => c.frame > 0)) {
        const arrays = Object.fromEntries(await Promise.all(Object.entries(quartet).map(async ([arm, r]) => [arm, await readParticles(out, r.checkpoints.find(p => p.frame === c.frame).particles)])));
        checkpoints.push({ frame: c.frame, time: c.time, ...interactionPaths(arrays) });
      }
      groups.push({ scenario: d.scenario, seed: d.seed, renderSeed: d.renderSeed, arms: Object.fromEntries(Object.entries(quartet).map(([a, r]) => [a, r.definition.id])),
        interaction: { checkpoints, pooled: poolInteraction(checkpoints) }, inputs: summarizeInputs(quartet.DD.checkpoints, P3C) });
    } catch (e) { failures.push({ group: d.id, reason: e.stack || String(e) }); }
  }
  return { comparisons, masks, groups, failures, complete: results.length === planned.length && results.every(r => r.status === 'passed') && comparisons.length === planned.length * .75 && groups.length === planned.length / 4 && failures.length === 0,
    interpretation: P3C.interpretation };
}

export async function main() {
  const args = parseP3cArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3c-run.mjs --suite all|pilot|quick [--out DIR] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3c-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true });
  const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { phase: 'P3c', status: 'running', exploratory: true, protocolComplete: args.suite === 'all', args, specification: P3C,
    metadata: hostMetadata(), plannedQuality: casesP3c(args.suite), plannedTiming: [], results: [], physicsAndBirthLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); const results = [], traces = new Map(); let server, launched; await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    for (let i = 0; i < manifest.plannedQuality.length; i++) {
      const d = manifest.plannedQuality[i], started = Date.now(); console.log(`[${i + 1}/${manifest.plannedQuality.length}] ${d.id}`);
      const r = await runP3cCase(launched.browser, server.url, d, out); r.hostElapsedMs = Date.now() - started;
      if (r.status === 'passed') {
        const key = `${d.scenario}-${d.seed}-${d.renderSeed}`, baseline = traces.get(key);
        try {
          if (baseline) requirePairedTrace(baseline.trace, r.trace); else traces.set(key, { id: d.id, trace: r.trace });
          manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: baseline?.id || d.id, steps: r.trace.length, passed: true });
        } catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
      }
      const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r)); results.push(r);
      manifest.results.push({ id: d.id, status: r.status, family: 'quality', rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null });
      console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
    }
    manifest.analysis = await compareP3c(out, results, manifest.plannedQuality);
    manifest.status = manifest.analysis.complete ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try { manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes); }
    catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; manifest.status = 'failed'; }
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3c results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
