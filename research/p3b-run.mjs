import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3B, p3bConfig, qualityCasesP3b, timingCasesP3b, parseP3bArgs } from './p3b-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3Snapshot } from './p3-run.mjs';
import { decodeFloat32, referenceMasks, distribution } from './lib/p3-metrics.mjs';
import { encodeParticles, decodeParticles, pairedParticles, pairedImageError, poolPairedImages, approximationGate, aggregateTiming, selectCache } from './lib/p3b-metrics.mjs';

export function validateP3bSnapshot(s) {
  validateP3Snapshot(s);
  if (!['tree', 'grid'].includes(s.field.mode) || !Number.isFinite(s.counters.cacheFallbacks)) throw new Error('P3b field API/counters missing');
  if (s.field.time > s.time || Math.abs(s.field.time - Math.max(0, s.time - P3B.dt)) > 1e-8) throw new Error('Field time differs from frozen pre-integration state');
  if (s.field.mode === 'grid') {
    const c = s.counters;
    if (c.fieldQueries !== c.cacheNodeQueries + c.cacheFallbacks || c.cacheHits + c.cacheMisses !== c.cacheStencilLookups ||
        c.cacheStencilLookups !== 8 * (c.tracerFieldQueries - c.cacheOutsideQueries) ||
        c.cacheFallbacks !== c.cacheCapacityFallbacks + c.cacheOutsideQueries ||
        (c.cacheFallbacks === 0 && c.cacheNodeQueries !== c.cacheMisses)) throw new Error('Grid cache accounting identity failed');
  }
  return s;
}
export function traceRow(s) {
  return { frame: s.frame, time: s.time, physicalHash: s.physicalHash,
    physicsRng: s.physics.rngState, physicsDraws: s.physics.randomDraws,
    renderRng: s.render.rngState, renderDraws: s.render.randomDraws,
    physicsEmitted: s.counters.physicsEmitted, tracerEmitted: s.counters.tracerEmitted,
    tracerPendingCredit: s.render.pendingEmissionCredit };
}
export function requirePairedTrace(a, b) {
  if (a.length !== b.length) throw new Error('Paired trace lengths differ');
  for (let i = 0; i < a.length; i++) if (JSON.stringify(a[i]) !== JSON.stringify(b[i])) throw new Error(`Physical state or birth RNG changed at step ${i}`);
  return true;
}

async function saveParticles(out, stem, points) {
  const { bytes, ...metadata } = encodeParticles(points); await fs.mkdir(path.join(out, 'particles'), { recursive: true });
  const file = `particles/${stem}.f64`; await fs.writeFile(path.join(out, file), bytes);
  return { ...metadata, file };
}
async function readParticles(out, record) { return decodeParticles(await fs.readFile(path.join(out, record.file)), record); }
async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }

export async function runP3bQualityCase(browser, baseUrl, definition, out) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, snapshots: [], trace: [], checkpoints: [], captures: [], browserErrors: errors };
  async function checkpoint(snapshot, probe = null) {
    validateP3bSnapshot(snapshot); const points = snapshot.renderParticles;
    delete snapshot.renderParticles; delete snapshot.physicsParticles;
    result.snapshots.push(snapshot);
    const particles = await saveParticles(out, `${definition.id}-f${snapshot.frame}`, points);
    result.checkpoints.push({ frame: snapshot.frame, time: snapshot.time, particles, probe });
  }
  try {
    const initial = await page.evaluate(({ seed, config }) => { const r = window.__demo.researchP3; r.reset(seed, config); return r.snapshot({ detail: true }); }, { seed: definition.seed, config: p3bConfig(definition) });
    result.trace.push(traceRow(initial)); await checkpoint(initial);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const state = await page.evaluate(({ dt, sample, positions }) => {
        const r = window.__demo.researchP3; r.step(1, dt); const s = r.snapshot({ detail: sample });
        let probe = null;
        if (sample) {
          probe = r.fieldProbe(positions); const after = r.snapshot();
          if (s.physicalHash !== after.physicalHash || s.tracerHash !== after.tracerHash || JSON.stringify(s.counters) !== JSON.stringify(after.counters)) throw new Error('Read-only probe changed production state');
        }
        return { snapshot: s, probe };
      }, { dt: P3B.dt, sample: frame % P3B.sampleEvery === 0 || frame === definition.frames, positions: P3B.probePositions });
      validateP3bSnapshot(state.snapshot); result.trace.push(traceRow(state.snapshot));
      if (state.snapshot.renderParticles) await checkpoint(state.snapshot, state.probe);
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3B.views) {
        const data = await page.evaluate(yaw => {
          const d = window.__demo, r = d.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          const preview = document.querySelector('canvas').toDataURL('image/png'); const image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Camera/capture changed state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, preview };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`, image = await saveImage(out, stem, data.image), preview = `images/${stem}.png`;
        if (image.summary.maxAlpha <= 0 || image.summary.meanRgb <= 0) throw new Error('Empty optical image');
        await fs.writeFile(path.join(out, preview), Buffer.from(data.preview.split(',')[1], 'base64'));
        result.captures.push({ frame, time: frame * P3B.dt, view, image, preview });
      }
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

export async function runP3bTimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, timings: [], trace: [], browserErrors: errors };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3;
      const trace = s => ({ frame: s.frame, time: s.time, physicalHash: s.physicalHash,
        physicsRng: s.physics.rngState, physicsDraws: s.physics.randomDraws, renderRng: s.render.rngState,
        renderDraws: s.render.randomDraws, physicsEmitted: s.counters.physicsEmitted,
        tracerEmitted: s.counters.tracerEmitted, tracerPendingCredit: s.render.pendingEmissionCredit });
      r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0);
      const timings = [], rows = [trace(initial)];
      for (let frame = 1; frame <= spec.timing.lastFrame; frame++) {
        const sampled = frame >= spec.timing.firstFrame && frame % spec.timing.sampleEvery === 0;
        const data = r.frame(spec.dt, { sync: sampled ? 'finish' : 'none' });
        if (!data.trace) throw new Error('Runtime omitted lightweight frame trace');
        rows.push(data.trace);
        if (sampled) timings.push({ frame, time: data.time, ...data.timing, counts: data.counts });
      }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), timings, trace: rows };
    }, { seed: definition.seed, config: p3bConfig(definition), spec: P3B });
    validateP3bSnapshot(data.initial); validateP3bSnapshot(data.final); Object.assign(result, data);
    const keys = ['simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
    result.distributions = Object.fromEntries(keys.map(k => [k, distribution(data.timings.map(t => t[k]))]));
    for (const t of data.timings) {
      if (!String(t.synchronization).includes('finish')) throw new Error('Unsynchronized timing sample');
      const accounted = t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.tracerAdvectionMs;
      if (accounted > t.tracerMs + .01) throw new Error('Tracer substage accounting exceeds tracer total');
    }
    if (errors.length) throw new Error(errors.join('\n')); result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

export async function compareP3b(out, results) {
  const comparisons = [], masks = [], failures = [];
  for (const candidate of results.filter(r => r.definition.method !== 'tree')) {
    const d = candidate.definition, tree = results.find(r => r.definition.method === 'tree' && r.definition.scenario === d.scenario && r.definition.seed === d.seed && r.definition.renderSeed === d.renderSeed);
    if (candidate.status !== 'passed' || tree?.status !== 'passed') { failures.push({ candidate: d.id, reason: 'Candidate or paired tree failed/missing' }); continue; }
    try {
      const physicsAndBirthRngMatched = requirePairedTrace(candidate.trace, tree.trace), paths = [], images = [];
      for (const point of candidate.checkpoints) {
        const reference = tree.checkpoints.find(p => p.frame === point.frame); if (!reference) throw new Error('Paired particle checkpoint missing');
        paths.push({ frame: point.frame, time: point.time, ...pairedParticles(await readParticles(out, point.particles), await readParticles(out, reference.particles)) });
      }
      for (const image of candidate.captures) {
        const reference = tree.captures.find(c => c.frame === image.frame && c.view.id === image.view.id); if (!reference) throw new Error('Paired tree image missing');
        const treeImage = await readImage(out, reference.image), roi = referenceMasks([treeImage], P3B.image), maskId = `${tree.definition.id}-f${image.frame}-${image.view.id}`;
        if (!masks.some(m => m.id === maskId)) {
          const record = { id: maskId, width: roi.width, height: roi.height, orientation: roi.orientation, reference: reference.image.file, masks: {} };
          for (const name of ['foregroundMask', 'holeMask']) {
            const bytes = Buffer.from(roi[name]), file = `images/roi-${maskId}-${name}.u8`; await fs.writeFile(path.join(out, file), bytes);
            record.masks[name] = { file, sha256: createHash('sha256').update(bytes).digest('hex'), count: bytes.reduce((a, b) => a + b, 0) };
          }
          masks.push(record);
        }
        images.push({ frame: image.frame, view: image.view, ...pairedImageError(await readImage(out, image.image), treeImage, roi, P3B.image) });
      }
      const last = candidate.snapshots.at(-1), c = last.counters;
      const comparison = { candidate: d.id, reference: tree.definition.id, scenario: d.scenario, seed: d.seed, renderSeed: d.renderSeed,
        method: d.method, role: d.role, paths, images, pooled: poolPairedImages(images), physicsAndBirthRngMatched,
        cacheFallbacks: c.cacheFallbacks, capacityBlocks: c.physicsFullSteps + c.physicsCapacityLimitedSteps + c.physicsSuppressedEmissionCredit + c.tracerCapacityDropped };
      comparison.errorGate = approximationGate(comparison, P3B.selection); comparisons.push(comparison);
      if (paths.some(p => p.visualStateMismatchIds.length)) failures.push({ candidate: d.id, reason: 'Matched birth IDs changed visual T/d/life; cache transport is not the only intervention' });
    } catch (e) { failures.push({ candidate: d.id, reason: e.stack || String(e) }); }
  }
  return { comparisons, masks, failures };
}

function timingCsv(rows) {
  const names = ['frame', 'time', 'simulationMs', 'tracerMs', 'tracerSetupMs', 'treeQueryAndAdvectionMs', 'cacheBuildMs', 'cacheLookupMs', 'tracerAdvectionMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
  return `${names.join(',')}\n${rows.map(r => names.map(k => r[k] ?? '').join(',')).join('\n')}\n`;
}

export async function main() {
  const args = parseP3bArgs(process.argv.slice(2));
  if (args.help) { console.log('node research/p3b-run.mjs --suite all|quality|timing|pilot|quick [--out DIR] [--browser-executable PATH]'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3b-${args.suite}-${Date.now()}`)); await fs.mkdir(out, { recursive: true });
  const filename = path.join(out, 'manifest.json');
  try { await fs.access(filename); throw new Error(`Output manifest already exists: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { phase: 'P3b', status: 'running', exploratory: ['pilot', 'quick'].includes(args.suite), args, specification: P3B,
    metadata: hostMetadata(), plannedQuality: qualityCasesP3b(args.suite), plannedTiming: timingCasesP3b(args.suite), results: [], physicsAndBirthLocks: [] };
  const save = () => fs.writeFile(filename, JSON.stringify(manifest, null, 2)); const quality = [], timing = [], traces = new Map();
  let server, launched; await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    const cases = [...manifest.plannedQuality, ...manifest.plannedTiming];
    for (let i = 0; i < cases.length; i++) {
      const d = cases[i], started = Date.now(); console.log(`[${i + 1}/${cases.length}] ${d.id}`);
      const r = d.family === 'quality' ? await runP3bQualityCase(launched.browser, server.url, d, out) : await runP3bTimingCase(launched.browser, server.url, d);
      r.hostElapsedMs = Date.now() - started;
      if (r.status === 'passed') {
        const key = `${d.scenario}-${d.seed}-${d.renderSeed}`, baseline = traces.get(key);
        try { if (baseline) requirePairedTrace(baseline.trace, r.trace); else traces.set(key, { id: d.id, trace: r.trace });
          manifest.physicsAndBirthLocks.push({ candidate: d.id, reference: baseline?.id || d.id, steps: r.trace.length, passed: true });
        } catch (e) { r.status = 'failed'; r.error = e.stack || String(e); manifest.physicsAndBirthLocks.push({ candidate: d.id, passed: false, error: r.error }); }
      }
      const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(r));
      if (d.family === 'quality') quality.push(r); else { timing.push(r); await fs.writeFile(path.join(out, `${d.id}.csv`), timingCsv(r.timings)); }
      manifest.results.push({ id: d.id, status: r.status, family: d.family, rawFile, elapsedMs: r.hostElapsedMs, error: r.error || null });
      console.log(`  ${r.status} ${(r.hostElapsedMs / 1000).toFixed(1)}s${r.error ? ` ${r.error}` : ''}`); await save();
    }
    if (quality.length) manifest.quality = await compareP3b(out, quality);
    manifest.timing = aggregateTiming(timing, P3B.scenarios, P3B.methods, P3B.timing.repeats);
    manifest.selection = selectCache(manifest.quality?.comparisons || [], manifest.timing, P3B.selection, P3B.scenarios, P3B.methods);
    manifest.selection.evidenceComplete = quality.length === 36 && timing.length === 60 && quality.every(r => r.status === 'passed') && timing.every(r => r.status === 'passed') && manifest.quality.comparisons.length === 27 && manifest.quality.failures.length === 0;
    manifest.selection.routeGo &&= manifest.selection.evidenceComplete;
    manifest.status = manifest.results.every(r => r.status === 'passed') && !manifest.quality?.failures.length ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close(); manifest.finalMetadata = hostMetadata();
    try { manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes); }
    catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; if (!manifest.exploratory) manifest.status = 'failed'; }
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3b results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
