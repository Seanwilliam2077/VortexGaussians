export const BASE_PARAMS = Object.freeze({ solver: 'vpm', dimMode: 'layer', mode: 'fire',
  layers: 3, simLayers: 3, ppl: 600, sliceMode: 'world', sliceDepth: .12,
  turb: 0, wind: 0, embers: false, flicker: false, orbit: false,
  emitterOn: false, spreadOn: true, sceneOn: true,
  spreadFlameHeat: true, spreadSceneFeed: true,
  spreadIgnR: .14, spreadHeat: 2.2, spreadIgnH: 1,
  spreadR: .11, spreadRate: 3, spreadBurnT: 6, spreadFeed: 5,
  spreadFrontierCap: 1400, spreadSampleCap: 160, spreadFeedCap: 48 });

export function buildCases(suite, seeds = [11, 23, 47]) {
  const result = [];
  const add = (name, params, options = {}) => {
    for (const seed of seeds) result.push({ id: `${name}-seed${seed}`, name, seed,
      fixture: 'raised-target', fixtureOptions: {}, frames: 720, dt: 1 / 60,
      sampleEvery: 15, yaw: 0, params: { ...BASE_PARAMS, ...params }, ...options });
  };
  if (['quick', 'feedback', 'all'].includes(suite)) {
    for (const heat of [false, true]) for (const feed of [false, true]) {
      add(`feedback-heat${+heat}-feed${+feed}`, { spreadFlameHeat: heat, spreadSceneFeed: feed },
        suite === 'quick' ? { frames: 120 } : {});
    }
  }
  if (['quick', 'sensitivity', 'all'].includes(suite)) {
    const length = suite === 'quick' ? 3 : 120;
    for (const cap of suite === 'quick' ? [1400, 2800] : [350, 700, 1400, 2800]) {
      add(`frontier-cap${cap}`, { spreadFlameHeat: false, spreadSceneFeed: false, spreadFrontierCap: cap },
        { fixture: 'cap-stress', frames: length, sampleEvery: suite === 'quick' ? 1 : 15 });
    }
    add('frontier-cap1400-reverse', { spreadFlameHeat: false, spreadSceneFeed: false, spreadFrontierCap: 1400 },
      { fixture: 'cap-stress', fixtureOptions: { order: 'reverse' }, frames: length, sampleEvery: suite === 'quick' ? 1 : 15 });
    for (const sampleCap of suite === 'quick' ? [0, 160] : [0, 16, 160, 1000000]) add(`sample-cap${sampleCap}`, { spreadSampleCap: sampleCap },
      { frames: suite === 'quick' ? 60 : 720 });
    for (const feedCap of suite === 'quick' ? [0, 48] : [0, 4, 48, 1000000]) add(`feed-cap${feedCap}`, { spreadFeedCap: feedCap },
      { frames: suite === 'quick' ? 60 : 720 });
    for (const order of ['forward', 'reverse', 'shuffle']) add(`order-${order}`, {
      spreadFlameHeat: false, spreadSceneFeed: false, spreadFrontierCap: 16 },
      { fixture: 'surface-strip', fixtureOptions: { order }, frames: suite === 'quick' ? 60 : 720 });
    for (const density of [1, 2, 4]) add(`duplicate-density${density}`, {
      spreadFlameHeat: false, spreadSceneFeed: false, spreadFrontierCap: 1000000 },
      { fixture: 'surface-strip', fixtureOptions: { density }, frames: suite === 'quick' ? 60 : 720 });
  }
  if (!result.length) throw new Error(`Unknown suite: ${suite}; choose quick, feedback, sensitivity, all`);
  return result;
}

export function parseArgs(argv) {
  const result = { suite: 'quick', seeds: null, dt: null, frames: null, seconds: null,
    sampleEvery: null, out: null, config: null, browserExecutable: null, timeout: 120000 };
  const names = { 'sample-every': 'sampleEvery', 'browser-executable': 'browserExecutable' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help' || argv[i] === '-h') { result.help = true; continue; }
    if (!argv[i].startsWith('--')) throw new Error(`Unexpected argument ${argv[i]}`);
    const key = names[argv[i].slice(2)] || argv[i].slice(2);
    if (!(key in result)) throw new Error(`Unknown argument ${argv[i]}`);
    const value = argv[++i];
    if (!value || value.startsWith('--')) throw new Error(`Missing value for ${key}`);
    result[key] = value;
  }
  for (const key of ['dt', 'frames', 'seconds', 'sampleEvery', 'timeout']) if (result[key] !== null) {
    result[key] = Number(result[key]);
    if (!Number.isFinite(result[key]) || result[key] <= 0) throw new Error(`${key} must be positive and finite`);
    if (['frames', 'sampleEvery', 'timeout'].includes(key) && !Number.isInteger(result[key])) throw new Error(`${key} must be an integer`);
  }
  if (result.frames !== null && result.seconds !== null) throw new Error('Use --frames or --seconds, not both');
  if (result.seeds !== null) {
    result.seeds = result.seeds.split(',').map(Number);
    if (!result.seeds.length || result.seeds.some(n => !Number.isInteger(n) || n < 0 || n > 0xffffffff)) throw new Error('Seeds must be uint32 integers');
  }
  return result;
}

export function configureCases(args, fileConfig = {}) {
  const reserved = ['spreadFlameHeat', 'spreadSceneFeed', 'spreadFrontierCap', 'spreadSampleCap', 'spreadFeedCap'];
  // Overrides of factors invalidate the matrix; fail instead of silently relabelling it.
  for (const key of reserved) if (key in (fileConfig.params || {})) throw new Error(`Matrix factor ${key} cannot be globally overridden`);
  for (const key of ['emitterOn', 'embers']) if (fileConfig.params?.[key] === true) throw new Error(`${key}=true invalidates the emitter-off diagnostic protocol`);
  for (const [key, value] of Object.entries({ sliceMode: 'world', solver: 'vpm', dimMode: 'layer', spreadOn: true })) {
    if (key in (fileConfig.params || {}) && fileConfig.params[key] !== value) throw new Error(`${key} must remain ${value} for this diagnostic matrix`);
  }
  if (fileConfig.frames !== undefined && fileConfig.seconds !== undefined) throw new Error('Config cannot specify both frames and seconds');
  const validateSeeds = seeds => {
    if (!Array.isArray(seeds) || !seeds.length || seeds.some(s => !Number.isInteger(s) || s < 0 || s > 0xffffffff) || new Set(seeds).size !== seeds.length) throw new Error('Seeds must be a nonempty list of unique uint32 integers');
  };
  if ('seeds' in fileConfig) validateSeeds(fileConfig.seeds);
  const seeds = args.seeds ?? fileConfig.seeds ?? (args.suite === 'quick' ? [11] : [11, 23, 47]);
  validateSeeds(seeds);
  return buildCases(args.suite, seeds).map(c => {
    const dt = args.dt ?? fileConfig.dt ?? c.dt;
    const frames = args.frames ?? (args.seconds !== null && args.seconds !== undefined
      ? Math.ceil(args.seconds / dt)
      : fileConfig.frames ?? (fileConfig.seconds === undefined || fileConfig.seconds === null ? c.frames : Math.ceil(fileConfig.seconds / dt)));
    return { ...c, dt, frames, sampleEvery: args.sampleEvery ?? fileConfig.sampleEvery ?? c.sampleEvery,
      params: { ...c.params, ...(fileConfig.params || {}) } };
  });
}
