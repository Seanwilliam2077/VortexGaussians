import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { P3D, p3dConfig, qualityCasesP3d, timingCasesP3d, parseP3dArgs } from '../p3d-design.mjs';
import { requireFrozenChecksum, requireOldFields, exactTracerReplay, compareRecordedHashes, costDecision } from '../lib/p3d-metrics.mjs';
import { validateQueryLedger, requireCompleteP3dCase } from '../p3d-run.mjs';

test('P3d fixes exactly 27 quality cases and 45 separately timed runs', () => {
  const q = qualityCasesP3d(), t = timingCasesP3d(); assert.equal(q.length, 27); assert.equal(t.length, 45);
  assert.equal(new Set([...q, ...t].map(c => c.id)).size, 72);
  for (const d of q) { const c = p3dConfig(d); assert.equal(c.nSim, 600); assert.equal(c.nRender, 9600); assert.equal(c.field.cellSize, .035); }
  assert.deepEqual(q.slice(0, 3).map(d => p3dConfig(d).field.evaluation), ['combined', 'combined', 'specialized']);
  assert.equal(qualityCasesP3d('timing').length, 0); assert.equal(timingCasesP3d('quality').length, 0);
  assert.throws(() => parseP3dArgs(['--h', '.01']), /Unknown/);
  const pin = JSON.parse(readFileSync(new URL('../lib/p3d-baseline.json', import.meta.url)));
  assert.equal(pin.archiveSha256, '204ebcebc2586a290a9f6eeca527766cdfb5f95d49d2c54bfcbbb9563e3eaee3');
  assert.equal(Object.keys(pin.files).length, 19); assert.ok(Object.values(pin.files).every(s => /^[a-f0-9]{64}$/.test(s)));
});
test('five timing repeats use the frozen partially balanced order and GPU-completed sample window', () => {
  const t = timingCasesP3d();
  for (const s of P3D.scenarios) for (let repeat = 0; repeat < 5; repeat++) assert.deepEqual(t.filter(d => d.scenario === s.id && d.repeat === repeat).map(d => d.method), P3D.timing.order[repeat]);
  assert.equal(P3D.timing.warmupFrames, 20); assert.equal(P3D.timing.firstFrame, 60); assert.equal(P3D.timing.lastFrame, 180); assert.equal(P3D.timing.sampleEvery, 3);
});
test('legacy subset comparison permits new instrumentation but rejects changes, removals and truncation', () => {
  assert.equal(requireOldFields({ x: [1, { y: 2 }], z: null }, { x: [1, { y: 2, extra: true }], z: null, new: 1 }), true);
  assert.throws(() => requireOldFields({ x: 1 }, { x: 2 }), /differs/);
  assert.throws(() => requireOldFields({ x: 1 }, {}), /missing/);
  assert.throws(() => requireOldFields([1, 2], [1]), /length/);
  const hash = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
  assert.equal(requireFrozenChecksum(Buffer.from('abc'), hash, 'fixture'), hash);
  assert.throws(() => requireFrozenChecksum(Buffer.from('abd'), hash, 'fixture'), /checksum mismatch/);
});
test('every-step tracer equality rejects single-step drift despite later convergence', () => {
  const a = Array.from({ length: 181 }, (_, frame) => ({ frame, tracerHash: String(frame) })), b = structuredClone(a);
  assert.equal(exactTracerReplay(a, b), true); b[33].tracerHash = 'changed'; assert.throws(() => exactTracerReplay(a, b), /step 33/);
  assert.throws(() => exactTracerReplay([], []), /incomplete/); assert.throws(() => exactTracerReplay(a, a.slice(1)), /incomplete/);
});
test('binary equality requires all 13 checkpoints and six fixed-view images', () => {
  const r = { checkpoints: Array.from({ length: 13 }, (_, i) => ({ frame: i * 15, particles: { sha256: `p${i}`, file: `p${i}` } })),
    captures: P3D.captures.flatMap(frame => P3D.views.map(view => ({ frame, view, image: { sha256: `${frame}-${view.id}`, file: `${frame}-${view.id}` } }))) };
  assert.equal(compareRecordedHashes(r, structuredClone(r)).passed, true);
  const bad = structuredClone(r); bad.captures[0].image.sha256 = 'changed'; assert.throws(() => compareRecordedHashes(r, bad), /RGBA/);
  const missing = structuredClone(r); missing.checkpoints.pop(); assert.throws(() => compareRecordedHashes(r, missing), /incomplete/);
});
test('specialized query ledger counts thermal support only where temperature was queried', () => {
  const c = { fieldQueries: 11, fullFieldQueries: 0, velocityOnlyFieldQueries: 3, thermalOnlyFieldQueries: 8,
    noThermalSupportQueries: 2, fullNoThermalSupportQueries: 0, thermalOnlyNoThermalSupportQueries: 2,
    componentDirectQueries: 3, tracerFieldQueries: 3, cacheNodeQueries: 8, componentDirectNoThermalSupportQueries: 0 };
  const s = { field: { mode: 'grid', components: 'temperature', evaluation: 'specialized' }, counters: c };
  assert.equal(validateQueryLedger(s), true);
  assert.throws(() => validateQueryLedger({ ...s, counters: { ...c, noThermalSupportQueries: 3 } }), /accounting/);
  assert.throws(() => validateQueryLedger({ ...s, counters: { ...c, componentDirectNoThermalSupportQueries: 1 } }), /redundant/);
});
test('engineering decision requires each condition and refuses incomplete or slower-tail evidence', () => {
  const times = P3D.scenarios.flatMap(s => P3D.methods.map(m => ({ scenario: s.id, method: m.id, complete: true, centralMs: m.id === 'DD' ? 10 : 5, tailMs: m.id === 'DD' ? 12 : 8 })));
  assert.equal(costDecision(times, P3D.decision, P3D.scenarios, true).engineeringGo, true);
  const accuracyFailed = costDecision(times, P3D.decision, P3D.scenarios, true, false);
  assert.equal(accuracyFailed.evidenceComplete, true); assert.equal(accuracyFailed.accuracyPassed, false); assert.equal(accuracyFailed.engineeringGo, false);
  times.find(t => t.scenario === 'curl' && t.method === 'DG-specialized').tailMs = 13;
  assert.equal(costDecision(times, P3D.decision, P3D.scenarios, true).engineeringGo, false);
  assert.equal(costDecision(times, P3D.decision, P3D.scenarios, false).engineeringGo, false);
  assert.equal(costDecision([], P3D.decision, P3D.scenarios, true).engineeringGo, false);
});
test('quality completeness independently requires the tracer hash trace and captures', () => {
  const d = qualityCasesP3d('quick')[0], r = { definition: d, trace: Array.from({ length: 16 }, (_, frame) => ({ frame })),
    tracerTrace: Array.from({ length: 16 }, (_, frame) => ({ frame, tracerHash: 'x' })), checkpoints: [{ frame: 0 }, { frame: 15 }], captures: P3D.views.map(view => ({ frame: 15, view })) };
  assert.equal(requireCompleteP3dCase(r), true); r.tracerTrace.pop(); assert.throws(() => requireCompleteP3dCase(r), /trace/);
});
