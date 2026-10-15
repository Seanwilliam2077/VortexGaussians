import test from 'node:test';
import assert from 'node:assert/strict';
import { buildThermalGraph, stepThermalGraph, thermalEnergy } from '../lib/p4-thermal.mjs';

const close = (a, b, tolerance = 1e-12) => assert.ok(Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b)), `${a} differs from ${b}`);
const surface = (id, position, temperature = 300, area = 1) => ({ id, position, temperature, area, capacityPerArea: 2 });
const gas = (id, position, temperature = 500, volume = 1) => ({ id, position, temperature, volume, capacityPerVolume: 3 });
const pairScene = () => ({ surface: [surface('s', [0, 0, 0])], gas: [gas('g', [0, 0, 0])] });
const options = { h: 1, beta: Math.PI / 3 }; // Unit conductance for the coincident unit measures.
function run(scene, dt, steps, opts = options) {
  const built = buildThermalGraph(scene, opts); let state = built.state;
  for (let k = 0; k < steps; k++) state = stepThermalGraph(state, built.graph, dt).state;
  return { graph: built.graph, state };
}
function keyed(state) { return new Map(state.ids.map((id, i) => [id, state.temperatures[i]])); }

test('P4a graph has explicit capacities, 3D compact support and product-measure conductance', () => {
  const scene = { surface: [surface('s', [0, 0, 0], 300, 2)], gas: [gas('near', [0, 0, .5], 500, .25), gas('cutoff', [0, 0, 1]), gas('far', [0, 0, 2])] };
  const { graph, state } = buildThermalGraph(scene, options);
  assert.deepEqual(graph.ids, ['s', 'near', 'cutoff', 'far']);
  assert.deepEqual(graph.capacities, [4, .75, 3, 3]); assert.equal(graph.edges.length, 1);
  assert.equal(graph.edges[0].i, 0); assert.equal(graph.edges[0].j, 1); close(graph.edges[0].G, .25);
  graph.sumG.forEach((v, i) => close(v, [.25, .25, 0, 0][i])); close(graph.maxRate, 1 / 3);
  assert.deepEqual(thermalEnergy(state, graph), { surface: 1200, gas: 3375, total: 4575 });
});

test('P4a one step transfers the same energy in opposite directions without mutating inputs', () => {
  const scene = pairScene(), original = structuredClone(scene), { graph, state } = buildThermalGraph(scene, options);
  const before = JSON.stringify({ graph, state }), result = stepThermalGraph(state, graph, .1);
  close(result.state.temperatures[0], 310); close(result.state.temperatures[1], 500 - 20 / 3);
  close(result.ledger.netSurface, 20); close(result.ledger.netGas, -20); close(result.ledger.energyResidual, 0);
  close(result.ledger.energyChangeSurface, result.ledger.netSurface); close(result.ledger.energyChangeGas, result.ledger.netGas);
  assert.equal(result.ledger.substeps, 1); assert.equal(result.ledger.edgeEvaluations, 1);
  assert.equal(result.state.time, .1); assert.equal(result.state.steps, 1);
  assert.notEqual(result.state, state); assert.notEqual(result.state.temperatures, state.temperatures);
  assert.equal(JSON.stringify({ graph, state }), before); assert.deepEqual(scene, original);
});

test('P4a two-reservoir solution approaches the independent exponential reference as dt halves', () => {
  const equilibrium = 420, decay = Math.exp(-(1 / 2 + 1 / 3));
  const exact = [equilibrium - 120 * decay, equilibrium + 80 * decay];
  const errors = [.1, .05, .025].map(dt => {
    const { state, graph } = run(pairScene(), dt, Math.round(1 / dt));
    close(thermalEnergy(state, graph).total, 2100);
    return Math.hypot(...state.temperatures.map((x, i) => x - exact[i]));
  });
  assert.ok(errors[1] < .6 * errors[0] && errors[2] < .6 * errors[1]);
  const { state } = run(pairScene(), .1, 1000);
  state.temperatures.forEach(t => close(t, equilibrium));
});

test('P4a an equilibrium state stays exactly fixed while ledger clocks advance', () => {
  const scene = pairScene(); scene.gas[0].temperature = 300;
  const { graph, state } = buildThermalGraph(scene, options), result = stepThermalGraph(state, graph, 10);
  assert.deepEqual(result.state.temperatures, [300, 300]);
  assert.equal(result.ledger.netSurface, 0); assert.equal(result.ledger.netGas, 0); assert.equal(result.ledger.energyResidual, 0);
  assert.equal(result.state.cumulative.substeps, result.ledger.substeps);
});

test('P4a CFL substeps preserve the maximum principle and energy on a heterogeneous 3D graph', () => {
  const scene = { surface: [surface('a', [0, 0, 0], 100, .2), surface('b', [.2, .1, .2], 700, .9)],
    gas: [gas('c', [.1, .2, .1], 300, .15), gas('d', [.4, .2, .1], 1000, .6)] };
  const { graph, state } = buildThermalGraph(scene, { h: .8, beta: 20 });
  const { state: next, ledger } = stepThermalGraph(state, graph, 2);
  assert.equal(ledger.substeps, Math.max(1, Math.ceil(2 * graph.maxRate / .9)));
  assert.ok(ledger.substeps > 1 && ledger.maxCfl <= .9);
  assert.ok(next.temperatures.every(t => t >= 100 && t <= 1000));
  close(ledger.Ebefore.total, ledger.Eafter.total); close(ledger.netSurface, -ledger.netGas);
  assert.equal(ledger.edgeEvaluations, ledger.substeps * graph.edges.length);
});

test('P4a surface and gas coincident splitting preserve temperatures, capacities and exchanged energy', () => {
  const reference = run(pairScene(), .02, 50);
  for (const [ns, ng] of [[2, 1], [1, 4], [4, 2]]) {
    const scene = { surface: Array.from({ length: ns }, (_, i) => surface(`s${i}`, [0, 0, 0], 300, 1 / ns)),
      gas: Array.from({ length: ng }, (_, i) => gas(`g${i}`, [0, 0, 0], 500, 1 / ng)) };
    const { graph, state } = run(scene, .02, 50);
    state.temperatures.slice(0, ns).forEach(t => close(t, reference.state.temperatures[0]));
    state.temperatures.slice(ns).forEach(t => close(t, reference.state.temperatures[1]));
    close(thermalEnergy(state, graph).total, thermalEnergy(reference.state, reference.graph).total);
    close(state.cumulative.netSurface, reference.state.cumulative.netSurface);
    close(graph.maxRate, reference.graph.maxRate);
  }
});

test('P4a node permutation preserves the labelled solution and the builder keeps input order', () => {
  const scene = { surface: [surface('s0', [0, 0, 0], 300, .4), surface('s1', [.1, -.2, .2], 410, .6)],
    gas: [gas('g0', [.2, .1, -.1], 500, .7), gas('g1', [-.2, .1, .1], 610, .3)] };
  const original = run(scene, .01, 100), reversed = run({ surface: [...scene.surface].reverse(), gas: [...scene.gas].reverse() }, .01, 100);
  assert.deepEqual(reversed.graph.ids, ['s1', 's0', 'g1', 'g0']);
  const a = keyed(original.state), b = keyed(reversed.state); for (const [id, t] of a) close(t, b.get(id));
  close(original.state.cumulative.netSurface, reversed.state.cumulative.netSurface);
});

test('P4a rigid 3D transforms preserve graph conductance and temperatures', () => {
  const scene = { surface: [surface('s', [0, .25, .5])], gas: [gas('g', [.25, .5, .25])] };
  const transformed = structuredClone(scene);
  for (const node of [...transformed.surface, ...transformed.gas]) {
    const [x, y, z] = node.position; node.position = [-y + 2, z - 4, -x + 1];
  }
  const a = run(scene, .02, 20), b = run(transformed, .02, 20);
  assert.deepEqual(a.graph.edges, b.graph.edges); assert.deepEqual(a.state.temperatures, b.state.temperatures);
});

test('P4a empty and disconnected graphs use one substep and leave temperatures unchanged', () => {
  for (const scene of [{ surface: [], gas: [] }, { surface: [surface('s', [0, 0, 0])], gas: [] },
    { surface: [surface('s', [0, 0, 0])], gas: [gas('g', [2, 0, 0])] }]) {
    const { state, graph } = buildThermalGraph(scene, options), result = stepThermalGraph(state, graph, 10);
    assert.equal(graph.edges.length, 0); assert.equal(result.ledger.substeps, 1);
    assert.deepEqual(result.state.temperatures, state.temperatures); assert.equal(result.ledger.edgeEvaluations, 0);
    assert.equal(result.ledger.energyResidual, 0);
  }
});

test('P4a zero dt is a finite no-op step with an explicit zero heat ledger', () => {
  const { state, graph } = buildThermalGraph(pairScene(), options), { state: next, ledger } = stepThermalGraph(state, graph, 0);
  assert.deepEqual(next.temperatures, state.temperatures); assert.equal(next.time, 0); assert.equal(next.steps, 1);
  assert.equal(ledger.substeps, 1); assert.equal(ledger.netSurface, 0); assert.equal(ledger.maxCfl, 0);
});

test('P4a rejects malformed authored material data rather than inventing or clipping physical state', () => {
  for (const mutate of [s => { s.surface[0].area = 0; }, s => { s.gas[0].volume = -1; },
    s => { s.surface[0].capacityPerArea = NaN; }, s => { s.gas[0].capacityPerVolume = Infinity; },
    s => { s.gas[0].temperature = -1; }, s => { delete s.surface[0].temperature; },
    s => { s.surface[0].position = [0, 1]; }, s => { s.gas[0].position[2] = Infinity; },
    s => { s.gas[0].id = 's'; }, s => { s.surface[0].id = 1; s.gas[0].id = '1'; },
    s => { s.surface[0].id = ''; }, s => { s.surface[0].areaWeight = 1; }]) {
    const scene = pairScene(); mutate(scene); assert.throws(() => buildThermalGraph(scene, options));
  }
  for (const opts of [{}, { h: 0, beta: 1 }, { h: 1, beta: 0 }, { h: 1, beta: NaN }, { ...options, unknown: true }])
    assert.throws(() => buildThermalGraph(pairScene(), opts));
});

test('P4a rejects incompatible state, inconsistent graph and unsafe substep counts', () => {
  const { graph, state } = buildThermalGraph(pairScene(), options);
  for (const opts of [{ safety: 0 }, { safety: 1.01 }, { maxSubsteps: 100001 }, { maxSubsteps: 0 }, { other: 1 }])
    assert.throws(() => stepThermalGraph(state, graph, .1, opts));
  for (const dt of [-1, NaN, Infinity]) assert.throws(() => stepThermalGraph(state, graph, dt));
  assert.throws(() => stepThermalGraph(state, graph, 10, { maxSubsteps: 1 }));
  assert.throws(() => stepThermalGraph(state, graph, Number.MAX_VALUE));
  const wrong = structuredClone(state); wrong.ids.reverse(); assert.throws(() => stepThermalGraph(wrong, graph, .1));
  const bad = structuredClone(graph); bad.edges[0].G *= 2; assert.throws(() => stepThermalGraph(state, bad, .1));
  const belowZero = structuredClone(state); belowZero.temperatures[0] = -.001; assert.throws(() => thermalEnergy(belowZero, graph));
});

test('P4a rejects arithmetic overflow or underflow that destroys positive physical quantities', () => {
  assert.throws(() => buildThermalGraph(pairScene(), { h: 1e-200, beta: 1 }));
  assert.throws(() => buildThermalGraph(pairScene(), { h: 1e200, beta: 1 }));
  const huge = pairScene(); huge.surface[0].area = Number.MAX_VALUE;
  assert.throws(() => buildThermalGraph(huge, options));
  const energy = pairScene(); energy.surface[0].temperature = Number.MAX_VALUE;
  assert.throws(() => buildThermalGraph(energy, options));
});
