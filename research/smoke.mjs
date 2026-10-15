import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { BASE_PARAMS } from './lib/design.mjs';
import { fixture } from './lib/fixtures.mjs';
import { assertSnapshot } from './lib/metrics.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';

const argv = process.argv.slice(2), option = name => { const i = argv.indexOf(name); return i < 0 ? undefined : argv[i + 1]; };
const out = path.resolve(option('--out') || path.join(researchRoot, 'runs', `smoke-${Date.now()}`));
await fs.mkdir(out, { recursive: true });
const report = { metadata: hostMetadata(), purpose: 'Behavioral smoke checks, not visual quality or performance claims', tests: [] };
let server, launched, session;
async function check(name, test) {
  process.stdout.write(`${name} ... `);
  try { const evidence = await test(); report.tests.push({ name, status: 'passed', evidence }); console.log('passed'); }
  catch (e) { report.tests.push({ name, status: 'failed', error: e.stack || String(e) }); console.log(`FAILED: ${e.message}`); }
  await fs.writeFile(path.join(out, 'smoke.json'), JSON.stringify(report, null, 2));
}
try {
  server = await startServer(); launched = await launchBrowser(option('--browser-executable'));
  session = await openResearchPage(launched.browser, server.url);
  report.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions, graphics: session.graphics };
  const init = async (f, overrides = {}, seed = 11) => session.page.evaluate(({ f, params, seed }) => {
    const r = window.__demo.research; r.setScene(f.points); r.reset(seed, params); r.camera(0);
    const lit = window.__demo.ignite(...f.ignition.position, f.ignition.radius);
    return { lit, snapshot: r.snapshot({ detail: true }) };
  }, { f, params: { ...BASE_PARAMS, ...overrides }, seed });
  const advance = async n => assertSnapshot(await session.page.evaluate(n => {
    window.__demo.research.step(n, 1 / 60); return window.__demo.research.snapshot({ detail: true });
  }, n));

  await check('deterministic replay resets burn state, params and RNG', async () => {
    const f = fixture('raised-target'); await init(f); const a = await advance(45);
    await session.page.evaluate(() => { window.__demo.research.camera(1.2); window.__demo.research.setParams({ spreadFeedCap: 0 }); });
    await init(f); const b = await advance(45);
    assert.equal(a.hash, b.hash); assert.equal(a.scene.burnHash, b.scene.burnHash);
    assert.deepEqual(a.points, b.points); assert.deepEqual(a.counters, b.counters);
    assert.equal(b.params.spreadFeedCap, 48); assert.equal(b.params.yaw, 0);
    assert.equal(a.randomDraws, b.randomDraws);
    return { first: a, replay: b };
  });

  await check('world-fixed camera trajectories preserve simulation and combustion hashes', async () => {
    const f = fixture('surface-strip');
    await init(f); const stationary = await advance(60);
    await init(f);
    let moving;
    for (const yaw of [.3, -.6, 1.2, -.2]) {
      await session.page.evaluate(yaw => window.__demo.research.camera(yaw), yaw);
      moving = await advance(15);
    }
    assert.equal(moving.hash, stationary.hash); assert.equal(moving.scene.burnHash, stationary.scene.burnHash);
    // View-aligned behavior is evidence, not a pass condition: a scene with no
    // geometric exposure is not guaranteed to exhibit a camera response.
    await init(f, { sliceMode: 'view' }); const viewStationary = await advance(60);
    await init(f, { sliceMode: 'view' });
    let viewMoving;
    for (const yaw of [.3, -.6, 1.2, -.2]) {
      await session.page.evaluate(yaw => window.__demo.research.camera(yaw), yaw);
      viewMoving = await advance(15);
    }
    return { stationary, moving, viewStationary, viewMoving,
      viewResponseObserved: viewStationary.hash !== viewMoving.hash,
      viewBurnResponseObserved: viewStationary.scene.burnHash !== viewMoving.scene.burnHash };
  });

  await check('synthetic scene renders without WebGL errors', async () => {
    await init(fixture('raised-target')); await advance(10);
    const result = await session.page.evaluate(() => {
      const d = window.__demo; d.render();
      return { error: d.gl.getError(), noError: d.gl.NO_ERROR, sceneCount: d.sceneN };
    });
    assert.equal(result.error, result.noError); assert.equal(result.sceneCount, 36);
    return result;
  });

  await check('four feedback toggles gate their own transport operations', async () => {
    const evidence = [];
    for (const heat of [false, true]) for (const feed of [false, true]) {
      await init(fixture('raised-target'), { spreadFlameHeat: heat, spreadSceneFeed: feed });
      const s = await advance(60); const c = s.counters;
      assert.equal(c.baseParticlesEmitted, 0); assert.equal(c.baseHeatApplied, 0);
      if (!heat) { assert.equal(c.flameHeatDeposited, 0); assert.equal(c.flameSamplesProcessed, 0); }
      if (!feed) { assert.equal(c.sceneFeedAttempts, 0); assert.equal(c.sceneSeedsEmitted, 0); assert.equal(s.particles.count, 0); }
      if (feed) {
        assert.ok(c.sceneFeedAttempts > 0); assert.ok(c.sceneSeedsEmitted > 0);
        assert.equal(c.sceneFeedAttempts, c.sceneSeedsEmitted + c.sceneFeedCapacityBlocked + c.sceneFeedRandomRejected);
      }
      if (heat && feed) assert.ok(c.flameSamplesProcessed > 0);
      evidence.push({ heat, feed, snapshot: s });
    }
    return evidence;
  });

  await check('disabling a running emitter stops base emissions and source heat', async () => {
    await init(fixture('raised-target'), { emitterOn: true, spreadSceneFeed: false, spreadFlameHeat: false });
    const before = await advance(30);
    assert.ok(before.counters.baseParticlesEmitted > 0); assert.ok(before.counters.baseHeatApplied > 0);
    await session.page.evaluate(() => window.__demo.research.setParams({ emitterOn: false }));
    const after = await advance(30);
    assert.equal(after.counters.baseParticlesEmitted, before.counters.baseParticlesEmitted);
    assert.equal(after.counters.baseHeatApplied, before.counters.baseHeatApplied);
    return { before, after };
  });

  await check('shipped frontier cap binds and reversed scene changes who is serviced', async () => {
    const options = { spreadFlameHeat: false, spreadSceneFeed: false };
    const start = await init(fixture('cap-stress'), options); assert.equal(start.lit, 1681);
    const a = await advance(1);
    assert.equal(a.counters.frontierProcessed, 1400); assert.equal(a.counters.frontierDeferred, 281);
    await init(fixture('cap-stress', { order: 'reverse' }), options); const b = await advance(1);
    assert.equal(b.counters.frontierProcessed, 1400); assert.equal(b.counters.frontierDeferred, 281);
    assert.notEqual(a.scene.burnHash, b.scene.burnHash);
    await init(fixture('cap-stress'), { ...options, spreadFrontierCap: 2800 }); const uncapped = await advance(1);
    assert.equal(uncapped.counters.frontierProcessed, 1681); assert.equal(uncapped.counters.frontierDeferred, 0);
    return { forward: a, reverse: b, uncapped };
  });

  await check('sample zero-cap and particle-cap counters are exercised', async () => {
    await init(fixture('raised-target'), { spreadSampleCap: 0, ppl: 1 }); const s = await advance(60);
    assert.equal(s.counters.flameSamplesProcessed, 0); assert.equal(s.counters.flameHeatDeposited, 0);
    assert.ok(s.counters.flameSampleCapHits > 0); assert.ok(s.counters.sceneFeedCapacityBlocked > 0);
    assert.equal(s.counters.sceneFeedAttempts, s.counters.sceneSeedsEmitted + s.counters.sceneFeedCapacityBlocked + s.counters.sceneFeedRandomRejected);
    return s;
  });
  if (session.errors.length) report.tests.push({ name: 'browser page errors', status: 'failed', error: session.errors.join('\n') });
} catch (e) { report.error = e.stack || String(e); console.error(report.error); }
finally {
  await session?.page.close(); await launched?.browser.close(); await server?.close();
  report.status = report.error || report.tests.some(t => t.status === 'failed') ? 'failed' : 'passed';
  await fs.writeFile(path.join(out, 'smoke.json'), JSON.stringify(report, null, 2));
  console.log(`Smoke evidence: ${out}`);
  if (report.status !== 'passed') process.exitCode = 1;
}
