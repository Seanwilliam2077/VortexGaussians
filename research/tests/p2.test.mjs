import test from 'node:test';
import assert from 'node:assert/strict';
import { p2Fixture } from '../p2-fixtures.mjs';
import { p2Cases, configureP2, compareP2, refinementCurveError } from '../p2-design.mjs';
import { parseArgs } from '../lib/design.mjs';

const close = (a, b, tolerance = 1e-12) => assert.ok(Math.abs(a - b) <= tolerance, `${a} != ${b}`);

test('P2 cell-centred refinements partition fixed area and retain every coarse anchor', () => {
  const base = p2Fixture(), anchors = new Map(base.points.map(p => [p.id, p.position]));
  for (const [variant, count] of [['base', 105], ['refine3', 945], ['refine5', 2625], ['adaptive', 545]]) {
    const f = p2Fixture('surface', variant); assert.equal(f.points.length, count);
    close(f.representedArea, .168); close(f.groupAreas.source, .016); close(f.groupAreas.target, .152);
    assert.equal(f.commonAnchorIds.length, 105);
    for (const p of f.points.filter(p => p.anchor)) assert.deepEqual(p.position, anchors.get(p.id));
    assert.ok(f.points.every(p => p.areaWeight > 0 && (p.group === 'source') === (p.position[0] < .06)));
    const cells = new Map();
    for (const p of f.points) cells.set(p.cell.join(':'), (cells.get(p.cell.join(':')) || 0) + p.areaWeight);
    assert.equal(cells.size, 105); for (const area of cells.values()) close(area, .0016);
  }
});

test('uniform and spatially variable splitting preserve per-position authored area', () => {
  for (const kind of ['surface', 'raised-target']) {
    const areas = f => { const result = new Map(); for (const p of f.points) result.set(p.position.join(','), (result.get(p.position.join(',')) || 0) + p.areaWeight); return result; };
    const base = p2Fixture(kind), reference = areas(base);
    for (const variant of ['uniform2', 'uniform4', 'variable-both', 'variable-source', 'variable-target']) {
      const f = p2Fixture(kind, variant, 'shuffle'), weighted = areas(f);
      close(f.representedArea, base.representedArea); assert.equal(weighted.size, reference.size);
      for (const [position, value] of weighted) close(value, reference.get(position));
      assert.deepEqual(f.commonAnchorIds, base.commonAnchorIds);
      assert.equal(new Set(f.points.map(p => p.id)).size, f.points.length);
      assert.ok(f.points.every(p => p.fuel === 1));
    }
  }
});

test('P2 matrix has 56 frozen comparisons and correct public suite aliases', () => {
  const cases = p2Cases('all'); assert.equal(cases.length, 56);
  assert.equal(cases.filter(c => c.family === 'graph-duplicate').length, 24);
  assert.equal(cases.filter(c => c.family === 'refinement').length, 8);
  assert.equal(cases.filter(c => c.family === 'closed-loop').length, 24);
  assert.equal(p2Cases('graph-duplicates').length, 24); assert.equal(p2Cases('feedback').length, 24);
  assert.ok(cases.every(c => c.params.spreadClockMode === 'elapsed' && c.params.ppl === 1200 && c.params.spreadFrontierCap === 1000000));
  assert.ok(cases.filter(c => c.family !== 'closed-loop').every(c => !c.params.spreadFlameHeat && !c.params.spreadSceneFeed));
  assert.equal(new Set(cases.map(c => c.id)).size, cases.length);
  assert.throws(() => configureP2(parseArgs([]), { params: { spreadAreaFeedRate: 40 } }), /frozen/);
});

test('refinement curve metric compares area-weighted ignition in fixed 0..6 window', () => {
  const result = { definition: { id: 'coarse' }, samples: Array.from({ length: 25 }, (_, i) => ({ time: i * .25, groups: { target: { ignitedFraction: i / 24 } } })) };
  const finest = { definition: { id: 'finest' }, samples: result.samples.map(s => ({ ...s, groups: { target: { ignitedFraction: 1 } } })) };
  const error = refinementCurveError(result, finest);
  assert.equal(error.completeStandardWindow, true); close(error.meanAbsoluteWeightedIgnitionCurveError, .5);
  assert.equal(error.checkpoints.length, 25);
});

test('duplicate comparison checks intermediate states, particle hashes and weighted totals', () => {
  const make = () => ({ definition: { id: 'case', family: 'graph-duplicate' }, fixture: { representedArea: .1, commonAnchorIds: ['x'] }, firstIgnition: { x: .25 },
    raw: [0, .25].map(time => ({ time, particleStateHash: 'abc', randomDraws: 3, points: [{ id: 'x', heat: time, fuel: 1, char: 0, state: +(time > 0) }],
      scene: { representedArea: .1, areaWeightedFuelRemaining: .1, areaWeightedHeat: 0, areaWeightedChar: 0 },
      counters: { areaFeedAttempts: 0, areaFeedAdmitted: 0, areaFeedBlocked: 0, areaFeedServiceCapDropped: 0,
        areaWeightedFlameHeatDeposited: 0, areaWeightedGraphHeatDeposited: 0, areaWeightedFuelConsumed: 0 } })) });
  const reference = make(), candidate = make();
  assert.equal(compareP2(candidate, reference).duplicateStateCriterionSatisfied, true);
  candidate.raw[0].points[0].heat += .01; candidate.raw[0].particleStateHash = 'different';
  candidate.raw[0].scene.areaWeightedHeat = .1;
  const c = compareP2(candidate, reference);
  assert.equal(c.duplicateStateCriterionSatisfied, false); assert.equal(c.particleStateHashMismatches, 1);
  assert.equal(c.weightedTotalCriterionSatisfied, false);
  candidate.definition.family = 'refinement'; assert.equal(compareP2(candidate, reference).duplicateStateCriterionSatisfied, null);
});
