import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3E, p3eConfig, parseP3eArgs } from './p3e-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes } from './lib/p3-runtime.mjs';
import { traceRow } from './p3b-run.mjs';
import { validateP3eSnapshot } from './p3e-run.mjs';
import { summarizeAffineDiagnostic, pathsWithOpticalWeights } from './lib/p3e-metrics.mjs';

export async function main() {
  const args = parseP3eArgs(process.argv.slice(2)), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3e-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'smoke.json');
  try { await fs.access(filename); throw new Error(`Refusing to overwrite ${filename}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3e', status: 'running', metadata: hostMetadata(), checks: [] }, server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const configs = { DD: p3eConfig({ method: 'DD' }), affine: p3eConfig({ method: 'affine' }) };
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  try {
    await check('affine configuration rejects invalid budgets, deltas and unsupported field combinations', async () => {
      const rejected = await page.evaluate(config => {
        const r = window.__demo.researchP3, field = config.field;
        const fields = [{ ...field, affine: { ...field.affine, maxGroups: 0 } }, { ...field, affine: { ...field.affine, maxGroups: 1.5 } },
          { ...field, affine: { ...field.affine, targetGroupSize: 0 } }, { ...field, affine: { ...field.affine, deltaScale: 0 } },
          { ...field, components: 'velocity' }, { ...field, evaluation: 'specialized' }, { ...field, cellSize: .035 }];
        return fields.map(field => { try { r.reset(11, { ...config, field }); return false; } catch { return true; } });
      }, configs.affine);
      assert.ok(rejected.every(Boolean)); return rejected;
    });
    await check('analytic constant and linear fields, stable tie grouping, empty input, clipping and force order', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3; r.reset(11, config); const before = r.snapshot({ detail: true }); return { before, diagnostic: r.affineSamplerDiagnostics(), after: r.snapshot({ detail: true }) }; }, configs.affine);
      assert.deepEqual(d.before, d.after); assertFiniteTree(d.diagnostic); assert.deepEqual(d.diagnostic.traceBefore, d.diagnostic.traceAfter);
      assert.deepEqual(d.diagnostic.cases.map(c => c.id), ['constant', 'linear', 'clipping']);
      for (const c of d.diagnostic.cases) {
        assert.equal(c.queryCount, 7 * c.groupCount); assert.equal(c.counters.affineReconstructions, c.inputCount);
        assert.deepEqual(c.models.map(m => m.memberIds.length).sort((a, b) => a - b), [3, 3, 4]);
        assert.ok(c.permutation.modelsExact && c.permutation.groupByIdEqual);
        for (const p of c.points) {
          for (const key of ['ux', 'uy', 'uz']) assert.ok(Math.abs(p.raw[key] - p.expectedRaw[key]) < 1e-12);
          assert.ok(Math.abs(p.raw.Tb - Math.max(0, Math.min(1.6, p.expectedRaw.Tb))) < 1e-12);
          assert.equal('thermalWeight' in p.raw, false); for (let a = 0; a < 3; a++) assert.ok(Math.abs(p.velocity[a] - p.expectedVelocity[a]) < 1e-12);
        }
      }
      const clip = d.diagnostic.cases.find(c => c.id === 'clipping'); assert.ok(clip.counters.affineTbClippedLow > 0 && clip.counters.affineTbClippedHigh > 0);
      assert.deepEqual(d.diagnostic.edgeCases.map(c => c.id), ['singleton', 'equal-axis-extent-tie']);
      for (const c of d.diagnostic.edgeCases) { assert.deepEqual(c.memberIds, c.expectedMembers); assert.equal(c.queryCount, 7 * c.memberIds.length); }
      assert.equal(d.diagnostic.empty.groupCount, 0); assert.equal(d.diagnostic.empty.queryCount, 0); return d.diagnostic;
    });
    await check('DD all-point diagnostics preserve full state and capture every actual preadvection input', async () => {
      const d = await page.evaluate(({ config, affine }) => {
        const r = window.__demo.researchP3; r.reset(11, config); r.step(14, 1 / 60); const prior = r.snapshot({ detail: true });
        const captured = r.stepWithInputs(1 / 60, { stride: 1 }), before = r.snapshot({ detail: true });
        const diagnostic = r.affineDiagnostics(captured.inputs, affine), after = r.snapshot({ detail: true });
        r.reset(11, config); r.step(15, 1 / 60); return { prior, captured, before, diagnostic, after, plain: r.snapshot({ detail: true }) };
      }, { config: configs.DD, affine: P3E.affine });
      assert.deepEqual(d.before, d.after); assert.deepEqual(d.after, d.plain); const old = new Map(d.prior.renderParticles.map(p => [p.id, p])), current = new Map(d.after.renderParticles.map(p => [p.id, p]));
      assert.equal(d.captured.inputs.length, 720); assert.equal(d.captured.inputs.filter(p => p.newborn).length, 48);
      for (const p of d.captured.inputs) { const prev = old.get(p.id); if (prev) { assert.deepEqual(p.position, [prev.x, prev.y, prev.z]); assert.equal(p.age, prev.life); } else assert.equal(p.age, 0); }
      for (const p of d.diagnostic.points) { const actual = current.get(p.id); assert.deepEqual(p.direct.velocity, [actual.vx, actual.vy, actual.vz]); }
      const record = { frame: 15, time: .25, inputPhase: d.captured.inputPhase, fieldTime: d.captured.fieldTime, inputs: d.captured.inputs, diagnostic: d.diagnostic };
      const summary = summarizeAffineDiagnostic(record, P3E); assert.equal(summary.groupCount, 45); assert.equal(summary.modelQueries, 315);
      await fs.writeFile(path.join(out, 'dd-diagnostic.json'), JSON.stringify(record)); return { fullStateUnchanged: true, diagnosticFile: 'dd-diagnostic.json', summary };
    });
    await check('production affine uses its own input grouping and exactly reproduces stored same-input predictions', async () => {
      const d = await page.evaluate(({ config, dd, affine }) => {
        const r = window.__demo.researchP3; r.reset(11, config); r.step(14, 1 / 60); const captured = r.stepWithInputs(1 / 60, { stride: 1 });
        const before = r.snapshot({ detail: true }), diagnostic = r.affineDiagnostics(captured.inputs, affine), after = r.snapshot({ detail: true });
        r.reset(11, dd); r.step(15, 1 / 60); return { captured, before, after, diagnostic, direct: r.snapshot({ detail: true }) };
      }, { config: configs.affine, dd: configs.DD, affine: P3E.affine });
      assert.deepEqual(d.before, d.after); validateP3eSnapshot(d.after); assert.deepEqual(d.after.physicsParticles, d.direct.physicsParticles); assert.deepEqual(traceRow(d.after), traceRow(d.direct));
      const alive = new Map(d.after.renderParticles.map(p => [p.id, p])); let matched = 0;
      for (const p of d.diagnostic.points) { const actual = alive.get(p.id); if (!actual) continue; matched++; assert.deepEqual(p.prediction.velocity, [actual.vx, actual.vy, actual.vz]);
        assert.equal(actual.x, p.position[0] + P3E.dt * actual.vx); assert.equal(actual.y, p.position[1] + P3E.dt * actual.vy); }
      assert.ok(matched > 0); const paths = pathsWithOpticalWeights(d.after.renderParticles, d.direct.renderParticles, P3E); assert.deepEqual(paths.visualStateMismatchIds, []);
      const summary = summarizeAffineDiagnostic({ frame: 15, fieldTime: d.captured.fieldTime, inputs: d.captured.inputs, diagnostic: d.diagnostic }, P3E);
      return { matched, field: d.after.field, counters: d.after.counters, diagnosticSummary: summary, paths };
    });
    await check('affine reset replay and camera motion leave full particle states deterministic', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3, run = moving => { r.reset(11, config);
        for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); } return r.snapshot({ detail: true }); }; return { a: run(false), b: run(false), moving: run(true) }; }, configs.affine);
      for (const s of [d.b, d.moving]) { assert.equal(s.physicalHash, d.a.physicalHash); assert.equal(s.tracerHash, d.a.tracerHash); assert.deepEqual(s.physicsParticles, d.a.physicsParticles); assert.deepEqual(s.renderParticles, d.a.renderParticles); }
      return { physicalHash: d.a.physicalHash, tracerHash: d.a.tracerHash, comparedParticles: d.a.render.count };
    });
    await check('completed GPU frame accounts for affine work and calls no diagnostic or dense snapshot', async () => {
      const d = await page.evaluate(config => {
        const d = window.__demo, r = d.researchP3; r.reset(11, config); r.step(15, 1 / 60);
        const finish = d.gl.finish.bind(d.gl), snapshot = r.snapshot, diag = r.affineDiagnostics, sampler = r.affineSamplerDiagnostics; let finishCalls = 0, snapshotCalls = 0;
        d.gl.finish = () => { finishCalls++; finish(); }; r.snapshot = (...a) => { snapshotCalls++; return snapshot(...a); };
        r.affineDiagnostics = r.affineSamplerDiagnostics = () => { throw new Error('Diagnostic executed in timed frame'); };
        try { const frame = r.frame(1 / 60, { sync: 'finish' }); return { frame, finishCalls, snapshotCalls, after: snapshot() }; }
        finally { d.gl.finish = finish; r.snapshot = snapshot; r.affineDiagnostics = diag; r.affineSamplerDiagnostics = sampler; }
      }, configs.affine);
      assertFiniteTree(d); assert.ok(d.finishCalls >= 2); assert.equal(d.snapshotCalls, 0); validateP3eSnapshot(d.after); assert.deepEqual(d.frame.trace, traceRow(d.after));
      const t = d.frame.timing, sum = t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.affineGroupingMs + t.affineModelBuildMs + t.affineLookupMs + t.tracerAdvectionMs;
      assert.ok(sum <= t.tracerMs + .01); assert.ok(t.tracerMs <= t.totalMs + .01); assert.ok(String(t.synchronization).includes('finish')); return d;
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); }
    catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  console.log(`P3e smoke: ${filename}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
