import { P3 } from './p3-design.mjs';

export const P3B = Object.freeze({
  phase: 'P3b', version: 1, dt: P3.dt, frames: 180, nSim: 600, nRender: 9600,
  width: P3.width, height: P3.height, sampleEvery: 15, captures: [...P3.captures], views: P3.views,
  seedPairs: [{ seed: 11, renderSeed: 101 }, { seed: 23, renderSeed: 211 }, { seed: 47, renderSeed: 307 }],
  scenarios: [{ id: 'stationary', wind: 0, turb: 0, role: 'development-and-confirmation' },
    { id: 'crosswind', wind: .35, turb: 0, role: 'heldout' },
    { id: 'curl', wind: .2, turb: .55, role: 'heldout' }],
  methods: [{ id: 'tree', mode: 'tree', cellSize: .07 },
    { id: 'grid035', mode: 'grid', cellSize: .035 },
    { id: 'grid070', mode: 'grid', cellSize: .07 },
    { id: 'grid140', mode: 'grid', cellSize: .14 }],
  params: { ...P3.params, eps: .07 }, optics: { ...P3.optics }, maxNodes: 200000,
  probePositions: [-.1, 0, .3, .8].flatMap(x => [.1, .5, 1, 2].flatMap(y => [-.25, 0, .25].map(z => [x, y, z]))),
  image: { foregroundAlpha: .01, holeReferenceAlpha: .2, holeCandidateAlpha: .05 },
  selection: { scenario: 'stationary', physicsSeed: 11, renderSeed: 101,
    maximumForegroundAlphaNrmse: .05, maximumForegroundRgbNrmse: .05,
    maximumCheckpointPositionRmse: .007, maximumCheckpointPositionP99: .035,
    minimumRouteMedianSpeedup: 1.5, maximumRouteP95Ratio: 1,
    expectedSampleFrames: Array.from({ length: 12 }, (_, i) => 15 * (i + 1)),
    expectedCaptureKeys: P3.captures.flatMap(f => P3.views.map(v => `${f}-${v.id}`)),
    requireNoUnmatchedIds: true, requireNoFallbacks: true,
    rule: 'Fastest grid passing the error gate by median of five repeat medians; tie-break smaller cell size. Select only on stationary physics11/render101. Route-go additionally requires all eight heldout condition/seed pairs to pass and all three conditions to achieve central speedup>=1.5 and tail no slower than tree. Central=median of five run medians; tail=median of five run p95 values, not pooled-frame p95. Heldouts never change the selection.' },
  timing: { repeats: 5, physicsSeed: 11, renderSeed: 101, warmupFrames: 20,
    firstFrame: 60, lastFrame: 180, sampleEvery: 3, sync: 'finish' },
  interpretation: 'Paired cache approximation to the same-seed tree tracer model. Fixed 3D physics; neither physical ground truth nor a claim of new numerical methodology.'
});

export function p3bConfig(d) {
  const scene = P3B.scenarios.find(s => s.id === d.scenario), method = P3B.methods.find(m => m.id === d.method);
  if (!scene || !method) throw new Error('Unknown P3b scenario/method');
  return { mode: 'passive', nSim: P3B.nSim, nRender: P3B.nRender, renderSeed: d.renderSeed,
    params: { ...P3B.params, wind: scene.wind, turb: scene.turb }, optics: { ...P3B.optics },
    field: { mode: method.mode, cellSize: method.cellSize, maxNodes: P3B.maxNodes } };
}

export function qualityCasesP3b(suite = 'all') {
  if (!['all', 'quality', 'timing', 'pilot', 'quick'].includes(suite)) throw new Error(`Unknown P3b suite ${suite}`);
  if (suite === 'timing') return [];
  const exploratory = ['pilot', 'quick'].includes(suite), out = [];
  for (const scenario of exploratory ? P3B.scenarios.slice(0, 1) : P3B.scenarios) {
    for (const { seed, renderSeed } of exploratory ? P3B.seedPairs.slice(0, 1) : P3B.seedPairs) {
        for (const method of P3B.methods) out.push({
          id: `${scenario.id}-${method.id}-s${seed}-r${renderSeed}`, family: 'quality', scenario: scenario.id,
          method: method.id, seed, renderSeed, frames: suite === 'quick' ? 15 : P3B.frames,
          captures: suite === 'quick' ? [15] : [...P3B.captures], exploratory,
          role: scenario.id === 'stationary' && seed === 11 && renderSeed === 101 ? 'selection' : 'heldout-confirmation'
        });
    }
  }
  return out;
}

export function timingCasesP3b(suite = 'all') {
  if (!['all', 'timing'].includes(suite)) return [];
  const cases = [];
  for (const scenario of P3B.scenarios) for (let repeat = 0; repeat < P3B.timing.repeats; repeat++) {
    for (let j = 0; j < P3B.methods.length; j++) {
      const method = P3B.methods[repeat < 4 ? (j + repeat) % 4 : 3 - j];
      cases.push({ id: `timing-${scenario.id}-${method.id}-r${repeat}`, family: 'timing', scenario: scenario.id,
        method: method.id, seed: P3B.timing.physicsSeed, renderSeed: P3B.timing.renderSeed, repeat });
    }
  }
  return cases;
}

export function parseP3bArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]];
    if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  qualityCasesP3b(args.suite); return args;
}
