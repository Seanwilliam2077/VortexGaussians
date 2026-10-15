// P4a is a finite-capacity exchange reference, not a new combustion method.
export const P4A = Object.freeze({
  phase: 'P4a', duration: 1, h: 0.65, beta: 2, safety: 0.9, maxSubsteps: 100000,
  shuffleSeed: 73013, energyTolerance: 1e-12, temperatureTolerance: 1e-9,
  units: { position: 'm', area: 'm^2', volume: 'm^3', temperature: 'K',
    capacityPerArea: 'J/(m^2 K)', capacityPerVolume: 'J/(m^3 K)',
    capacity: 'J/K', beta: 'W/(m^2 K)', conductance: 'W/K', time: 's' },
  interpretation: 'Toy material parameters; fixed-node closed heat exchange only. No combustion, losses, motion, real-material calibration, or performance claim.'
});

const options = beta => ({ h: P4A.h, beta, safety: P4A.safety, maxSubsteps: P4A.maxSubsteps });
function definition(id, family, spec, stepsPerSecond = 60, extra = {}) {
  return { id, family, model: 'conservative', fixture: spec, dt: 1 / stepsPerSecond,
    steps: stepsPerSecond, duration: P4A.duration, options: options(P4A.beta), ...extra };
}

export function allP4aCases() {
  const base = 'corner-base-dt60';
  const comparison = type => ({ reference: base, type });
  const corner = overrides => ({ kind: 'corner', resolution: 4, ...overrides });
  return [
    ...[30, 60, 120].map(n => definition(`pair-dt${n}`, 'pair-temporal', { kind: 'pair' }, n)),
    definition('pair-reverse-temperature', 'pair-control', { kind: 'pair', reverseTemperature: true }),
    definition('pair-disconnected', 'pair-control', { kind: 'pair', disconnected: true }),
    definition('pair-cfl-stress', 'cfl-control', { kind: 'pair' }, 10, { options: options(100) }),
    definition(base, 'corner-temporal', corner({})),
    definition('corner-uniform2', 'representation', corner({ surfaceCopies: 2, gasCopies: 2 }), 60, { comparison: comparison('split') }),
    definition('corner-uniform4', 'representation', corner({ surfaceCopies: 4, gasCopies: 4 }), 60, { comparison: comparison('split') }),
    definition('corner-variable', 'representation', corner({ surfaceCopies: 'variable', gasCopies: 'variable' }), 60, { comparison: comparison('split') }),
    definition('corner-surface-only2', 'representation', corner({ surfaceCopies: 2 }), 60, { comparison: comparison('split') }),
    definition('corner-gas-only2', 'representation', corner({ gasCopies: 2 }), 60, { comparison: comparison('split') }),
    definition('corner-reverse', 'representation', corner({ order: 'reverse' }), 60, { comparison: comparison('order') }),
    definition('corner-shuffle', 'representation', corner({ order: 'shuffle' }), 60, { comparison: comparison('order') }),
    definition('corner-rigid', 'representation', corner({ rigid: true }), 60, { comparison: comparison('rigid') }),
    definition('corner-uniform4-shuffle', 'representation', corner({ surfaceCopies: 4, gasCopies: 4, order: 'shuffle' }), 60, { comparison: comparison('split-and-order') }),
    definition('corner-dt30', 'corner-temporal', corner({}), 30),
    definition('corner-dt120', 'corner-temporal', corner({}), 120),
    definition('corner-refine-coarse', 'spatial-refinement', corner({ resolution: 2 })),
    definition('corner-refine-fine', 'spatial-refinement', corner({ resolution: 6 })),
    definition('corner-undebited-negative', 'model-diagnostic', corner({}), 60, {
      model: 'one-sided-undebited', interpretation: 'Apply surface heat increment without the equal gas debit. Energy-defect diagnostic only; not a physically competing discretization.' })
  ];
}

export function p4aCases(suite = 'all') {
  if (suite === 'all') return allP4aCases();
  if (suite !== 'quick') throw new RangeError('P4a suite must be all or quick');
  const selected = new Set(['pair-dt60', 'corner-base-dt60', 'corner-uniform4-shuffle', 'corner-undebited-negative']);
  return allP4aCases().filter(c => selected.has(c.id)).map(c => ({ ...c, duration: 0.1,
    steps: Math.round(0.1 / c.dt), exploratory: true }));
}

function rigidPosition([x, y, z]) {
  // Rz(pi/7) Rx(pi/5), followed by translation. Temperature is a transported
  // scalar: evaluate the initial field in the original coordinates, not here.
  const a = Math.PI / 5, b = Math.PI / 7;
  const yy = Math.cos(a) * y - Math.sin(a) * z, zz = Math.sin(a) * y + Math.cos(a) * z;
  return [Math.cos(b) * x - Math.sin(b) * yy + 1.25,
    Math.sin(b) * x + Math.cos(b) * yy - 0.7, zz + 2.1];
}

function seededShuffle(items, random) {
  for (let i = items.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1)); [items[i], items[j]] = [items[j], items[i]];
  }
}

export function makeP4aFixture(spec) {
  const surface = [], gas = [], cells = new Map();
  if (spec.kind === 'pair') {
    surface.push({ id: 'surface-0', position: [0, 0, 0], area: 0.5, capacityPerArea: 2,
      temperature: spec.reverseTemperature ? 300 : 600 });
    gas.push({ id: 'gas-0', position: [spec.disconnected ? 0.8 : 0.2, 0, 0], volume: 0.125,
      capacityPerVolume: 4, temperature: spec.reverseTemperature ? 600 : 300 });
    cells.set('surface-0', [0, 0, 0]); cells.set('gas-0', [0, 0, 0]);
  } else if (spec.kind === 'corner') {
    const n = spec.resolution;
    if (![2, 4, 6].includes(n)) throw new RangeError('Frozen P4a corner resolutions are 2, 4, 6');
    const dx = 0.8 / n;
    for (let panel = 0; panel < 2; panel++) for (let u = 0; u < n; u++) for (let v = 0; v < n; v++) {
      const uu = (u + 0.5) / n, vv = (v + 0.5) / n, id = `surface-${panel}-${u}-${v}`;
      surface.push({ id, position: panel === 0 ? [0, 0.1 + 0.8 * uu, -0.4 + 0.8 * vv] : [0.1 + 0.8 * uu, 0, -0.4 + 0.8 * vv],
        area: dx * dx, capacityPerArea: 2, temperature: 300 + 120 * uu + 60 * vv });
      cells.set(id, [panel, u, v]);
    }
    for (let x = 0; x < n; x++) for (let y = 0; y < n; y++) for (let z = 0; z < n; z++) {
      const xx = (x + 0.5) / n, yy = (y + 0.5) / n, zz = (z + 0.5) / n, id = `gas-${x}-${y}-${z}`;
      gas.push({ id, position: [0.1 + 0.8 * xx, 0.1 + 0.8 * yy, -0.4 + 0.8 * zz], volume: dx * dx * dx,
        capacityPerVolume: 3, temperature: 500 - 105 * xx - 60 * yy + 30 * zz });
      cells.set(id, [x, y, z]);
    }
  } else throw new RangeError(`Unknown P4a fixture ${spec.kind}`);
  const anchors = [];
  function split(items, kind, policy = 1) {
    return items.flatMap(point => {
      const cell = cells.get(point.id), count = policy === 'variable' ? 1 + ((cell[0] + 2 * cell[1] + 3 * cell[2]) % 4) : policy;
      if (!Number.isSafeInteger(count) || count < 1 || count > 4) throw new RangeError('Invalid split multiplicity');
      return Array.from({ length: count }, (_, copy) => {
        const id = count === 1 ? point.id : `${point.id}-copy${copy}`;
        anchors.push({ id, anchorId: point.id, kind, copy, copies: count, cell });
        const result = { ...point, id, position: spec.rigid ? rigidPosition(point.position) : [...point.position] };
        result[kind === 'surface' ? 'area' : 'volume'] /= count;
        return result;
      });
    });
  }
  const input = { surface: split(surface, 'surface', spec.surfaceCopies), gas: split(gas, 'gas', spec.gasCopies) };
  if (spec.order === 'reverse') { input.surface.reverse(); input.gas.reverse(); }
  else if (spec.order === 'shuffle') {
    let state = P4A.shuffleSeed;
    const random = () => { state ^= state << 13; state ^= state >>> 17; state ^= state << 5; return (state >>> 0) / 4294967296; };
    seededShuffle(input.surface, random); seededShuffle(input.gas, random);
  } else if (spec.order && spec.order !== 'forward') throw new RangeError('Unknown P4a order');
  const sum = (items, key) => items.reduce((a, p) => a + p[key], 0);
  return { input, metadata: {
    kind: spec.kind, resolution: spec.resolution ?? null, anchors,
    surfaceArea: sum(input.surface, 'area'), gasVolume: sum(input.gas, 'volume'),
    surfaceCapacity: input.surface.reduce((a, p) => a + p.area * p.capacityPerArea, 0),
    gasCapacity: input.gas.reduce((a, p) => a + p.volume * p.capacityPerVolume, 0),
    physicalDomain: spec.kind === 'corner' ? { surface: 'x=0 and y=0; other planar coordinate [0.1,0.9], z[-0.4,0.4]',
      gas: 'x,y in [0.1,0.9], z in [-0.4,0.4]', surfaceArea: 1.28, gasVolume: 0.512 } : null,
    temperatureLaw: spec.kind === 'corner' ? { surface: '300+120*u+60*v K; local normalized panel coordinates',
      gas: '500-105*xNorm-60*yNorm+30*zNorm K' } : '600/300 K, reversed only in the explicit reverse-temperature control',
    splitLaw: '1+((cell[0]+2*cell[1]+3*cell[2]) mod 4), or explicit uniform copies; measure divided among copies',
    order: spec.order ?? 'forward', shuffleSeed: spec.order === 'shuffle' ? P4A.shuffleSeed : null,
    rigid: spec.rigid ? { rotation: 'Rz(pi/7) Rx(pi/5)', translation: [1.25, -0.7, 2.1] } : null,
    units: P4A.units } };
}

export function parseP4aArgs(argv) {
  const args = { suite: 'all', out: null, help: false };
  for (let i = 0; i < argv.length; i++) {
    const value = argv[i];
    if (value === '--help' || value === '-h') args.help = true;
    else if (value === '--suite' || value === '--out') {
      if (!argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Missing value for ${value}`);
      args[value.slice(2)] = argv[++i];
    } else throw new Error(`Unknown argument ${value}`);
  }
  if (!['all', 'quick'].includes(args.suite)) throw new Error('Expected --suite all|quick');
  return args;
}
