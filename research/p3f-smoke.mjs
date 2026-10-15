import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3F, p3fConfig, parseP3fArgs } from './p3f-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes } from './lib/p3-runtime.mjs';
import { traceRow } from './p3b-run.mjs';
import { validateP3fSnapshot } from './p3f-run.mjs';
import { curvatureScore, correctionHash, selectedIdsHash, validateSelectionSummary, summarizeCorrectionSelection } from './lib/p3f-metrics.mjs';

export async function main() {
  const args = parseP3fArgs(process.argv.slice(2)), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3f-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'smoke.json');
  try { await fs.access(filename); throw new Error(`Refusing to overwrite ${filename}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3f', status: 'running', metadata: hostMetadata(), checks: [] }, server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const configs = Object.fromEntries(['DD', 'affine', 'curvature', 'hash'].map(method => [method, p3fConfig({ method, renderSeed: 101 })]));
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  try {
    await check('correction rejects unsupported routes, policies, fractions, salt and partial observers', async () => {
      const rejected = await page.evaluate(config => {
        const r = window.__demo.researchP3, field = config.field, correction = field.correction;
        const fields = [{ ...field, correction: { ...correction, method: 'random' } }, { ...field, correction: { ...correction, fraction: -1 } }, { ...field, correction: { ...correction, fraction: 1.1 } },
          { ...field, correction: { ...correction, salt: -1 } }, { ...field, correction: { ...correction, salt: 1.5 } }, { ...field, correction: { ...correction, extra: true } }, { mode: 'tree', correction }];
        const result = fields.map(field => { try { r.reset(11, { ...config, field }); return false; } catch { return true; } });
        r.reset(11, config); try { r.stepWithInputs(1 / 60, { stride: 97, correctionDetails: true }); result.push(false); } catch { result.push(true); } return result;
      }, configs.curvature); assert.ok(rejected.every(Boolean)); return rejected;
    });
    await check('shared analytic selector reconstructs diagonal scores, hash ranks, stable ties and mixed-partial blind spot', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3; r.reset(11, config); const before = r.snapshot({ detail: true }); const diagnostic = r.correctionSamplerDiagnostics(); return { before, diagnostic, after: r.snapshot({ detail: true }) }; }, configs.curvature);
      assert.deepEqual(d.before, d.after); assert.deepEqual(d.diagnostic.traceBefore, d.diagnostic.traceAfter); assertFiniteTree(d.diagnostic);
      assert.deepEqual(d.diagnostic.cases.map(c => c.id), ['constant', 'linear', 'axis-quadratic', 'mixed-xy']); let maximumHessianError = 0;
      for (const c of d.diagnostic.cases) for (const method of ['curvature', 'hash']) {
        const s = c.selections[method]; assert.ok(s.permutationExact); validateSelectionSummary(s.summary, s.config, c.config);
        const byId = new Map(c.points.map(p => [p.id, { ...p, position: [p.x, p.y, p.z] }]));
        for (const m of s.models) {
          const score = curvatureScore(m, m.memberIds.map(id => byId.get(id)), c.delta, c.buoy);
          assert.deepEqual(score.diagonalHessian, m.diagonalHessian); assert.equal(score.score, m.score); assert.equal(m.hashRank, correctionHash(c.frame, m.memberIds[0], s.config.salt));
          for (let i = 0; i < 9; i++) { const error = Math.abs(m.diagonalHessian[i] - c.expectedDiagonalHessian[i]); maximumHessianError = Math.max(maximumHessianError, error); assert.ok(error < 1e-10); }
        }
        const ranked = [...s.models].sort((a, b) => (method === 'curvature' ? b.score - a.score : a.hashRank - b.hashRank) || a.id - b.id);
        assert.deepEqual(ranked.map(m => m.id), s.rankedGroupIds); assert.equal(s.summary.selectionIDHash, selectedIdsHash(s.selectedMemberIds));
        if (c.id === 'constant' && method === 'curvature') assert.deepEqual(s.summary.selectedGroupIds, [0, 1]);
      }
      assert.ok(d.diagnostic.cases.find(c => c.id === 'mixed-xy').omittedMixedPartial); return { maximumHessianError, diagnostic: d.diagnostic };
    });
    await check('zero correction preserves old affine and full correction exactly reproduces DD particle trajectories', async () => {
      const d = await page.evaluate(configs => {
        const r = window.__demo.researchP3, run = config => { r.reset(11, config); const trace = []; for (let i = 0; i < 15; i++) { r.step(1, 1 / 60); const s = r.snapshot(); trace.push([s.physicalHash, s.tracerHash]); } return { trace, snapshot: r.snapshot({ detail: true }) }; };
        const corrected = fraction => ({ ...configs.curvature, field: { ...configs.curvature.field, correction: { ...configs.curvature.field.correction, fraction } } });
        return { dd: run(configs.DD), affine: run(configs.affine), zero: run(corrected(0)), all: run(corrected(1)) };
      }, configs);
      for (const [a, b] of [[d.dd, d.all], [d.affine, d.zero]]) { assert.deepEqual(a.trace, b.trace); assert.deepEqual(a.snapshot.renderParticles, b.snapshot.renderParticles); assert.deepEqual(a.snapshot.physicsParticles, b.snapshot.physicsParticles); }
      assert.equal(d.zero.snapshot.counters.correctionDirectQueries, 0); assert.equal(d.all.snapshot.counters.affineReconstructions, 0);
      return { frames: 15, zero: d.zero.snapshot.tracerHash, full: d.all.snapshot.tracerHash };
    });
    await check('production observer adds no queries or state changes and exposes actual own-trajectory selection', async () => {
      const evidence = [];
      for (const method of ['curvature', 'hash']) {
        const d = await page.evaluate(config => {
          const r = window.__demo.researchP3; r.reset(11, config); r.step(14, 1 / 60); const captured = r.stepWithInputs(1 / 60, { stride: 1, correctionDetails: true }), observed = r.snapshot({ detail: true });
          r.reset(11, config); r.step(15, 1 / 60); return { captured, observed, plain: r.snapshot({ detail: true }) };
        }, configs[method]);
        assert.deepEqual(d.observed, d.plain); validateP3fSnapshot(d.observed); assert.equal(d.captured.inputs.length, 720); assert.equal(d.captured.inputs.filter(p => p.newborn).length, 48);
        const record = { frame: 15, time: .25, fieldTime: d.captured.fieldTime, inputPhase: d.captured.inputPhase, params: d.observed.params, inputs: d.captured.inputs, selection: d.captured.correctionSelection };
        const summary = summarizeCorrectionSelection(record, d.observed.renderParticles, P3F); assert.equal(summary.selectedGroupCount, 5); assert.equal(summary.correctionQueries, 80);
        await fs.writeFile(path.join(out, `${method}-production-selection.json`), JSON.stringify(record)); evidence.push({ method, summary, fullStateEqual: true, counters: d.observed.counters });
      }
      return evidence;
    });
    await check('corrected reset replay and camera motion preserve complete physics, sampling RNG and tracer state', async () => {
      const d = await page.evaluate(({ config, dd }) => {
        const r = window.__demo.researchP3, run = moving => { r.reset(11, config); for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); } return r.snapshot({ detail: true }); };
        const a = run(false), b = run(false), moving = run(true); r.reset(11, dd); r.step(15, 1 / 60); return { a, b, moving, dd: r.snapshot({ detail: true }) };
      }, { config: configs.curvature, dd: configs.DD });
      for (const s of [d.b, d.moving]) { assert.equal(s.physicalHash, d.a.physicalHash); assert.equal(s.tracerHash, d.a.tracerHash); assert.deepEqual(s.renderParticles, d.a.renderParticles); }
      assert.deepEqual(d.a.physicsParticles, d.dd.physicsParticles); assert.deepEqual(traceRow(d.a), traceRow(d.dd)); return { physicalHash: d.a.physicalHash, tracerHash: d.a.tracerHash, particles: d.a.render.count };
    });
    await check('completed frame includes scoring and direct-query cost without dense snapshots or observers', async () => {
      const d = await page.evaluate(config => {
        const demo = window.__demo, r = demo.researchP3; r.reset(11, config); r.step(15, 1 / 60);
        const finish = demo.gl.finish.bind(demo.gl), snapshot = r.snapshot, diagnostic = r.correctionDiagnostics, observer = r.stepWithInputs; let finishCalls = 0, snapshotCalls = 0;
        demo.gl.finish = () => { finishCalls++; finish(); }; r.snapshot = (...args) => { snapshotCalls++; return snapshot(...args); };
        r.correctionDiagnostics = r.stepWithInputs = () => { throw new Error('Observer/diagnostic called during timed frame'); };
        try { const frame = r.frame(1 / 60, { sync: 'finish' }); return { frame, finishCalls, snapshotCalls, after: snapshot() }; }
        finally { demo.gl.finish = finish; r.snapshot = snapshot; r.correctionDiagnostics = diagnostic; r.stepWithInputs = observer; }
      }, configs.curvature);
      assertFiniteTree(d); assert.equal(d.snapshotCalls, 0); assert.ok(d.finishCalls >= 2); validateP3fSnapshot(d.after); assert.deepEqual(d.frame.trace, traceRow(d.after)); assert.deepEqual(d.frame.correctionSummary, d.after.field.lastCorrection);
      const t = d.frame.timing; assert.ok(Number.isFinite(t.correctionSelectionMs) && Number.isFinite(t.correctionQueryMs));
      const sum = t.tracerSetupMs + t.affineGroupingMs + t.affineModelBuildMs + t.correctionSelectionMs + t.correctionQueryMs + t.affineLookupMs + t.tracerAdvectionMs;
      assert.ok(sum <= t.tracerMs + .01); assert.ok(t.tracerMs <= t.totalMs + .01); assert.ok(String(t.synchronization).includes('finish')); return d;
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); } catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  console.log(`P3f smoke: ${filename}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
