import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P3, qualityCases, timingCases, parseP3Args, p3Config } from './p3-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, requireSamePhysics, checkSourceHashes, saveImage, timingCsv } from './lib/p3-runtime.mjs';
import { decodeFloat32, imageError, referenceMasks, poolErrors, referenceGate, distribution } from './lib/p3-metrics.mjs';

export function validateP3Snapshot(s, requireUnblocked = true) {
  assertFiniteTree(s);
  if (!s.physicalHash || !s.tracerHash || s.precision !== 'rgba32f') throw new Error('Missing hashes or required RGBA32F precision');
  if (s.physics.count > s.config.nSim || s.render.count > (s.config.mode === 'passive' ? s.config.nRender : s.config.nSim)) throw new Error('Particle capacity exceeded');
  const c = s.counters;
  for (const key of ['physicsFullSteps', 'physicsCapacityLimitedSteps', 'physicsSuppressedEmissionCredit', 'tracerCapacityDropped']) {
    if (!Number.isFinite(c[key])) throw new Error(`Missing source-capacity counter ${key}`);
    if (requireUnblocked && c[key] !== 0) throw new Error(`Primary source was capacity limited: ${key}=${c[key]}`);
  }
  if (Math.abs(c.physicsInjectedOpticalWeight - c.physicsEmitted) > 1e-8) throw new Error('Physical optical injection ledger mismatch');
  if (c.physicsEmitted - c.physicsRetired !== s.physics.count) throw new Error('Physical population ledger mismatch');
  if (requireUnblocked && Math.abs(c.physicsNominalEmissionCredit - c.physicsEmitted - s.physics.pendingEmissionCredit) > 1e-8 * Math.max(1, c.physicsNominalEmissionCredit)) throw new Error('Physical emission credit ledger mismatch');
  if (s.config.mode === 'passive') {
    const expected = c.tracerEmitted * s.config.nSim / s.config.nRender;
    if (Math.abs(c.tracerInjectedOpticalWeight - expected) > 1e-8 * Math.max(1, expected)) throw new Error('Tracer optical injection ledger mismatch');
    if (c.tracerEmissionAttempts !== c.tracerEmitted + c.tracerCapacityDropped) throw new Error('Tracer admission ledger mismatch');
    if (!s.render.overridden && c.tracerEmitted - c.tracerRetired !== s.render.count) throw new Error('Tracer population ledger mismatch');
    if (Math.abs(c.tracerNominalEmissionCredit - c.tracerEmissionAttempts - s.render.pendingEmissionCredit) > 1e-8 * Math.max(1, c.tracerNominalEmissionCredit)) throw new Error('Tracer emission credit ledger mismatch');
  }
  return s;
}

export async function runP3QualityCase(browser, baseUrl, definition, out, onProgress) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, snapshots: [], physicalHashes: [], captures: [], browserErrors: errors };
  try {
    const initial = await page.evaluate(({ seed, config }) => window.__demo.researchP3.reset(seed, config), { seed: definition.seed, config: p3Config(definition) });
    validateP3Snapshot(initial); result.snapshots.push(initial); result.physicalHashes.push(initial.physicalHash);
    for (let frame = 1; frame <= definition.frames; frame++) {
      const state = await page.evaluate(dt => window.__demo.researchP3.step(1, dt), P3.dt);
      if (!state.physicalHash) throw new Error('Step omitted physical hash');
      result.physicalHashes.push(state.physicalHash);
      if (frame % 15 === 0 || frame === definition.frames) {
        result.snapshots.push(validateP3Snapshot(await page.evaluate(() => window.__demo.researchP3.snapshot())));
        onProgress?.(frame, definition.frames);
      }
      if (!definition.captures.includes(frame)) continue;
      for (const view of P3.views) {
        const capture = await page.evaluate(yaw => {
          const r = window.__demo.researchP3, before = r.snapshot(); r.camera(yaw); r.render({ sync: 'finish' });
          // Capture in the same JS task: WebGL's non-preserved default framebuffer
          // may already have been cleared by the next Playwright screenshot call.
          const previewDataUrl = document.querySelector('canvas').toDataURL('image/png');
          const gl = window.__demo.gl, display = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
          gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, display);
          let previewMaximum = 0; for (let i = 0; i < display.length; i++) if (i % 4 !== 3) previewMaximum = Math.max(previewMaximum, display[i]);
          if (previewMaximum === 0) throw new Error('Composite canvas has no RGB signal');
          const image = r.readHDR(), after = r.snapshot();
          if (before.physicalHash !== after.physicalHash || before.tracerHash !== after.tracerHash) throw new Error('Camera/render/readback advanced state');
          return { image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: after.precision }, snapshot: after, previewDataUrl, previewMaximum };
        }, view.yaw);
        const stem = `${definition.id}-f${frame}-${view.id}`;
        const image = await saveImage(out, stem, capture.image);
        // Canvas screenshots are preview evidence only; linear RGBA is authoritative.
        const preview = `images/${stem}.png`;
        if (!capture.previewDataUrl.startsWith('data:image/png;base64,')) throw new Error('Canvas PNG capture failed');
        await fs.writeFile(path.join(out, preview), Buffer.from(capture.previewDataUrl.split(',')[1], 'base64'));
        result.captures.push({ frame, time: frame * P3.dt, view, image, preview, previewMaximum: capture.previewMaximum, snapshot: capture.snapshot });
      }
    }
    if (errors.length) throw new Error(`Browser errors: ${errors.join('\n')}`);
    result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

export async function runP3TimingCase(browser, baseUrl, definition) {
  const { page, errors, graphics } = await openP3Page(browser, baseUrl);
  const result = { definition, status: 'running', graphics, timings: [], physicalHashes: [], browserErrors: errors,
    timingInterpretation: 'Serialized GPU-completed wall latency. Snapshot/hash serialization and image readback excluded from timed interval. Independent new page and reset per repetition.' };
  try {
    const data = await page.evaluate(({ seed, config, spec }) => {
      const r = window.__demo.researchP3; r.reset(seed, config); r.camera(0);
      for (let i = 0; i < spec.timing.warmupFrames; i++) r.frame(spec.dt, { sync: 'none' });
      window.__demo.gl.finish(); const initial = r.reset(seed, config); r.camera(0);
      const timings = [], physicalHashes = [initial.physicalHash];
      for (let frame = 1; frame <= spec.timing.lastFrame; frame++) {
        const sampled = frame >= spec.timing.firstFrame && frame % spec.timing.sampleEvery === 0;
        const state = r.frame(spec.dt, { sync: sampled ? 'finish' : 'none' });
        physicalHashes.push(state.physicalHash);
        if (sampled) timings.push({ frame, time: frame * spec.dt, ...state.timing, counts: state.counts });
      }
      window.__demo.gl.finish(); return { initial, final: r.snapshot(), timings, physicalHashes };
    }, { seed: definition.seed, config: p3Config(definition), spec: P3 });
    validateP3Snapshot(data.initial); validateP3Snapshot(data.final); Object.assign(result, data);
    const fields = ['simulationMs', 'tracerMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs'];
    result.distributions = Object.fromEntries(fields.map(k => [k, distribution(data.timings.map(t => t[k]))]));
    if (data.timings.some(t => !String(t.synchronization).includes('finish'))) throw new Error('Missing GPU-completed synchronization label');
    if (errors.length) throw new Error(`Browser errors: ${errors.join('\n')}`);
    result.status = 'passed';
  } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); }
  finally { await page.close(); }
  return result;
}

async function readImage(out, record) { return decodeFloat32(await fs.readFile(path.join(out, record.file)), record); }
export async function compareP3Quality(out, results) {
  const passed = results.filter(r => r.status === 'passed'), comparisons = [], gates = [], masks = [];
  const planned = results.map(r => r.definition);
  const formal = planned.length === 48 && planned.every(d => !d.exploratory);
  for (const seed of [...new Set(planned.map(r => r.seed))]) {
    const plannedRefs = planned.filter(d => d.seed === seed && d.family === 'reference');
    const refs = passed.filter(r => r.definition.seed === seed && r.definition.family === 'reference');
    const complete = refs.length === plannedRefs.length && refs.every(r => r.captures.length === r.definition.captures.length * P3.views.length);
    if (!complete || !refs.length) {
      for (const ref of plannedRefs) gates.push({ seed, repeat: ref.repeat, passed: false, reason: 'Reference ensemble incomplete; fixed ROI and convergence gate unavailable' });
      continue;
    }
    const maskByKey = new Map();
    for (const c of refs[0].captures) {
      const key = `${c.frame}-${c.view.id}`;
      const records = refs.map(r => r.captures.find(x => x.frame === c.frame && x.view.id === c.view.id)?.image);
      if (records.some(x => !x)) throw new Error('Reference image missing from ROI ensemble');
      const roi = referenceMasks(await Promise.all(records.map(r => readImage(out, r))), P3.image);
      const record = { seed, frame: c.frame, view: c.view, referenceCount: refs.length, referenceFiles: records.map(r => r.file),
        width: roi.width, height: roi.height, orientation: roi.orientation, thresholds: P3.image, masks: {} };
      for (const name of ['foregroundMask', 'holeMask']) {
        const bytes = Buffer.from(roi[name]); const file = `images/roi-s${seed}-f${c.frame}-${c.view.id}-${name}.u8`;
        await fs.writeFile(path.join(out, file), bytes);
        record.masks[name] = { file, sha256: createHash('sha256').update(bytes).digest('hex'),
          pixels: bytes.reduce((a, b) => a + b, 0), type: 'uint8', layout: 'one byte per pixel, same orientation as RGBA' };
      }
      masks.push(record); maskByKey.set(key, roi);
    }
    for (const ref of refs) {
      const matching = passed.filter(r => r.definition.seed === seed && (r.definition.repeat === ref.definition.repeat || r.definition.family === 'shared'));
      const repeatComparisons = [];
      for (const candidate of matching) {
        if (candidate === ref) continue;
        const errors = [];
        for (const c of candidate.captures) {
          const r = ref.captures.find(x => x.frame === c.frame && x.view.id === c.view.id);
          if (!r) throw new Error('Capture correspondence missing');
          const roi = maskByKey.get(`${c.frame}-${c.view.id}`);
          const e = imageError(await readImage(out, c.image), await readImage(out, r.image), { ...P3.image, ...roi });
          errors.push({ frame: c.frame, view: c.view, ...e });
        }
        const comparison = { candidate: candidate.definition.id, reference: ref.definition.id, seed, repeat: ref.definition.repeat,
          family: candidate.definition.family, nRender: candidate.definition.nRender, images: errors, pooled: poolErrors(errors) };
        comparisons.push(comparison); repeatComparisons.push(comparison);
      }
      const low = repeatComparisons.find(c => c.family === 'candidate' && c.nRender === P3.budgets[0]);
      const double = repeatComparisons.find(c => c.family === 'double-reference');
      if (low && double) gates.push({ seed, repeat: ref.definition.repeat, low: low.candidate, reference: ref.definition.id,
        doubleReference: double.candidate, ...referenceGate(low.pooled, double.pooled, P3.image.convergenceRatio) });
      else gates.push({ seed, repeat: ref.definition.repeat, passed: false, reason: 'Low/reference/double-reference measurement incomplete' });
    }
  }
  return { comparisons, masks, referenceGates: gates,
    referenceAccepted: formal && gates.length === 9 && gates.every(g => g.passed),
    exploratoryScreenPassed: !formal && gates.length > 0 && gates.every(g => g.passed),
    interpretation: 'Execution and physics-lock success are separate from reference acceptance; no quality winner is declared when any preregistered convergence gate fails.' };
}

export async function main() {
  const args = parseP3Args(process.argv.slice(2));
  if (args.help) { console.log('node research/p3-run.mjs --suite all|quality|timing|pilot|quick [--out DIR] [--browser-executable PATH]\nP3 parameters are frozen in p3-design.mjs; pilot/quick are explicitly exploratory.'); return; }
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3-${args.suite}-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const manifestPath = path.join(out, 'manifest.json');
  try { await fs.access(manifestPath); throw new Error(`Refusing to overwrite manifest: ${out}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const manifest = { phase: 'P3a', status: 'running', exploratory: ['quick', 'pilot'].includes(args.suite), args, specification: P3,
    metadata: hostMetadata(), plannedQuality: qualityCases(args.suite), plannedTiming: timingCases(args.suite), results: [], physicsLocks: [] };
  const save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  let server, launched; const quality = [], trajectories = new Map(); await save();
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions };
    const cases = [...manifest.plannedQuality, ...manifest.plannedTiming];
    for (let index = 0; index < cases.length; index++) {
      const d = cases[index]; console.log(`[${index + 1}/${cases.length}] ${d.id}`); const started = Date.now();
      let lastProgress = Date.now();
      const result = d.family === 'timing' ? await runP3TimingCase(launched.browser, server.url, d) :
        await runP3QualityCase(launched.browser, server.url, d, out, (f, n) => { if (Date.now() - lastProgress > 10000) { console.log(`  ${f}/${n} frames`); lastProgress = Date.now(); } });
      result.hostElapsedMs = Date.now() - started;
      if (result.status === 'passed') {
        try {
          const reference = trajectories.get(d.seed);
          if (reference) requireSamePhysics(reference.hashes, result.physicalHashes, d.id);
          else trajectories.set(d.seed, { id: d.id, hashes: result.physicalHashes });
          manifest.physicsLocks.push({ candidate: d.id, reference: reference?.id || d.id, steps: result.physicalHashes.length, passed: true });
        } catch (e) { result.status = 'failed'; result.error = e.stack || String(e); manifest.physicsLocks.push({ candidate: d.id, passed: false, error: result.error }); }
      }
      const rawFile = `${d.id}.json`; await fs.writeFile(path.join(out, rawFile), JSON.stringify(result));
      if (d.family === 'timing') await fs.writeFile(path.join(out, `${d.id}.csv`), timingCsv(result.timings)); else quality.push(result);
      manifest.results.push({ id: d.id, family: d.family, status: result.status, rawFile, elapsedMs: result.hostElapsedMs, error: result.error || null });
      console.log(`  ${result.status} ${(result.hostElapsedMs / 1000).toFixed(1)}s${result.error ? ` ${result.error}` : ''}`); await save();
    }
    if (quality.length) manifest.quality = await compareP3Quality(out, quality);
    manifest.status = manifest.results.every(r => r.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { manifest.status = 'failed'; manifest.error = e.stack || String(e); console.error(manifest.error); }
  finally {
    await launched?.browser.close(); await server?.close();
    manifest.finalMetadata = hostMetadata();
    try { manifest.sourceFreeze = checkSourceHashes(manifest.metadata.sourceHashes, manifest.finalMetadata.sourceHashes); }
    catch (e) { manifest.sourceFreeze = { matched: false, error: e.message }; if (!manifest.exploratory) manifest.status = 'failed'; }
    manifest.completed = new Date().toISOString(); await save();
  }
  console.log(`P3 results: ${out}`); if (manifest.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
