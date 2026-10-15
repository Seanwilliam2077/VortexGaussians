import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3, p3Config, parseP3Args } from './p3-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, requireSamePhysics, checkSourceHashes, saveImage, assertFiniteTree } from './lib/p3-runtime.mjs';
import { imageError } from './lib/p3-metrics.mjs';
import { validateP3Snapshot } from './p3-run.mjs';

export async function main() {
  const args = parseP3Args(process.argv.slice(2));
  const out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const filename = path.join(out, 'smoke.json');
  try { await fs.access(filename); throw new Error(`Refusing to overwrite ${filename}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3a', status: 'running', metadata: hostMetadata(), checks: [] };
  const server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const config = p3Config({ mode: 'passive', nRender: 2400, renderSeed: 101 });
  async function check(name, fn) {
    try { const evidence = await fn(); report.checks.push({ name, status: 'passed', evidence }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  try {
    await check('invalid budgets, optics and unsupported modes are rejected', async () => {
      const rejected = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        return [{ ...config, nSim: 601 }, { ...config, nRender: 0 }, { ...config, mode: 'layer' },
          { ...config, mode: 'shared3d' }, { ...config, renderSeed: -1 },
          { ...config, optics: { radius: 0, tau: .2 } }].map(c => { try { r.reset(11, c); return false; } catch { return true; } });
      }, config); assert.ok(rejected.every(Boolean)); return rejected;
    });
    await check('reset replay and full physical arrays are invariant to render budget/seed', async () => {
      const data = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        function run(c) { r.reset(11, c); const hashes = [r.physicalHash()]; for (let i = 0; i < 60; i++) hashes.push(r.step(1, 1 / 60).physicalHash); return { hashes, snapshot: r.snapshot({ detail: true }) }; }
        return { first: run(config), replay: run(config), other: run({ ...config, nRender: 9600, renderSeed: 211 }), shared: run({ ...config, mode: 'shared3d', nRender: 600 }) };
      }, config);
      requireSamePhysics(data.first.hashes, data.replay.hashes, 'replay');
      for (const name of ['replay', 'other', 'shared']) {
        requireSamePhysics(data.first.hashes, data[name].hashes, name);
        assert.deepEqual(data.first.snapshot.physicsParticles, data[name].snapshot.physicsParticles);
        validateP3Snapshot(data[name].snapshot);
      }
      assert.equal(data.first.snapshot.tracerHash, data.replay.snapshot.tracerHash);
      assert.notEqual(data.first.snapshot.tracerHash, data.other.snapshot.tracerHash);
      const physical = data.first.snapshot.physicsParticles;
      const threeDimensionalMotion = { nonzeroVz: physical.filter(p => Math.abs(p.vz) > 1e-12).length,
        maxAbsoluteVz: Math.max(...physical.map(p => Math.abs(p.vz))),
        zMinimum: Math.min(...physical.map(p => p.z)), zMaximum: Math.max(...physical.map(p => p.z)) };
      assert.ok(threeDimensionalMotion.nonzeroVz > 0); assert.ok(threeDimensionalMotion.zMaximum > threeDimensionalMotion.zMinimum);
      return { comparedSteps: 61, independentArrayCount: data.first.snapshot.physicsParticles.length, physicalHash: data.first.snapshot.physicalHash,
        threeDimensionalMotion, first: data.first.snapshot, other: data.other.snapshot, shared: data.shared.snapshot };
    });
    await check('moving camera and extra render calls preserve both physics and tracer trajectories', async () => {
      const data = await page.evaluate(config => {
        const r = window.__demo.researchP3;
        function run(moving) { r.reset(11, config); const trace = []; for (let i = 0; i < 30; i++) {
          if (moving) { r.camera(Math.sin(i * .2) * 1.4); r.render({ sync: 'finish' }); }
          r.step(1, 1 / 60); const s = r.snapshot(); trace.push([s.physicalHash, s.tracerHash]);
        } return { trace, physicsParticles: r.snapshot({ detail: true }).physicsParticles }; } return { fixed: run(false), moving: run(true) };
      }, config); assert.deepEqual(data.fixed, data.moving); return { frames: 30, final: data.fixed.trace.at(-1), independentlyComparedPhysicsParticles: data.fixed.physicsParticles.length };
    });
    await check('constant/varied thermal fields, zero support and direct-sum traversal diagnostics', async () => {
      const data = await page.evaluate(config => { const r = window.__demo.researchP3; r.reset(11, config); r.step(12, 1 / 60); return r.samplerDiagnostics(); }, config);
      assertFiniteTree(data); assert.equal(data.physicalHashBefore, data.physicalHashAfter); assert.equal(data.cases.length, 6);
      for (const c of data.cases) {
        assert.ok(c.velocityError <= 1e-8, `velocity ${c.velocityError}`); assert.ok(c.temperatureError <= 1e-8); assert.ok(c.weightError <= 1e-8);
        if (c.constant && c.expected.thermalWeight > 0) assert.ok(Math.abs(c.actual.Tb - .75) <= 1e-8);
      }
      assert.ok(data.cases.some(c => c.actual.Tb === 0 && c.expected.thermalWeight === 0));
      const cluster = data.thermalClusterCase;
      assert.ok(cluster.overlappingVelocityClusters > 0); assert.ok(cluster.thermalContributions > 0);
      assert.ok(cluster.temperatureError < 1e-12); assert.ok(cluster.weightError < 1e-12);
      return data;
    });
    await check('RGBA32F optical split 1/2/4/32/64 preserves image and records all errors', async () => {
      const records = []; let baseline;
      for (const n of [1, 2, 4, 32, 64]) {
        const image = await page.evaluate(({ config, n }) => {
          const r = window.__demo.researchP3; r.reset(11, config); r.camera(0);
          r.setRenderParticles(Array.from({ length: n }, () => ({ position: [0, .5, 0], T: .8, d: 1, weight: 1 / n })));
          r.render({ sync: 'finish' }); const gl = window.__demo.gl, display = new Uint8Array(gl.drawingBufferWidth * gl.drawingBufferHeight * 4);
          gl.readPixels(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight, gl.RGBA, gl.UNSIGNED_BYTE, display);
          let previewMaximum = 0; for (let i = 0; i < display.length; i++) if (i % 4 !== 3) previewMaximum = Math.max(previewMaximum, display[i]);
          const im = r.readHDR(); return { ...im, orientation: im.origin, precision: r.snapshot().precision, previewMaximum, data: Array.from(im.data) };
        }, { config, n });
        baseline ||= image; const error = imageError(image, baseline); let maxAbsoluteError = 0, alphaSum = 0, referenceAlphaSum = 0;
        for (let i = 0; i < image.data.length; i++) { maxAbsoluteError = Math.max(maxAbsoluteError, Math.abs(image.data[i] - baseline.data[i]));
          if (i % 4 === 3) { alphaSum += image.data[i]; referenceAlphaSum += baseline.data[i]; } }
        const imageFile = await saveImage(out, `optical-split-${n}`, image);
        records.push({ copies: n, maxAbsoluteError, alphaSum, referenceAlphaSum, previewMaximum: image.previewMaximum, alphaIntegralAbsoluteError: Math.abs(alphaSum - referenceAlphaSum), error, image: imageFile });
        assert.ok(referenceAlphaSum > 0); assert.ok(image.previewMaximum > 0, 'Composite canvas is black despite nonzero HDR signal');
        assert.ok(maxAbsoluteError <= 1e-4, `split ${n} error ${maxAbsoluteError}`);
      }
      return records;
    });
    await check('source ledgers preserve normalized optical injection and expose capacity blocks', async () => {
      const data = await page.evaluate(config => {
        const r = window.__demo.researchP3, states = [];
        for (const nRender of [600, 2400, 9600]) { r.reset(11, { ...config, nRender }); r.step(60, 1 / 60); states.push(r.snapshot()); }
        r.reset(11, { ...config, nSim: 6, nRender: 12 }); r.step(60, 1 / 60); return { states, capped: r.snapshot() };
      }, config);
      for (const s of data.states) { validateP3Snapshot(s); assert.equal(s.counters.physicsInjectedOpticalWeight, 180); assert.ok(Math.abs(s.counters.tracerInjectedOpticalWeight - 180) < 1e-8); }
      validateP3Snapshot(data.capped, false); assert.ok(data.capped.counters.physicsFullSteps > 0); assert.ok(data.capped.counters.tracerCapacityDropped > 0);
      assert.throws(() => validateP3Snapshot(data.capped), /capacity limited/); return data;
    });
    await check('synchronized frame drains and completes GPU work with finite stage measurements', async () => {
      const data = await page.evaluate(config => {
        const d = window.__demo, r = d.researchP3; r.reset(11, config); r.step(12, 1 / 60);
        const original = d.gl.finish.bind(d.gl); let finishCalls = 0; d.gl.finish = () => { finishCalls++; original(); };
        try { return { frame: r.frame(1 / 60, { sync: 'finish' }), finishCalls }; } finally { d.gl.finish = original; }
      }, config);
      assert.ok(data.finishCalls >= 2); assertFiniteTree(data);
      for (const name of ['simulationMs', 'tracerMs', 'gatherSortUploadMs', 'drawSubmitMs', 'finishWaitMs', 'totalMs']) assert.ok(data.frame.timing[name] >= 0);
      assert.ok(String(data.frame.timing.synchronization).includes('finish')); return data;
    });
    if (errors.length) throw new Error(errors.join('\n'));
    report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); }
    catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(filename, JSON.stringify(report, null, 2));
  }
  console.log(`P3 smoke: ${filename}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
