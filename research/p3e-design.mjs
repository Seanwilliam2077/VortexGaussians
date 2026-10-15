import { P3D } from './p3d-design.mjs';
import { P3B } from './p3b-design.mjs';

export const P3E = Object.freeze({
  phase: 'P3e', version: 1, dt: P3D.dt, frames: 180, nSim: 600, nRender: 9600, seed: 11, renderSeed: 101,
  width: P3D.width, height: P3D.height, sampleEvery: 15, captures: P3D.captures, views: P3D.views,
  scenarios: [{ id: 'stationary', wind: 0, turb: 0 }], params: { ...P3D.params, wind: 0, turb: 0 }, optics: P3D.optics,
  methods: [{ id: 'DD', mode: 'tree' }, { id: 'affine', mode: 'affine' }],
  affine: { maxGroups: 600, targetGroupSize: 16, deltaScale: .125 },
  grouping: 'K=min(maxGroups,ceil(N/targetGroupSize)); recursively split longest axis (ties x/y/z), coordinate then stable-ID order; leftK=floor(K/2), cut=floor(N*leftK/K); leaves in DFS order, centroid summed in stable-ID order.',
  stencil: ['center', '+x', '-x', '+y', '-y', '+z', '-z'], temperatureClip: [0, 1.6],
  image: P3D.image, accuracy: P3B.selection,
  timing: { ...P3D.timing, order: [['DD', 'affine'], ['affine', 'DD'], ['DD', 'affine'], ['affine', 'DD'], ['DD', 'affine']],
    orderInterpretation: 'Five alternating orders start DD first three times and affine first twice; not perfectly position-balanced.' },
  decision: P3D.decision,
  interpretation: 'Exploratory local first-order field model on one previously observed condition/seed. Actual DD-input diagnostics explain approximation and do not replace the deployable trajectory gate.'
});
export function p3eConfig(d) {
  const method = P3E.methods.find(m => m.id === d.method); if (!method) throw new Error('Unknown P3e method');
  return { mode: 'passive', nSim: P3E.nSim, nRender: P3E.nRender, renderSeed: 101,
    params: { ...P3E.params }, optics: { ...P3E.optics },
    field: { mode: method.mode, components: 'both', evaluation: 'combined',
      ...(method.mode === 'affine' ? { affine: { ...P3E.affine } } : { cellSize: .035, maxNodes: 200000 }) } };
}
export function qualityCasesP3e(suite = 'all') {
  if (!['all', 'quick'].includes(suite)) throw new Error('P3e suite must be all or quick; timing cannot bypass quality');
  return P3E.methods.map(m => ({ id: `stationary-${m.id}-s11-r101`, family: 'quality', scenario: 'stationary', seed: 11, renderSeed: 101,
    method: m.id, frames: suite === 'quick' ? 15 : 180, captures: suite === 'quick' ? [15] : [...P3E.captures] }));
}
export function timingCasesP3e() {
  return P3E.timing.order.flatMap((order, repeat) => order.map(method => ({ id: `timing-stationary-${method}-r${repeat}`,
    family: 'timing', scenario: 'stationary', seed: 11, renderSeed: 101, method, repeat })));
}
export function parseP3eArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable', '--baseline': 'baseline', '--baseline-archive': 'baselineArchive' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]]; if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  qualityCasesP3e(args.suite); return args;
}
