import test from 'node:test';
import assert from 'node:assert/strict';
import { p1Cases, configureP1, p1Metrics } from '../p1-design.mjs';
import { parseArgs } from '../lib/design.mjs';

test('P1 matrix isolates clock and lifecycle before combined settings', () => {
  const cases = p1Cases('all'); assert.equal(cases.length, 53);
  assert.equal(cases.filter(c => c.family === 'clock').length, 16);
  assert.equal(cases.filter(c => c.family === 'connected-clock').length, 4);
  assert.equal(cases.filter(c => c.family === 'lifetime').length, 18);
  assert.equal(cases.filter(c => c.family === 'combined').length, 12);
  assert.equal(cases.filter(c => c.family === 'method-control').length, 3);
  assert.ok(cases.filter(c => c.family === 'connected-clock').every(c => c.frames === 720));
  assert.ok(cases.filter(c => c.family === 'clock').every(c => !c.params.spreadSceneFeed && !c.params.spreadFlameHeat));
  assert.ok(cases.filter(c => c.family === 'lifetime').every(c => c.params.spreadClockMode === 'legacy'));
  assert.ok(cases.every(c => !c.params.emitterOn && !c.params.embers && c.params.sliceMode === 'world'));
  assert.equal(new Set(cases.map(c => c.id)).size, cases.length);
});

test('P1 duration overrides are explicit and matrix parameters are frozen', () => {
  assert.ok(configureP1(parseArgs(['--seconds', '2', '--dt', '.1']), { frames: 999 }).every(c => c.frames === 20));
  assert.throws(() => configureP1(parseArgs([]), { params: { spreadRecycleMinAge: .1 } }), /frozen/);
  assert.throws(() => p1Cases('all', [1, 1]), /distinct/);
});

test('P1 hot integral excludes uncertain burnout intervals and reports sampled nulls', () => {
  const s = (time, burning, hotCount) => ({ time, scene: { count: 1, burning, charred: +!burning }, particles: { hotCount },
    counters: { sceneFeedAttempts: 4, sceneSeedsEmitted: 2, sceneSeedsRecycled: 1, recycledDensitySum: .3 }, groups: {} });
  const result = { definition: { dt: 1 / 60, sampleEvery: 15 }, fixture: { points: [{ id: 't', group: 'target' }] },
    firstIgnition: {}, samples: [s(0, 1, 0), s(.25, 1, 4), s(.5, 0, 10)] };
  const m = p1Metrics(result);
  assert.equal(m.hotParticleSecondsWhileBurning, .5); assert.equal(m.sampledBurningDuration, .25);
  assert.equal(m.hotFreeSampleFractionWhileBurning, .5); assert.equal(m.firstTargetIgnition, null);
  assert.equal(m.admissionFraction, .5); assert.equal(m.recyclingLossProxies.recycledDensitySum, .3);
});

test('predeclared 3..6 window retains all thirteen counts and conditions on burning', () => {
  const samples = Array.from({ length: 13 }, (_, i) => ({ time: 3 + i * .25,
    scene: { count: 1, burning: +(i < 12), charred: +(i >= 12) }, particles: { count: 20, hotCount: +(i < 6) },
    counters: { sceneFeedAttempts: 20, sceneSeedsEmitted: 10 }, groups: {} }));
  const m = p1Metrics({ samples, definition: { dt: 1 / 60, sampleEvery: 15 }, fixture: { points: [] }, firstIgnition: {} });
  assert.equal(m.predeclaredWindow3to6.sampleCount, 13);
  assert.equal(m.predeclaredWindow3to6.checkpoints.length, 13);
  assert.equal(m.predeclaredWindow3to6.hotCoverageConditionalOnBurning, .5);
  assert.equal(m.predeclaredWindow3to6.burningWithHotFractionOfAllCheckpoints, 6 / 13);
});
