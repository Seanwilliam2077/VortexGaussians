import { P1_DEFAULTS } from './p1-design.mjs';

export const P2_DEFAULTS = Object.freeze({ ...P1_DEFAULTS, spreadClockMode: 'elapsed',
  spreadParticlePolicy: 'recycle-cold', spreadMeasureMode: 'legacy', spreadReferenceArea: .0016,
  spreadAreaFeedRate: 30, ppl: 1200, spreadFrontierCap: 1000000, spreadSampleCap: 1000000, spreadFeedCap: 1000000 });

export function p2Cases(suite = 'all', seeds = [11, 23, 47]) {
  if (!Array.isArray(seeds) || !seeds.length || seeds.some(s => !Number.isInteger(s) || s < 0 || s > 0xffffffff) || new Set(seeds).size !== seeds.length) throw new Error('Seeds must be distinct uint32 integers');
  const cases = [], quick = suite === 'quick';
  const add = (family, kind, variant, mode, order = 'forward', selectedSeeds = [seeds[0]]) => {
    for (const seed of selectedSeeds) cases.push({ id: `p2-${family}-${variant}-${mode}-${order}-seed${seed}`,
      family, kind, variant, order, seed, frames: quick ? 120 : family === 'closed-loop' ? 720 : 480,
      dt: 1 / 60, sampleEvery: 15, yaw: 0,
      params: { ...P2_DEFAULTS, spreadMeasureMode: mode,
        spreadFlameHeat: family === 'closed-loop', spreadSceneFeed: family === 'closed-loop' } });
  };
  if (['all', 'quick', 'graph', 'graph-duplicates'].includes(suite)) {
    for (const variant of quick ? ['base', 'uniform4'] : ['base', 'uniform2', 'uniform4', 'variable-both', 'variable-source', 'variable-target']) {
      for (const mode of ['legacy', 'area']) for (const order of ['forward', 'shuffle']) add('graph-duplicate', 'surface', variant, mode, order);
    }
  }
  if (['all', 'quick', 'refinement'].includes(suite)) {
    for (const variant of quick ? ['base', 'adaptive'] : ['base', 'refine3', 'refine5', 'adaptive']) {
      for (const mode of ['legacy', 'area']) add('refinement', 'surface', variant, mode);
    }
  }
  if (['all', 'quick', 'closed-loop', 'feedback'].includes(suite)) {
    for (const variant of quick ? ['base', 'uniform4'] : ['base', 'uniform2', 'uniform4', 'variable-both']) {
      for (const mode of ['legacy', 'area']) add('closed-loop', 'raised-target', variant, mode, 'forward', seeds);
    }
  }
  if (!cases.length) throw new Error(`Unknown P2 suite ${suite}; use all, quick, graph-duplicates, refinement, feedback`);
  return cases;
}

export function configureP2(args, config = {}) {
  if (config.params && Object.keys(config.params).length) throw new Error('P2 policy parameters are frozen; create a separately named protocol for tuning');
  if (config.frames !== undefined && config.seconds !== undefined) throw new Error('Config cannot specify both frames and seconds');
  return p2Cases(args.suite, args.seeds ?? config.seeds ?? (args.suite === 'quick' ? [11] : [11, 23, 47])).map(c => {
    const dt = args.dt ?? config.dt ?? c.dt;
    const frames = args.frames ?? (args.seconds != null ? Math.ceil(args.seconds / dt) : config.frames ?? (config.seconds != null ? Math.ceil(config.seconds / dt) : c.frames));
    const sampleEvery = args.sampleEvery ?? config.sampleEvery ?? c.sampleEvery;
    if (!(Number.isFinite(dt) && dt > 0 && Number.isInteger(frames) && frames > 0 && Number.isInteger(sampleEvery) && sampleEvery > 0)) throw new Error('Invalid P2 time configuration');
    return { ...c, dt, frames, sampleEvery };
  });
}

export function compareP2(result, reference) {
  const out = { reference: reference.definition.id, candidate: result.definition.id,
    kind: result.definition.family === 'refinement' ? 'refinement-diagnostic' : 'duplicate-invariance',
    tolerance: 1e-5, matchedCheckpoints: 0, matchedAnchors: 0, maxAbsHeat: 0, maxAbsFuel: 0,
    maxAbsChar: 0, stateMismatches: 0, firstObservedIgnitionMismatches: 0,
    particleStateHashMismatches: 0, randomDrawMismatches: 0, areaFeedTraceMismatches: 0,
    weightedTotalMaxAbsoluteErrors: {}, weightedTotalToleranceScale: 1e-8, weightedTotalCriterionSatisfied: true,
    representedAreaAbsoluteDifference: Math.abs(result.fixture.representedArea - reference.fixture.representedArea) };
  const ids = new Set(reference.fixture.commonAnchorIds);
  const anchors = result.fixture.commonAnchorIds.filter(id => ids.has(id));
  out.matchedAnchors = anchors.length;
  for (const s of result.raw) {
    const r = reference.raw.find(r => Math.abs(r.time - s.time) < 1e-8);
    if (!r) continue;
    out.matchedCheckpoints++;
    const a = new Map(s.points.map(p => [p.id, p])), b = new Map(r.points.map(p => [p.id, p]));
    for (const id of anchors) {
      const x = a.get(id), y = b.get(id);
      out.maxAbsHeat = Math.max(out.maxAbsHeat, Math.abs(x.heat - y.heat));
      out.maxAbsFuel = Math.max(out.maxAbsFuel, Math.abs(x.fuel - y.fuel));
      out.maxAbsChar = Math.max(out.maxAbsChar, Math.abs(x.char - y.char));
      out.stateMismatches += +(x.state !== y.state);
    }
    if (s.particleStateHash !== r.particleStateHash) out.particleStateHashMismatches++;
    if (s.randomDraws !== r.randomDraws) out.randomDrawMismatches++;
    for (const [location, keys] of [['scene', ['representedArea', 'areaWeightedFuelRemaining', 'areaWeightedHeat', 'areaWeightedChar']],
      ['counters', ['areaWeightedFlameHeatDeposited', 'areaWeightedGraphHeatDeposited', 'areaWeightedFuelConsumed']]]) {
      for (const key of keys) {
        const error = Math.abs(s[location][key] - r[location][key]), name = `${location}.${key}`;
        out.weightedTotalMaxAbsoluteErrors[name] = Math.max(out.weightedTotalMaxAbsoluteErrors[name] || 0, error);
        if (error > 1e-8 * Math.max(1, Math.abs(r[location][key]))) out.weightedTotalCriterionSatisfied = false;
      }
    }
    for (const key of ['areaFeedAttempts', 'areaFeedAdmitted', 'areaFeedBlocked', 'areaFeedServiceCapDropped']) {
      if (s.counters[key] !== r.counters[key]) { out.areaFeedTraceMismatches++; break; }
    }
  }
  for (const id of anchors) if (result.firstIgnition[id] !== reference.firstIgnition[id]) out.firstObservedIgnitionMismatches++;
  out.anchorEqualityWithinTolerance = out.matchedCheckpoints === result.raw.length
    && out.matchedAnchors === reference.fixture.commonAnchorIds.length
    && out.maxAbsHeat <= out.tolerance && out.maxAbsFuel <= out.tolerance && out.maxAbsChar <= out.tolerance
    && out.stateMismatches === 0 && out.firstObservedIgnitionMismatches === 0;
  out.duplicateStateCriterionSatisfied = out.kind === 'duplicate-invariance' ? out.anchorEqualityWithinTolerance : null;
  out.feedAndParticleTraceCriterionSatisfied = out.particleStateHashMismatches === 0 && out.randomDrawMismatches === 0 && out.areaFeedTraceMismatches === 0;
  out.interpretation = out.kind === 'refinement-diagnostic' ? 'Errors versus coarse anchors are convergence diagnostics, not an exact-invariance requirement.'
    : 'Software run success is separate from this predeclared scientific criterion; negative comparisons remain in results.';
  return out;
}

export function refinementCurveError(result, finest) {
  const pairs = result.samples.filter(s => s.time >= -1e-8 && s.time <= 6 + 1e-8).map(s => {
    const r = finest.samples.find(r => Math.abs(r.time - s.time) < 1e-8);
    if (!r) return null;
    const value = s.groups.target.ignitedFraction, reference = r.groups.target.ignitedFraction;
    return { time: s.time, value, reference, absoluteError: Math.abs(value - reference) };
  }).filter(Boolean);
  let integral = 0;
  for (let i = 1; i < pairs.length; i++) integral += .5 * (pairs[i - 1].absoluteError + pairs[i].absoluteError) * (pairs[i].time - pairs[i - 1].time);
  const duration = pairs.length > 1 ? pairs.at(-1).time - pairs[0].time : 0;
  return { reference: finest.definition.id, window: [0, 6], checkpoints: pairs,
    completeStandardWindow: pairs.length === 25 && Math.abs(pairs[0].time) < 1e-8 && Math.abs(pairs.at(-1).time - 6) < 1e-8,
    integratedAbsoluteWeightedIgnitionError: integral,
    meanAbsoluteWeightedIgnitionCurveError: duration > 0 ? integral / duration : null,
    sampledMeanAbsoluteError: pairs.length ? pairs.reduce((a, p) => a + p.absoluteError, 0) / pairs.length : null,
    interpretation: 'Area-weighted target ignition fraction versus finest grid over the fixed 0..6s window; a convergence diagnostic, not an exact-invariance test.' };
}
