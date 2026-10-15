import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { P3F, p3fConfig, qualityCasesP3f, regressionCasesP3f, timingCasesP3f, parseP3fArgs } from '../p3f-design.mjs';
import { curvatureScore, correctionHash, selectedIdsHash, partitionMembers, validateSelectionSummary, summarizeCorrectionSelection, selectionBudgetLock, correctionGate, correctionDecision } from '../lib/p3f-metrics.mjs';
import { timingPermission } from '../lib/p3e-metrics.mjs';

function modelFor(field, center = [0, 0, 0]) {
  const delta = P3F.params.eps * P3F.affine.deltaScale, positions = [[...center]];
  for (let a = 0; a < 3; a++) for (const sign of [1, -1]) { const p = [...center]; p[a] += sign * delta; positions.push(p); }
  return { id: 0, center, memberIds: [0, 1], radius: .1, stencil: positions.map(position => ({ position, raw: field(position) })), Ju: Array(9).fill(0), gradTb: [0, 0, 0] };
}
function selectionFixture() {
  const frame = 15, fieldTime = 14 / 60, raw = { ux: .2, uy: .1, uz: .03, Tb: .5, thermalWeight: 1 }, velocity = [.2, .1 + .9 * .5, .03];
  const inputs = [-.1, .1].map((x, id) => ({ id, position: [x, 0, 0], frame, fieldTime, age: 0, newborn: true }));
  const model = { ...modelFor(() => ({ ...raw })), diagonalHessian: Array(9).fill(0), score: 0, hashRank: correctionHash(frame, 0, P3F.correction.salt), selected: true };
  const summary = { frame, inputCount: 2, groupCount: 1, selectedGroupCount: 1, selectedMemberCount: 2, stencilQueries: 7, correctionQueries: 2, scoreEvaluations: 2, selectedGroupIds: [0], selectionIDHash: selectedIdsHash([0, 1]), scoreSum: 0, selectedScoreSum: 0 };
  const record = { frame, time: .25, fieldTime, params: { buoy: .9, wind: 0, turb: 0, sliceDepth: .7 }, inputs,
    selection: { summary, config: { method: 'curvature', ...P3F.correction }, delta: P3F.params.eps * .125, fieldTime, models: [model], rankedGroupIds: [0], selectedMemberIds: [0, 1], directQueries: inputs.map(p => ({ id: p.id, groupId: 0, position: p.position, raw, velocity })) } };
  const particles = inputs.map(p => ({ id: p.id, x: p.position[0] + P3F.dt * velocity[0], y: P3F.dt * velocity[1], z: P3F.dt * velocity[2], vx: velocity[0], vy: velocity[1], vz: velocity[2], life: P3F.dt }));
  return { record, particles };
}
function gateFixture() {
  const comparisons = P3F.pairs.flatMap(pair => ['curvature', 'hash'].map(method => ({ ...pair, method, candidate: `${method}-${pair.seed}`,
    accuracyCheck: { passed: method === 'curvature', maxPositionRmse: method === 'curvature' ? .003 : .006, maxPositionP99: method === 'curvature' ? .02 : .03, checks: { noUnmatchedIds: true } } })));
  return { comparisons, locks: P3F.pairs.map(p => ({ ...p, passed: true })) };
}

test('P3f fixes six new quality cases, one old affine replay, three baseline pins and conditional ten runs', () => {
  assert.equal(qualityCasesP3f().length, 6); assert.equal(regressionCasesP3f().length, 1); assert.equal(timingCasesP3f().length, 10);
  assert.deepEqual(qualityCasesP3f().map(c => [c.seed, c.renderSeed]), [[11, 101], [11, 101], [11, 101], [59, 409], [59, 409], [59, 409]]);
  assert.equal(p3fConfig(qualityCasesP3f()[4]).renderSeed, 409); assert.equal(p3fConfig(regressionCasesP3f()[0]).field.correction, undefined);
  assert.throws(() => parseP3fArgs(['--suite', 'timing']), /bypass/);
  const pin = JSON.parse(readFileSync(new URL('../lib/p3f-baseline.json', import.meta.url))); assert.equal(Object.keys(pin.files).length, 3); assert.equal(pin.archiveSha256, '8732952c34a9e4755ba92842ea9c19cf48fe2496cc319d56ac8aec38de1b53a4');
});
test('curvature heuristic detects diagonal quadratic curvature but explicitly misses mixed xy curvature', () => {
  const points = [{ position: [-1, 0, 0] }, { position: [1, 0, 0] }], delta = P3F.params.eps * .125;
  const diagonal = curvatureScore(modelFor(([x]) => ({ ux: x * x, uy: 0, uz: 0, Tb: 0 })), points, delta, .9);
  assert.equal(diagonal.diagonalHessian[0], 2); assert.equal(diagonal.score, 2);
  const mixed = curvatureScore(modelFor(([x, y]) => ({ ux: x * y, uy: 0, uz: 0, Tb: 0 })), points, delta, .9);
  assert.equal(mixed.score, 0); assert.deepEqual(mixed.diagonalHessian, Array(9).fill(0));
});
test('stable partition and fixed uint32 hash do not depend on input permutation', () => {
  const points = Array.from({ length: 8 }, (_, id) => ({ id, position: [id & 1 ? -1 : 1, id & 2 ? -1 : 1, id & 4 ? -1 : 1] }));
  const config = { maxGroups: 2, targetGroupSize: 4 };
  assert.deepEqual(partitionMembers(points, config), [[1, 3, 5, 7], [0, 2, 4, 6]]); assert.deepEqual(partitionMembers([...points].reverse(), config), partitionMembers(points, config));
  const h = correctionHash(15, 0, P3F.correction.salt); assert.ok(Number.isInteger(h) && h >= 0 && h <= 0xffffffff); assert.notEqual(h, correctionHash(16, 0, P3F.correction.salt));
});
test('fixed ceil of 10% of integer K gives the predeclared actual query budget', () => {
  let groups = 0, selected = 0; for (let frame = 1; frame <= 180; frame++) { const K = 3 * frame; groups += K; selected += Math.ceil(.1 * K); }
  assert.equal(groups, 48870); assert.equal(selected, 4968); assert.equal(7 * groups + 16 * selected, 421578);
  const { record } = selectionFixture(); assert.equal(validateSelectionSummary(record.selection.summary, record.selection.config, P3F.affine), true);
  record.selection.summary.scoreEvaluations = 1; assert.throws(() => validateSelectionSummary(record.selection.summary, record.selection.config, P3F.affine), /ledger/);
});
test('production observer reconstructs selection, direct force and Euler transport, preserving retired IDs', () => {
  const { record, particles } = selectionFixture(), result = summarizeCorrectionSelection(record, particles, P3F);
  assert.equal(result.correctionQueries, 2); assert.equal(result.maximumVelocityReconstructionError, 0);
  const retired = summarizeCorrectionSelection(record, particles.slice(0, 1), P3F); assert.deepEqual(retired.retiredIds, [1]);
  for (const mutate of [r => { r.selection.models[0].score = 1; }, r => { r.selection.directQueries[0].raw.ux = null; }, r => r.selection.selectedMemberIds.pop(), r => { r.selection.models[0].hashRank++; }]) {
    const f = selectionFixture(); mutate(f.record); assert.throws(() => summarizeCorrectionSelection(f.record, f.particles, P3F));
  }
});
test('equal-budget claim fails on retirement or different actual selected member work', () => {
  const s = { frame: 1, inputCount: 48, groupCount: 3, selectedGroupCount: 1, selectedMemberCount: 16, stencilQueries: 21, correctionQueries: 16 };
  const caseOf = id => ({ definition: { id }, selectionTrace: [{ ...s }], snapshots: [{ counters: { tracerRetired: 0 } }] });
  const a = caseOf('curvature'), b = caseOf('hash'), dd = caseOf('DD'); assert.equal(selectionBudgetLock(a, b, dd, 1).passed, true);
  b.selectionTrace[0].selectedMemberCount--; assert.equal(selectionBudgetLock(a, b, dd, 1).passed, false); b.selectionTrace[0] = { ...s }; b.snapshots[0].counters.tracerRetired = 1; assert.equal(selectionBudgetLock(a, b, dd, 1).passed, false);
});
test('both seed pairs must independently improve both worst-checkpoint metrics; equality and null fail', () => {
  const f = gateFixture(); assert.equal(correctionGate(f.comparisons, f.locks, P3F.pairs).passed, true);
  f.comparisons[3].accuracyCheck.maxPositionP99 = .02; assert.equal(correctionGate(f.comparisons, f.locks, P3F.pairs).passed, false);
  f.comparisons[3].accuracyCheck.maxPositionP99 = null; assert.equal(correctionGate(f.comparisons, f.locks, P3F.pairs).passed, false);
});
test('absolute accuracy stays distinct from selector success and a valid selector STOP never triggers timing', () => {
  const f = gateFixture(); f.comparisons[1].accuracyCheck.maxPositionRmse = .003;
  const gate = correctionGate(f.comparisons, f.locks, P3F.pairs), d = correctionDecision([], gate, true, P3F.decision);
  assert.equal(d.accuracyPassed, true); assert.equal(d.selectionPassed, false); assert.equal(d.engineeringGo, false);
  assert.equal(timingPermission({ suite: 'all', executionValid: true, qualityGate: gate }).stageStatus, 'stopped_after_quality');
  assert.equal(timingPermission({ suite: 'quick', executionValid: true, qualityGate: { passed: true } }).run, false);
});
