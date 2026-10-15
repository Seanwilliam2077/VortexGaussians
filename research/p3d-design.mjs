import { P3C } from './p3c-design.mjs';
import { P3B } from './p3b-design.mjs';

export const P3D = Object.freeze({
  phase: 'P3d', version: 1, dt: P3C.dt, frames: P3C.frames, nSim: P3C.nSim, nRender: P3C.nRender,
  width: P3C.width, height: P3C.height, sampleEvery: 15, captures: P3C.captures, views: P3C.views,
  seedPairs: P3C.seedPairs, scenarios: P3C.scenarios, params: P3C.params, optics: P3C.optics,
  cellSize: .035, maxNodes: 200000, image: P3C.image,
  methods: [{ id: 'DD', mode: 'tree', components: 'both', evaluation: 'combined', baselineArm: 'DD' },
    { id: 'DG-original', mode: 'grid', components: 'temperature', evaluation: 'combined', baselineArm: 'DG' },
    { id: 'DG-specialized', mode: 'grid', components: 'temperature', evaluation: 'specialized', baselineArm: null }],
  timing: { ...P3B.timing, order: [ ['DD', 'DG-original', 'DG-specialized'], ['DG-original', 'DG-specialized', 'DD'],
    ['DG-specialized', 'DD', 'DG-original'], ['DG-specialized', 'DG-original', 'DD'], ['DD', 'DG-specialized', 'DG-original'] ],
    orderInterpretation: 'First three repeats rotate positions; two further reverse orders. Five repeats are not perfectly position-balanced.' },
  decision: { minimumCentralSpeedup: 1.5, maximumMedianRunP95Ratio: 1 },
  interpretation: 'Engineering specialization of the previously observed DG model at fixed h. Exact state and image equivalence is required; previously observed conditions are not fresh heldouts.'
});
export function p3dConfig(d) {
  const scene = P3D.scenarios.find(s => s.id === d.scenario), method = P3D.methods.find(m => m.id === d.method);
  if (!scene || !method) throw new Error('Unknown P3d scenario/method');
  return { mode: 'passive', nSim: P3D.nSim, nRender: P3D.nRender, renderSeed: d.renderSeed,
    params: { ...P3D.params, wind: scene.wind, turb: scene.turb }, optics: { ...P3D.optics },
    field: { mode: method.mode, components: method.components, evaluation: method.evaluation, cellSize: P3D.cellSize, maxNodes: P3D.maxNodes } };
}
function suiteCheck(suite) { if (!['all', 'quality', 'timing', 'quick'].includes(suite)) throw new Error(`Unknown P3d suite ${suite}`); }
export function qualityCasesP3d(suite = 'all') {
  suiteCheck(suite); if (suite === 'timing') return [];
  const short = suite === 'quick', cases = [];
  for (const s of short ? P3D.scenarios.slice(0, 1) : P3D.scenarios) for (const p of short ? P3D.seedPairs.slice(0, 1) : P3D.seedPairs) for (const m of P3D.methods) {
    cases.push({ id: `${s.id}-${m.id}-s${p.seed}-r${p.renderSeed}`, family: 'quality', scenario: s.id, ...p,
      method: m.id, frames: short ? 15 : P3D.frames, captures: short ? [15] : P3D.captures, baselineArm: m.baselineArm });
  }
  return cases;
}
export function timingCasesP3d(suite = 'all') {
  suiteCheck(suite); if (!['all', 'timing'].includes(suite)) return [];
  const cases = [];
  for (const scene of P3D.scenarios) for (let repeat = 0; repeat < P3D.timing.repeats; repeat++) for (const method of P3D.timing.order[repeat]) {
    cases.push({ id: `timing-${scene.id}-${method}-r${repeat}`, family: 'timing', scenario: scene.id, method, repeat,
      seed: P3D.timing.physicsSeed, renderSeed: P3D.timing.renderSeed });
  }
  return cases;
}
export function parseP3dArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable', '--baseline': 'baseline', '--baseline-archive': 'baselineArchive' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]]; if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  suiteCheck(args.suite); return args;
}
