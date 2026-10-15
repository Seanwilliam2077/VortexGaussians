import test from 'node:test';
import assert from 'node:assert/strict';
import { fixture, graphDescription } from '../lib/fixtures.mjs';

test('raised target has exactly nine initial source sites and no graph bridge', () => {
  const f = fixture('raised-target');
  assert.equal(f.points.length, 36);
  const inside = f.points.filter(p => Math.hypot(...p.position.map((v, k) => v - f.ignition.position[k])) <= f.ignition.radius);
  assert.equal(inside.length, 9); assert.ok(inside.every(p => p.group === 'source'));
  assert.equal(f.graph.components, 2);
  assert.equal(graphDescription(f.points, .3).components, 1);
});

test('cap stress exercises real 1400 budget without graph neighbors', () => {
  const f = fixture('cap-stress');
  assert.equal(f.points.length, 1681); assert.ok(f.points.length > 1400);
  assert.equal(f.graph.maxDegree, 0); assert.equal(f.graph.components, 1681);
  assert.ok(f.points.every(p => Math.hypot(...p.position.map((v, k) => v - f.ignition.position[k])) <= f.ignition.radius));
});

test('density maps retain common anchors/geometry and normalize analysis only', () => {
  const base = fixture('surface-strip'), dense = fixture('surface-strip', { density: 4 });
  assert.equal(dense.points.length, base.points.length * 4);
  assert.deepEqual(dense.points.filter(p => p.anchor).map(p => [p.id, p.position]), base.points.map(p => [p.id, p.position]));
  const sum = f => f.points.reduce((a, p) => a + p.analysisWeight, 0);
  assert.ok(Math.abs(sum(base) - sum(dense)) < 1e-10);
  assert.ok(dense.points.every(p => p.fuel === 1));
  assert.equal(new Set(dense.points.map(p => p.id)).size, dense.points.length);
});

test('permutations preserve stable IDs and deterministic shuffled geometry', () => {
  const forward = fixture('surface-strip'), reverse = fixture('surface-strip', { order: 'reverse' });
  assert.deepEqual(forward.points, [...reverse.points].reverse());
  assert.deepEqual(fixture('surface-strip', { order: 'shuffle' }).points, fixture('surface-strip', { order: 'shuffle' }).points);
  assert.notDeepEqual(forward.points, fixture('surface-strip', { order: 'shuffle' }).points);
});
