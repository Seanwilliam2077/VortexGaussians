import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3B, p3bConfig, parseP3bArgs } from './p3b-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes } from './lib/p3-runtime.mjs';
import { validateP3bSnapshot, traceRow } from './p3b-run.mjs';
import { pairedParticles } from './lib/p3b-metrics.mjs';

export async function main() {
  const args = parseP3bArgs(process.argv.slice(2));
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3b-smoke-${Date.now()}`)); await fs.mkdir(out, { recursive: true });
  const file = path.join(out, 'smoke.json');
  try { await fs.access(file); throw new Error(`Refusing to overwrite ${file}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3b', status: 'running', metadata: hostMetadata(), checks: [] };
  const server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const config = p3bConfig({ scenario: 'stationary', method: 'grid070', renderSeed: 101 });
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  try {
    await check('field configuration rejects invalid modes, spacing, capacity and unsupported use', async () => {
      const rejected = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        return [{ ...config, field: { mode: 'bad' } }, { ...config, field: { mode: 'grid', cellSize: 0 } },
          { ...config, field: { mode: 'grid', maxNodes: 0 } }, { ...config, field: { mode: 'grid', maxNodes: 1.5 } },
          { ...config, field: { mode: 'grid', ignored: true } }, { ...config, mode: 'shared3d', nRender: 600 }].map(c => {
          try { r.reset(11, c); return false; } catch { return true; }
        });
      }, config); assert.ok(rejected.every(Boolean)); return rejected;
    });
    await check('constant/affine and negative-grid interpolation, unique nodes, invalidation, support and clamp order', async () => {
      const d = await page.evaluate(config => { const r = window.__demo.researchP3; r.reset(11, config); return r.cacheDiagnostics(); }, config);
      assertFiniteTree(d); assert.equal(d.physicalHashBefore, d.physicalHashAfter); assert.equal(d.cases.length, 2);
      for (const c of d.cases) { assert.equal(c.maxQueriesPerNode, 1); for (const e of c.errors) { assert.ok(e.velocityError < 1e-12); assert.ok(e.temperatureError < 1e-12); } }
      assert.equal(d.capacity.nodeCount, 8); assert.deepEqual(d.capacity.fallbackByPoint, [false, true, false]);
      assert.ok(d.emptySupport.every(p => p.Tb === 0 && p.supportFraction === 0));
      for (const p of d.freshStep) { assert.ok(Math.abs(p.ux - 1) < 1e-12); assert.ok(Math.abs(p.Tb - .25) < 1e-12); }
      for (const k of ['Tb', 'thermalWeight', 'supportFraction']) assert.ok(Math.abs(d.mixedSupport.actual[k] - d.mixedSupport.expected[k]) < 1e-12);
      assert.ok(d.clampOrder.velocityError < 1e-12); assert.notDeepEqual(d.clampOrder.expectedVelocity, d.clampOrder.prematureNodeClampVelocity);
      return d;
    });
    await check('all-fallback grid exactly replays tree including curl forces and visual state', async () => {
      const data = await page.evaluate(config => {
        const r = window.__demo.researchP3, params = { ...config.params, wind: .2, turb: .55 };
        const run = field => { r.reset(11, { ...config, params, field }); const trace = [];
          for (let i = 0; i < 15; i++) { r.step(1, 1 / 60); const s = r.snapshot(); trace.push([s.physicalHash, s.tracerHash]); }
          return { trace, snapshot: r.snapshot({ detail: true }) }; };
        return { tree: run({ mode: 'tree' }), fallback: run({ mode: 'grid', cellSize: .07, maxNodes: 1 }) };
      }, config);
      assert.deepEqual(data.tree.trace, data.fallback.trace); assert.deepEqual(data.tree.snapshot.physicsParticles, data.fallback.snapshot.physicsParticles);
      assert.deepEqual(data.tree.snapshot.renderParticles, data.fallback.snapshot.renderParticles); validateP3bSnapshot(data.fallback.snapshot);
      assert.ok(data.fallback.snapshot.counters.cacheFallbacks > 0); return data;
    });
    await check('different cache spacings preserve physical arrays, birth RNG and matched visual evolution', async () => {
      const data = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        return [.035, .07, .14].map(cellSize => { r.reset(11, { ...config, field: { ...config.field, cellSize } }); r.step(30, 1 / 60); return r.snapshot({ detail: true }); });
      }, config);
      for (const s of data) {
        validateP3bSnapshot(s); assert.equal(s.physicalHash, data[0].physicalHash); assert.deepEqual(s.physicsParticles, data[0].physicsParticles);
        assert.equal(s.render.rngState, data[0].render.rngState); assert.equal(s.render.randomDraws, data[0].render.randomDraws);
        const p = pairedParticles(s.renderParticles, data[0].renderParticles);
        assert.deepEqual(p.onlyCandidate, []); assert.deepEqual(p.onlyReference, []); assert.deepEqual(p.visualStateMismatchIds, []);
        assert.equal(s.counters.cacheFallbacks, 0); assert.ok(s.counters.cacheHits > 0);
      }
      return data.map(s => ({ field: s.field, physics: s.physics, render: s.render, counters: s.counters }));
    });
    await check('grid reset is deterministic and camera trajectories preserve physics and render arrays', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        const run = moving => { r.reset(11, config); for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); } return r.snapshot({ detail: true }); };
        return { first: run(false), replay: run(false), moving: run(true) };
      }, config);
      for (const s of [d.replay, d.moving]) { assert.equal(d.first.physicalHash, s.physicalHash); assert.equal(d.first.tracerHash, s.tracerHash);
        assert.deepEqual(d.first.physicsParticles, s.physicsParticles); assert.deepEqual(d.first.renderParticles, s.renderParticles); }
      return { physicalHash: d.first.physicalHash, tracerHash: d.first.tracerHash, comparedParticles: d.first.renderParticles.length };
    });
    await check('fixed world probes use the frozen tree and leave full production state unchanged', async () => {
      const d = await page.evaluate(({ config, positions }) => {
        const r = window.__demo.researchP3; r.reset(11, config); r.step(30, 1 / 60); const before = r.snapshot({ detail: true });
        const probe = r.fieldProbe(positions); return { before, probe, after: r.snapshot({ detail: true }) };
      }, { config, positions: P3B.probePositions });
      assert.deepEqual(d.before, d.after); assertFiniteTree(d.probe); assert.equal(d.probe.samples.length, 48);
      assert.ok(d.probe.samples.every(s => !s.fallback)); assert.equal(d.probe.physicalHashBefore, d.probe.physicalHashAfter);
      assert.deepEqual(d.probe.renderRngBefore, d.probe.renderRngAfter);
      return { probe: d.probe, unchangedFullState: true, directProbeNoSupport: d.probe.samples.filter(s => s.tree.thermalWeight === 0).length,
        nodeNoSupport: d.probe.counters.noThermalSupportQueries, warning: 'Different query populations; do not divide node no-support by tracer count.' };
    });
    await check('GPU-completed timing includes cache build and lookup without double counting', async () => {
      const d = await page.evaluate(config => {
        const d = window.__demo, r = d.researchP3; r.reset(11, config); r.step(30, 1 / 60);
        const original = d.gl.finish.bind(d.gl); let calls = 0; d.gl.finish = () => { calls++; original(); };
        try {
          const before = r.snapshot({ detail: true }), lightweight = r.trace(), afterTrace = r.snapshot({ detail: true });
          if (JSON.stringify(before) !== JSON.stringify(afterTrace)) throw new Error('Lightweight trace changed state');
          return { result: r.frame(1 / 60, { sync: 'finish' }), calls, lightweight, before, after: r.snapshot() };
        } finally { d.gl.finish = original; }
      }, config);
      assertFiniteTree(d); assert.ok(d.calls >= 2); const t = d.result.timing;
      assert.deepEqual(d.lightweight, traceRow(d.before)); assert.deepEqual(d.result.trace, traceRow(d.after));
      const sum = t.tracerSetupMs + t.treeQueryAndAdvectionMs + t.cacheBuildMs + t.cacheLookupMs + t.tracerAdvectionMs;
      assert.ok(sum <= t.tracerMs + .01); assert.ok(t.tracerMs <= t.totalMs + .01); assert.ok(String(t.synchronization).includes('finish'));
      return d;
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); }
    catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  console.log(`P3b smoke: ${file}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
