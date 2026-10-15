import test from 'node:test';
import assert from 'node:assert/strict';
import { P3C, casesP3c, p3cConfig, parseP3cArgs } from '../p3c-design.mjs';
import { ageBin, directionalPaths, poolDirectional, interactionPaths, poolInteraction, summarizeInputs } from '../lib/p3c-metrics.mjs';
import { validateComponentLedger, requireCompleteCase } from '../p3c-run.mjs';

const p = (id = 0, xyz = [0, 0, 0], life = .5) => ({ id, x: xyz[0], y: xyz[1], z: xyz[2], vx: 0, vy: 0, vz: 0, T: .8, d: .7, life });
test('P3c freezes 36 diagnostic arms without performance or new heldout claims', () => {
  const cases = casesP3c(); assert.equal(cases.length, 36); assert.equal(new Set(cases.map(c => c.id)).size, 36);
  assert.equal(casesP3c('pilot').length, 4); assert.throws(() => casesP3c('timing'), /no performance/);
  const modes = cases.slice(0, 4).map(c => p3cConfig(c).field);
  assert.deepEqual(modes.map(m => [m.mode, m.components]), [['tree', 'both'], ['grid', 'velocity'], ['grid', 'temperature'], ['grid', 'both']]);
  assert.ok(modes.every(m => m.cellSize === .035)); assert.throws(() => parseP3cArgs(['--cell-size', '.1']), /Unknown/);
});
test('step-rounded ages consistently classify floating boundaries and reject fractional steps', () => {
  for (const life of [.5 - 1e-15, .5, .5 + 1e-15]) assert.equal(ageBin(life, P3C), '.5-1');
  assert.equal(ageBin(1, P3C), '1-2'); assert.equal(ageBin(2, P3C), '2+');
  assert.throws(() => ageBin(.501, P3C), /integer/); assert.throws(() => ageBin(NaN, P3C), /integer/);
  const d = directionalPaths([p()], [p()], P3C); assert.equal(d.ageBins['2+'].positionRmse, null);
});
test('signed vertical bias and xz RMSE pair by ID with explicit lost and visual-state IDs', () => {
  const m = directionalPaths([p(1, [3, -2, 4]), p(0, [0, 2, 0])], [p(0), p(1)], P3C);
  assert.equal(m.directional.ySignedBias, 0); assert.equal(m.directional.yRmse, 2); assert.equal(m.directional.xzRmse, Math.sqrt(12.5));
  assert.equal(m.directional.positionSquared, 33);
  const lost = directionalPaths([{ ...p(0), T: .9 }], [p(0), p(1)], P3C);
  assert.deepEqual(lost.onlyReference, [1]); assert.deepEqual(lost.visualStateMismatchIds, [0]);
});
test('pooled directional errors sum squared vectors and counts rather than average checkpoint RMSEs', () => {
  const a = directionalPaths([p(0, [3, 0, 0])], [p(0)], P3C);
  const b = directionalPaths([p(0), p(1), p(2)], [p(0), p(1), p(2)], P3C);
  const pooled = poolDirectional([a, b], P3C); assert.equal(pooled.directional.count, 4); assert.equal(pooled.directional.positionRmse, 1.5);
});
test('vector interaction handles orthogonal additivity, cancellation and zero GG denominator', () => {
  const a = interactionPaths({ DD: [p()], GD: [p(0, [1, 0, 0])], DG: [p(0, [0, 1, 0])], GG: [p(0, [1, 1, 0])] });
  assert.equal(a.interactionSquared, 0); assert.equal(a.gdOverGg, Math.SQRT1_2);
  const b = interactionPaths({ DD: [p()], GD: [p(0, [1, 0, 0])], DG: [p(0, [-1, 0, 0])], GG: [p()] });
  assert.equal(b.interactionRmse, 0); assert.equal(b.gdOverGg, null);
  const pooled = poolInteraction([a, b]); assert.equal(pooled.count, 2); assert.equal(pooled.ggRmse, 1);
});
test('four-arm interaction exposes union/exclusions and refuses appearance changes or duplicate IDs', () => {
  const a = interactionPaths({ DD: [p(0), p(1)], GD: [p(1)], DG: [p(0), p(1)], GG: [p(1), p(2)] });
  assert.equal(a.unionCount, 3); assert.equal(a.excludedCount, 2); assert.equal(a.count, 1); assert.deepEqual(a.missingByArm.DD, [2]);
  assert.throws(() => interactionPaths({ DD: [p()], GD: [{ ...p(), d: 1 }], DG: [p()], GG: [p()] }), /visual/);
  assert.throws(() => interactionPaths({ DD: [p(), p()], GD: [], DG: [], GG: [] }), /Duplicate/);
});
test('actual-input summaries use tolerant six-way support groups, signed Tb and empty-bin nulls', () => {
  const sample = supportFraction => ({ position: [0, 0, 0], tree: { thermalWeight: 1, Tb: 1 }, grid: { supportFraction, Tb: .5 },
    errors: { inducedVelocitySquared: .01, temperatureSquared: .25 }, transportVelocities: { DD: [0, 1, 0], GD: [.1, 1, 0], DG: [0, .5, 0], GG: [.1, .5, 0] },
    combinations: Object.fromEntries(['DD', 'GD', 'DG', 'GG'].map(a => [a, { speedClamped: false, preClampVelocity: [0, 0, 0], inducedVelocity: [0, 0, 0], velocity: [0, 0, 0], Tb: 0, preClampSpeed: 0 }])) });
  const c = { frame: 15, time: .25, inputs: [0, 97, 194].map(id => ({ id, position: [0, 0, 0], age: 0, newborn: true, frame: 15, fieldTime: 14 / 60 })),
    probe: { fieldTime: 14 / 60, samples: [sample(0), sample(.5), sample(1 - 1e-15)] } };
  const m = summarizeInputs([c], P3C)[0]; assert.equal(m.count, 3); assert.equal(m.tbSignedBias, -.5);
  assert.equal(m.directSupportButPartialGrid, 1); assert.equal(m.supportGroups['supported-full'].count, 1);
  assert.equal(m.supportGroups['unsupported-full'].tbRmse, null); assert.equal(m.ageBins['2+'].gdVelocityRmse, null);
  assert.equal(m.interactionSquared, 0);
  const bad = structuredClone(c); bad.probe.samples[0].combinations.GD.preClampVelocity[0] = null;
  assert.throws(() => summarizeInputs([bad], P3C), /Nonfinite/);
  c.inputs[0].position[0] = 1; assert.throws(() => summarizeInputs([c], P3C), /exact captured/);
});
test('hybrid ledger includes direct component work and evidence completeness rejects missing checkpoints', () => {
  const c = { fieldQueries: 9, cacheNodeQueries: 8, cacheFallbacks: 0, componentDirectQueries: 1,
    cacheHits: 0, cacheMisses: 8, cacheStencilLookups: 8, tracerFieldQueries: 1, cacheOutsideQueries: 0, cacheCapacityFallbacks: 0 };
  assert.doesNotThrow(() => validateComponentLedger({ mode: 'grid', components: 'velocity' }, c));
  assert.throws(() => validateComponentLedger({ mode: 'grid', components: 'velocity' }, { ...c, fieldQueries: 8 }), /accounting/);
  const d = casesP3c('quick')[1], r = { definition: d, trace: Array.from({ length: 16 }, (_, frame) => ({ frame })), checkpoints: [{ frame: 0 }, { frame: 15 }], captures: P3C.views.map(view => ({ frame: 15, view })) };
  assert.equal(requireCompleteCase(r), true); r.checkpoints.pop(); assert.throws(() => requireCompleteCase(r), /checkpoints/);
});
