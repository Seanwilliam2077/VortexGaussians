import { pairedParticles } from './p3b-metrics.mjs';

export function ageBin(life, spec) {
  const steps = Math.round(life / spec.dt);
  if (!Number.isFinite(life) || life < 0 || Math.abs(life - steps * spec.dt) >= spec.ageStepTolerance) throw new Error('Particle age is not an integer integration-step count');
  return spec.ageBins.find(b => steps >= b.minSteps && (b.maxSteps === null || steps < b.maxSteps)).id;
}
const newSums = () => ({ count: 0, ySum: 0, ySquared: 0, xzSquared: 0, positionSquared: 0 });
function add(s, dx, dy, dz) { s.count++; s.ySum += dy; s.ySquared += dy * dy; s.xzSquared += dx * dx + dz * dz; s.positionSquared += dx * dx + dy * dy + dz * dz; }
export function finishSums(s) { return { ...s, ySignedBias: s.count ? s.ySum / s.count : null,
  yRmse: s.count ? Math.sqrt(s.ySquared / s.count) : null, xzRmse: s.count ? Math.sqrt(s.xzSquared / s.count) : null,
  positionRmse: s.count ? Math.sqrt(s.positionSquared / s.count) : null }; }
function index(points) { const map = new Map(); for (const p of points) { if (map.has(p.id)) throw new Error('Duplicate stable birth ID'); map.set(p.id, p); } return map; }
export function directionalPaths(candidate, reference, spec) {
  const base = pairedParticles(candidate, reference), b = index(reference), total = newSums();
  const bins = Object.fromEntries(spec.ageBins.map(bin => [bin.id, newSums()]));
  const norms = Object.fromEntries(spec.ageBins.map(bin => [bin.id, []]));
  for (const p of candidate) {
    const q = b.get(p.id); if (!q) continue;
    const bin = ageBin(q.life, spec), delta = [p.x - q.x, p.y - q.y, p.z - q.z]; add(total, ...delta); add(bins[bin], ...delta);
    norms[bin].push(Math.hypot(...delta));
  }
  return { ...base, matchedOpticalWeight: base.matched * spec.nSim / spec.nRender,
    onlyArmOpticalWeight: base.onlyCandidate.length * spec.nSim / spec.nRender, onlyDDOpticalWeight: base.onlyReference.length * spec.nSim / spec.nRender,
    directional: finishSums(total), ageBins: Object.fromEntries(Object.entries(bins).map(([k, v]) => {
    norms[k].sort((a, b) => a - b); return [k, { ...finishSums(v), positionP99: norms[k].length ? norms[k][Math.floor((norms[k].length - 1) * .99)] : null }];
  })) };
}
export function poolDirectional(records, spec) {
  const pool = list => { const total = newSums(); for (const s of list) for (const k of Object.keys(total)) total[k] += s[k]; return finishSums(total); };
  return { directional: pool(records.map(r => r.directional)),
    ageBins: Object.fromEntries(spec.ageBins.map(b => [b.id, pool(records.map(r => r.ageBins[b.id]))])),
    interpretation: 'Pooled over matched particle-checkpoints; repeated observations of a particle are not independent samples.' };
}

function interactionFinish(s) {
  const rms = key => s.count ? Math.sqrt(s[key] / s.count) : null;
  return { ...s, gdRmse: rms('gdSquared'), dgRmse: rms('dgSquared'), ggRmse: rms('ggSquared'), interactionRmse: rms('interactionSquared'),
    gdOverGg: s.ggSquared > 0 ? Math.sqrt(s.gdSquared / s.ggSquared) : null,
    dgOverGg: s.ggSquared > 0 ? Math.sqrt(s.dgSquared / s.ggSquared) : null,
    interactionOverGg: s.ggSquared > 0 ? Math.sqrt(s.interactionSquared / s.ggSquared) : null };
}
export function interactionPaths(arms) {
  for (const name of ['DD', 'GD', 'DG', 'GG']) if (!arms[name]) throw new Error(`Missing interaction arm ${name}`);
  const maps = Object.fromEntries(Object.entries(arms).map(([k, v]) => [k, index(v)]));
  const sums = { count: 0, gdSquared: 0, dgSquared: 0, ggSquared: 0, interactionSquared: 0 }, missingByArm = { DD: [], GD: [], DG: [], GG: [] };
  const union = [...new Set(Object.values(maps).flatMap(m => [...m.keys()]))];
  for (const id of union) {
    const absent = Object.keys(maps).filter(k => !maps[k].has(id));
    if (absent.length) { for (const k of absent) missingByArm[k].push(id); continue; }
    const [dd, gd, dg, gg] = ['DD', 'GD', 'DG', 'GG'].map(k => maps[k].get(id));
    if ([gd, dg, gg].some(p => p.T !== dd.T || p.d !== dd.d || p.life !== dd.life)) throw new Error('Interaction arms changed matched visual evolution');
    sums.count++;
    for (const key of ['x', 'y', 'z']) {
      const a = gd[key] - dd[key], b = dg[key] - dd[key], c = gg[key] - dd[key], e = c - a - b;
      if (![a, b, c, e].every(Number.isFinite)) throw new Error('Nonfinite interaction vector');
      sums.gdSquared += a * a; sums.dgSquared += b * b; sums.ggSquared += c * c; sums.interactionSquared += e * e;
    }
  }
  return { ...interactionFinish(sums), missingByArm, unionCount: union.length, excludedCount: union.length - sums.count,
    countsByArm: Object.fromEntries(Object.entries(maps).map(([k, v]) => [k, v.size])),
    definition: 'Per-ID vector eI=(GG-DD)-(GD-DD)-(DG-DD); RMS ratios are not additive percentages of error.' };
}
export function poolInteraction(records) {
  const sums = { count: 0, gdSquared: 0, dgSquared: 0, ggSquared: 0, interactionSquared: 0 };
  for (const r of records) for (const key of Object.keys(sums)) sums[key] += r[key];
  return { ...interactionFinish(sums), interpretation: 'Ratios of pooled vector RMS over common particle-checkpoints. Zero GG denominator yields null; no dominant-component label is assigned.' };
}

export function summarizeInputs(checkpoints, spec) {
  const summaries = [];
  for (const c of checkpoints) {
    if (!c.inputs) continue;
    if (!c.probe || c.inputs.length !== c.probe.samples.length) throw new Error('Captured DD inputs and field probes differ in count');
    const total = { count: 0, sumTbDifference: 0, inducedVelocitySquared: 0, temperatureSquared: 0, DD: 0, GD: 0, DG: 0, GG: 0,
      interactionSquared: 0, directNoThermalSupport: 0, gridNoThermalSupport: 0, directSupportButPartialGrid: 0,
      speedClamped: { DD: 0, GD: 0, DG: 0, GG: 0 }, newborn: 0, maximumPreClampInteraction: 0 };
    const probeSums = () => ({ count: 0, sumTbDifference: 0, temperatureSquared: 0, inducedVelocitySquared: 0, GD: 0, DG: 0, GG: 0, interactionSquared: 0 });
    const bins = Object.fromEntries(spec.ageBins.map(b => [b.id, probeSums()]));
    const supportGroups = Object.fromEntries(['supported', 'unsupported'].flatMap(d => ['zero', 'partial', 'full'].map(g => [`${d}-${g}`, probeSums()])));
    c.inputs.forEach((input, i) => {
      const s = c.probe.samples[i], vector = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
      if (!vector(input.position) || !vector(s.position) || !Number.isInteger(input.id) || input.id < 0 ||
          ![s.tree.Tb, s.tree.thermalWeight, s.grid.Tb, s.grid.supportFraction, s.errors.inducedVelocitySquared, s.errors.temperatureSquared].every(Number.isFinite)) throw new Error('Nonfinite or malformed captured field sample');
      for (const arm of ['DD', 'GD', 'DG', 'GG']) {
        const f = s.combinations[arm];
        if (!vector(s.transportVelocities[arm]) || !vector(f.inducedVelocity) || !vector(f.velocity) || !vector(f.preClampVelocity) ||
            !Number.isFinite(f.Tb) || !Number.isFinite(f.preClampSpeed) || typeof f.speedClamped !== 'boolean') throw new Error('Nonfinite or malformed component vector');
      }
      if (input.id % spec.inputStride !== 0 || JSON.stringify(input.position) !== JSON.stringify(s.position)) throw new Error('Probe lost exact captured DD position or ID sampling');
      if (input.frame !== c.frame || input.fieldTime !== c.probe.fieldTime || input.newborn !== (input.age === 0)) throw new Error('Captured input frame, field time, or newborn age mismatch');
      const pre = s.combinations;
      const preInteraction = Math.hypot(...pre.GG.preClampVelocity.map((v, a) => v - pre.GD.preClampVelocity[a] - pre.DG.preClampVelocity[a] + pre.DD.preClampVelocity[a]));
      total.maximumPreClampInteraction = Math.max(total.maximumPreClampInteraction, preInteraction);
      if (!Number.isFinite(preInteraction) || preInteraction > 1e-12) throw new Error('Pre-clamp component composition is not additive');
      const bin = bins[ageBin(input.age, spec)], support = s.grid.supportFraction;
      const supportClass = support <= 0 ? 'zero' : support >= 1 - 1e-12 ? 'full' : 'partial';
      const group = supportGroups[`${s.tree.thermalWeight > 0 ? 'supported' : 'unsupported'}-${supportClass}`];
      total.count++; bin.count++; group.count++; total.newborn += +input.newborn;
      for (const x of [bin, group]) { x.sumTbDifference += s.grid.Tb - s.tree.Tb; x.temperatureSquared += s.errors.temperatureSquared; x.inducedVelocitySquared += s.errors.inducedVelocitySquared; }
      total.inducedVelocitySquared += s.errors.inducedVelocitySquared; total.temperatureSquared += s.errors.temperatureSquared;
      total.sumTbDifference += s.grid.Tb - s.tree.Tb;
      total.directNoThermalSupport += +(s.tree.thermalWeight === 0); total.gridNoThermalSupport += +(s.grid.supportFraction === 0);
      total.directSupportButPartialGrid += +(s.tree.thermalWeight > 0 && supportClass === 'partial');
      const vectors = s.transportVelocities, diff = {};
      for (const arm of ['DD', 'GD', 'DG', 'GG']) {
        diff[arm] = vectors[arm].map((x, axis) => x - vectors.DD[axis]);
        const sq = diff[arm].reduce((sum, x) => sum + x * x, 0); total[arm] += sq;
        if (arm !== 'DD') { bin[arm] += sq; group[arm] += sq; }
        total.speedClamped[arm] += +s.combinations[arm].speedClamped;
      }
      const interactionSquared = diff.GG.reduce((sum, x, axis) => sum + (x - diff.GD[axis] - diff.DG[axis]) ** 2, 0);
      total.interactionSquared += interactionSquared; bin.interactionSquared += interactionSquared; group.interactionSquared += interactionSquared;
    });
    const finalize = x => ({ ...x, tbSignedBias: x.count && x.sumTbDifference !== undefined ? x.sumTbDifference / x.count : null,
      tbRmse: x.count ? Math.sqrt(x.temperatureSquared / x.count) : null,
      inducedVelocityRmse: x.count ? Math.sqrt(x.inducedVelocitySquared / x.count) : null,
      gdVelocityRmse: x.count ? Math.sqrt(x.GD / x.count) : null,
      dgVelocityRmse: x.count ? Math.sqrt(x.DG / x.count) : null, ggVelocityRmse: x.count ? Math.sqrt(x.GG / x.count) : null,
      interactionVelocityRmse: x.count ? Math.sqrt(x.interactionSquared / x.count) : null });
    summaries.push({ frame: c.frame, time: c.time, fieldTime: c.probe.fieldTime, ...finalize(total),
      ageBins: Object.fromEntries(Object.entries(bins).map(([k, x]) => [k, finalize(x)])),
      supportGroups: Object.fromEntries(Object.entries(supportGroups).map(([k, x]) => [k, finalize(x)])) });
  }
  return summaries;
}
