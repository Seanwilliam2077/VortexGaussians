import test from 'node:test';
import assert from 'node:assert/strict';
import { allP4bCases, p4bCases, p4bConfig, makeP4bFixture, parseP4bArgs } from '../p4b-design.mjs';
import { compareP4bReplay, p4bStateDifference, singleP4bAnalytic } from '../p4b-run.mjs';

const close = (a, b, tolerance = 1e-12) => assert.ok(Math.abs(a - b) <= tolerance, `${a} differs from ${b}`);
const cases = () => new Map(allP4bCases().map(d => [d.id, d]));

test('P4b freezes 12 cases with distinct full temporal schedules and labels quick evidence exploratory', () => {
  const all = allP4bCases(); assert.equal(all.length, 12); assert.equal(new Set(all.map(d => d.id)).size, 12);
  for (const d of all) close(d.steps * d.dt, d.duration);
  assert.deepEqual(all.filter(d => d.id === 'main-coupled-dt60' || d.family === 'temporal-refinement').map(d => d.steps), [60, 120, 240]);
  const quick = p4bCases('quick'); assert.equal(quick.length, 8); assert.ok(quick.every(d => d.exploratory));
  assert.ok(quick.every(d => d.fixture.kind === 'single' ? d.steps === 1 : d.duration === .1 && d.steps === 6));
  assert.throws(() => p4bCases('selected-after-looking'), /all or quick/);
});

test('P4b causal controls change exactly the declared exchange, feedback or transport switch', () => {
  const map = cases(), base = p4bConfig(map.get('main-no-exchange-no-feedback'));
  for (const [id, change] of [
    ['main-no-exchange-feedback', c => { c.transport.thermalFeedback = true; }],
    ['main-exchange-no-feedback', c => { c.exchange = true; }],
    ['main-coupled-dt60', c => { c.exchange = true; c.transport.thermalFeedback = true; }],
    ['main-static-exchange', c => { c.exchange = true; c.transport.mode = 'static'; }]
  ]) { const expected = structuredClone(base); change(expected); assert.deepEqual(p4bConfig(map.get(id)), expected); }
  assert.deepEqual(p4bConfig(map.get('main-coupled-observed')), p4bConfig(map.get('main-coupled-dt60')));
  const copy = p4bConfig(map.get('main-coupled-dt60')); copy.thermal.beta = 99; copy.gas[0].G[0] = 99;
  assert.notDeepEqual(copy, p4bConfig(map.get('main-coupled-dt60')));
});

test('P4b authored 3D measures, capacities and circulation remain fixed under input reversal', () => {
  const a = makeP4bFixture({ kind: 'main', uniformTemperature: null, order: 'forward' });
  const b = makeP4bFixture({ kind: 'main', uniformTemperature: null, order: 'reverse' });
  assert.equal(a.surface.length, 32); assert.equal(a.gas.length, 64);
  close(a.surface.reduce((s, p) => s + p.area, 0), .2048);
  close(a.gas.reduce((s, p) => s + p.volume, 0), .032768);
  close(a.surface.reduce((s, p) => s + p.area * p.capacityPerArea, 0), .4096);
  close(a.gas.reduce((s, p) => s + p.volume * p.capacityPerVolume, 0), .098304);
  assert.deepEqual(b.surface, [...a.surface].reverse()); assert.deepEqual(b.gas, [...a.gas].reverse());
  assert.deepEqual(a.gas[0].position, [-.12, .40, -.12]); assert.deepEqual(a.gas.at(-1).position, [.12, .64, .12]);
  assert.deepEqual(a.gas[0].G, [-.15, .25, -.15]); assert.equal(a.gas[0].temperature, 500); assert.equal(a.gas.at(-1).temperature, 620);
  const eq = makeP4bFixture({ kind: 'main', uniformTemperature: 450, order: 'forward' });
  assert.ok([...eq.surface, ...eq.gas].every(p => p.temperature === 450));
  assert.throws(() => makeP4bFixture({ kind: 'main', uniformTemperature: 451, order: 'forward' }), /450/);
});

function sample() {
  return { frame: 1, time: .5, dynamicsHash: 'same-hash', thermalStateHash: 'thermal', fullStateHash: 'full',
    gas: [{ id: 'a', position: [0, 0, 0], velocity: [0, 0, 0], G: [0, 0, 0], sg: .07, mappedTb: .5, displayT: .5, density: 1, life: .5 },
      { id: 'b', position: [0, 0, 0], velocity: [0, 0, 0], G: [0, 0, 0], sg: .07, mappedTb: .5, displayT: .5, density: 1, life: .5 }],
    cloudOrder: ['a', 'b'], rng: { state: 11, draws: 0 },
    thermalState: { ids: ['s', 'a', 'b'], temperatures: [300, 400, 500] }, capacities: [1, 2, 3] };
}

test('P4b exposure uses matched-vector RMS and capacity-weighted temperature RMSE, not maxima', () => {
  const a = sample(), b = structuredClone(a); b.gas[0].position = [3, 4, 0]; b.gas[1].position = [0, 0, 0];
  b.thermalState.temperatures = [300, 403, 504];
  const d = p4bStateDifference(a, b); close(d.positionRms, Math.sqrt(25 / 2)); assert.equal(d.positionMax, 5);
  close(d.capacityWeightedTemperatureRmse, Math.sqrt((2 * 9 + 3 * 16) / 6)); assert.equal(d.temperatureMax, 4);
  b.gas.reverse(); b.thermalState.ids.reverse(); b.thermalState.temperatures.reverse(); b.capacities.reverse();
  assert.deepEqual(p4bStateDifference(a, b), d);
});

test('P4b comparison rejects missing identities, changed capacity and nonfinite matched quantities', () => {
  const a = sample(), b = structuredClone(a); b.gas[0].id = 'missing';
  assert.throws(() => p4bStateDifference(a, b), /identity missing/);
  const c = structuredClone(a); c.capacities[0] = 2; assert.throws(() => p4bStateDifference(a, c), /capacity differs/);
  const e = structuredClone(a); e.gas[0].position[0] = NaN; assert.throws(() => p4bStateDifference(a, e), /Invalid number/);
  const f = structuredClone(a); f.thermalState.temperatures[0] = null; assert.throws(() => p4bStateDifference(a, f), /Invalid number/);
});

test('P4b replay verifies complete physical values beyond hash and excludes display-only temperature', () => {
  const a = { definition: { id: 'reference' }, raw: [sample()] }, b = structuredClone(a); b.definition.id = 'candidate';
  b.raw[0].gas[0].displayT = .25; b.raw[0].fullStateHash = 'different';
  assert.equal(compareP4bReplay(a, b).passed, true); assert.equal(compareP4bReplay(a, b, true).passed, false);
  b.raw[0].gas[0].velocity[0] = 1e-12; assert.equal(compareP4bReplay(a, b).passed, false);
  b.raw[0].gas[0].velocity[0] = 0; b.raw[0].last = { fields: [{ id: 'a', field: { TT: .2 } }] };
  assert.equal(compareP4bReplay(a, b).exactNativeFields, false); assert.equal(compareP4bReplay(a, b).passed, false);
  b.raw = []; assert.throws(() => compareP4bReplay(a, b), /missing steps/);
});

test('P4b single-step reference combines synchronous transfer with actual Float32 buoyancy', () => {
  const definition = allP4bCases()[0], config = p4bConfig(definition), dt = definition.dt;
  const Cs = .08 ** 2 * 2, Cg = .08 ** 3 * 3;
  const G = 4 * (.08 ** 2) * (.08 ** 3) * 3 / (Math.PI * (.3 ** 3)) * (1 - .08 / .3);
  const Q = dt * G * (560 - 330), Ts = 330 + Q / Cs, Tg = 560 - Q / Cg;
  const vy = .5 * Math.fround((Tg - 300) / 300);
  const record = { definition, config, raw: [{}, { thermalState: { temperatures: [Ts, Tg] },
    gas: [{ velocity: [0, vy, 0], position: [-.12, .4 + dt * vy, 0] }] }] };
  const result = singleP4bAnalytic(record); assert.equal(result.passed, true); assert.equal(result.substeps, 1);
  record.raw[1].gas[0].velocity[1] += 1e-5; assert.equal(singleP4bAnalytic(record).passed, false);
});

test('P4b CLI rejects silent overrides and accepts an explicit portable browser executable', () => {
  assert.deepEqual(parseP4bArgs(['--suite', 'quick', '--out', 'runs/example', '--browser-executable', 'C:/Program Files/Browser/browser.exe']),
    { suite: 'quick', out: 'runs/example', browserExecutable: 'C:/Program Files/Browser/browser.exe', help: false });
  for (const argv of [['--suite', 'picked'], ['--seconds', '5'], ['--out'], ['--seed', '9']]) assert.throws(() => parseP4bArgs(argv));
  assert.equal(parseP4bArgs(['--help']).help, true);
});
