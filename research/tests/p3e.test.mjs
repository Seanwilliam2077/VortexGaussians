import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { P3E, p3eConfig, qualityCasesP3e, timingCasesP3e, parseP3eArgs } from '../p3e-design.mjs';
import { pathsWithOpticalWeights, deployedQualityGate, timingPermission, affineDecision, summarizeAffineDiagnostic, requireTimingProductionMatch } from '../lib/p3e-metrics.mjs';
import { pairedImageError, poolPairedImages } from '../lib/p3b-metrics.mjs';
import { validateAffineLedger } from '../p3e-run.mjs';

function diagnosticFixture() {
  const delta = P3E.params.eps * .125, fieldTime = 14 / 60, points = [-.1, 0, .1].map((x, id) => ({ id, position: [x, 0, 0], age: 0, newborn: true, frame: 15, fieldTime }));
  const raw = ([x, y, z]) => ({ ux: 2 * x, uy: 3 * y, uz: -z, Tb: .8 + 10 * x, thermalWeight: 1 });
  const positions = [[0, 0, 0], [delta, 0, 0], [-delta, 0, 0], [0, delta, 0], [0, -delta, 0], [0, 0, delta], [0, 0, -delta]];
  const model = { id: 0, memberIds: [0, 1, 2], center: [0, 0, 0], radius: .1, stencil: positions.map(position => ({ position, raw: raw(position) })), Ju: [2, 0, 0, 0, 3, 0, 0, 0, -1], gradTb: [10, 0, 0] };
  const transport = q => ({ raw: q, velocity: [q.ux, q.uy, q.uz], preClampVelocity: [q.ux, q.uy, q.uz], preClampSpeed: Math.hypot(q.ux, q.uy, q.uz), speedClamped: false });
  const samples = points.map(p => { const q = raw(p.position), { thermalWeight, ...r } = q;
    return { id: p.id, groupId: 0, position: p.position, age: 0, newborn: true, direct: transport({ ...q, Tb: .8 }), prediction: transport({ ...r, TbRaw: q.Tb, Tb: Math.max(0, Math.min(1.6, q.Tb)), clippedLow: q.Tb < 0, clippedHigh: q.Tb > 1.6 }) }; });
  const counters = { affineGroups: 1, affineStencilQueries: 7, affineReconstructions: 3, fullFieldQueries: 10, fieldQueries: 10, velocityOnlyFieldQueries: 0, thermalOnlyFieldQueries: 0, noThermalSupportQueries: 0, affineTbClippedLow: 1, affineTbClippedHigh: 1 };
  return { frame: 15, fieldTime, inputs: points, diagnostic: { frame: 15, fieldTime, delta, inputCount: 3, groupCount: 1, models: [model], points: samples, counters,
    support: { stencilQueries: 7, stencilNoThermalSupport: 0, directQueries: 3, directNoThermalSupport: 0, directUnsupportedPositivePrediction: 0 }, traceBefore: { x: 1 }, traceAfter: { x: 1 } } };
}
function comparisonWithPaths(paths) {
  return { paths, images: P3E.captures.flatMap(frame => P3E.views.map(view => ({ frame, view }))), pooled: { foreground: { alphaNrmse: 0, rgbNrmse: 0 } }, cacheFallbacks: 0, capacityBlocks: 0, physicsAndBirthRngMatched: true };
}
test('P3e fixes two quality arms and ten conditional alternating runs without a timing bypass', () => {
  assert.equal(qualityCasesP3e().length, 2); assert.equal(timingCasesP3e().length, 10); assert.equal(new Set(timingCasesP3e().map(c => c.id)).size, 10);
  assert.deepEqual(timingCasesP3e().map(c => c.method), ['DD', 'affine', 'affine', 'DD', 'DD', 'affine', 'affine', 'DD', 'DD', 'affine']);
  assert.throws(() => parseP3eArgs(['--suite', 'timing']), /bypass/);
  const [dd, affine] = qualityCasesP3e().map(p3eConfig); assert.equal(dd.field.cellSize, .035); assert.equal(dd.field.maxNodes, 200000);
  assert.equal(affine.field.cellSize, undefined); assert.deepEqual(affine.field.affine, { maxGroups: 600, targetGroupSize: 16, deltaScale: .125 });
  const pin = JSON.parse(readFileSync(new URL('../lib/p3e-baseline.json', import.meta.url))); assert.equal(Object.keys(pin.files).length, 2); assert.equal(pin.archiveSha256, '1c486850a886e5291d7b1aa6e1ce125b3988d694064c4c38f75920fffd72bc44');
});
test('missing or wholly empty candidate populations remain explicit quality failures with optical weight', () => {
  const p = { id: 0, x: 0, y: 0, z: 0, vx: 0, vy: 0, vz: 0, T: 1, d: 1, life: .1 };
  const m = pathsWithOpticalWeights([], [p], P3E); assert.equal(m.positionRmse, null); assert.equal(m.onlyReferenceOpticalWeight, 1 / 16);
  const paths = P3E.accuracy.expectedSampleFrames.map(frame => ({ frame, ...m }));
  assert.equal(deployedQualityGate(comparisonWithPaths(paths), P3E.accuracy).passed, false);
});
test('finite black candidate pixels produce unit relative error rather than execution failure', () => {
  const image = data => ({ width: 1, height: 1, data, orientation: 'bottom-left' });
  const error = pairedImageError(image([0, 0, 0, 0]), image([1, 1, 1, .5]), { foregroundMask: Uint8Array.of(1), holeMask: Uint8Array.of(1) }, P3E.image);
  const pooled = poolPairedImages([error]); assert.equal(pooled.foreground.rgbNrmse, 1); assert.equal(pooled.foreground.alphaNrmse, 1); assert.equal(error.holes.fraction, 1);
});
test('valid quality STOP is distinct from execution failure and cannot trigger conditional timing', () => {
  const failed = timingPermission({ suite: 'all', executionValid: true, qualityGate: { passed: false } }); assert.equal(failed.run, false); assert.equal(failed.stageStatus, 'stopped_after_quality');
  assert.equal(timingPermission({ suite: 'all', executionValid: false, qualityGate: { passed: true } }).stageStatus, 'execution_failed');
  assert.equal(timingPermission({ suite: 'quick', executionValid: true, qualityGate: { passed: true } }).run, false);
  assert.equal(timingPermission({ suite: 'all', executionValid: true, qualityGate: { passed: true } }).run, true);
  assert.equal(affineDecision([], { passed: false }, true, P3E.decision).engineeringGo, false);
});
test('diagnostic rebuilds stored finite differences and records raw versus clipped temperature error', () => {
  const m = summarizeAffineDiagnostic(diagnosticFixture(), P3E);
  assert.equal(m.count, 3); assert.equal(m.modelQueries, 7); assert.equal(m.clippedLow, 1); assert.equal(m.clippedHigh, 1);
  assert.equal(m.totalVelocityRmse, 0); assert.ok(Math.abs(m.rawTemperatureSquaredError - 2) < 1e-12); assert.ok(Math.abs(m.temperatureSquaredError - 1.28) < 1e-12);
});
test('diagnostic rejects missing members, nonfinite fields, query ledger drift and changed state', () => {
  for (const mutate of [r => r.diagnostic.models[0].memberIds.pop(), r => { r.diagnostic.points[0].prediction.raw.ux = null; }, r => { r.diagnostic.counters.fullFieldQueries++; }, r => { r.diagnostic.traceAfter.x++; }]) {
    const r = diagnosticFixture(); mutate(r); assert.throws(() => summarizeAffineDiagnostic(r, P3E));
  }
});
test('affine production ledger requires exactly seven raw queries per model and one reconstruction per tracer', () => {
  const c = { affineGroups: 2, affineStencilQueries: 14, affineReconstructions: 30, affineGroupSortCalls: 3, affineSortedPointCount: 60, affineTbClippedLow: 0, affineTbClippedHigh: 0,
    fieldQueries: 14, fullFieldQueries: 14, tracerFieldQueries: 30, velocityOnlyFieldQueries: 0, thermalOnlyFieldQueries: 0, componentDirectQueries: 0, cacheNodeQueries: 0, cacheFallbacks: 0 };
  assert.equal(validateAffineLedger({ field: { mode: 'affine' }, counters: c }), true);
  assert.throws(() => validateAffineLedger({ field: { mode: 'affine' }, counters: { ...c, fieldQueries: 15 } }), /accounting/);
});
test('engineering result needs a passed deployed quality gate and complete independent timing', () => {
  const times = [{ method: 'DD', complete: true, centralMs: 12, tailMs: 20 }, { method: 'affine', complete: true, centralMs: 6, tailMs: 18 }];
  assert.equal(affineDecision(times, { passed: true }, true, P3E.decision).engineeringGo, true);
  assert.equal(affineDecision(times, { passed: false }, true, P3E.decision).engineeringGo, false);
  times[1].tailMs = 21; assert.equal(affineDecision(times, { passed: true }, true, P3E.decision).engineeringGo, false);
  const s = { frame: 0, time: 0, physicalHash: 'a', tracerHash: 'b', physics: {}, render: { count: 0 }, counters: {}, field: {} }, quality = { snapshots: [s, s] }, timing = { initial: structuredClone(s), final: structuredClone(s) };
  assert.equal(requireTimingProductionMatch(quality, timing).passed, true); timing.final.render.count = 1;
  assert.throws(() => requireTimingProductionMatch(quality, timing), /final.render/);
});
