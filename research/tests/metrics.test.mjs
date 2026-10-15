import test from 'node:test';
import assert from 'node:assert/strict';
import { measure, classify, timeseriesCsv, assertSnapshot } from '../lib/metrics.mjs';

const f = { points: [{ id: 'a', group: 'target', analysisWeight: .5, anchor: true }, { id: 'b', group: 'target', analysisWeight: .5, anchor: false }] };
const snapshot = () => ({ time: 1, frame: 60, hash: 'h', scene: { burnHash: 'b' }, particles: { count: 0 }, counters: { sceneSeedsEmitted: 0 },
  points: f.points.map(p => ({ id: p.id, group: p.group, state: 0, fuel: 1, fuelInitial: 1, heat: 0, char: 0 })) });

test('metrics retain individual states, weights and sampled ignition times', () => {
  const s = snapshot(); s.points[0].state = 1; s.points[0].fuel = .5; s.points[0].char = .5;
  const times = new Map(), m = measure(s, f, times);
  assert.equal(m.groups.target.ignitedFraction, .5); assert.equal(m.groups.target.meanChar, .25);
  assert.equal(m.groups.target.meanFuelConsumed, .25); assert.equal(m.groups.target.anchors.length, 1);
  assert.equal(times.get('a'), 1); assert.match(timeseriesCsv([m]), /counters.sceneSeedsEmitted/);
});

test('zero exposure remains an explicit diagnostic limitation', () => {
  const m = measure(snapshot(), f, new Map());
  assert.equal(classify([m], 'raised-target').outcome, 'no_target_exposure_observed');
  m.groups.target.heatMax = .1;
  assert.equal(classify([m], 'raised-target').outcome, 'exposed_without_ignition');
});

test('invalid data never becomes a silent zero result', () => {
  const s = snapshot(); s.points[0].heat = NaN;
  assert.throws(() => assertSnapshot(s), /Non-finite/);
  assert.throws(() => assertSnapshot({}), /Missing/);
  const wrong = snapshot(); wrong.points[1].id = 'a'; assert.throws(() => assertSnapshot(wrong), /Duplicate/);
});
