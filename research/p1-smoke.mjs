import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fixture } from './lib/fixtures.mjs';
import { assertSnapshot } from './lib/metrics.mjs';
import { P1_DEFAULTS } from './p1-design.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';

const argv = process.argv.slice(2), option = name => { const i = argv.indexOf(name); return i < 0 ? undefined : argv[i + 1]; };
const out = path.resolve(option('--out') || path.join(researchRoot, 'runs', `p1-smoke-${Date.now()}`));
await fs.mkdir(out, { recursive: true });
try { await fs.access(path.join(out, 'smoke.json')); throw new Error('Smoke output already exists; use a new directory'); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const report = { metadata: hostMetadata(), purpose: 'P1 clock and cold-recycling behavioral invariants; not visual-quality evidence', tests: [] };
let server, launched, session;
const save = () => fs.writeFile(path.join(out, 'smoke.json'), JSON.stringify(report, null, 2));
async function check(name, test) {
  process.stdout.write(`${name} ... `);
  try { const evidence = await test(); report.tests.push({ name, status: 'passed', evidence }); console.log('passed'); }
  catch (e) { report.tests.push({ name, status: 'failed', error: e.stack || String(e) }); console.log(`FAILED: ${e.message}`); }
  await save();
}
try {
  server = await startServer(); launched = await launchBrowser(option('--browser-executable'));
  session = await openResearchPage(launched.browser, server.url);
  report.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions, graphics: session.graphics };
  const init = async (name = 'raised-target', overrides = {}) => session.page.evaluate(({ f, params }) => {
    const r = window.__demo.research; r.setScene(f.points); r.reset(11, params); r.camera(0);
    window.__demo.ignite(...f.ignition.position, f.ignition.radius);
    return r.snapshot({ detail: true });
  }, { f: fixture(name), params: { ...P1_DEFAULTS, ...overrides } });
  const advance = async n => assertSnapshot(await session.page.evaluate(n => {
    window.__demo.research.step(n, 1 / 60); return window.__demo.research.snapshot({ detail: true });
  }, n));
  const bounds = s => {
    assert.equal(s.particles.layerCounts.length, s.params.layers);
    assert.ok(s.particles.layerCounts.every(n => n >= 0 && n <= s.params.ppl));
    assert.equal(s.particles.layerCounts.reduce((a, b) => a + b, 0), s.particles.count);
  };

  await check('elapsed zero frontier cap still consumes fuel and retires on elapsed time', async () => {
    await init('cap-stress', { spreadClockMode: 'elapsed', spreadFrontierCap: 0, spreadSceneFeed: false, spreadFlameHeat: false });
    const twoSeconds = await advance(120);
    assert.equal(twoSeconds.counters.frontierProcessed, 0); assert.equal(twoSeconds.counters.graphHeatDeposited, 0);
    assert.equal(twoSeconds.counters.clockProcessed, 1681 * 120);
    assert.ok(twoSeconds.points.every(p => p.fuel > 0 && p.fuel < 1 && p.char > 0));
    const retired = await advance(242); // 6 seconds + two steps, allowing float32 subtraction rounding.
    assert.equal(retired.scene.burning, 0); assert.equal(retired.scene.charred, 1681);
    assert.ok(retired.points.every(p => p.fuel === 0 && p.char === 1));
    return { twoSeconds, retired };
  });

  await check('nonbinding elapsed clocks agree with legacy state up to fuel clamp', async () => {
    const params = { spreadFrontierCap: 2800, spreadSceneFeed: false, spreadFlameHeat: false };
    await init('cap-stress', params); const legacy2 = await advance(120), legacy7 = await advance(300);
    await init('cap-stress', { ...params, spreadClockMode: 'elapsed' }); const elapsed2 = await advance(120), elapsed7 = await advance(300);
    for (const [a, b] of [[legacy2, elapsed2], [legacy7, elapsed7]]) {
      for (let i = 0; i < a.points.length; i++) {
        assert.equal(a.points[i].id, b.points[i].id); assert.equal(a.points[i].state, b.points[i].state);
        assert.ok(Math.abs(Math.max(0, a.points[i].fuel) - b.points[i].fuel) < 1e-6);
        assert.ok(Math.abs(a.points[i].char - b.points[i].char) < 1e-6);
      }
    }
    return { legacy2, elapsed2, legacy7, elapsed7 };
  });

  await check('cold recycling respects per-layer capacity, both temperatures and minimum age', async () => {
    await init('raised-target', { ppl: 30, spreadParticlePolicy: 'recycle-cold' });
    const evidence = [];
    for (let i = 0; i < 16; i++) { const s = await advance(15); bounds(s); evidence.push(s); }
    const s = evidence.at(-1), c = s.counters;
    assert.ok(c.sceneSeedsRecycled > 0); assert.equal(c.recycledHotRemoved, 0);
    assert.ok(c.recycledMaxTemperature < .55); assert.ok(c.recycledMaxDynamicTemperature < .55);
    assert.ok(c.recycledMinAge >= .5 - 1e-9);
    assert.equal(c.sceneFeedAttempts, c.sceneSeedsEmitted + c.sceneFeedCapacityBlocked + c.sceneFeedRandomRejected);
    return evidence;
  });

  await check('full hot young pools reject without removal; non-full admission preserves legacy randomness', async () => {
    await init('raised-target', { ppl: 5, spreadParticlePolicy: 'recycle-cold' });
    const fullHot = await advance(15); bounds(fullHot);
    assert.ok(fullHot.counters.sceneFeedNoColdSlot > 0);
    assert.equal(fullHot.counters.sceneSeedsRecycled, 0); assert.equal(fullHot.particles.coldCount, 0);
    await init('raised-target', { ppl: 1200 }); const block = await advance(15);
    await init('raised-target', { ppl: 1200, spreadParticlePolicy: 'recycle-cold' }); const reuse = await advance(15);
    assert.equal(block.hash, reuse.hash); assert.equal(block.scene.burnHash, reuse.scene.burnHash);
    assert.equal(block.randomDraws, reuse.randomDraws);
    assert.equal(reuse.counters.sceneFeedCapacityBlocked, 0); assert.equal(reuse.counters.sceneSeedsRecycled, 0);
    return { fullHot, block, reuse };
  });

  await check('recycling never occurs with scene feedback disabled', async () => {
    await init('raised-target', { ppl: 30, spreadClockMode: 'elapsed', spreadParticlePolicy: 'recycle-cold', spreadSceneFeed: false });
    const s = await advance(240);
    assert.equal(s.counters.sceneFeedAttempts, 0); assert.equal(s.counters.sceneSeedsRecycled, 0);
    assert.equal(s.particles.count, 0); assert.equal(s.counters.recycledMinAge, null);
    return s;
  });

  await check('minimum age independently blocks replacement of cold particles', async () => {
    await init('raised-target', { ppl: 30, spreadParticlePolicy: 'recycle-cold', spreadRecycleMinAge: 100 });
    const s = await advance(240); bounds(s);
    assert.equal(s.particles.count, 90); assert.ok(s.particles.coldCount > 0);
    assert.equal(s.counters.sceneSeedsRecycled, 0);
    assert.ok(s.counters.sceneFeedNoColdSlot > 0); assert.ok(s.counters.sceneFeedCapacityBlocked > 0);
    return s;
  });

  await check('combined clocks and recycling reset deterministically including burn state', async () => {
    const params = { ppl: 30, spreadClockMode: 'elapsed', spreadParticlePolicy: 'recycle-cold' };
    await init('raised-target', params); const a = await advance(240);
    await init('raised-target', params); const b = await advance(240);
    assert.ok(a.counters.sceneSeedsRecycled > 0);
    assert.equal(a.hash, b.hash); assert.equal(a.scene.burnHash, b.scene.burnHash);
    assert.equal(a.randomDraws, b.randomDraws); assert.deepEqual(a.counters, b.counters);
    return { first: a, replay: b };
  });

  await check('world-fixed moving camera preserves combined dynamics', async () => {
    const params = { ppl: 30, spreadClockMode: 'elapsed', spreadParticlePolicy: 'recycle-cold' };
    await init('raised-target', params); const fixed = await advance(180);
    await init('raised-target', params); let moving;
    for (let i = 0; i < 12; i++) {
      await session.page.evaluate(yaw => window.__demo.research.camera(yaw), Math.sin(i) * 1.2);
      moving = await advance(15); bounds(moving);
    }
    assert.equal(fixed.hash, moving.hash); assert.equal(fixed.scene.burnHash, moving.scene.burnHash);
    return { fixed, moving };
  });

  await check('unknown modes and invalid retirement ages are rejected', async () => {
    const results = await session.page.evaluate(() => [
      { spreadClockMode: 'unknown' }, { spreadParticlePolicy: 'unknown' },
      { spreadRecycleMinAge: -1 }, { spreadRecycleMinAge: NaN }, { spreadRecycleMinAge: Infinity },
    ].map(params => { try { window.__demo.research.setParams(params); return false; } catch { return true; } }));
    assert.ok(results.every(Boolean)); return results;
  });
  if (session.errors.length) report.tests.push({ name: 'browser page errors', status: 'failed', error: session.errors.join('\n') });
} catch (e) { report.error = e.stack || String(e); console.error(report.error); }
finally {
  await session?.page.close(); await launched?.browser.close(); await server?.close();
  report.status = report.error || report.tests.some(t => t.status === 'failed') ? 'failed' : 'passed';
  await save(); console.log(`P1 smoke: ${out}`);
  if (report.status !== 'passed') process.exitCode = 1;
}
