import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3D, p3dConfig, parseP3dArgs } from './p3d-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3dSnapshot } from './p3d-run.mjs';
import { traceRow, requirePairedTrace } from './p3b-run.mjs';
import { exactTracerReplay } from './lib/p3d-metrics.mjs';

export async function main() {
  const args = parseP3dArgs(process.argv.slice(2)), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3d-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const file = path.join(out, 'smoke.json');
  try { await fs.access(file); throw new Error(`Refusing to overwrite ${file}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3d', status: 'running', metadata: hostMetadata(), checks: [] };
  const server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const configs = Object.fromEntries(P3D.methods.map(m => [m.id, p3dConfig({ scenario: 'curl', method: m.id, renderSeed: 101 })]));
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  try {
    await check('evaluation defaults to legacy combined and rejects unsupported specializations', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3, field = { ...config.field }; delete field.evaluation;
        r.reset(11, { ...config, field }); r.step(15, 1 / 60); const defaultState = r.snapshot({ detail: true });
        r.reset(11, config); r.step(15, 1 / 60); const explicitState = r.snapshot({ detail: true });
        const rejected = [{ ...field, evaluation: 'bad' }, { ...field, mode: 'tree', evaluation: 'specialized' },
          { ...field, components: 'both', evaluation: 'specialized' }, { ...field, components: 'velocity', evaluation: 'specialized' }].map(field => { try { r.reset(11, { ...config, field }); return false; } catch { return true; } });
        return { defaultState, explicitState, rejected };
      }, configs['DG-original']);
      assert.deepEqual(d.defaultState, d.explicitState); assert.ok(d.rejected.every(Boolean)); return { defaultIsCombined: true, rejected: d.rejected, tracerHash: d.defaultState.tracerHash };
    });
    await check('specialized component samplers exactly match combined leaf, cluster, unsupported and empty queries', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3; r.reset(11, config); r.step(30, 1 / 60); const before = r.snapshot({ detail: true });
        const positions = before.renderParticles.filter(p => p.id % 97 === 0).map(p => [p.x, p.y, p.z]);
        const diagnostic = r.componentDiagnostics(positions), after = r.snapshot({ detail: true }); return { before, diagnostic, after };
      }, configs['DG-specialized']);
      assert.deepEqual(d.before, d.after); assertFiniteTree(d.diagnostic); assert.deepEqual(d.diagnostic.traceBefore, d.diagnostic.traceAfter);
      assert.deepEqual(d.diagnostic.cases.map(c => c.id), ['leaf-supported', 'leaf-unsupported', 'cluster-thermal-overlap', 'cluster-unsupported', 'empty-tree']);
      for (const s of [...d.diagnostic.samples, ...d.diagnostic.cases]) {
        assert.equal(s.velocityEqual, true); assert.equal(s.thermalEqual, true); assert.deepEqual(s.combined, s.specialized);
        assert.equal(s.counters.combined.fullFieldQueries, 1); assert.equal(s.counters.velocity.velocityOnlyFieldQueries, 1); assert.equal(s.counters.thermal.thermalOnlyFieldQueries, 1);
        assert.equal(s.counters.velocity.thermalContributions, 0); assert.equal(s.counters.thermal.velocityClusterEvaluations, 0); assert.equal(s.counters.thermal.velocityLeafEvaluations, 0);
      }
      assert.ok(d.diagnostic.cases.find(c => c.id === 'cluster-thermal-overlap').counters.combined.thermalOverlapVelocityClusters > 0);
      return { unchanged: true, diagnostic: d.diagnostic };
    });
    await check('original and specialized DG match every tracer hash, full particle arrays and raw optical pixels', async () => {
      const d = await page.evaluate(configs => {
        const r = window.__demo.researchP3, result = {};
        for (const method of ['DG-original', 'DG-specialized']) {
          r.reset(11, configs[method]); const trace = [r.trace()], hashes = [{ frame: 0, tracerHash: r.snapshot().tracerHash }];
          for (let frame = 1; frame <= 30; frame++) { r.step(1, 1 / 60); trace.push(r.trace()); hashes.push({ frame, tracerHash: r.snapshot().tracerHash }); }
          r.camera(.7); r.render({ sync: 'finish' }); const image = r.readHDR();
          result[method] = { trace, hashes, snapshot: r.snapshot({ detail: true }), image: { ...image, data: Array.from(image.data), orientation: image.origin, precision: 'rgba32f' } };
        } return result;
      }, configs);
      const a = d['DG-original'], b = d['DG-specialized']; requirePairedTrace(a.trace, b.trace); exactTracerReplay(a.hashes, b.hashes);
      assert.deepEqual(a.snapshot.physicsParticles, b.snapshot.physicsParticles); assert.deepEqual(a.snapshot.renderParticles, b.snapshot.renderParticles); assert.deepEqual(a.image, b.image);
      validateP3dSnapshot(a.snapshot); validateP3dSnapshot(b.snapshot);
      const images = []; for (const [method, data] of Object.entries(d)) images.push(await saveImage(out, method, data.image));
      return { frames: a.hashes.length, comparedParticles: a.snapshot.render.count, originalCounters: a.snapshot.counters, specializedCounters: b.snapshot.counters, images };
    });
    await check('DD and both DG implementations preserve physical state and source RNG with honest component counters', async () => {
      const d = await page.evaluate(configs => { const r = window.__demo.researchP3;
        return Object.fromEntries(Object.entries(configs).map(([method, config]) => { r.reset(11, config); r.step(15, 1 / 60); return [method, r.snapshot({ detail: true })]; })); }, configs);
      for (const s of Object.values(d)) { validateP3dSnapshot(s); assert.deepEqual(s.physicsParticles, d.DD.physicsParticles); assert.deepEqual(traceRow(s), traceRow(d.DD)); }
      return Object.fromEntries(Object.entries(d).map(([method, s]) => [method, { counters: s.counters, physics: s.physics, render: s.render }]));
    });
    await check('specialized reset replay and camera motion leave full particle states unchanged', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3, run = moving => { r.reset(11, config);
        for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); }
        return r.snapshot({ detail: true }); }; return { a: run(false), b: run(false), moving: run(true) }; }, configs['DG-specialized']);
      for (const s of [d.b, d.moving]) { assert.equal(s.tracerHash, d.a.tracerHash); assert.equal(s.physicalHash, d.a.physicalHash); assert.deepEqual(s.physicsParticles, d.a.physicsParticles); assert.deepEqual(s.renderParticles, d.a.renderParticles); }
      return { tracerHash: d.a.tracerHash, physicalHash: d.a.physicalHash, comparedParticles: d.a.render.count };
    });
    await check('GPU-completed frame includes specialized work without dense snapshot collection', async () => {
      const d = await page.evaluate(config => {
        const d = window.__demo, r = d.researchP3; r.reset(11, config); r.step(30, 1 / 60);
        const finish = d.gl.finish.bind(d.gl), snapshot = r.snapshot; let finishCalls = 0, snapshotCalls = 0;
        d.gl.finish = () => { finishCalls++; finish(); }; r.snapshot = (...args) => { snapshotCalls++; return snapshot(...args); };
        try { const frame = r.frame(1 / 60, { sync: 'finish' }); return { frame, finishCalls, snapshotCalls, after: snapshot() }; }
        finally { d.gl.finish = finish; r.snapshot = snapshot; }
      }, configs['DG-specialized']);
      assertFiniteTree(d); assert.ok(d.finishCalls >= 2); assert.equal(d.snapshotCalls, 0); assert.deepEqual(d.frame.trace, traceRow(d.after)); validateP3dSnapshot(d.after);
      const t = d.frame.timing; assert.ok(String(t.synchronization).includes('finish'));
      assert.ok(t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.tracerAdvectionMs <= t.tracerMs + .01); assert.ok(t.tracerMs <= t.totalMs + .01); return d;
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); }
    catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  console.log(`P3d smoke: ${file}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
