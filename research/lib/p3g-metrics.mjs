import { selectedIdsHash, validateSelectionSummary, summarizeCorrectionSelection, selectionBudgetLock as priorBudgetLock } from './p3f-metrics.mjs';
import { affineDecision } from './p3e-metrics.mjs';
export { validateSelectionSummary };
const finite = n => typeof n === 'number' && Number.isFinite(n);
const vec = (a, n = 3) => Array.isArray(a) && a.length === n && a.every(finite);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const close = (a, b, label) => { if (!finite(a) || !finite(b) || Math.abs(a - b) > 1e-12 * Math.max(1, Math.abs(a), Math.abs(b))) throw new Error(`Memory reconstruction mismatch: ${label}`); };

export function cacheHash(cache) {
  const encoded = cache.map(e => ({ id: e.id, frame: e.frame, residualF64LE: e.residual.map(v => { const bytes = Buffer.alloc(8); bytes.writeDoubleLE(v === 0 ? 0 : v); return bytes.toString('hex'); }) }));
  return selectedIdsHash(encoded);
}
export function selectionBudgetLock(memory, curvature, direct, expectedFrames) {
  const lock = priorBudgetLock(memory, curvature, direct, expectedFrames);
  return { ...lock, frames: lock.frames.map(({ curvature: memoryBudget, hash: curvatureBudget, ...rest }) => ({ ...rest, memory: memoryBudget, curvature: curvatureBudget })) };
}
export function memoryGate(comparisons, locks, pairs, exposure) {
  const records = pairs.map(pair => {
    const own = comparisons.filter(c => c.seed === pair.seed && c.renderSeed === pair.renderSeed), memory = own.find(c => c.method === 'memory'), curvature = own.find(c => c.method === 'curvature'), a = memory?.accuracyCheck, b = curvature?.accuracyCheck;
    const lock = locks.find(l => l.seed === pair.seed && l.renderSeed === pair.renderSeed), e = exposure.find(x => x.seed === pair.seed && x.renderSeed === pair.renderSeed);
    const comparable = [a?.maxPositionRmse, a?.maxPositionP99, b?.maxPositionRmse, b?.maxPositionP99].every(finite);
    return { ...pair, memory: memory?.candidate ?? null, curvature: curvature?.candidate ?? null, accuracyPassed: a?.passed === true, equalBudget: lock?.passed === true,
      noMissingIds: own.length === 2 && own.every(c => c.accuracyCheck.checks.noUnmatchedIds), comparable, reuseExposed: (e?.usedCount ?? 0) > 0,
      memoryWorstRmse: a?.maxPositionRmse ?? null, curvatureWorstRmse: b?.maxPositionRmse ?? null, memoryWorstP99: a?.maxPositionP99 ?? null, curvatureWorstP99: b?.maxPositionP99 ?? null,
      strictlyBetterRmse: comparable && a.maxPositionRmse < b.maxPositionRmse, strictlyBetterP99: comparable && a.maxPositionP99 < b.maxPositionP99 };
  });
  const complete = comparisons.length === pairs.length * 2 && locks.length === pairs.length && exposure.length === pairs.length && records.every(r => r.memory && r.curvature);
  return { complete, pairs: records, passed: complete && records.every(r => r.accuracyPassed && r.equalBudget && r.noMissingIds && r.reuseExposed && r.strictlyBetterRmse && r.strictlyBetterP99),
    interpretation: 'Each seed independently requires the original deployed accuracy constraints and strict worst-checkpoint RMSE/p99 improvement over the same-query curvature control. Reuse exposure must be nonzero; its continuous ratio is reported without tuning a threshold.' };
}
export function memoryDecision(timings, gate, evidenceComplete, spec) {
  const translated = timings.map(t => ({ ...t, method: t.method === 'memory' ? 'affine' : t.method }));
  return { ...affineDecision(translated, gate, evidenceComplete, spec), accuracyPassed: gate?.pairs?.length === 2 && gate.pairs.every(r => r.accuracyPassed), memoryGatePassed: gate?.passed === true,
    interpretation: 'One old stationary pair is timed only after both seed-pair quality and temporal-reuse gates pass. A complete planned quality STOP remains valid evidence.' };
}

function requireCache(cache, frame) {
  if (!Array.isArray(cache)) throw new Error('Missing memory cache'); let previous = -1;
  for (const e of cache) { if (!Number.isSafeInteger(e.id) || e.id <= previous || e.frame !== frame || !vec(e.residual, 4)) throw new Error('Invalid cache order, age, identity or residual'); previous = e.id; }
}
function rawVector(raw) { return [raw.ux, raw.uy, raw.uz, raw.TbRaw]; }
export function evaluateUnclipped(model, position) {
  const b = model.stencil[0].raw, J = model.Ju, g = model.gradTb, dx = position.map((x, a) => x - model.center[a]);
  return { ux: b.ux + J[0] * dx[0] + J[1] * dx[1] + J[2] * dx[2], uy: b.uy + J[3] * dx[0] + J[4] * dx[1] + J[5] * dx[2], uz: b.uz + J[6] * dx[0] + J[7] * dx[1] + J[8] * dx[2], TbRaw: b.Tb + g[0] * dx[0] + g[1] * dx[1] + g[2] * dx[2] };
}
function validateEventModel(m, delta) {
  if (!Number.isSafeInteger(m.id) || !vec(m.center) || !vec(m.Ju, 9) || !vec(m.gradTb) || !Array.isArray(m.memberIds) || !m.memberIds.length || new Set(m.memberIds).size !== m.memberIds.length || !Array.isArray(m.stencil) || m.stencil.length !== 7) throw new Error('Invalid event model');
  for (let k = 0; k < 7; k++) {
    const q = m.stencil[k], expected = [...m.center]; if (k) expected[Math.floor((k - 1) / 2)] += k % 2 ? delta : -delta;
    if (!vec(q.position) || !q.raw || !['ux', 'uy', 'uz', 'Tb', 'thermalWeight'].every(key => finite(q.raw[key]))) throw new Error('Nonfinite event model query');
    for (let a = 0; a < 3; a++) close(q.position[a], expected[a], 'stencil position');
  }
  for (let a = 0; a < 3; a++) {
    const p = m.stencil[1 + 2 * a].raw, n = m.stencil[2 + 2 * a].raw;
    for (const [row, key] of ['ux', 'uy', 'uz'].entries()) close(m.Ju[row * 3 + a], (p[key] - n[key]) / (2 * delta), 'event Jacobian');
    close(m.gradTb[a], (p.Tb - n.Tb) / (2 * delta), 'event temperature gradient');
  }
}
function forced(raw, params) {
  const v = [raw.ux, raw.uy + params.buoy * raw.Tb, raw.uz], v2 = v[0] * v[0] + v[1] * v[1] + v[2] * v[2];
  if (v2 > 16) { const k = 4 / Math.sqrt(v2); for (let a = 0; a < 3; a++) v[a] *= k; } return v;
}

export function summarizeMemoryEvents(record, previousCache, spec, postParticles = null) {
  const { events: e, params } = record;
  if (!e || e.frame !== record.frame || e.fieldTime !== record.fieldTime || e.config?.ttl !== 1 || !params || params.wind !== 0 || params.turb !== 0 || !finite(params.buoy)) throw new Error('Memory observation time/configuration differs');
  requireCache(e.cacheBefore, record.frame - 1); requireCache(e.cacheAfter, record.frame);
  if (!same(e.cacheBefore, previousCache)) throw new Error('Memory cache lineage is not continuous');
  const before = new Map(e.cacheBefore.map(c => [c.id, c])), models = new Map(), delta = spec.params.eps * spec.affine.deltaScale;
  if (!Array.isArray(e.models) || !Array.isArray(e.created) || !Array.isArray(e.used) || !Array.isArray(e.overlappingIds) || !Array.isArray(e.expiredMissingIds)) throw new Error('Incomplete memory event evidence');
  if (!Array.isArray(e.inputIds) || e.inputIds.some(id => !Number.isSafeInteger(id) || id < 0) || new Set(e.inputIds).size !== e.inputIds.length) throw new Error('Incomplete actual input ID coverage');
  const live = new Set(e.inputIds);
  for (const m of e.models) { validateEventModel(m, delta); if (models.has(m.id)) throw new Error('Duplicate event model'); models.set(m.id, m); }
  const created = new Map(), used = new Map(), modelIds = new Set();
  let clippedLow = 0, clippedHigh = 0, maximumVelocityError = 0, maximumEulerError = 0;
  const post = postParticles ? new Map(postParticles.map(p => [p.id, p])) : null;
  function validateBase(p) {
    const model = models.get(p.groupId);
    if (!Number.isSafeInteger(p.id) || !live.has(p.id) || !model || !model.memberIds.includes(p.id) || !vec(p.position) || !p.affineRaw || !vec(rawVector(p.affineRaw), 4) || !finite(p.age) || p.age < 0 || p.newborn !== (p.age === 0)) throw new Error('Invalid memory event identity/base');
    modelIds.add(model.id); const expected = evaluateUnclipped(model, p.position);
    for (const key of ['ux', 'uy', 'uz', 'TbRaw']) close(p.affineRaw[key], expected[key], 'unclipped affine event value');
  }
  for (const p of e.created) {
    validateBase(p); if (created.has(p.id) || !p.directRaw || !['ux', 'uy', 'uz', 'Tb', 'thermalWeight'].every(k => finite(p.directRaw[k])) || !vec(p.residual, 4)) throw new Error('Invalid residual creation');
    const expected = [p.directRaw.ux - p.affineRaw.ux, p.directRaw.uy - p.affineRaw.uy, p.directRaw.uz - p.affineRaw.uz, p.directRaw.Tb - p.affineRaw.TbRaw];
    for (let k = 0; k < 4; k++) close(p.residual[k], expected[k], 'created raw residual');
    created.set(p.id, p);
  }
  for (const p of e.used) {
    validateBase(p); const old = before.get(p.id);
    if (!old || created.has(p.id) || used.has(p.id) || p.creatorFrame !== record.frame - 1 || old.frame !== p.creatorFrame || !vec(p.storedResidual, 4) || !same(p.storedResidual, old.residual) || !p.finalRaw || !vec(rawVector(p.finalRaw), 4) || !finite(p.finalRaw.Tb) || !vec(p.velocity)) throw new Error('Invalid TTL1 reuse or direct-priority violation');
    const base = rawVector(p.affineRaw), expected = base.map((x, k) => x + old.residual[k]);
    for (const [k, key] of ['ux', 'uy', 'uz', 'TbRaw'].entries()) close(p.finalRaw[key], expected[k], 'reused raw residual');
    close(p.finalRaw.Tb, Math.max(0, Math.min(1.6, expected[3])), 'clip only after residual addition'); clippedLow += +(expected[3] < 0); clippedHigh += +(expected[3] > 1.6);
    const velocity = forced(p.finalRaw, params);
    for (let a = 0; a < 3; a++) { close(p.velocity[a], velocity[a], 'reused force/clamp'); maximumVelocityError = Math.max(maximumVelocityError, Math.abs(p.velocity[a] - velocity[a])); }
    if (post?.has(p.id)) {
      const actual = post.get(p.id), position = p.position.map((v, a) => v + spec.dt * velocity[a]); position[2] = Math.max(-params.sliceDepth / 2, Math.min(params.sliceDepth / 2, position[2]));
      for (const [a, key] of ['vx', 'vy', 'vz'].entries()) close(actual[key], velocity[a], 'actual reused velocity');
      for (const [a, key] of ['x', 'y', 'z'].entries()) { close(actual[key], position[a], 'actual reused Euler position'); maximumEulerError = Math.max(maximumEulerError, Math.abs(actual[key] - position[a])); }
    }
    used.set(p.id, p);
  }
  const overlap = [...before.keys()].filter(id => created.has(id)).sort((a, b) => a - b), missing = [...before.keys()].filter(id => !live.has(id)).sort((a, b) => a - b);
  const expectedUsed = [...before.keys()].filter(id => live.has(id) && !created.has(id)).sort((a, b) => a - b);
  if (!same(expectedUsed, [...used.keys()].sort((a, b) => a - b))) throw new Error('Eligible previous entry was omitted or ineligible entry reused');
  if (!same(overlap, e.overlappingIds) || !same(missing, e.expiredMissingIds) || modelIds.size !== models.size) throw new Error('Memory cache fate/model coverage differs');
  const after = [...created.values()].sort((a, b) => a.id - b.id).map(p => ({ id: p.id, frame: record.frame, residual: p.residual }));
  if (!same(after, e.cacheAfter)) throw new Error('Reuse renewed an entry or cache did not retain exactly current selected points');
  const summary = e.summary, counts = { frame: record.frame, inputCount: e.inputIds.length, unselectedMembers: e.inputIds.length - created.size, newSelectedMembers: created.size - overlap.length,
    previousMembers: before.size, previousLiveMembers: before.size - missing.length, overlappingMembers: overlap.length, expiredMissingMembers: missing.length, savedMembers: created.size, reusedMembers: used.size, modelEvaluations: created.size };
  if (!summary) throw new Error('Missing production memory summary');
  for (const [key, value] of Object.entries(counts)) if (summary[key] !== value) throw new Error(`Production memory summary differs: ${key}`);
  for (const [key, ids] of [['previousIDHash', [...before.keys()]], ['savedIDHash', [...created.keys()].sort((a, b) => a - b)], ['reusedIDHash', expectedUsed], ['overlappingIDHash', overlap]]) if (summary[key] !== selectedIdsHash(ids)) throw new Error(`Memory ID hash differs: ${key}`);
  function residualStats(values) { const s = { uSquaredSum: 0, TbSquaredSum: 0, uNormMax: 0, TbAbsMax: 0, signedTbSum: 0 }; for (const r of values) { const q = r[0] * r[0] + r[1] * r[1] + r[2] * r[2]; s.uSquaredSum += q; s.TbSquaredSum += r[3] * r[3]; s.uNormMax = Math.max(s.uNormMax, Math.sqrt(q)); s.TbAbsMax = Math.max(s.TbAbsMax, Math.abs(r[3])); s.signedTbSum += r[3]; } return s; }
  const createdResidual = residualStats(e.created.map(p => p.residual)), reusedResidual = residualStats(e.used.map(p => p.storedResidual));
  for (const [key, expected] of [['createdResidual', createdResidual], ['reusedResidual', reusedResidual]]) for (const k of Object.keys(expected)) close(summary[key]?.[k], expected[k], `${key}.${k}`);
  for (const key of ['finalTbClippedLow', 'finalTbClippedHigh', 'speedClamped']) if (!Number.isSafeInteger(summary[key]) || summary[key] < 0 || summary[key] > e.inputIds.length) throw new Error('Invalid full-frame clipping count');
  if (summary.finalTbClippedLow < clippedLow || summary.finalTbClippedHigh < clippedHigh) throw new Error('Full-frame clip count omits reused events');
  return { frame: record.frame, inputCount: live.size, unselectedCount: live.size - created.size, beforeCount: before.size, afterCount: after.length, createdCount: created.size, usedCount: used.size, overlappingCount: overlap.length, expiredMissingCount: missing.length,
    previousLiveCount: before.size - missing.length, reuseFractionOfPreviousLive: before.size > missing.length ? used.size / (before.size - missing.length) : null,
    reuseFractionOfInputs: live.size ? used.size / live.size : null, reuseFractionOfUnselected: live.size > created.size ? used.size / (live.size - created.size) : null,
    createdResidual, reusedResidual, reuseClippedLow: clippedLow, reuseClippedHigh: clippedHigh, eventModelCount: models.size, beforeHash: cacheHash(e.cacheBefore), afterHash: cacheHash(after), maximumVelocityError, maximumEulerError,
    checkedAgainstParticleCheckpoint: !!postParticles,
    interpretation: 'All event affine values are rebuilt from observed model stencils and derivatives; complete global partition membership is audited only at the 12 full-input checkpoints. Cache lineage and TTL are checked on every step.' };
}

export function summarizeMemorySelection(record, postParticles, spec, events = null) {
  if (!events) return summarizeCorrectionSelection(record, postParticles, spec);
  const input = new Map(record.inputs.map(p => [p.id, p]));
  if (!same([...input.keys()].sort((a, b) => a - b), [...events.inputIds].sort((a, b) => a - b))) throw new Error('Full checkpoint inputs differ from memory event IDs');
  const direct = new Map(record.selection.directQueries.map(p => [p.id, p])), used = new Map(events.used.map(p => [p.id, p]));
  for (const p of [...events.created, ...events.used]) { const actual = input.get(p.id); if (!actual || !same(p.position, actual.position) || p.age !== actual.age || p.newborn !== actual.newborn) throw new Error('Memory event differs from actual full checkpoint input'); }
  for (const p of events.created) if (!direct.has(p.id) || !same(direct.get(p.id).raw, p.directRaw)) throw new Error('Creation did not share the actual selected direct query');
  const members = new Map(); for (const m of record.selection.models) for (const id of m.memberIds) members.set(id, m);
  for (const m of events.models) { const original = record.selection.models.find(n => n.id === m.id); for (const key of ['memberIds', 'center', 'radius', 'stencil', 'Ju', 'gradTb']) if (!same(m[key], original?.[key])) throw new Error('Event model differs from full checkpoint model'); }
  const reused = new Set(events.used.map(p => p.id)), baseParticles = postParticles.filter(p => !reused.has(p.id));
  const base = summarizeCorrectionSelection(record, baseParticles, spec), alive = new Set(postParticles.map(p => p.id));
  let low = 0, high = 0, speedClamped = 0;
  for (const p of record.inputs) {
    let raw; if (direct.has(p.id)) raw = direct.get(p.id).raw;
    else { raw = used.get(p.id)?.finalRaw ?? evaluateUnclipped(members.get(p.id), p.position); low += +(raw.TbRaw < 0); high += +(raw.TbRaw > 1.6); raw = { ...raw, Tb: Math.max(0, Math.min(1.6, raw.TbRaw)) }; }
    const x = raw.ux, y = raw.uy + record.params.buoy * raw.Tb, z = raw.uz; speedClamped += +(x * x + y * y + z * z > 16);
  }
  if (events.summary.finalTbClippedLow !== low || events.summary.finalTbClippedHigh !== high || events.summary.speedClamped !== speedClamped) throw new Error('Full checkpoint transport clip/speed summary differs');
  return { ...base, postCount: postParticles.length, retiredIds: record.inputs.filter(p => !alive.has(p.id)).map(p => p.id), baseBranchValidatedCount: baseParticles.length, reuseBranchValidatedCount: postParticles.length - baseParticles.length,
    fullFrameTbClippedLow: low, fullFrameTbClippedHigh: high, fullFrameSpeedClamped: speedClamped,
    interpretation: 'Complete grouping/selection is checked. Non-reused surviving particles are checked by the original affine/direct validator; reused particles are independently checked by the same-frame memory event validator.' };
}
