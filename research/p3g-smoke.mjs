import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3G, p3gConfig, parseP3gArgs } from './p3g-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes } from './lib/p3-runtime.mjs';
import { traceRow } from './p3b-run.mjs';
import { validateP3gSnapshot } from './p3g-run.mjs';
import { cacheHash, summarizeMemoryEvents, summarizeMemorySelection } from './lib/p3g-metrics.mjs';

export async function main() {
  const args = parseP3gArgs(process.argv.slice(2)), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3g-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'smoke.json');
  try { await fs.access(filename); throw new Error(`Refusing to overwrite ${filename}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3g', status: 'running', metadata: hostMetadata(), checks: [] }, server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const configs = Object.fromEntries(['DD', 'curvature', 'memory'].map(method => [method, p3gConfig({ method, renderSeed: 101 })]));
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  try {
    await check('memory accepts only TTL1 curvature correction and reset clears every cached value', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3, field = config.field, c = field.correction;
        const variants = [{ ...c, memory: { ttl: 0 } }, { ...c, memory: { ttl: 2 } }, { ...c, memory: { ttl: 1, extra: true } }, { ...c, method: 'hash' }];
        const rejected = variants.map(correction => { try { r.reset(11, { ...config, field: { ...field, correction } }); return false; } catch { return true; } });
        r.reset(11, config); r.step(3, 1 / 60); const populated = r.snapshot({ detail: true }); r.reset(11, config); return { rejected, populated, reset: r.snapshot({ detail: true }) };
      }, configs.memory); assert.ok(d.rejected.every(Boolean)); assert.ok(d.populated.memoryEntries.length > 0); assert.deepEqual(d.reset.memoryEntries, []); assert.equal(d.reset.memoryStateHash, cacheHash([])); assert.equal(d.reset.counters.memorySavedMembers, 0); return { rejected: d.rejected, populated: d.populated.memoryEntries.length, resetHash: d.reset.memoryStateHash };
    });
    await check('production residual arithmetic subtracts the unclipped origin and clips after reuse', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3; r.reset(11, config); const before = r.snapshot({ detail: true }), diagnostic = r.memorySamplerDiagnostics(); return { before, diagnostic, after: r.snapshot({ detail: true }) }; }, configs.memory);
      assert.deepEqual(d.before, d.after); assert.deepEqual(d.diagnostic.traceBefore, d.diagnostic.traceAfter); assertFiniteTree(d.diagnostic);
      assert.deepEqual(d.diagnostic.cases.map(c => c.id), ['unclipped-origin', 'upper-final-clip', 'lower-final-clip']);
      for (const c of d.diagnostic.cases) {
        const residual = [c.direct.ux - c.savedBase.ux, c.direct.uy - c.savedBase.uy, c.direct.uz - c.savedBase.uz, c.direct.Tb - c.savedBase.TbRaw]; assert.deepEqual(c.residual, residual);
        assert.equal(c.result.TbRaw, c.currentBase.TbRaw + residual[3]); assert.equal(c.result.Tb, Math.max(0, Math.min(1.6, c.result.TbRaw)));
      }
      assert.ok(Math.abs(d.diagnostic.cases[0].result.Tb - 1.1) < 1e-12); assert.equal(d.diagnostic.cases[1].result.Tb, 1.6); assert.equal(d.diagnostic.cases[2].result.Tb, 0); return d.diagnostic;
    });
    await check('zero correction equals old affine and full correction equals DD including native direct temperature', async () => {
      const d = await page.evaluate(configs => {
        const r = window.__demo.researchP3, affine = structuredClone(configs.memory); delete affine.field.correction;
        const corrected = fraction => ({ ...configs.memory, field: { ...configs.memory.field, correction: { ...configs.memory.field.correction, fraction } } });
        const run = config => { r.reset(11, config); const trace = []; for (let frame = 1; frame <= 15; frame++) { r.step(1, 1 / 60); const s = r.snapshot(); trace.push([s.physicalHash, s.tracerHash]); } return { trace, snapshot: r.snapshot({ detail: true }) }; };
        const dd = run(configs.DD), oldAffine = run(affine), zero = run(corrected(0)), all = run(corrected(1));
        r.reset(11, corrected(1)); const captured = r.stepWithInputs(1 / 60, { stride: 1, memoryDetails: true, correctionDetails: true }); return { dd, oldAffine, zero, all, native: captured.memoryEvents.created.map(p => p.directRaw.Tb), first: r.snapshot({ detail: true }), captured };
      }, configs);
      for (const [a, b] of [[d.dd, d.all], [d.oldAffine, d.zero]]) { assert.deepEqual(a.trace, b.trace); assert.deepEqual(a.snapshot.renderParticles, b.snapshot.renderParticles); assert.deepEqual(a.snapshot.physicsParticles, b.snapshot.physicsParticles); }
      assert.equal(d.zero.snapshot.counters.memorySavedMembers, 0); assert.equal(d.all.snapshot.counters.memoryReusedMembers, 0);
      return { frames: 15, nativeDirectMaximumTb: Math.max(...d.native), nativeFloat32Of1point6: Math.fround(1.6), observedNativeAbove1point6: d.native.some(Tb => Tb > 1.6),
        boundaryCoverage: 'The actual fixture does not require a direct Tb above 1.6. That numeric boundary is covered by the synthetic unit fixture; this browser check establishes full-correction equivalence with DD over all 15 steps.',
        fullHash: d.all.snapshot.tracerHash, zeroHash: d.zero.snapshot.tracerHash };
    });
    await check('all-frame observer preserves state while exposing complete TTL1 creation reuse overlap and expiry chain', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3; r.reset(11, config); const frames = [];
        for (let frame = 1; frame <= 15; frame++) { const captured = r.stepWithInputs(1 / 60, { stride: 1, memoryDetails: true, correctionDetails: frame === 15 }); frames.push({ captured, snapshot: r.snapshot({ detail: true }) }); }
        const observed = r.snapshot({ detail: true }); r.reset(11, config); r.step(15, 1 / 60); return { frames, observed, plain: r.snapshot({ detail: true }) };
      }, configs.memory); assert.deepEqual(d.observed, d.plain); let previous = [], used = 0, overlap = 0; const records = [];
      for (const { captured, snapshot } of d.frames) {
        validateP3gSnapshot(snapshot); const record = { frame: snapshot.frame, time: snapshot.time, fieldTime: captured.fieldTime, params: snapshot.params, events: captured.memoryEvents };
        const summary = summarizeMemoryEvents(record, previous, P3G, snapshot.renderParticles); previous = captured.memoryEvents.cacheAfter;
        assert.equal(summary.afterHash, snapshot.memoryStateHash); assert.deepEqual(previous, snapshot.memoryEntries); assert.deepEqual(record.events.summary, snapshot.field.lastMemory); used += summary.usedCount; overlap += summary.overlappingCount;
        assert.equal(record.events.summary.savedIDHash, snapshot.field.lastCorrection.selectionIDHash); records.push(record);
        if (captured.correctionSelection) summarizeMemorySelection({ frame: snapshot.frame, fieldTime: captured.fieldTime, params: snapshot.params, inputs: captured.inputs, selection: captured.correctionSelection }, snapshot.renderParticles, P3G, record.events);
      }
      assert.ok(used > 0 && overlap > 0); await fs.writeFile(path.join(out, 'memory-chain.json'), JSON.stringify(records)); return { frames: 15, used, overlap, finalHash: d.observed.memoryStateHash, fullObserverStateUnchanged: true, file: 'memory-chain.json' };
    });
    await check('memory reset replay and camera changes preserve cache, physical RNG and full particles', async () => {
      const d = await page.evaluate(({ config, dd }) => {
        const r = window.__demo.researchP3, run = moving => { r.reset(11, config); for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); } return r.snapshot({ detail: true }); };
        const a = run(false), b = run(false), moving = run(true); r.reset(11, dd); r.step(15, 1 / 60); return { a, b, moving, dd: r.snapshot({ detail: true }) };
      }, { config: configs.memory, dd: configs.DD });
      for (const s of [d.b, d.moving]) { assert.equal(s.tracerHash, d.a.tracerHash); assert.equal(s.memoryStateHash, d.a.memoryStateHash); assert.deepEqual(s.memoryEntries, d.a.memoryEntries); assert.deepEqual(s.renderParticles, d.a.renderParticles); }
      assert.deepEqual(d.a.physicsParticles, d.dd.physicsParticles); assert.deepEqual(traceRow(d.a), traceRow(d.dd)); return { physicalHash: d.a.physicalHash, tracerHash: d.a.tracerHash, memoryStateHash: d.a.memoryStateHash };
    });
    await check('completed frame includes cache maintenance and invokes neither dense snapshots nor observers', async () => {
      const d = await page.evaluate(config => {
        const demo = window.__demo, r = demo.researchP3; r.reset(11, config); r.step(15, 1 / 60);
        const finish = demo.gl.finish.bind(demo.gl), snapshot = r.snapshot, observer = r.stepWithInputs, diagnostic = r.memorySamplerDiagnostics; let finishCalls = 0, snapshotCalls = 0;
        demo.gl.finish = () => { finishCalls++; finish(); }; r.snapshot = (...args) => { snapshotCalls++; return snapshot(...args); }; r.stepWithInputs = r.memorySamplerDiagnostics = () => { throw new Error('Observer called in timed frame'); };
        try { const frame = r.frame(1 / 60, { sync: 'finish' }); return { frame, finishCalls, snapshotCalls, after: snapshot() }; }
        finally { demo.gl.finish = finish; r.snapshot = snapshot; r.stepWithInputs = observer; r.memorySamplerDiagnostics = diagnostic; }
      }, configs.memory);
      assertFiniteTree(d); assert.equal(d.snapshotCalls, 0); assert.ok(d.finishCalls >= 2); validateP3gSnapshot(d.after); assert.deepEqual(d.frame.trace, traceRow(d.after)); assert.deepEqual(d.frame.memorySummary, d.after.field.lastMemory);
      const t = d.frame.timing; for (const k of ['correctionSelectionMs', 'correctionQueryMs', 'memoryModelMs', 'memoryFinalizeMs']) assert.ok(Number.isFinite(t[k]) && t[k] >= 0);
      const sum = t.tracerSetupMs + t.affineGroupingMs + t.affineModelBuildMs + t.correctionSelectionMs + t.correctionQueryMs + t.memoryModelMs + t.affineLookupMs + t.tracerAdvectionMs + t.memoryFinalizeMs;
      assert.ok(sum <= t.tracerMs + .01); assert.ok(t.tracerMs <= t.totalMs + .01); assert.ok(String(t.synchronization).includes('finish')); return d;
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); } catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  console.log(`P3g smoke: ${filename}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
