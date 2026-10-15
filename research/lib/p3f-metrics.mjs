import { affineDecision } from './p3e-metrics.mjs';

const finite = x => typeof x === 'number' && Number.isFinite(x);
const vector = (x, n = 3) => Array.isArray(x) && x.length === n && x.every(finite);
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const close = (a, b, name) => { if (!finite(a) || !finite(b) || Math.abs(a - b) > 1e-12 * Math.max(1, Math.abs(a), Math.abs(b))) throw new Error(`Correction reconstruction differs: ${name}`); };

export function curvatureScore(model, points, delta, buoy) {
  const q = raw => [raw.ux, raw.uy + buoy * raw.Tb, raw.uz], center = q(model.stencil[0].raw), H = new Array(9);
  for (let axis = 0; axis < 3; axis++) {
    const plus = q(model.stencil[1 + 2 * axis].raw), minus = q(model.stencil[2 + 2 * axis].raw);
    for (let row = 0; row < 3; row++) H[3 * row + axis] = (plus[row] - 2 * center[row] + minus[row]) / (delta * delta);
  }
  let score = 0;
  for (const p of points) {
    const d2 = p.position.map((v, i) => (v - model.center[i]) ** 2);
    const r = [0, 1, 2].map(row => .5 * (H[row * 3] * d2[0] + H[row * 3 + 1] * d2[1] + H[row * 3 + 2] * d2[2]));
    score += r[0] * r[0] + r[1] * r[1] + r[2] * r[2];
  }
  if (![...H, score].every(finite)) throw new Error('Nonfinite curvature score');
  return { diagonalHessian: H, score };
}

export function selectionBudgetLock(curvature, hash, reference, expectedFrames) {
  const expected = Array.from({ length: expectedFrames }, (_, i) => i + 1), failures = [], comparisons = [];
  const a = curvature.selectionTrace, b = hash.selectionTrace;
  if (a.length !== expectedFrames || b.length !== expectedFrames || !same(a.map(s => s.frame), expected) || !same(b.map(s => s.frame), expected)) throw new Error('Incomplete correction selection traces');
  for (let i = 0; i < expectedFrames; i++) {
    const x = a[i], y = b[i], keys = ['inputCount', 'groupCount', 'selectedGroupCount', 'selectedMemberCount', 'stencilQueries', 'correctionQueries'];
    const matched = keys.every(k => x[k] === y[k]); comparisons.push({ frame: i + 1, matched, curvature: Object.fromEntries(keys.map(k => [k, x[k]])), hash: Object.fromEntries(keys.map(k => [k, y[k]])) });
    if (!matched) failures.push({ frame: i + 1, reason: 'Different actual model or correction query budgets' });
  }
  const retired = [curvature, hash, reference].map(r => ({ id: r.definition.id, count: r.snapshots.at(-1).counters.tracerRetired }));
  if (retired.some(r => r.count !== 0)) failures.push({ reason: 'Retirement invalidates a strictly matched population budget', retired });
  return { passed: failures.length === 0, frames: comparisons, retired, failures,
    interpretation: 'Same group fraction alone does not imply equal actual query counts after population changes.' };
}

export function correctionGate(comparisons, budgetLocks, pairs) {
  const records = pairs.map(pair => {
    const own = comparisons.filter(c => c.seed === pair.seed && c.renderSeed === pair.renderSeed), curvature = own.find(c => c.method === 'curvature'), hash = own.find(c => c.method === 'hash');
    const lock = budgetLocks.find(c => c.seed === pair.seed && c.renderSeed === pair.renderSeed), a = curvature?.accuracyCheck, b = hash?.accuracyCheck;
    const comparable = [a?.maxPositionRmse, a?.maxPositionP99, b?.maxPositionRmse, b?.maxPositionP99].every(finite);
    const noMissingIds = own.length === 2 && own.every(c => c.accuracyCheck.checks.noUnmatchedIds);
    return { ...pair, curvature: curvature?.candidate ?? null, hash: hash?.candidate ?? null, accuracyPassed: a?.passed === true,
      equalBudget: lock?.passed === true, noMissingIds, comparable,
      curvatureWorstRmse: a?.maxPositionRmse ?? null, hashWorstRmse: b?.maxPositionRmse ?? null,
      curvatureWorstP99: a?.maxPositionP99 ?? null, hashWorstP99: b?.maxPositionP99 ?? null,
      strictlyBetterRmse: comparable && a.maxPositionRmse < b.maxPositionRmse,
      strictlyBetterP99: comparable && a.maxPositionP99 < b.maxPositionP99 };
  });
  const complete = comparisons.length === 2 * pairs.length && budgetLocks.length === pairs.length && records.every(r => r.curvature && r.hash);
  return { complete, pairs: records, passed: complete && records.every(r => r.accuracyPassed && r.equalBudget && r.noMissingIds && r.strictlyBetterRmse && r.strictlyBetterP99),
    interpretation: 'Both per-seed deployed quality gates and strict worst-checkpoint RMSE/p99 improvements over one fixed hash control are required. No pooling across seed pairs or diagnostic substitute.' };
}
export function correctionDecision(timings, gate, evidenceComplete, spec) {
  const translated = timings.map(t => ({ ...t, method: t.method === 'curvature' ? 'affine' : t.method }));
  return { ...affineDecision(translated, gate, evidenceComplete, spec), accuracyPassed: gate?.pairs?.length === 2 && gate.pairs.every(p => p.accuracyPassed === true), selectionPassed: gate?.passed === true,
    interpretation: 'Conditional stationary old-pair timing only. Cost compares curvature correction with DD; hash is a fixed-budget mechanism control, not a performance competitor. A complete quality STOP is a valid planned negative result.' };
}

export function validateSelectionSummary(s, correction, affine) {
  for (const k of ['frame', 'inputCount', 'groupCount', 'selectedGroupCount', 'selectedMemberCount', 'stencilQueries', 'correctionQueries', 'scoreEvaluations']) if (!Number.isSafeInteger(s[k]) || s[k] < 0) throw new Error(`Invalid selection summary ${k}`);
  const K = s.inputCount ? Math.min(affine.maxGroups, Math.ceil(s.inputCount / affine.targetGroupSize)) : 0;
  if (s.groupCount !== K || s.selectedGroupCount !== Math.ceil(correction.fraction * K) || s.stencilQueries !== 7 * K || s.correctionQueries !== s.selectedMemberCount || s.scoreEvaluations !== s.inputCount || s.selectedMemberCount > s.inputCount) throw new Error('Selection budget ledger failed');
  if (!Array.isArray(s.selectedGroupIds) || s.selectedGroupIds.length !== s.selectedGroupCount || new Set(s.selectedGroupIds).size !== s.selectedGroupCount || s.selectedGroupIds.some(id => !Number.isInteger(id) || id < 0 || id >= K)) throw new Error('Invalid selected group identities');
  return true;
}

export function correctionHash(frame, minBirthId, salt) {
  let h = (salt ^ Math.imul(frame + 1, 0x9e3779b9) ^ Math.imul(minBirthId + 1, 0x85ebca6b)) >>> 0;
  h = Math.imul(h ^ (h >>> 16), 0x7feb352d) >>> 0;
  h = Math.imul(h ^ (h >>> 15), 0x846ca68b) >>> 0;
  return (h ^ (h >>> 16)) >>> 0;
}
export function selectedIdsHash(ids) {
  let h = 0x811c9dc5; const json = JSON.stringify(ids);
  for (let i = 0; i < json.length; i++) h = Math.imul(h ^ json.charCodeAt(i), 16777619) >>> 0;
  return h.toString(16).padStart(8, '0');
}
export function partitionMembers(inputs, config) {
  const groups = [], K = inputs.length ? Math.min(config.maxGroups, Math.ceil(inputs.length / config.targetGroupSize)) : 0;
  function split(points, k) {
    if (k === 1) { groups.push(points.map(p => p.id).sort((a, b) => a - b)); return; }
    const spans = [0, 1, 2].map(axis => Math.max(...points.map(p => p.position[axis])) - Math.min(...points.map(p => p.position[axis])));
    let axis = 0; for (let a = 1; a < 3; a++) if (spans[a] > spans[axis]) axis = a;
    points.sort((a, b) => a.position[axis] - b.position[axis] || a.id - b.id);
    const leftK = Math.floor(k / 2), cut = Math.floor(points.length * leftK / k); split(points.slice(0, cut), leftK); split(points.slice(cut), k - leftK);
  }
  if (K) split([...inputs], K); return groups;
}
export function summarizeCorrectionSelection(record, postParticles, spec) {
  const { selection: d, inputs, params } = record;
  if (!d || !Array.isArray(inputs) || !Array.isArray(postParticles) || !params || params.wind !== 0 || params.turb !== 0 || !finite(params.buoy)) throw new Error('Invalid stationary correction evidence');
  validateSelectionSummary(d.summary, d.config, spec.affine);
  if (d.summary.frame !== record.frame || d.fieldTime !== record.fieldTime || d.summary.inputCount !== inputs.length || !['curvature', 'hash'].includes(d.config.method) || d.config.fraction !== spec.correction.fraction || d.config.salt !== spec.correction.salt) throw new Error('Selection configuration or time differs');
  close(d.delta, spec.params.eps * spec.affine.deltaScale, 'delta');
  const byId = new Map();
  for (const p of inputs) {
    if (!Number.isSafeInteger(p.id) || byId.has(p.id) || !vector(p.position) || !finite(p.age) || p.age < 0 || p.newborn !== (p.age === 0) || p.frame !== record.frame || p.fieldTime !== record.fieldTime) throw new Error('Invalid pre-advection input');
    byId.set(p.id, p);
  }
  if (!Array.isArray(d.models) || d.models.length !== d.summary.groupCount) throw new Error('Incomplete production models');
  const expectedGroups = partitionMembers(inputs, spec.affine), groupByMember = new Map(); let scoreSum = 0, selectedScoreSum = 0, maxRadius = 0;
  for (let i = 0; i < d.models.length; i++) {
    const m = d.models[i];
    if (m.id !== i || !same(m.memberIds, expectedGroups[i]) || !vector(m.center) || !vector(m.Ju, 9) || !vector(m.gradTb) || !vector(m.diagonalHessian, 9) || !finite(m.radius) || !Array.isArray(m.stencil) || m.stencil.length !== 7 || typeof m.selected !== 'boolean') throw new Error('Invalid production group model');
    const points = m.memberIds.map(id => byId.get(id)), center = [0, 0, 0];
    for (const p of points) { groupByMember.set(p.id, m); for (let a = 0; a < 3; a++) center[a] += p.position[a]; }
    for (let a = 0; a < 3; a++) { center[a] /= points.length; close(center[a], m.center[a], 'center'); }
    const radius = Math.max(...points.map(p => Math.sqrt(p.position.reduce((sum, v, a) => sum + (v - center[a]) ** 2, 0)))); close(radius, m.radius, 'radius'); maxRadius = Math.max(maxRadius, radius);
    for (let k = 0; k < 7; k++) {
      const q = m.stencil[k], position = [...center]; if (k) position[Math.floor((k - 1) / 2)] += k % 2 ? d.delta : -d.delta;
      if (!vector(q.position) || !q.raw || !['ux', 'uy', 'uz', 'Tb', 'thermalWeight'].every(key => finite(q.raw[key]))) throw new Error('Invalid raw model query');
      for (let a = 0; a < 3; a++) close(q.position[a], position[a], 'stencil position');
    }
    for (let a = 0; a < 3; a++) {
      const plus = m.stencil[1 + 2 * a].raw, minus = m.stencil[2 + 2 * a].raw;
      for (const [row, key] of ['ux', 'uy', 'uz'].entries()) close(m.Ju[row * 3 + a], (plus[key] - minus[key]) / (2 * d.delta), 'Jacobian');
      close(m.gradTb[a], (plus.Tb - minus.Tb) / (2 * d.delta), 'temperature gradient');
    }
    const recomputed = curvatureScore(m, points, d.delta, params.buoy);
    for (let k = 0; k < 9; k++) close(m.diagonalHessian[k], recomputed.diagonalHessian[k], 'diagonal Hessian');
    // Ranking is based on this exact scalar arithmetic order, not rounded scores.
    if (m.score !== recomputed.score || m.hashRank !== correctionHash(record.frame, m.memberIds[0], d.config.salt)) throw new Error('Exact score/hash ranking inputs differ');
    scoreSum += m.score; if (m.selected) selectedScoreSum += m.score;
  }
  const ranked = [...d.models].sort((a, b) => (d.config.method === 'curvature' ? b.score - a.score : a.hashRank - b.hashRank) || a.id - b.id), chosen = new Set(ranked.slice(0, d.summary.selectedGroupCount).map(m => m.id));
  if (!same(ranked.map(m => m.id), d.rankedGroupIds) || d.models.some(m => m.selected !== chosen.has(m.id))) throw new Error('Selected rank differs');
  const selectedGroups = d.models.filter(m => m.selected).map(m => m.id), selectedIds = d.models.filter(m => m.selected).flatMap(m => m.memberIds).sort((a, b) => a - b);
  if (!same(selectedGroups, d.summary.selectedGroupIds) || !same(selectedIds, d.selectedMemberIds) || selectedIds.length !== d.summary.selectedMemberCount || selectedIdsHash(selectedIds) !== d.summary.selectionIDHash) throw new Error('Selected identity ledger differs');
  close(scoreSum, d.summary.scoreSum, 'score sum'); close(selectedScoreSum, d.summary.selectedScoreSum, 'selected score sum');
  const direct = new Map();
  if (!Array.isArray(d.directQueries) || d.directQueries.length !== selectedIds.length) throw new Error('Incomplete selected direct query evidence');
  for (const q of d.directQueries) {
    const p = byId.get(q.id), model = groupByMember.get(q.id);
    if (!p || !model.selected || direct.has(q.id) || q.groupId !== model.id || !same(q.position, p.position) || !vector(q.velocity) || !q.raw || !['ux', 'uy', 'uz', 'Tb', 'thermalWeight'].every(key => finite(q.raw[key]))) throw new Error('Invalid selected member direct query');
    direct.set(q.id, q);
  }
  const postById = new Map(postParticles.map(p => [p.id, p]));
  if (postById.size !== postParticles.length || postParticles.some(p => !byId.has(p.id))) throw new Error('Post-advection identities not derived from actual input');
  let maxVelocityError = 0, maxEulerError = 0;
  for (const p of inputs) {
    const model = groupByMember.get(p.id), q = direct.get(p.id), dx = p.position.map((x, a) => x - model.center[a]), origin = model.stencil[0].raw;
    let raw;
    if (q) raw = q.raw;
    else {
      raw = Object.fromEntries(['ux', 'uy', 'uz'].map((key, row) => [key, origin[key] + model.Ju[row * 3] * dx[0] + model.Ju[row * 3 + 1] * dx[1] + model.Ju[row * 3 + 2] * dx[2]]));
      raw.Tb = Math.max(0, Math.min(1.6, origin.Tb + model.gradTb[0] * dx[0] + model.gradTb[1] * dx[1] + model.gradTb[2] * dx[2]));
    }
    const velocity = [raw.ux, raw.uy + params.buoy * raw.Tb, raw.uz], speed2 = velocity[0] * velocity[0] + velocity[1] * velocity[1] + velocity[2] * velocity[2];
    if (speed2 > 16) { const k = 4 / Math.sqrt(speed2); for (let a = 0; a < 3; a++) velocity[a] *= k; }
    if (q) for (let a = 0; a < 3; a++) close(q.velocity[a], velocity[a], 'selected direct force/clamp');
    const post = postById.get(p.id); if (!post) continue; // Retirement is a scientific failure, not missing raw data.
    for (const [a, key] of ['vx', 'vy', 'vz'].entries()) { close(post[key], velocity[a], 'production velocity'); maxVelocityError = Math.max(maxVelocityError, Math.abs(post[key] - velocity[a])); }
    const position = p.position.map((x, a) => x + spec.dt * velocity[a]); position[2] = Math.max(-params.sliceDepth / 2, Math.min(params.sliceDepth / 2, position[2]));
    for (const [a, key] of ['x', 'y', 'z'].entries()) { close(post[key], position[a], 'Euler transport'); maxEulerError = Math.max(maxEulerError, Math.abs(post[key] - position[a])); }
    close(post.life, p.age + spec.dt, 'age');
  }
  return { frame: record.frame, inputCount: inputs.length, postCount: postParticles.length, retiredIds: inputs.filter(p => !postById.has(p.id)).map(p => p.id), groupsScored: d.models.length,
    selectedGroupCount: selectedGroups.length, selectedMemberCount: selectedIds.length, modelQueries: 7 * d.models.length, correctionQueries: direct.size,
    scoreSum, selectedScoreSum, selectionIDHash: d.summary.selectionIDHash, maximumRadius: maxRadius, maximumVelocityReconstructionError: maxVelocityError, maximumEulerError: maxEulerError,
    interpretation: 'Observed production inputs and queries only; selected points use their actual direct query, all other points use their own group affine model. No additional direct oracle.' };
}
