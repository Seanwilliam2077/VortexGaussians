import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { P3G, p3gConfig, qualityCasesP3g, timingCasesP3g, parseP3gArgs } from '../p3g-design.mjs';
import { cacheHash, summarizeMemoryEvents, evaluateUnclipped, memoryGate, memoryDecision } from '../lib/p3g-metrics.mjs';
import { selectedIdsHash } from '../lib/p3f-metrics.mjs';
import { timingPermission } from '../lib/p3e-metrics.mjs';

function stats(rs) { const s = { uSquaredSum: 0, TbSquaredSum: 0, uNormMax: 0, TbAbsMax: 0, signedTbSum: 0 }; for (const r of rs) { const u = r[0] ** 2 + r[1] ** 2 + r[2] ** 2; s.uSquaredSum += u; s.TbSquaredSum += r[3] ** 2; s.uNormMax = Math.max(s.uNormMax, Math.sqrt(u)); s.TbAbsMax = Math.max(s.TbAbsMax, Math.abs(r[3])); s.signedTbSum += r[3]; } return s; }
function eventFixture(frame, before, selected, live = [0, 1], baseTb = .5, directTb = .75) {
  const base = { ux: .125, uy: .25, uz: 0, TbRaw: baseTb }, direct = { ux: .375, uy: .25, uz: 0, Tb: directTb, thermalWeight: 1 }, delta = P3G.params.eps * .125;
  const beforeIds = before.map(p => p.id), usedIds = beforeIds.filter(id => live.includes(id) && !selected.includes(id)), overlap = beforeIds.filter(id => selected.includes(id)), missing = beforeIds.filter(id => !live.includes(id));
  const modelIds = [...new Set([...selected, ...usedIds])].sort((a, b) => a - b);
  const models = modelIds.map(id => {
    const center = [id * .1, 0, 0], positions = [[...center]]; for (let a = 0; a < 3; a++) for (const sign of [1, -1]) { const p = [...center]; p[a] += sign * delta; positions.push(p); }
    return { id, center, memberIds: [id], radius: 0, Ju: Array(9).fill(0), gradTb: [0, 0, 0], stencil: positions.map(position => ({ position, raw: { ux: base.ux, uy: base.uy, uz: base.uz, Tb: baseTb, thermalWeight: 1 } })) };
  });
  const created = selected.map(id => ({ id, groupId: id, position: [id * .1, 0, 0], age: (frame - 1) / 60, newborn: frame === 1, affineRaw: { ...base }, directRaw: { ...direct }, residual: [.25, 0, 0, directTb - baseTb] }));
  const used = usedIds.map(id => { const old = before.find(p => p.id === id), raw = { ux: base.ux + old.residual[0], uy: base.uy + old.residual[1], uz: base.uz + old.residual[2], TbRaw: baseTb + old.residual[3] }; raw.Tb = Math.max(0, Math.min(1.6, raw.TbRaw)); return { id, groupId: id, creatorFrame: old.frame, position: [id * .1, 0, 0], age: (frame - 1) / 60, newborn: false, affineRaw: { ...base }, storedResidual: [...old.residual], finalRaw: raw, velocity: [raw.ux, raw.uy + .9 * raw.Tb, raw.uz] }; });
  const after = created.map(p => ({ id: p.id, frame, residual: p.residual }));
  const summary = { frame, inputCount: live.length, unselectedMembers: live.length - selected.length, newSelectedMembers: selected.length - overlap.length, previousMembers: before.length, previousLiveMembers: before.length - missing.length,
    overlappingMembers: overlap.length, expiredMissingMembers: missing.length, savedMembers: after.length, reusedMembers: used.length, modelEvaluations: after.length,
    previousIDHash: selectedIdsHash(beforeIds), savedIDHash: selectedIdsHash(selected), reusedIDHash: selectedIdsHash(usedIds), overlappingIDHash: selectedIdsHash(overlap), createdResidual: stats(created.map(p => p.residual)), reusedResidual: stats(used.map(p => p.storedResidual)),
    finalTbClippedLow: used.filter(p => p.finalRaw.TbRaw < 0).length, finalTbClippedHigh: used.filter(p => p.finalRaw.TbRaw > 1.6).length, speedClamped: 0 };
  return { frame, time: frame / 60, fieldTime: (frame - 1) / 60, params: { wind: 0, turb: 0, buoy: .9, sliceDepth: .7 }, events: { frame, fieldTime: (frame - 1) / 60, config: { ttl: 1 }, inputIds: live, cacheBefore: before, cacheAfter: after, models, created, used, overlappingIds: overlap, expiredMissingIds: missing, summary } };
}
function gates() {
  return { comparisons: P3G.pairs.flatMap(pair => ['curvature', 'memory'].map(method => ({ ...pair, method, candidate: `${method}-${pair.seed}`, accuracyCheck: { passed: method === 'memory', checks: { noUnmatchedIds: true }, maxPositionRmse: method === 'memory' ? .003 : .006, maxPositionP99: method === 'memory' ? .015 : .03 } }))),
    locks: P3G.pairs.map(p => ({ ...p, passed: true })), exposure: P3G.pairs.map(p => ({ ...p, usedCount: 1 })) };
}

test('P3g fixes six quality trajectories, TTL1, new seed pair and ten conditional runs without a bypass', () => {
  const cases = qualityCasesP3g(); assert.equal(cases.length, 6); assert.equal(timingCasesP3g().length, 10); assert.deepEqual(cases.map(c => c.method), ['DD', 'curvature', 'memory', 'DD', 'curvature', 'memory']);
  assert.equal(p3gConfig(cases[5]).renderSeed, 521); assert.deepEqual(p3gConfig(cases[2]).field.correction.memory, { ttl: 1 }); assert.equal(p3gConfig(cases[1]).field.correction.memory, undefined);
  assert.throws(() => parseP3gArgs(['--suite', 'timing']), /bypass/); const pin = JSON.parse(readFileSync(new URL('../lib/p3g-baseline.json', import.meta.url))); assert.equal(Object.keys(pin.files).length, 3); assert.equal(pin.archiveSha256, '7fb3e177b5709ea0eecafd94d087752c6252c8879475ab602d4ae1430566d49e');
});
test('cache hash uses exact Float64 little endian values with zero canonicalization', () => {
  const cache = [{ id: 3, frame: 1, residual: [.1, -0, 0, 1.6] }], encoded = [{ id: 3, frame: 1, residualF64LE: ['9a9999999999b93f', '0000000000000000', '0000000000000000', '9a9999999999f93f'] }];
  assert.equal(cacheHash(cache), selectedIdsHash(encoded)); assert.equal(cacheHash(cache), cacheHash(JSON.parse(JSON.stringify(cache)))); const changed = structuredClone(cache); changed[0].residual[0] = Math.fround(.1); assert.notEqual(cacheHash(cache), cacheHash(changed));
});
test('TTL1 reuse consumes old provenance once and never renews its frame or cache membership', () => {
  const a = eventFixture(1, [], [0]), b = eventFixture(2, a.events.cacheAfter, [1]), c = eventFixture(3, b.events.cacheAfter, []);
  assert.equal(summarizeMemoryEvents(a, [], P3G).createdCount, 1); assert.equal(summarizeMemoryEvents(b, a.events.cacheAfter, P3G).usedCount, 1);
  const end = summarizeMemoryEvents(c, b.events.cacheAfter, P3G); assert.equal(end.usedCount, 1); assert.equal(end.afterCount, 0); assert.deepEqual(c.events.used.map(p => p.id), [1]);
  c.events.cacheAfter.push({ id: 1, frame: 3, residual: [0, 0, 0, 0] }); assert.throws(() => summarizeMemoryEvents(c, b.events.cacheAfter, P3G), /renewed/);
});
test('current direct correction overrides old residual and missing old IDs expire explicitly', () => {
  const a = eventFixture(1, [], [0, 1]), b = eventFixture(2, a.events.cacheAfter, [0], [0]);
  const s = summarizeMemoryEvents(b, a.events.cacheAfter, P3G); assert.equal(s.overlappingCount, 1); assert.equal(s.expiredMissingCount, 1); assert.equal(s.usedCount, 0);
  b.events.expiredMissingIds = []; assert.throws(() => summarizeMemoryEvents(b, a.events.cacheAfter, P3G), /coverage/);
});
test('residual origin uses unclipped affine Tb and clips only after reuse, preserving native direct Tb', () => {
  const a = eventFixture(1, [], [0], [0, 1], -.4, .2), b = eventFixture(2, a.events.cacheAfter, [], [0, 1], .5);
  summarizeMemoryEvents(a, [], P3G); const s = summarizeMemoryEvents(b, a.events.cacheAfter, P3G); assert.equal(s.usedCount, 1); assert.ok(Math.abs(b.events.used[0].finalRaw.Tb - 1.1) < 1e-12);
  const native = eventFixture(1, [], [0], [0, 1], 2, Math.fround(1.6)); summarizeMemoryEvents(native, [], P3G); assert.ok(native.events.created[0].directRaw.Tb > 1.6);
  const upper = eventFixture(2, a.events.cacheAfter, [], [0, 1], 1.3); assert.equal(summarizeMemoryEvents(upper, a.events.cacheAfter, P3G).reuseClippedHigh, 1);
  const lower = eventFixture(2, a.events.cacheAfter, [], [0, 1], -1); assert.equal(summarizeMemoryEvents(lower, a.events.cacheAfter, P3G).reuseClippedLow, 1);
});
test('raw event audit rejects missing eligible reuse, changed lineage, nonfinite data and tampered model gradients', () => {
  const a = eventFixture(1, [], [0]);
  for (const mutate of [r => r.events.used.pop(), r => { r.events.used[0].creatorFrame = 0; }, r => { r.events.used[0].storedResidual[0] = null; }, r => { r.events.models[0].Ju[0] = 1; }]) { const b = eventFixture(2, a.events.cacheAfter, []); mutate(b); assert.throws(() => summarizeMemoryEvents(b, a.events.cacheAfter, P3G)); }
});
test('whole-model affine evaluation remains unclipped for residual creation', () => {
  const r = eventFixture(1, [], [0], [0], -2), model = r.events.models[0]; assert.equal(evaluateUnclipped(model, [0, 0, 0]).TbRaw, -2);
  const x = summarizeMemoryEvents(r, [], P3G); assert.ok(x.createdResidual.TbSquaredSum > 0); assert.equal('residualSquared' in x, false);
});
test('zero reuse exposure, tied quality or one failed seed prevent timing without erasing absolute accuracy', () => {
  const f = gates(); assert.equal(memoryGate(f.comparisons, f.locks, P3G.pairs, f.exposure).passed, true);
  f.exposure[1].usedCount = 0; const gate = memoryGate(f.comparisons, f.locks, P3G.pairs, f.exposure), d = memoryDecision([], gate, true, P3G.decision);
  assert.equal(gate.passed, false); assert.equal(d.accuracyPassed, true); assert.equal(d.memoryGatePassed, false); assert.equal(timingPermission({ suite: 'all', executionValid: true, qualityGate: gate }).stageStatus, 'stopped_after_quality');
  f.exposure[1].usedCount = 1; f.comparisons[2].accuracyCheck.maxPositionP99 = .015; assert.equal(memoryGate(f.comparisons, f.locks, P3G.pairs, f.exposure).passed, false);
});
