import test from 'node:test';
import assert from 'node:assert/strict';
import { P3B, qualityCasesP3b, timingCasesP3b, p3bConfig, parseP3bArgs } from '../p3b-design.mjs';
import { encodeParticles, decodeParticles, pairedParticles, pairedImageError, poolPairedImages, approximationGate, aggregateTiming, selectCache } from '../lib/p3b-metrics.mjs';
import { requirePairedTrace } from '../p3b-run.mjs';

const particle = (id, x = 0) => ({ id, x, y: .2, z: 0, vx: 0, vy: 1, vz: 0, T: .75, d: .5, life: 1 });
const image = data => ({ width: data.length / 4, height: 1, data, orientation: 'bottom-left' });
function validComparison(d = {}) {
  return { scenario: 'stationary', seed: 11, renderSeed: 101, method: 'grid035', ...d,
    paths: P3B.selection.expectedSampleFrames.map(frame => ({ frame, positionRmse: .001, positionP99: .005, onlyCandidate: [], onlyReference: [], visualStateMismatchIds: [] })),
    images: P3B.captures.flatMap(frame => P3B.views.map(view => ({ frame, view }))),
    pooled: { foreground: { rgbNrmse: .01, alphaNrmse: .01 } }, cacheFallbacks: 0, capacityBlocks: 0, physicsAndBirthRngMatched: true };
}

test('P3b uses three paired RNG seeds and immutable development/heldout conditions', () => {
  const q = qualityCasesP3b(), t = timingCasesP3b(); assert.equal(q.length, 36); assert.equal(t.length, 60);
  assert.equal(q.filter(d => d.role === 'selection').length, 4); assert.equal(new Set(q.map(d => d.id)).size, 36);
  assert.equal(new Set(q.map(d => `${d.seed}/${d.renderSeed}`)).size, 3);
  assert.deepEqual(P3B.methods.filter(m => m.mode === 'grid').map(m => m.cellSize), [.035, .07, .14]);
  assert.equal(P3B.probePositions.length, 48);
  for (const d of q) { const c = p3bConfig(d); assert.equal(c.nRender, 9600); assert.equal(c.nSim, 600); assert.equal(c.params.eps, .07); }
  assert.throws(() => parseP3bArgs(['--cell-size', '.001']), /Unknown/);
});

test('particle binary preserves double precision and stable birth IDs, rejecting corruption', () => {
  const p = [particle(17, .123456789012345), particle(3, -.2)], e = encodeParticles(p);
  assert.deepEqual(decodeParticles(e.bytes, e), p);
  const bytes = Buffer.from(e.bytes); bytes[0] ^= 1; assert.throws(() => decodeParticles(bytes, e), /checksum/);
  assert.throws(() => encodeParticles([particle(1), particle(1)]), /duplicate/);
  assert.throws(() => encodeParticles([{ ...particle(1), vx: NaN }]), /Nonfinite/);
});

test('path comparison pairs by birth ID across permutation/culling and checks unchanged appearance evolution', () => {
  const a = [particle(2, .01), particle(1)], b = [particle(1), particle(2)];
  const m = pairedParticles(a, b); assert.equal(m.matched, 2); assert.equal(m.positionSquaredError, .0001);
  assert.deepEqual(m.onlyCandidate, []); assert.deepEqual(m.visualStateMismatchIds, []);
  const culled = pairedParticles([{ ...particle(2), T: .8 }, particle(3)], b);
  assert.deepEqual(culled.onlyCandidate, [3]); assert.deepEqual(culled.onlyReference, [1]); assert.deepEqual(culled.visualStateMismatchIds, [2]);
});

test('paired foreground NRMSE uses tree signal energy with pooled SSE, not average per-image ratios', () => {
  const mask = { foregroundMask: Uint8Array.of(1), holeMask: Uint8Array.of(1) };
  const e = pairedImageError(image([.9, .9, .9, .45]), image([1, 1, 1, .5]), mask, P3B.image);
  assert.ok(Math.abs(e.foreground.rgbNrmse - .1) < 1e-12); assert.ok(Math.abs(e.foreground.alphaNrmse - .1) < 1e-12);
  const zero = pairedImageError(image([0, 0, 0, 0]), image([0, 0, 0, 0]), mask, P3B.image);
  assert.equal(zero.foreground.rgbNrmse, null); assert.equal(poolPairedImages([e, zero]).foreground.rgbNrmse, e.foreground.rgbNrmse);
});

test('approximation gate rejects missing checkpoints, late drift, image holes in evidence, culling and visual changes', () => {
  const c = validComparison(); assert.equal(approximationGate(c, P3B.selection).passed, true);
  for (const mutate of [x => x.paths.pop(), x => x.images.pop(), x => { x.paths.at(-1).positionRmse = .008; },
    x => { x.paths.at(-1).positionP99 = .04; }, x => x.paths[0].onlyReference.push(1),
    x => x.paths[0].visualStateMismatchIds.push(1), x => { x.cacheFallbacks = 1; }]) {
    const invalid = validComparison(); mutate(invalid); assert.equal(approximationGate(invalid, P3B.selection).passed, false);
  }
});

test('timing aggregation uses independent run medians/tails and refuses incomplete repeats', () => {
  const runs = [1, 2, 3, 4, 100].map((v, repeat) => ({ status: 'passed', definition: { scenario: 'stationary', method: 'tree', repeat },
    timings: Array(41).fill({}), distributions: { totalMs: { median: v, p95: v * 2 } } }));
  const summary = aggregateTiming(runs, [{ id: 'stationary' }], [{ id: 'tree' }])[0];
  assert.equal(summary.centralMs, 3); assert.equal(summary.tailMs, 6); assert.equal(summary.worstRunP95Ms, 200);
  assert.equal(aggregateTiming(runs.slice(1), [{ id: 'stationary' }], [{ id: 'tree' }])[0].complete, false);
});

test('heldout failure cannot change development-selected cache and instead rejects the route', () => {
  const comparisons = qualityCasesP3b().filter(d => d.method !== 'tree').map(d => {
    const c = validComparison(d); c.candidate = d.id; c.errorGate = { passed: true }; return c;
  });
  const times = P3B.scenarios.flatMap(s => P3B.methods.map((m, i) => ({ scenario: s.id, method: m.id, complete: true, centralMs: i ? 4 - i : 10, tailMs: i ? 5 - i : 12 })));
  const first = selectCache(comparisons, times, P3B.selection, P3B.scenarios, P3B.methods);
  assert.equal(first.selected, 'grid140'); assert.equal(first.routeGo, true);
  comparisons.find(c => c.scenario === 'curl' && c.method === 'grid140').errorGate.passed = false;
  const after = selectCache(comparisons, times, P3B.selection, P3B.scenarios, P3B.methods);
  assert.equal(after.selected, 'grid140'); assert.equal(after.routeGo, false);
  const incomplete = comparisons.filter(c => !(c.scenario === 'stationary' && c.seed === 11 && c.method === 'grid035'));
  assert.equal(selectCache(incomplete, times, P3B.selection, P3B.scenarios, P3B.methods).selected, null);
});

test('paired trajectory hard lock rejects RNG drift even when physical hash remains equal', () => {
  assert.throws(() => requirePairedTrace([{ physicalHash: 'a', renderRng: 1 }], [{ physicalHash: 'a', renderRng: 2 }]), /step 0/);
});
