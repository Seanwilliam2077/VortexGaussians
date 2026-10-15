import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { P3C, p3cConfig, parseP3cArgs } from './p3c-design.mjs';
import { startServer, launchBrowser, hostMetadata, researchRoot } from './lib/runtime.mjs';
import { openP3Page, assertFiniteTree, checkSourceHashes, saveImage } from './lib/p3-runtime.mjs';
import { validateP3cSnapshot } from './p3c-run.mjs';
import { traceRow } from './p3b-run.mjs';
import { directionalPaths, summarizeInputs } from './lib/p3c-metrics.mjs';

export async function main() {
  const args = parseP3cArgs(process.argv.slice(2)), out = path.resolve(args.out || path.join(researchRoot, 'runs', `p3c-smoke-${Date.now()}`));
  await fs.mkdir(out, { recursive: true }); const file = path.join(out, 'smoke.json');
  try { await fs.access(file); throw new Error(`Refusing to overwrite ${file}`); } catch (e) { if (e.code !== 'ENOENT') throw e; }
  const report = { phase: 'P3c', status: 'running', metadata: hostMetadata(), checks: [] };
  const server = await startServer(), launched = await launchBrowser(args.browserExecutable);
  const { page, errors, graphics } = await openP3Page(launched.browser, server.url); report.graphics = graphics;
  const configs = Object.fromEntries(P3C.arms.map(a => [a.id, p3cConfig({ scenario: 'curl', arm: a.id, renderSeed: 101 })]));
  let armData;
  async function check(name, fn) {
    try { report.checks.push({ name, status: 'passed', evidence: await fn() }); console.log(`PASS ${name}`); }
    catch (e) { report.checks.push({ name, status: 'failed', error: e.stack || String(e) }); console.error(`FAIL ${name}: ${e.message}`); }
    await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  try {
    await check('invalid component and input-observer options fail without advancing a valid state', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3; let invalidComponents = false;
        try { r.reset(11, { ...config, field: { ...config.field, components: 'invalid' } }); } catch { invalidComponents = true; }
        r.reset(11, config); const before = r.snapshot({ detail: true });
        const rejected = [0, -1, 1.5, NaN].map(stride => { try { r.stepWithInputs(1 / 60, { stride }); return false; } catch { return true; } });
        return { invalidComponents, rejected, before, after: r.snapshot({ detail: true }) };
      }, configs.DD);
      assert.ok(d.invalidComponents && d.rejected.every(Boolean)); assert.deepEqual(d.before, d.after); return { invalidComponents: d.invalidComponents, rejected: d.rejected, unchanged: true };
    });
    await check('DD preadvection observation leaves every physical and tracer value and RNG unchanged', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3, run = observe => { r.reset(11, config); const trace = [];
          for (let frame = 1; frame <= 30; frame++) { if (observe && frame % 15 === 0) r.stepWithInputs(1 / 60, { stride: 97 }); else r.step(1, 1 / 60); trace.push(r.trace()); }
          return { trace, snapshot: r.snapshot({ detail: true }) }; }; return { observed: run(true), plain: run(false) };
      }, configs.DD);
      assert.deepEqual(d.observed, d.plain); return { exactFullState: true, physicalHash: d.plain.snapshot.physicalHash, tracerHash: d.plain.snapshot.tracerHash, steps: d.plain.trace.length, particles: d.plain.snapshot.render.count };
    });
    await check('captured preadvection positions include sampled newborns and four probe combinations reproduce actual velocities', async () => {
      armData = await page.evaluate(configs => {
        const r = window.__demo.researchP3, data = {};
        for (const [arm, config] of Object.entries(configs)) {
          r.reset(11, config); r.step(14, 1 / 60); const prior = r.snapshot({ detail: true });
          const captured = r.stepWithInputs(1 / 60, { stride: 97 }), before = r.snapshot({ detail: true });
          const probe = r.fieldProbe(captured.inputs.map(p => p.position), { cellSize: .035, maxNodes: 200000 });
          const after = r.snapshot({ detail: true }); data[arm] = { prior, captured, probe, before, after };
        } return data;
      }, configs);
      const evidence = {};
      for (const [arm, d] of Object.entries(armData)) {
        assert.deepEqual(d.before, d.after); assertFiniteTree(d.probe);
        const prior = new Map(d.prior.renderParticles.map(p => [p.id, p])), after = new Map(d.after.renderParticles.map(p => [p.id, p]));
        const expectedIds = d.after.renderParticles.filter(p => p.id % 97 === 0).map(p => p.id);
        assert.deepEqual(d.captured.inputs.map(p => p.id), expectedIds); assert.ok(expectedIds.includes(0)); assert.ok(d.captured.inputs.some(p => p.newborn));
        for (let i = 0; i < d.captured.inputs.length; i++) {
          const input = d.captured.inputs[i], old = prior.get(input.id), current = after.get(input.id), s = d.probe.samples[i];
          if (old) { assert.deepEqual(input.position, [old.x, old.y, old.z]); assert.equal(input.age, old.life); } else { assert.equal(input.age, 0); assert.equal(input.newborn, true); }
          assert.deepEqual(s.position, input.position); assert.equal(input.frame, 15); assert.equal(input.fieldTime, d.probe.fieldTime);
          assert.deepEqual(s.transportVelocities[arm], [current.vx, current.vy, current.vz]);
          assert.deepEqual(s.combinations.GD.inducedVelocity, s.grid.inducedVelocity); assert.equal(s.combinations.GD.Tb, s.tree.Tb);
          assert.deepEqual(s.combinations.DG.inducedVelocity, s.tree.inducedVelocity); assert.equal(s.combinations.DG.Tb, s.grid.Tb);
        }
        const summary = summarizeInputs([{ frame: 15, time: .25, inputs: d.captured.inputs, probe: d.probe }], P3C);
        evidence[arm] = { inputCount: expectedIds.length, maxVelocityDifference: 0, fullStateUnchangedByProbe: true, summary, captured: d.captured, probe: d.probe };
      }
      return evidence;
    });
    await check('all four arms preserve full physics, births and T/d/life with component-aware query accounting', async () => {
      assert.ok(armData); const direct = armData.DD.after, evidence = {};
      for (const [arm, d] of Object.entries(armData)) {
        const s = d.after; validateP3cSnapshot(s); assert.deepEqual(s.physicsParticles, direct.physicsParticles); assert.deepEqual(traceRow(s), traceRow(direct));
        const p = directionalPaths(s.renderParticles, direct.renderParticles, P3C);
        assert.deepEqual(p.visualStateMismatchIds, []); assert.deepEqual(p.onlyReference, []); assert.deepEqual(p.onlyCandidate, []);
        assert.equal(s.counters.componentDirectQueries, ['GD', 'DG'].includes(arm) ? s.counters.tracerFieldQueries : 0);
        evidence[arm] = { field: s.field, counters: s.counters, physicalHash: s.physicalHash, paths: p };
      } return evidence;
    });
    await check('hybrid reset replay and changing cameras leave deterministic trajectories identical', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3, run = moving => { r.reset(11, config);
          for (let i = 0; i < 15; i++) { if (moving) { r.camera(Math.sin(i)); r.render({ sync: 'finish' }); } r.step(1, 1 / 60); }
          return r.snapshot({ detail: true }); }; return { first: run(false), replay: run(false), moving: run(true) };
      }, configs.GD);
      for (const s of [d.replay, d.moving]) { assert.equal(s.physicalHash, d.first.physicalHash); assert.equal(s.tracerHash, d.first.tracerHash); assert.deepEqual(s.physicsParticles, d.first.physicsParticles); assert.deepEqual(s.renderParticles, d.first.renderParticles); }
      return { physicalHash: d.first.physicalHash, tracerHash: d.first.tracerHash, comparedParticles: d.first.render.count };
    });
    await check('linear RGBA32F and display PNG captures are nonempty and preserve production state', async () => {
      const d = await page.evaluate(config => {
        const r = window.__demo.researchP3; r.reset(11, config); r.step(15, 1 / 60); const before = r.snapshot(); r.camera(.7); r.render({ sync: 'finish' });
        const preview = document.querySelector('canvas').toDataURL('image/png'), hdr = r.readHDR();
        return { before, after: r.snapshot(), preview, image: { ...hdr, data: Array.from(hdr.data), orientation: hdr.origin, precision: 'rgba32f' } };
      }, configs.DG);
      assert.equal(d.after.params.yaw, .7); d.before.params.yaw = d.after.params.yaw;
      assert.deepEqual(d.before, d.after); const image = await saveImage(out, 'smoke-DG', d.image);
      assert.ok(image.summary.maxAlpha > 0 && image.summary.meanRgb > 0); const preview = 'images/smoke-DG.png';
      await fs.writeFile(path.join(out, preview), Buffer.from(d.preview.split(',')[1], 'base64')); return { image, preview, unchanged: true };
    });
    if (errors.length) throw new Error(errors.join('\n')); report.status = report.checks.every(c => c.status === 'passed') ? 'passed' : 'failed';
  } catch (e) { report.status = 'failed'; report.error = e.stack || String(e); }
  finally {
    await page.close(); await launched.browser.close(); await server.close(); report.finalMetadata = hostMetadata();
    try { report.sourceFreeze = checkSourceHashes(report.metadata.sourceHashes, report.finalMetadata.sourceHashes); }
    catch (e) { report.sourceFreeze = { matched: false, error: e.message }; report.status = 'failed'; }
    report.completed = new Date().toISOString(); await fs.writeFile(file, JSON.stringify(report, null, 2));
  }
  console.log(`P3c smoke: ${file}`); if (report.status !== 'passed') process.exitCode = 1;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main().catch(e => { console.error(e.stack || e); process.exitCode = 1; });
