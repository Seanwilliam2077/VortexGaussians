import { createHash } from 'node:crypto';
import { imageError, poolErrors, validateImage } from './p3-metrics.mjs';

export const PARTICLE_COLUMNS = ['id', 'x', 'y', 'z', 'vx', 'vy', 'vz', 'T', 'd', 'life'];
export function encodeParticles(points) {
  const ids = new Set(), bytes = Buffer.alloc(points.length * PARTICLE_COLUMNS.length * 8);
  points.forEach((p, i) => {
    if (!Number.isSafeInteger(p.id) || p.id < 0 || ids.has(p.id)) throw new Error('Invalid or duplicate stable birth ID');
    ids.add(p.id);
    PARTICLE_COLUMNS.forEach((key, k) => { if (!Number.isFinite(p[key])) throw new Error(`Nonfinite or missing particle ${key}`); bytes.writeDoubleLE(p[key], (i * PARTICLE_COLUMNS.length + k) * 8); });
  });
  return { bytes, count: points.length, columns: PARTICLE_COLUMNS, type: 'float64', endianness: 'little',
    sha256: createHash('sha256').update(bytes).digest('hex') };
}
export function decodeParticles(bytes, metadata) {
  if (JSON.stringify(metadata.columns) !== JSON.stringify(PARTICLE_COLUMNS) || bytes.length !== metadata.count * PARTICLE_COLUMNS.length * 8) throw new Error('Particle binary layout/length mismatch');
  if (createHash('sha256').update(bytes).digest('hex') !== metadata.sha256) throw new Error('Particle binary checksum mismatch');
  const points = Array.from({ length: metadata.count }, (_, i) => Object.fromEntries(PARTICLE_COLUMNS.map((key, k) => [key, bytes.readDoubleLE((i * PARTICLE_COLUMNS.length + k) * 8)])));
  const ids = new Set(); for (const p of points) { if (!Number.isSafeInteger(p.id) || ids.has(p.id) || Object.values(p).some(x => !Number.isFinite(x))) throw new Error('Invalid decoded particle'); ids.add(p.id); }
  return points;
}

export function pairedParticles(candidate, reference) {
  const index = points => { const map = new Map(); for (const p of points) { if (map.has(p.id)) throw new Error('Duplicate birth ID in path comparison'); map.set(p.id, p); } return map; };
  const a = index(candidate), b = index(reference), distances = [], velocityDistances = [];
  const onlyCandidate = [], onlyReference = [], visualStateMismatchIds = []; let positionSquaredError = 0, velocitySquaredError = 0, treeVelocitySquared = 0;
  for (const [id, p] of a) {
    const q = b.get(id); if (!q) { onlyCandidate.push(id); continue; }
    if (p.T !== q.T || p.d !== q.d || p.life !== q.life) visualStateMismatchIds.push(id);
    const d2 = (p.x - q.x) ** 2 + (p.y - q.y) ** 2 + (p.z - q.z) ** 2;
    const v2 = (p.vx - q.vx) ** 2 + (p.vy - q.vy) ** 2 + (p.vz - q.vz) ** 2;
    if (![d2, v2].every(Number.isFinite)) throw new Error('Nonfinite paired particle error');
    distances.push(Math.sqrt(d2)); velocityDistances.push(Math.sqrt(v2));
    positionSquaredError += d2; velocitySquaredError += v2; treeVelocitySquared += q.vx ** 2 + q.vy ** 2 + q.vz ** 2;
  }
  for (const id of b.keys()) if (!a.has(id)) onlyReference.push(id);
  distances.sort((x, y) => x - y); velocityDistances.sort((x, y) => x - y);
  const n = distances.length, quantile = (v, p) => v.length ? v[Math.floor((v.length - 1) * p)] : null;
  return { matched: n, candidateCount: a.size, referenceCount: b.size, onlyCandidate, onlyReference, visualStateMismatchIds,
    positionSquaredError, velocitySquaredError, treeVelocitySquared,
    positionRmse: n ? Math.sqrt(positionSquaredError / n) : null, positionP99: quantile(distances, .99), positionMaximum: distances.at(-1) ?? null,
    velocityRmse: n ? Math.sqrt(velocitySquaredError / n) : null, velocityP99: quantile(velocityDistances, .99),
    velocityRelativeRmse: treeVelocitySquared > 0 ? Math.sqrt(velocitySquaredError / treeVelocitySquared) : null };
}

export function pairedImageError(candidate, tree, masks, thresholds) {
  validateImage(tree); const result = imageError(candidate, tree, { ...thresholds, ...masks });
  for (const name of ['full', 'foreground']) {
    let rgbSignalSquared = 0, alphaSignalSquared = 0;
    for (let p = 0; p < tree.width * tree.height; p++) {
      if (name === 'foreground' && !masks.foregroundMask[p]) continue;
      for (let c = 0; c < 3; c++) rgbSignalSquared += tree.data[4 * p + c] ** 2;
      alphaSignalSquared += tree.data[4 * p + 3] ** 2;
    }
    Object.assign(result[name], { rgbSignalSquared, alphaSignalSquared,
      rgbNrmse: rgbSignalSquared > 0 ? Math.sqrt(result[name].rgbSquaredError / rgbSignalSquared) : null,
      alphaNrmse: alphaSignalSquared > 0 ? Math.sqrt(result[name].alphaSquaredError / alphaSignalSquared) : null });
  }
  return result;
}
export function poolPairedImages(errors) {
  const pooled = poolErrors(errors);
  for (const name of ['full', 'foreground']) {
    const rgbSignalSquared = errors.reduce((sum, e) => sum + e[name].rgbSignalSquared, 0);
    const alphaSignalSquared = errors.reduce((sum, e) => sum + e[name].alphaSignalSquared, 0);
    Object.assign(pooled[name], { rgbSignalSquared, alphaSignalSquared,
      rgbNrmse: rgbSignalSquared > 0 ? Math.sqrt(pooled[name].rgbSquaredError / rgbSignalSquared) : null,
      alphaNrmse: alphaSignalSquared > 0 ? Math.sqrt(pooled[name].alphaSquaredError / alphaSignalSquared) : null });
  }
  return pooled;
}

export function approximationGate(comparison, spec) {
  const paths = comparison.paths.filter(p => p.frame > 0);
  const maxPositionRmse = paths.length && paths.every(p => Number.isFinite(p.positionRmse)) ? Math.max(...paths.map(p => p.positionRmse)) : null;
  const maxPositionP99 = paths.length && paths.every(p => Number.isFinite(p.positionP99)) ? Math.max(...paths.map(p => p.positionP99)) : null;
  const checks = {
    completeSampleFrames: paths.length === spec.expectedSampleFrames.length && new Set(paths.map(p => p.frame)).size === paths.length && spec.expectedSampleFrames.every(f => paths.some(p => p.frame === f)),
    completeImageCaptures: comparison.images.length === spec.expectedCaptureKeys.length && new Set(comparison.images.map(i => `${i.frame}-${i.view.id}`)).size === comparison.images.length && spec.expectedCaptureKeys.every(k => comparison.images.some(i => `${i.frame}-${i.view.id}` === k)),
    foregroundAlphaNrmse: Number.isFinite(comparison.pooled.foreground.alphaNrmse) && comparison.pooled.foreground.alphaNrmse <= spec.maximumForegroundAlphaNrmse,
    foregroundRgbNrmse: Number.isFinite(comparison.pooled.foreground.rgbNrmse) && comparison.pooled.foreground.rgbNrmse <= spec.maximumForegroundRgbNrmse,
    worstCheckpointPositionRmse: Number.isFinite(maxPositionRmse) && maxPositionRmse <= spec.maximumCheckpointPositionRmse,
    worstCheckpointPositionP99: Number.isFinite(maxPositionP99) && maxPositionP99 <= spec.maximumCheckpointPositionP99,
    noUnmatchedIds: paths.length > 0 && paths.every(p => p.onlyCandidate.length === 0 && p.onlyReference.length === 0),
    unchangedVisualEvolution: paths.every(p => p.visualStateMismatchIds.length === 0),
    noFallbacks: comparison.cacheFallbacks === 0, noCapacityBlocks: comparison.capacityBlocks === 0,
    exactPhysicsAndBirthRng: comparison.physicsAndBirthRngMatched === true
  };
  return { passed: Object.values(checks).every(Boolean), checks, maxPositionRmse, maxPositionP99,
    foregroundAlphaNrmse: comparison.pooled.foreground.alphaNrmse, foregroundRgbNrmse: comparison.pooled.foreground.rgbNrmse };
}

export function aggregateTiming(results, scenarios, methods, repeats = 5) {
  const median = a => [...a].sort((x, y) => x - y)[Math.floor(a.length / 2)];
  const groups = [];
  for (const scenario of scenarios) for (const method of methods) {
    const runs = results.filter(r => r.definition.scenario === scenario.id && r.definition.method === method.id);
    const complete = runs.length === repeats && new Set(runs.map(r => r.definition.repeat)).size === repeats && runs.every(r => r.status === 'passed' && r.timings.length === 41);
    const record = { scenario: scenario.id, method: method.id, complete,
      interpretation: 'Central is median of independent run medians; tail is median of independent run p95 values, not pooled-frame p95.' };
    if (complete) {
      record.runs = runs.map(r => ({ id: r.definition.id, median: r.distributions.totalMs.median, p95: r.distributions.totalMs.p95, samples: r.timings.length }));
      record.centralMs = median(record.runs.map(r => r.median)); record.tailMs = median(record.runs.map(r => r.p95));
      record.worstRunP95Ms = Math.max(...record.runs.map(r => r.p95));
    }
    groups.push(record);
  }
  return groups;
}

export function selectCache(comparisons, timings, spec, scenarios, methods) {
  const calibration = comparisons.filter(c => c.scenario === spec.scenario && c.seed === spec.physicsSeed && c.renderSeed === spec.renderSeed);
  const candidates = methods.filter(m => m.mode === 'grid').map(m => {
    const quality = calibration.find(c => c.method === m.id), timing = timings.find(t => t.scenario === spec.scenario && t.method === m.id);
    return { method: m.id, cellSize: m.cellSize, eligible: quality?.errorGate.passed === true && timing?.complete === true,
      qualityAvailable: !!quality, errorGate: quality?.errorGate || null, centralMs: timing?.centralMs ?? null };
  });
  const calibrationComplete = calibration.length === candidates.length && candidates.every(c => c.qualityAvailable && Number.isFinite(c.centralMs));
  const eligible = calibrationComplete ? candidates.filter(c => c.eligible).sort((a, b) => a.centralMs - b.centralMs || a.cellSize - b.cellSize) : [];
  const selected = eligible[0]?.method || null;
  const heldout = selected ? comparisons.filter(c => c.method === selected && !(c.scenario === spec.scenario && c.seed === spec.physicsSeed && c.renderSeed === spec.renderSeed)) : [];
  const cost = selected ? scenarios.map(s => {
    const tree = timings.find(t => t.scenario === s.id && t.method === 'tree'), grid = timings.find(t => t.scenario === s.id && t.method === selected);
    const valid = tree?.complete && grid?.complete && tree.centralMs > 0 && grid.centralMs > 0;
    const speedup = valid ? tree.centralMs / grid.centralMs : null, tailRatio = valid && tree.tailMs > 0 ? grid.tailMs / tree.tailMs : null;
    return { scenario: s.id, centralSpeedup: speedup, medianRunP95Ratio: tailRatio,
      passed: valid && speedup >= spec.minimumRouteMedianSpeedup && tailRatio !== null && tailRatio <= spec.maximumRouteP95Ratio };
  }) : [];
  return { selected, candidates, calibrationComplete,
    selectionUsedOnly: { scenario: spec.scenario, physicsSeed: spec.physicsSeed, renderSeed: spec.renderSeed },
    heldout: heldout.map(c => ({ candidate: c.candidate, scenario: c.scenario, seed: c.seed, renderSeed: c.renderSeed, passed: c.errorGate.passed })),
    cost, routeGo: !!selected && heldout.length === 8 && heldout.every(c => c.errorGate.passed) && cost.length === scenarios.length && cost.every(c => c.passed),
    reason: selected ? null : 'No grid passed development error constraints with complete timing, or required evidence is missing. Heldout outcomes were not used to change this selection.' };
}
