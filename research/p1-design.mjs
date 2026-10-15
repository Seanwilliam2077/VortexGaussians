import { BASE_PARAMS } from './lib/design.mjs';

export const P1_DEFAULTS = Object.freeze({ ...BASE_PARAMS, spreadClockMode: 'legacy',
  spreadParticlePolicy: 'block', spreadRecycleMinAge: .5 });

export function p1Cases(suite = 'all', seeds = [11, 23, 47]) {
  if (!Array.isArray(seeds) || !seeds.length || seeds.some(s => !Number.isInteger(s) || s < 0 || s > 0xffffffff) || new Set(seeds).size !== seeds.length) throw new Error('Seeds must be distinct uint32 integers');
  const cases = [], quick = suite === 'quick';
  const add = (name, family, params, options = {}, selectedSeeds = seeds) => {
    for (const seed of selectedSeeds) cases.push({ id: `p1-${name}-seed${seed}`, name, family, seed,
      fixture: 'raised-target', fixtureOptions: {}, frames: quick ? 120 : 720,
      dt: 1 / 60, sampleEvery: 15, yaw: 0, params: { ...P1_DEFAULTS, ...params }, ...options });
  };
  if (['quick', 'clock', 'all'].includes(suite)) {
    for (const mode of ['legacy', 'elapsed']) for (const cap of quick ? [350, 2800] : [350, 700, 1400, 2800]) {
      for (const order of ['forward', 'reverse']) add(`clock-${mode}-cap${cap}-${order}`, 'clock', {
        spreadClockMode: mode, spreadFrontierCap: cap, spreadFlameHeat: false, spreadSceneFeed: false,
      }, { fixture: 'cap-stress', fixtureOptions: { order }, frames: quick ? 120 : 420 }, [seeds[0]]);
    }
    if (!quick) for (const mode of ['legacy', 'elapsed']) for (const cap of [16, 1400]) {
      add(`connected-${mode}-cap${cap}`, 'connected-clock', { spreadClockMode: mode,
        spreadFrontierCap: cap, spreadFlameHeat: false, spreadSceneFeed: false },
      { fixture: 'surface-strip', frames: 720 }, [seeds[0]]);
    }
  }
  if (['quick', 'lifetime', 'all'].includes(suite)) {
    for (const policy of ['block', 'recycle-cold']) for (const budget of quick ? [150, 600] : [150, 600, 1200]) {
      add(`lifetime-${policy}-ppl${budget}`, 'lifetime', { spreadParticlePolicy: policy, ppl: budget });
    }
    if (!quick) add('method-elapsed-block-ppl600', 'method-control', { spreadClockMode: 'elapsed', ppl: 600 });
  }
  if (['quick', 'combined', 'all'].includes(suite)) {
    for (const heat of [false, true]) for (const feed of [false, true]) add(`combined-heat${+heat}-feed${+feed}`, 'combined', {
      spreadClockMode: 'elapsed', spreadParticlePolicy: 'recycle-cold', ppl: 600,
      spreadFlameHeat: heat, spreadSceneFeed: feed,
    });
  }
  if (!cases.length) throw new Error(`Unknown P1 suite ${suite}: choose quick, clock, lifetime, combined, all`);
  return cases;
}

export function configureP1(args, config = {}) {
  if (config.params && Object.keys(config.params).length) throw new Error('P1 comparison parameters are frozen; use a new named protocol for parameter tuning');
  if (config.frames !== undefined && config.seconds !== undefined) throw new Error('Config cannot contain frames and seconds together');
  const seeds = args.seeds ?? config.seeds ?? (args.suite === 'quick' ? [11] : [11, 23, 47]);
  return p1Cases(args.suite, seeds).map(c => {
    const dt = args.dt ?? config.dt ?? c.dt;
    const frames = args.frames ?? (args.seconds != null ? Math.ceil(args.seconds / dt)
      : config.frames ?? (config.seconds != null ? Math.ceil(config.seconds / dt) : c.frames));
    const sampleEvery = args.sampleEvery ?? config.sampleEvery ?? c.sampleEvery;
    if (!(Number.isFinite(dt) && dt > 0 && Number.isInteger(frames) && frames > 0 && Number.isInteger(sampleEvery) && sampleEvery > 0)) throw new Error('Invalid P1 duration, dt, or sampling interval');
    return { ...c, dt, frames, sampleEvery };
  });
}

export function p1Metrics(result) {
  if (!result.samples?.length) return null;
  const samples = result.samples, last = samples.at(-1), burning = samples.filter(s => s.scene.burning > 0);
  let hotParticleSecondsWhileBurning = 0, sampledBurningDuration = 0;
  for (let i = 1; i < samples.length; i++) {
    const a = samples[i - 1], b = samples[i];
    if (a.scene.burning > 0 && b.scene.burning > 0) {
      const duration = b.time - a.time;
      sampledBurningDuration += duration;
      hotParticleSecondsWhileBurning += .5 * (a.particles.hotCount + b.particles.hotCount) * duration;
    }
  }
  const targetIds = result.fixture.points.filter(p => p.group === 'target').map(p => p.id);
  const targetTimes = targetIds.map(id => result.firstIgnition[id]).filter(t => t !== undefined);
  const counters = last.counters;
  const window3to6 = samples.filter(s => s.time >= 3 - 1e-8 && s.time <= 6 + 1e-8);
  const windowBurning = window3to6.filter(s => s.scene.burning > 0);
  const windowEngaged = windowBurning.filter(s => s.particles.hotCount > 0);
  const endpoint = time => {
    const s = samples.find(s => Math.abs(s.time - time) < result.definition.dt * .1);
    if (!s) return null;
    return { time: s.time, scene: s.scene, counters: s.counters,
      groups: Object.fromEntries(Object.entries(s.groups).map(([key, value]) => [key,
        { count: value.count, burning: value.burning, charred: value.charred,
          meanChar: value.meanChar, meanFuelConsumed: value.meanFuelConsumed, ignitedFraction: value.ignitedFraction }])) };
  };
  return { hotParticleSecondsWhileBurning, sampledBurningDuration,
    integralMethod: 'Trapezoids only between two burning samples; omits uncertain final extinction interval. Units: hot-particle seconds, not energy.',
    hotFreeSampleFractionWhileBurning: burning.length ? burning.filter(s => s.particles.hotCount === 0).length / burning.length : null,
    burningSampleCount: burning.length, burningSamplesWithoutHotParticles: burning.filter(s => s.particles.hotCount === 0).length,
    predeclaredWindow3to6: {
      sampleCount: window3to6.length, expectedStandardQuarterSecondSampleCount: 13,
      burningSampleCount: windowBurning.length, burningWithHotSampleCount: windowEngaged.length,
      hotCoverageConditionalOnBurning: windowBurning.length ? windowEngaged.length / windowBurning.length : null,
      hotFreeFractionConditionalOnBurning: windowBurning.length ? 1 - windowEngaged.length / windowBurning.length : null,
      burningWithHotFractionOfAllCheckpoints: window3to6.length ? windowEngaged.length / window3to6.length : null,
      checkpoints: window3to6.map(s => ({ time: s.time, burning: s.scene.burning,
        hotCount: s.particles.hotCount, particleCount: s.particles.count,
        temperatureSum: s.particles.temperatureSum, dynamicTemperatureSum: s.particles.dynamicTemperatureSum,
        sceneSeedsRecycled: s.counters.sceneSeedsRecycled, randomDraws: result.raw?.find(r => r.time === s.time)?.randomDraws })),
    },
    firstTargetIgnition: targetTimes.length ? Math.min(...targetTimes) : null,
    allTargetIgnition: targetIds.length && targetTimes.length === targetIds.length ? Math.max(...targetTimes) : null,
    targetCount: targetIds.length, targetIgnited: targetTimes.length,
    ignitionTimeResolution: result.definition.sampleEvery * result.definition.dt,
    admissionFraction: counters.sceneFeedAttempts ? counters.sceneSeedsEmitted / counters.sceneFeedAttempts : null,
    sceneFeedAttempts: counters.sceneFeedAttempts, sceneSeedsEmitted: counters.sceneSeedsEmitted,
    capacityBlocked: counters.sceneFeedCapacityBlocked, randomRejected: counters.sceneFeedRandomRejected,
    sceneSeedsRecycled: counters.sceneSeedsRecycled, noColdSlot: counters.sceneFeedNoColdSlot,
    recyclingLossProxies: Object.fromEntries(Object.entries(counters).filter(([key]) => key.startsWith('recycled'))),
    finalParticles: last.particles, finalScene: last.scene, endpoint2s: endpoint(2), endpoint7s: endpoint(7),
    firstSampleAllCharred: samples.find(s => s.scene.charred === s.scene.count)?.time ?? null,
    interpretation: 'Density, smoke and circulation losses are numerical proxies, not measured visual quality. Shared RNG histories can diverge after policy-dependent admissions.' };
}
