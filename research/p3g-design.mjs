import { P3F } from './p3f-design.mjs';

export const P3G = Object.freeze({
  ...P3F, phase: 'P3g', version: 1,
  pairs: [{ seed: 11, renderSeed: 101, role: 'previously-observed' }, { seed: 83, renderSeed: 521, role: 'previously-unrun-seed-pair' }],
  methods: [{ id: 'DD', mode: 'tree' }, { id: 'curvature', mode: 'affine' }, { id: 'memory', mode: 'affine' }],
  memory: { ttl: 1 },
  timing: { ...P3F.timing, order: [['DD', 'memory'], ['memory', 'DD'], ['DD', 'memory'], ['memory', 'DD'], ['DD', 'memory']] },
  interpretation: 'Fixed-budget TTL1 raw-field residual reuse on one previous and one previously unrun seed pair in the same stationary condition. Each cache entry is created by an actual selected direct query; reuse never renews its age. This is an exploratory temporal-reuse ablation, not a physical or general performance validation.'
});
export function p3gConfig(d) {
  if (!['DD', 'curvature', 'memory'].includes(d.method)) throw new Error('Unknown P3g method');
  const affine = d.method !== 'DD';
  return { mode: 'passive', nSim: P3G.nSim, nRender: P3G.nRender, renderSeed: d.renderSeed,
    params: { ...P3G.params }, optics: { ...P3G.optics }, field: { mode: affine ? 'affine' : 'tree', components: 'both', evaluation: 'combined',
      ...(affine ? { affine: { ...P3G.affine }, correction: { method: 'curvature', ...P3G.correction, ...(d.method === 'memory' ? { memory: { ...P3G.memory } } : {}) } } : { cellSize: .035, maxNodes: 200000 }) } };
}
export function qualityCasesP3g(suite = 'all') {
  if (!['all', 'quick'].includes(suite)) throw new Error('P3g suite must be all or quick; timing cannot bypass quality');
  return P3G.pairs.flatMap(pair => P3G.methods.map(m => ({ id: `stationary-${m.id}-s${pair.seed}-r${pair.renderSeed}`,
    family: 'quality', scenario: 'stationary', ...pair, method: m.id, frames: suite === 'quick' ? 15 : 180,
    captures: suite === 'quick' ? [15] : [...P3G.captures] })));
}
export function timingCasesP3g() {
  return P3G.timing.order.flatMap((order, repeat) => order.map(method => ({ id: `timing-stationary-${method}-r${repeat}`,
    family: 'timing', scenario: 'stationary', seed: 11, renderSeed: 101, method, repeat })));
}
export function parseP3gArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable', '--baseline': 'baseline', '--baseline-archive': 'baselineArchive' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]]; if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  qualityCasesP3g(args.suite); return args;
}
