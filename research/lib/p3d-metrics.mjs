import { createHash } from 'node:crypto';

export function requireFrozenChecksum(bytes, expected, label) {
  const actual = createHash('sha256').update(bytes).digest('hex');
  if (actual !== expected) throw new Error(`Frozen baseline checksum mismatch: ${label}`); return actual;
}
export function requireOldFields(reference, candidate, label = 'snapshot') {
  if (reference === null || typeof reference !== 'object') {
    if (!Object.is(reference, candidate)) throw new Error(`Legacy field differs: ${label}`); return true;
  }
  if (typeof candidate !== 'object' || candidate === null || Array.isArray(reference) !== Array.isArray(candidate)) throw new Error(`Legacy field type differs: ${label}`);
  if (Array.isArray(reference) && reference.length !== candidate.length) throw new Error(`Legacy array length differs: ${label}`);
  for (const key of Object.keys(reference)) { if (!(key in candidate)) throw new Error(`Legacy field missing: ${label}.${key}`); requireOldFields(reference[key], candidate[key], `${label}.${key}`); }
  return true;
}
export function exactTracerReplay(reference, candidate) {
  if (!Array.isArray(reference) || !Array.isArray(candidate) || reference.length !== candidate.length || !reference.length) throw new Error('Tracer hash trace incomplete');
  for (let i = 0; i < reference.length; i++) {
    if (reference[i].frame !== i || candidate[i].frame !== i || !reference[i].tracerHash || reference[i].tracerHash !== candidate[i].tracerHash) throw new Error(`Tracer hash differs at step ${i}`);
  }
  return true;
}
export function compareRecordedHashes(reference, candidate, { partial = false } = {}) {
  const particleChecks = [], imageChecks = [];
  for (const p of candidate.checkpoints) {
    const r = reference.checkpoints.find(v => v.frame === p.frame);
    if (!r || r.particles.sha256 !== p.particles.sha256) throw new Error(`Particle binary SHA differs at frame ${p.frame}`);
    particleChecks.push({ frame: p.frame, reference: r.particles.file, candidate: p.particles.file, sha256: p.particles.sha256 });
  }
  for (const p of candidate.captures) {
    const r = reference.captures.find(v => v.frame === p.frame && v.view.id === p.view.id);
    if (!r && partial) continue;
    if (!r || r.image.sha256 !== p.image.sha256) throw new Error(`RGBA SHA differs at frame ${p.frame}/${p.view.id}`);
    imageChecks.push({ frame: p.frame, view: p.view.id, reference: r.image.file, candidate: p.image.file, sha256: p.image.sha256 });
  }
  if (!partial && (particleChecks.length !== 13 || imageChecks.length !== 6 || reference.checkpoints.length !== 13 || candidate.checkpoints.length !== 13 || reference.captures.length !== 6 || candidate.captures.length !== 6)) throw new Error('Exact replay has incomplete captures');
  return { passed: true, particleChecks, imageChecks, partial, interpretation: 'SHA equality of independently verified bytes; previews are excluded from numerical equality.' };
}
export function costDecision(timings, spec, scenarios, evidenceComplete, accuracyPassed = true) {
  const cost = scenarios.map(scene => {
    const find = method => timings.find(t => t.scenario === scene.id && t.method === method);
    const dd = find('DD'), original = find('DG-original'), specialized = find('DG-specialized');
    const valid = [dd, original, specialized].every(t => t?.complete && Number.isFinite(t.centralMs) && t.centralMs > 0 && Number.isFinite(t.tailMs) && t.tailMs > 0);
    const centralSpeedup = valid ? dd.centralMs / specialized.centralMs : null, tailRatio = valid ? specialized.tailMs / dd.tailMs : null;
    return { scenario: scene.id, complete: !!valid, centralSpeedup, medianRunP95Ratio: tailRatio,
      specializationSpeedup: valid ? original.centralMs / specialized.centralMs : null,
      passed: !!valid && centralSpeedup >= spec.minimumCentralSpeedup && tailRatio <= spec.maximumMedianRunP95Ratio };
  });
  return { cost, evidenceComplete, accuracyPassed, engineeringGo: evidenceComplete && accuracyPassed && cost.length === scenarios.length && cost.every(c => c.passed),
    interpretation: 'Central is median of five run medians; tail is median of five run p95 values, not pooled-frame p95. Every condition must pass; no parameters are reselected.' };
}
