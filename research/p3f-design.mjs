import { P3E } from './p3e-design.mjs';

export const P3F = Object.freeze({
  ...P3E, phase: 'P3f', version: 1,
  pairs: [{ seed: 11, renderSeed: 101, role: 'previously-observed' }, { seed: 59, renderSeed: 409, role: 'previously-unrun-seed-pair' }],
  methods: [{ id: 'DD', mode: 'tree' }, { id: 'curvature', mode: 'affine' }, { id: 'hash', mode: 'affine' }],
  correction: { fraction: .1, salt: 0xa511e9b3 },
  timing: { ...P3E.timing, order: [['DD', 'curvature'], ['curvature', 'DD'], ['DD', 'curvature'], ['curvature', 'DD'], ['DD', 'curvature']] },
  interpretation: 'Exploratory fixed 10% group correction. One previous and one previously unrun seed pair in the same stationary condition. A single deterministic hash selector is a mechanism control, not a statistical random-method comparison. Both selectors pay all seven model queries per group.'
});
export function p3fConfig(d) {
  if (!['DD', 'affine', 'curvature', 'hash'].includes(d.method)) throw new Error('Unknown P3f method');
  const affine = d.method !== 'DD', corrected = ['curvature', 'hash'].includes(d.method);
  return { mode: 'passive', nSim: P3F.nSim, nRender: P3F.nRender, renderSeed: d.renderSeed,
    params: { ...P3F.params }, optics: { ...P3F.optics },
    field: { mode: affine ? 'affine' : 'tree', components: 'both', evaluation: 'combined',
      ...(affine ? { affine: { ...P3F.affine } } : { cellSize: .035, maxNodes: 200000 }),
      ...(corrected ? { correction: { method: d.method, ...P3F.correction } } : {}) } };
}
export function qualityCasesP3f(suite = 'all') {
  if (!['all', 'quick'].includes(suite)) throw new Error('P3f suite must be all or quick; timing cannot bypass quality');
  return P3F.pairs.flatMap(pair => P3F.methods.map(m => ({ id: `stationary-${m.id}-s${pair.seed}-r${pair.renderSeed}`,
    family: 'quality', scenario: 'stationary', ...pair, method: m.id, frames: suite === 'quick' ? 15 : 180,
    captures: suite === 'quick' ? [15] : [...P3F.captures] })));
}
export function regressionCasesP3f(suite = 'all') {
  qualityCasesP3f(suite);
  return [{ id: 'stationary-affine-s11-r101', family: 'regression', scenario: 'stationary', seed: 11, renderSeed: 101,
    method: 'affine', frames: suite === 'quick' ? 15 : 180, captures: suite === 'quick' ? [15] : [...P3F.captures] }];
}
export function timingCasesP3f() {
  return P3F.timing.order.flatMap((order, repeat) => order.map(method => ({ id: `timing-stationary-${method}-r${repeat}`,
    family: 'timing', scenario: 'stationary', seed: 11, renderSeed: 101, method, repeat })));
}
export function parseP3fArgs(argv) {
  const args = { suite: 'all' }, names = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable', '--baseline': 'baseline', '--baseline-archive': 'baselineArchive' };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--help') { args.help = true; continue; }
    const key = names[argv[i]]; if (!key || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Unknown option or missing value: ${argv[i]}`);
    args[key] = argv[++i];
  }
  qualityCasesP3f(args.suite); return args;
}
