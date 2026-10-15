import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { p2Fixture } from './p2-fixtures.mjs';
import { P2_DEFAULTS, compareP2 } from './p2-design.mjs';
import { runP2Case, checkP2Snapshot } from './p2-run.mjs';
import { startServer, launchBrowser, openResearchPage, hostMetadata, researchRoot } from './lib/runtime.mjs';

const argv = process.argv.slice(2), option = name => { const i = argv.indexOf(name); return i < 0 ? undefined : argv[i + 1]; };
const out = path.resolve(option('--out') || path.join(researchRoot, 'runs', `p2-smoke-${Date.now()}`));
await fs.mkdir(out, { recursive: true });
const report = { metadata: hostMetadata(), purpose: 'P2 authored-area API, duplicate and feed-ledger invariants; synthetic implementation checks', tests: [] };
const save = () => fs.writeFile(path.join(out, 'smoke.json'), JSON.stringify(report, null, 2));
let server, launched, session, activeFixture;
const close = (a, b, tolerance = 1e-8) => assert.ok(Math.abs(a - b) <= tolerance, `${a} != ${b}`);
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
  const init = async (overrides = {}, variant = 'base', order = 'forward') => {
    activeFixture = p2Fixture('raised-target', variant, order);
    const s = await session.page.evaluate(({ f, params }) => {
      const r = window.__demo.research; r.setScene(f.points); r.reset(11, params); r.camera(0);
      for (const position of f.sourcePositions) window.__demo.ignite(...position, f.ignitionRadius);
      return r.snapshot({ detail: true });
    }, { f: activeFixture, params: { ...P2_DEFAULTS, spreadMeasureMode: 'area', ...overrides } });
    return checkP2Snapshot(s, activeFixture);
  };
  const advance = async n => checkP2Snapshot(await session.page.evaluate(n => {
    window.__demo.research.step(n, 1 / 60); return window.__demo.research.snapshot({ detail: true });
  }, n), activeFixture);
  const shortCase = async (kind, variant, order, params = {}) => {
    const result = await runP2Case(launched.browser, server.url, {
      id: `${kind}-${variant}-${order}`, family: kind === 'surface' ? 'graph-duplicate' : 'closed-loop',
      kind, variant, order, seed: 11, frames: 60, sampleEvery: 15, dt: 1 / 60, yaw: 0,
      params: { ...P2_DEFAULTS, spreadMeasureMode: 'area', ...params },
    });
    assert.equal(result.status, 'passed', result.error); return result;
  };

  await check('area mode rejects missing/inferred/nonpositive measures and a legacy clock', async () => {
    const checks = await session.page.evaluate(params => {
      const r = window.__demo.research;
      const base = { id: 'point', group: 'source', position: [0, .2, 0], fuel: 1, areaWeight: .0016 };
      r.setScene([base]); r.reset(11, { ...params, spreadMeasureMode: 'legacy' });
      const results = [];
      for (const value of [0, -1, NaN, Infinity]) {
        try { r.setScene([{ ...base, areaWeight: value }]); results.push(false); } catch { results.push(true); }
      }
      const missing = { ...base, analysisWeight: .0016 }; delete missing.areaWeight;
      r.setScene([missing]);
      try { r.reset(11, { ...params, spreadMeasureMode: 'area' }); results.push(false); } catch { results.push(true); }
      r.setScene([base]);
      try { r.reset(11, { ...params, spreadMeasureMode: 'area', spreadClockMode: 'legacy' }); results.push(false); } catch { results.push(true); }
      try { r.reset(11, { ...params, spreadMeasureMode: 'unknown' }); results.push(false); } catch { results.push(true); }
      try { r.reset(11, { ...params, spreadMeasureMode: 'area', spreadReferenceArea: 0 }); results.push(false); } catch { results.push(true); }
      return results;
    }, P2_DEFAULTS);
    assert.ok(checks.every(Boolean)); return checks;
  });

  await check('graph duplicate splitting preserves sampled anchor states and weighted totals', async () => {
    const params = { spreadFlameHeat: false, spreadSceneFeed: false };
    const reference = await shortCase('surface', 'base', 'forward', params);
    const evidence = [];
    for (const variant of ['uniform4', 'variable-both']) {
      const result = await shortCase('surface', variant, 'shuffle', params), c = compareP2(result, reference);
      assert.equal(c.duplicateStateCriterionSatisfied, true, JSON.stringify(c));
      assert.equal(c.weightedTotalCriterionSatisfied, true, JSON.stringify(c));
      evidence.push(c);
    }
    return evidence;
  });

  await check('coalesced area feedback preserves particle and event traces across shuffled splits', async () => {
    // Isolate source selection: all nine sources burn, no target heat/ignition feedback.
    const params = { spreadFlameHeat: false, spreadRate: 0 };
    const reference = await shortCase('raised-target', 'base', 'forward', params), evidence = [];
    for (const variant of ['uniform4', 'variable-both']) {
      const result = await shortCase('raised-target', variant, 'shuffle', params), c = compareP2(result, reference);
      assert.equal(c.feedAndParticleTraceCriterionSatisfied, true, JSON.stringify(c));
      assert.equal(c.duplicateStateCriterionSatisfied, true, JSON.stringify(c));
      evidence.push(c);
    }
    assert.ok(reference.raw.at(-1).counters.areaFeedAdmitted > 0); return evidence;
  });

  await check('service cap drops integer overflow and retains only fractional credit', async () => {
    await init({ spreadFeedCap: 2, spreadFlameHeat: false, spreadRate: 0 }); const s = await advance(5);
    const c = s.counters;
    close(c.areaFeedCreditsGenerated, 22.5); assert.equal(c.areaFeedAttempts, 10);
    assert.equal(c.areaFeedServiceCapDropped, 12); close(s.areaFeed.creditBalance, .5);
    assert.equal(s.areaFeed.wholeEventsPending, 0);
    close(c.areaFeedCreditsGenerated, c.areaFeedAttempts + c.areaFeedServiceCapDropped + c.areaFeedCancelledCredits + s.areaFeed.creditBalance);
    return s;
  });

  await check('extinction cancels residual fraction without transferring emission debt', async () => {
    await init({ spreadBurnT: .02, spreadFlameHeat: false, spreadRate: 0 });
    const first = await advance(1), extinct = await advance(1);
    close(first.areaFeed.creditBalance, .5); assert.equal(extinct.scene.burning, 0);
    close(extinct.counters.areaFeedCancelledCredits, .5); assert.equal(extinct.areaFeed.creditBalance, 0);
    assert.equal(extinct.counters.areaFeedAttempts, first.counters.areaFeedAttempts);
    return { first, extinct };
  });

  await check('area replay resets credit/RNG and remains world-camera invariant', async () => {
    const params = { ppl: 30 };
    await init(params); const first = await advance(180);
    await init(params); const replay = await advance(180);
    assert.equal(first.hash, replay.hash); assert.equal(first.particleStateHash, replay.particleStateHash);
    assert.deepEqual(first.counters, replay.counters); assert.deepEqual(first.areaFeed, replay.areaFeed);
    await init(params); let moving;
    for (let i = 0; i < 12; i++) {
      await session.page.evaluate(yaw => window.__demo.research.camera(yaw), Math.sin(i) * 1.2);
      moving = await advance(15);
    }
    assert.equal(first.hash, moving.hash); assert.equal(first.particleStateHash, moving.particleStateHash);
    return { first, replay, moving };
  });

  await check('area admissions remain bounded and feedback-off creates no credit', async () => {
    await init({ ppl: 5 }); const snapshots = [];
    for (let i = 0; i < 16; i++) snapshots.push(await advance(15));
    const last = snapshots.at(-1);
    assert.ok(last.counters.areaFeedBlocked > 0); assert.ok(last.counters.sceneSeedsRecycled > 0);
    assert.equal(last.counters.recycledHotRemoved, 0);
    assert.ok(snapshots.every(s => s.particles.layerCounts.every(n => n <= 5)));
    await init({ spreadSceneFeed: false }); const disabled = await advance(60);
    assert.equal(disabled.counters.areaFeedCreditsGenerated, 0); assert.equal(disabled.counters.areaFeedAttempts, 0);
    assert.equal(disabled.particles.count, 0); return { snapshots, disabled };
  });
  if (session.errors.length) report.tests.push({ name: 'browser page errors', status: 'failed', error: session.errors.join('\n') });
} catch (e) { report.error = e.stack || String(e); console.error(report.error); }
finally {
  await session?.page.close(); await launched?.browser.close(); await server?.close();
  report.status = report.error || report.tests.some(t => t.status === 'failed') ? 'failed' : 'passed';
  await save(); console.log(`P2 smoke: ${out}`); if (report.status !== 'passed') process.exitCode = 1;
}
