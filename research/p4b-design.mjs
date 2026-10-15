// Fixed P4b interface-validation experiment. This is a standard reference,
// not a new fluid/combustion model or a performance benchmark.
export const P4B = Object.freeze({
  phase: 'P4b', duration: 1, seed: 11,
  thermal: { h: .30, beta: 4, safety: .9, maxSubsteps: 100000 },
  mapping: { ambientK: 300, scaleK: 300 },
  nativeParams: { gam: 1, theta: .6, baro: 1.4, stretch3: 1, buoy: .5,
    turb: 0, wind: 0, layers: 3, sliceDepth: 1.2 },
  energyTolerance: 1e-12, temperatureTolerance: 1e-9,
  feedbackPositionRmsExposure: 1e-6, movingGeometryTemperatureRmseExposure: 1e-6,
  interpretation: 'Fixed explicit parcels, Kelvin heat state, geometry-frozen exchange then native 3D VPM. No births, losses, combustion, inferred material, renderer comparison, or speed claim. Conserved sensible heat is not total thermal-plus-mechanical energy.'
});

function definition(id, family, extra = {}) {
  return { id, family, fixture: { kind: 'main', uniformTemperature: null, order: 'forward' },
    dt: 1 / 60, steps: 60, duration: 1, exchange: true, thermalFeedback: true,
    transportMode: 'native-vpm3', observe: false, seed: P4B.seed, ...extra };
}

export function allP4bCases() {
  return [
    definition('single-step-analytic', 'analytic-interface', {
      fixture: { kind: 'single', uniformTemperature: null, order: 'forward' }, steps: 1, duration: 1 / 60 }),
    definition('main-no-exchange-no-feedback', 'causal-control', { exchange: false, thermalFeedback: false }),
    definition('main-no-exchange-feedback', 'causal-control', { exchange: false }),
    definition('main-exchange-no-feedback', 'causal-control', { thermalFeedback: false }),
    definition('main-coupled-dt60', 'coupled'),
    definition('main-static-exchange', 'geometry-control', { transportMode: 'static', thermalFeedback: false }),
    definition('main-coupled-dt120', 'temporal-refinement', { dt: 1 / 120, steps: 120 }),
    definition('main-coupled-dt240', 'temporal-refinement', { dt: 1 / 240, steps: 240 }),
    definition('uniform-exchange', 'equilibrium-control', { fixture: { kind: 'main', uniformTemperature: 450, order: 'forward' } }),
    definition('uniform-no-exchange', 'equilibrium-control', { fixture: { kind: 'main', uniformTemperature: 450, order: 'forward' }, exchange: false }),
    definition('main-coupled-observed', 'observation-control', { observe: true }),
    definition('main-coupled-reordered', 'order-control', { fixture: { kind: 'main', uniformTemperature: null, order: 'reverse' } })
  ];
}

export function p4bCases(suite = 'all') {
  if (suite === 'all') return allP4bCases();
  if (suite !== 'quick') throw new RangeError('P4b suite must be all or quick');
  const selected = new Set(['single-step-analytic', 'main-no-exchange-no-feedback',
    'main-no-exchange-feedback', 'main-exchange-no-feedback', 'main-coupled-dt60',
    'main-static-exchange', 'main-coupled-observed', 'main-coupled-reordered']);
  return allP4bCases().filter(d => selected.has(d.id)).map(d => d.fixture.kind === 'single'
    ? { ...d, exploratory: true } : { ...d, duration: .1, steps: 6, exploratory: true });
}

export function makeP4bFixture(spec) {
  if (!['main', 'single'].includes(spec.kind)) throw new RangeError('Unknown P4b fixture');
  if (![null, 450].includes(spec.uniformTemperature)) throw new RangeError('Frozen uniform temperature is 450 K');
  if (!['forward', 'reverse'].includes(spec.order)) throw new RangeError('Unknown P4b input order');
  const surface = [], gas = [];
  if (spec.kind === 'single') {
    surface.push({ id: 'surface-0', position: [-.20, .40, 0], area: .08 ** 2,
      capacityPerArea: 2, temperature: 330 });
    gas.push({ id: 'gas-0', position: [-.12, .40, 0], volume: .08 ** 3,
      capacityPerVolume: 3, temperature: 560, G: [0, 0, 0], sg: .07 });
  } else {
    const xz = [-.12, -.04, .04, .12], ys = [.40, .48, .56, .64];
    for (let side = 0; side < 2; side++) for (let iy = 0; iy < 4; iy++) for (let iz = 0; iz < 4; iz++) {
      surface.push({ id: `surface-${side}-${iy}-${iz}`, position: [side === 0 ? -.20 : .20, ys[iy], xz[iz]],
        area: .08 ** 2, capacityPerArea: 2, temperature: spec.uniformTemperature ?? (side === 0 ? 330 : 390) });
    }
    for (let ix = 0; ix < 4; ix++) for (let iy = 0; iy < 4; iy++) for (let iz = 0; iz < 4; iz++) {
      const x = xz[ix], z = xz[iz];
      gas.push({ id: `gas-${ix}-${iy}-${iz}`, position: [x, ys[iy], z], volume: .08 ** 3,
        capacityPerVolume: 3, temperature: spec.uniformTemperature ?? (560 + 40 * (x / .12) + 20 * (z / .12)),
        G: [.15 * z / .12, .25, .15 * x / .12], sg: .07 });
    }
  }
  if (spec.order === 'reverse') { surface.reverse(); gas.reverse(); }
  return { surface, gas };
}

export function p4bConfig(d) {
  const input = makeP4bFixture(d.fixture);
  return { ...input, seed: d.seed, exchange: d.exchange,
    thermal: { ...P4B.thermal }, mapping: { ...P4B.mapping },
    transport: { mode: d.transportMode, thermalFeedback: d.thermalFeedback,
      params: { ...P4B.nativeParams, ...(d.fixture.kind === 'single' ? { baro: 0 } : {}) } } };
}

export function parseP4bArgs(argv) {
  const result = { suite: 'all', out: null, browserExecutable: null, help: false };
  const keys = { '--suite': 'suite', '--out': 'out', '--browser-executable': 'browserExecutable' };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') result.help = true;
    else if (keys[arg]) {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing value for ${arg}`);
      result[keys[arg]] = argv[++i];
    } else throw new Error(`Unknown argument ${arg}`);
  }
  if (!['all', 'quick'].includes(result.suite)) throw new RangeError('Expected --suite all|quick');
  return result;
}
