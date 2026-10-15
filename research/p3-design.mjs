// P3a measures render sampling at ONE frozen physical discretization.
export const P3 = Object.freeze({
  phase: 'P3a', version: 1, dt: 1 / 60, frames: 180, nSim: 600,
  width: 256, height: 192, captures: [90, 180],
  views: [{ id: 'front', yaw: 0 }, { id: 'oblique', yaw: .7 }, { id: 'side', yaw: 1.4 }],
  physicsSeeds: [11, 23, 47], renderSeeds: [101, 211, 307],
  referenceSeeds: [401, 503, 607], doubleReferenceSeeds: [701, 809, 907],
  budgets: [600, 2400, 9600], referenceBudget: 19200, doubleReferenceBudget: 38400,
  params: { layers: 3, rate: 180 }, optics: { radius: .045, tau: .2 },
  image: { foregroundAlpha: .01, holeReferenceAlpha: .2, holeCandidateAlpha: .05,
    convergenceRatio: .25, regions: ['full', 'foreground'], channels: ['rgb', 'alpha'] },
  timing: { repeats: 5, seed: 11, renderSeed: 101, warmupFrames: 20,
    firstFrame: 60, lastFrame: 180, sampleEvery: 3, sync: 'finish' },
  interpretation: 'Fixed 3D physics and one source. View coverage is not scene coverage. Linear optical-model agreement is not physical or perceptual ground truth. Serialized GPU-completed wall latency is not pure GPU time.'
});

export function p3Config(definition) {
  return { mode: definition.mode, nSim: P3.nSim, nRender: definition.nRender,
    renderSeed: definition.renderSeed, params: { ...P3.params }, optics: { ...P3.optics } };
}

export function qualityCases(suite = 'all') {
  if (!['all', 'quality', 'quick', 'pilot', 'timing'].includes(suite)) throw new Error(`Unknown P3 suite ${suite}`);
  if (suite === 'timing') return [];
  const seeds = ['quick', 'pilot'].includes(suite) ? [P3.physicsSeeds[0]] : P3.physicsSeeds;
  const repeats = ['quick', 'pilot'].includes(suite) ? [0] : [0, 1, 2];
  const cases = [];
  for (const seed of seeds) {
    cases.push({ id: `shared-s${seed}`, family: 'shared', mode: 'shared3d', seed,
      repeat: null, renderSeed: 101, nRender: P3.nSim });
    for (const repeat of repeats) {
      for (const nRender of P3.budgets) cases.push({ id: `passive-n${nRender}-s${seed}-r${repeat}`, family: 'candidate',
        mode: 'passive', seed, repeat, renderSeed: P3.renderSeeds[repeat], nRender });
      cases.push({ id: `reference-s${seed}-r${repeat}`, family: 'reference', mode: 'passive', seed, repeat,
        renderSeed: P3.referenceSeeds[repeat], nRender: P3.referenceBudget });
      cases.push({ id: `double-reference-s${seed}-r${repeat}`, family: 'double-reference', mode: 'passive', seed, repeat,
        renderSeed: P3.doubleReferenceSeeds[repeat], nRender: P3.doubleReferenceBudget });
    }
  }
  return cases.map(d => ({ ...d, frames: suite === 'quick' ? 12 : P3.frames,
    captures: suite === 'quick' ? [12] : [...P3.captures], exploratory: ['quick', 'pilot'].includes(suite) }));
}

export function timingCases(suite = 'all') {
  if (!['all', 'timing'].includes(suite)) return [];
  const modes = [{ mode: 'shared3d', nRender: P3.nSim }, ...[...P3.budgets, P3.referenceBudget].map(nRender => ({ mode: 'passive', nRender }))];
  const cases = [];
  // Cyclic order balances each method's position across the five repetitions.
  for (let repeat = 0; repeat < P3.timing.repeats; repeat++) {
    for (let j = 0; j < modes.length; j++) {
      const mode = modes[(j + repeat) % modes.length];
      cases.push({ id: `timing-${mode.mode}-n${mode.nRender}-r${repeat}`, ...mode,
        family: 'timing', seed: P3.timing.seed, renderSeed: P3.timing.renderSeed, repeat });
    }
  }
  return cases;
}

export function parseP3Args(argv) {
  const args = { suite: 'all' };
  const names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]];
    if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  qualityCases(args.suite);
  return args;
}
