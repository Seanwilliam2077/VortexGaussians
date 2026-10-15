import { pairedParticles, approximationGate } from './p3b-metrics.mjs';

const vec = (v, n = 3) => Array.isArray(v) && v.length === n && v.every(Number.isFinite);
const squared = a => a.reduce((sum, x) => sum + x * x, 0);
const difference = (a, b) => a.map((x, i) => x - b[i]);
const close = (a, b, label) => { if (!Number.isFinite(a) || !Number.isFinite(b) || Math.abs(a - b) > 1e-12 * Math.max(1, Math.abs(a), Math.abs(b))) throw new Error(`Diagnostic reconstruction mismatch: ${label}`); };
export function pathsWithOpticalWeights(candidate, reference, spec) {
  const p = pairedParticles(candidate, reference), weight = spec.nSim / spec.nRender;
  return { ...p, opticalWeightPerParticle: weight, matchedOpticalWeight: p.matched * weight,
    onlyCandidateOpticalWeight: p.onlyCandidate.length * weight, onlyReferenceOpticalWeight: p.onlyReference.length * weight };
}
export function deployedQualityGate(comparison, spec) {
  // Empty matched populations and finite black candidate images are ordinary negative outcomes.
  return { ...approximationGate(comparison, spec), interpretation: 'The deployable trajectory alone gates timing. Same-position diagnostics do not override this decision.' };
}
export function timingPermission({ suite, executionValid, qualityGate }) {
  if (!executionValid) return { run: false, stageStatus: 'execution_failed', reason: 'Required data, provenance, or physical-state invariants failed.' };
  if (suite !== 'all') return { run: false, stageStatus: 'quick_complete', reason: 'Quick suite does not implement the full quality gate or timing protocol.' };
  if (!qualityGate?.passed) return { run: false, stageStatus: 'stopped_after_quality', reason: 'Predeclared deployable quality gate failed; no timing, parameter adjustment, or extra budget tier is run.' };
  return { run: true, stageStatus: 'quality_passed', reason: null };
}
export function affineDecision(timings, qualityGate, evidenceComplete, spec) {
  const direct = timings.find(t => t.method === 'DD'), affine = timings.find(t => t.method === 'affine');
  const valid = [direct, affine].every(t => t?.complete && Number.isFinite(t.centralMs) && t.centralMs > 0 && Number.isFinite(t.tailMs) && t.tailMs > 0);
  const centralSpeedup = valid ? direct.centralMs / affine.centralMs : null, medianRunP95Ratio = valid ? affine.tailMs / direct.tailMs : null;
  const cost = { complete: !!valid, centralSpeedup, medianRunP95Ratio,
    passed: !!valid && centralSpeedup >= spec.minimumCentralSpeedup && medianRunP95Ratio <= spec.maximumMedianRunP95Ratio };
  return { evidenceComplete, accuracyPassed: qualityGate?.passed === true, cost,
    engineeringGo: evidenceComplete && qualityGate?.passed === true && cost.passed,
    interpretation: 'One previously observed condition. Central=median of five run medians; tail=median of five run p95 values. A valid quality STOP is a complete planned negative experiment.' };
}
export function requireTimingProductionMatch(quality, timing) {
  const keys = ['frame', 'time', 'physicalHash', 'tracerHash', 'physics', 'render', 'counters', 'field'];
  for (const [a, b, phase] of [[quality.snapshots[0], timing.initial, 'initial'], [quality.snapshots.at(-1), timing.final, 'final']]) {
    if (!a || !b) throw new Error('Quality/timing endpoints missing');
    for (const key of keys) if (JSON.stringify(a[key]) !== JSON.stringify(b[key])) throw new Error(`Quality/timing production differs at ${phase}.${key}`);
  }
  return { passed: true, initialTracerHash: timing.initial.tracerHash, finalTracerHash: timing.final.tracerHash,
    compared: keys, interpretation: 'Compared outside timed frames against the same-method quality run. Camera-only parameters are excluded.' };
}

export function summarizeAffineDiagnostic(record, spec) {
  const { inputs, diagnostic: d } = record;
  if (!Array.isArray(inputs) || !Array.isArray(d.models) || !Array.isArray(d.points) || d.inputCount !== inputs.length || d.points.length !== inputs.length || d.groupCount !== d.models.length) throw new Error('Incomplete affine diagnostic populations');
  if (d.frame !== record.frame || d.fieldTime !== record.fieldTime || JSON.stringify(d.traceBefore) !== JSON.stringify(d.traceAfter)) throw new Error('Diagnostic changed state or sampled a different time');
  close(d.delta, spec.params.eps * spec.affine.deltaScale, 'delta');
  const expectedGroups = Math.min(spec.affine.maxGroups, Math.ceil(inputs.length / spec.affine.targetGroupSize));
  if (d.models.length !== expectedGroups) throw new Error('Wrong number of target groups');
  const c = d.counters, support = d.support;
  if (!c || c.affineGroups !== expectedGroups || c.affineStencilQueries !== 7 * expectedGroups || c.affineReconstructions !== inputs.length ||
      c.fullFieldQueries !== 7 * expectedGroups + inputs.length || c.fieldQueries !== c.fullFieldQueries ||
      c.velocityOnlyFieldQueries !== 0 || c.thermalOnlyFieldQueries !== 0 || !support || support.stencilQueries !== 7 * expectedGroups || support.directQueries !== inputs.length ||
      !Number.isInteger(support.stencilNoThermalSupport) || support.stencilNoThermalSupport < 0 || support.stencilNoThermalSupport > support.stencilQueries ||
      !Number.isInteger(support.directNoThermalSupport) || support.directNoThermalSupport < 0 || support.directNoThermalSupport > inputs.length ||
      c.noThermalSupportQueries !== support.stencilNoThermalSupport + support.directNoThermalSupport) throw new Error('Diagnostic query/support ledger failed');
  const byId = new Map(); for (const input of inputs) {
    if (!Number.isSafeInteger(input.id) || byId.has(input.id) || !vec(input.position) || !Number.isFinite(input.age) || input.age < 0 || input.frame !== record.frame || input.fieldTime !== d.fieldTime || input.newborn !== (input.age === 0)) throw new Error('Invalid actual preadvection input');
    byId.set(input.id, input);
  }
  const modelById = new Map(), membership = new Map();
  for (const m of d.models) {
    if (!Number.isSafeInteger(m.id) || modelById.has(m.id) || !vec(m.center) || !vec(m.Ju, 9) || !vec(m.gradTb) || !Number.isFinite(m.radius) || m.radius < 0 || !Array.isArray(m.memberIds) || !m.memberIds.length || m.stencil.length !== 7) throw new Error('Invalid affine model');
    modelById.set(m.id, m); const members = m.memberIds.map(id => { if (!byId.has(id) || membership.has(id)) throw new Error('Invalid group membership'); membership.set(id, m.id); return byId.get(id); }).sort((a, b) => a.id - b.id);
    const center = [0, 0, 0]; for (const p of members) for (let axis = 0; axis < 3; axis++) center[axis] += p.position[axis];
    for (let axis = 0; axis < 3; axis++) { center[axis] /= members.length; close(center[axis], m.center[axis], 'centroid'); }
    close(Math.max(...members.map(p => Math.hypot(...difference(p.position, center)))), m.radius, 'radius');
    for (let k = 0; k < 7; k++) {
      const q = m.stencil[k], expected = [...m.center]; if (k) expected[Math.floor((k - 1) / 2)] += k % 2 ? d.delta : -d.delta;
      if (!vec(q.position) || ![q.raw.ux, q.raw.uy, q.raw.uz, q.raw.Tb, q.raw.thermalWeight].every(Number.isFinite)) throw new Error('Nonfinite stencil query');
      for (let axis = 0; axis < 3; axis++) close(q.position[axis], expected[axis], 'stencil position');
    }
    for (let axis = 0; axis < 3; axis++) {
      const plus = m.stencil[1 + 2 * axis].raw, minus = m.stencil[2 + 2 * axis].raw;
      for (const [component, key] of ['ux', 'uy', 'uz'].entries()) close(m.Ju[component * 3 + axis], (plus[key] - minus[key]) / (2 * d.delta), 'velocity Jacobian');
      close(m.gradTb[axis], (plus.Tb - minus.Tb) / (2 * d.delta), 'temperature gradient');
    }
  }
  if (membership.size !== inputs.length) throw new Error('Groups do not cover every captured input');
  const total = { count: 0, groupCount: d.models.length, modelQueries: 7 * d.models.length, directReferenceQueries: inputs.length,
    inducedVelocitySquaredError: 0, totalVelocitySquaredError: 0, temperatureSquaredError: 0, temperatureDifferenceSum: 0,
    rawTemperatureSquaredError: 0, rawTemperatureDifferenceSum: 0,
    clippedLow: 0, clippedHigh: 0, directNoThermalSupport: 0, stencilNoThermalSupport: support.stencilNoThermalSupport,
    directUnsupportedPositivePrediction: 0, directSpeedClamped: 0, predictedSpeedClamped: 0,
    newborn: 0, maximumRadius: d.models.length ? Math.max(...d.models.map(m => m.radius)) : null };
  const distances = [], ids = new Set();
  for (const p of d.points) {
    const input = byId.get(p.id), m = modelById.get(p.groupId);
    if (!input || !m || ids.has(p.id) || membership.get(p.id) !== p.groupId || JSON.stringify(p.position) !== JSON.stringify(input.position) || p.age !== input.age || p.newborn !== input.newborn) throw new Error('Prediction lost captured-input identity'); ids.add(p.id);
    const a = p.direct, b = p.prediction;
    for (const q of [a, b]) if (!vec(q.velocity) || !vec(q.preClampVelocity) || !Number.isFinite(q.preClampSpeed) || typeof q.speedClamped !== 'boolean') throw new Error('Nonfinite final field');
    if (![a.raw.ux, a.raw.uy, a.raw.uz, a.raw.Tb, a.raw.thermalWeight, b.raw.ux, b.raw.uy, b.raw.uz, b.raw.TbRaw, b.raw.Tb].every(Number.isFinite)) throw new Error('Nonfinite raw field');
    const dx = difference(p.position, m.center), origin = m.stencil[0].raw;
    for (const [component, key] of ['ux', 'uy', 'uz'].entries()) close(b.raw[key], origin[key] + m.Ju[component * 3] * dx[0] + m.Ju[component * 3 + 1] * dx[1] + m.Ju[component * 3 + 2] * dx[2], 'affine velocity');
    close(b.raw.TbRaw, origin.Tb + m.gradTb[0] * dx[0] + m.gradTb[1] * dx[1] + m.gradTb[2] * dx[2], 'affine temperature');
    close(b.raw.Tb, Math.max(spec.temperatureClip[0], Math.min(spec.temperatureClip[1], b.raw.TbRaw)), 'temperature clip');
    if (b.raw.clippedLow !== (b.raw.TbRaw < spec.temperatureClip[0]) || b.raw.clippedHigh !== (b.raw.TbRaw > spec.temperatureClip[1])) throw new Error('Temperature clip flags differ');
    const induced = squared(['ux', 'uy', 'uz'].map(k => b.raw[k] - a.raw[k])), final = squared(difference(b.velocity, a.velocity)), tb = b.raw.Tb - a.raw.Tb;
    total.count++; total.inducedVelocitySquaredError += induced; total.totalVelocitySquaredError += final; total.temperatureSquaredError += tb * tb; total.temperatureDifferenceSum += tb;
    const rawTbDifference = b.raw.TbRaw - a.raw.Tb; total.rawTemperatureSquaredError += rawTbDifference * rawTbDifference; total.rawTemperatureDifferenceSum += rawTbDifference;
    total.clippedLow += +b.raw.clippedLow; total.clippedHigh += +b.raw.clippedHigh; total.directNoThermalSupport += +(a.raw.thermalWeight === 0);
    total.directUnsupportedPositivePrediction += +(a.raw.thermalWeight === 0 && b.raw.Tb > 0);
    total.directSpeedClamped += +a.speedClamped; total.predictedSpeedClamped += +b.speedClamped; total.newborn += +input.newborn; distances.push(Math.sqrt(final));
  }
  if (total.directNoThermalSupport !== support.directNoThermalSupport || total.directUnsupportedPositivePrediction !== support.directUnsupportedPositivePrediction ||
      total.clippedLow !== c.affineTbClippedLow || total.clippedHigh !== c.affineTbClippedHigh) throw new Error('Diagnostic point/support counters disagree');
  distances.sort((a, b) => a - b);
  return { ...total, inducedVelocityRmse: total.count ? Math.sqrt(total.inducedVelocitySquaredError / total.count) : null,
    totalVelocityRmse: total.count ? Math.sqrt(total.totalVelocitySquaredError / total.count) : null,
    totalVelocityP99: total.count ? distances[Math.floor((total.count - 1) * .99)] : null,
    temperatureRmse: total.count ? Math.sqrt(total.temperatureSquaredError / total.count) : null,
    temperatureSignedBias: total.count ? total.temperatureDifferenceSum / total.count : null,
    rawTemperatureRmse: total.count ? Math.sqrt(total.rawTemperatureSquaredError / total.count) : null,
    rawTemperatureSignedBias: total.count ? total.rawTemperatureDifferenceSum / total.count : null,
    interpretation: 'Same-position DD-input field diagnostic only; these are not cumulative trajectory error bounds or timing gates.' };
}
