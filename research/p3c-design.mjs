import { P3B } from './p3b-design.mjs';

export const P3C = Object.freeze({
  phase: 'P3c', version: 1, dt: P3B.dt, frames: 180, nSim: 600, nRender: 9600,
  width: P3B.width, height: P3B.height, sampleEvery: 15, captures: [...P3B.captures], views: P3B.views,
  seedPairs: P3B.seedPairs, scenarios: P3B.scenarios.map(s => ({ ...s, role: 'previously-observed-diagnostic' })),
  arms: [{ id: 'DD', mode: 'tree', components: 'both' }, { id: 'GD', mode: 'grid', components: 'velocity' },
    { id: 'DG', mode: 'grid', components: 'temperature' }, { id: 'GG', mode: 'grid', components: 'both' }],
  params: P3B.params, optics: P3B.optics, cellSize: .035, maxNodes: 200000, inputStride: 97,
  image: P3B.image, ageBins: [{ id: '0-.5', minSteps: 0, maxSteps: 30 },
    { id: '.5-1', minSteps: 30, maxSteps: 60 }, { id: '1-2', minSteps: 60, maxSteps: 120 },
    { id: '2+', minSteps: 120, maxSteps: null }], ageStepTolerance: 1e-9,
  interpretation: 'Exploratory component attribution on previously observed P3b conditions. Fixed grid spacing; no new heldout evaluation, scale selection, or performance claim.'
});
export function p3cConfig(d) {
  const scene = P3C.scenarios.find(s => s.id === d.scenario), arm = P3C.arms.find(a => a.id === d.arm);
  if (!scene || !arm) throw new Error('Unknown P3c scenario/arm');
  return { mode: 'passive', nSim: P3C.nSim, nRender: P3C.nRender, renderSeed: d.renderSeed,
    params: { ...P3C.params, wind: scene.wind, turb: scene.turb }, optics: { ...P3C.optics },
    field: { mode: arm.mode, components: arm.components, cellSize: P3C.cellSize, maxNodes: P3C.maxNodes } };
}
export function casesP3c(suite = 'all') {
  if (!['all', 'pilot', 'quick'].includes(suite)) throw new Error(`Unknown P3c suite ${suite}; this phase has no performance matrix`);
  const short = suite !== 'all', cases = [];
  for (const scene of short ? P3C.scenarios.slice(0, 1) : P3C.scenarios) {
    for (const pair of short ? P3C.seedPairs.slice(0, 1) : P3C.seedPairs) for (const arm of P3C.arms) {
      cases.push({ id: `${scene.id}-${arm.id}-s${pair.seed}-r${pair.renderSeed}`, scenario: scene.id, ...pair,
        arm: arm.id, frames: suite === 'quick' ? 15 : 180, captures: suite === 'quick' ? [15] : [...P3C.captures],
        exploratory: true, protocolComplete: suite === 'all' });
    }
  }
  return cases;
}
export function parseP3cArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]];
    if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  casesP3c(args.suite); return args;
}
