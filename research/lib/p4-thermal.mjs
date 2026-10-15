// P4a: a standard conservative, explicit surface/gas heat-exchange baseline.
// This module is independent of the demo, combustion, rendering and fluid solver.
const VERSION = 1;
const HARD_MAX_SUBSTEPS = 100000;
const GRAPH_KEYS = ['version', 'h', 'beta', 'surfaceCount', 'gasCount', 'ids', 'positions',
  'measures', 'capacityPerMeasure', 'capacities', 'sumG', 'maxRate', 'edges'];
const STATE_KEYS = ['version', 'ids', 'temperatures', 'time', 'steps', 'cumulative'];
const CUMULATIVE_KEYS = ['netSurface', 'netGas', 'substeps', 'edgeEvaluations'];

function object(value, name, keys) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError(`${name} must be an object`);
  if (Object.keys(value).some(k => !keys.includes(k))) throw new TypeError(`${name} has an unknown field`);
}
function finite(value, name, minimum = -Infinity, strict = false) {
  if (typeof value !== 'number' || !Number.isFinite(value) || (strict ? value <= minimum : value < minimum))
    throw new RangeError(`${name} must be finite and ${strict ? '>' : '>='} ${minimum}`);
  return value;
}
function integer(value, name, minimum = 0, maximum = Number.MAX_SAFE_INTEGER) {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) throw new RangeError(`${name} must be a safe integer in [${minimum}, ${maximum}]`);
  return value;
}
function array(value, name, length) {
  if (!Array.isArray(value) || (length !== undefined && value.length !== length)) throw new TypeError(`${name} has an invalid array length/type`);
}
function identifiers(ids) {
  const seen = new Set();
  for (const id of ids) {
    if (!((typeof id === 'string' && id.trim().length > 0) || (Number.isSafeInteger(id) && id >= 0)))
      throw new TypeError('IDs must be nonempty strings or nonnegative safe integers');
    // One namespace across node types and JSON-friendly numeric/string forms.
    const key = String(id);
    if (seen.has(key)) throw new RangeError(`duplicate node ID: ${key}`);
    seen.add(key);
  }
}
function position(p, name) {
  array(p, name, 3);
  p.forEach((x, i) => finite(x, `${name}[${i}]`));
}
function add(sum, correction, i, value) {
  const y = value - correction[i], next = sum[i] + y;
  correction[i] = (next - sum[i]) - y;
  sum[i] = next;
  if (!Number.isFinite(next) || !Number.isFinite(correction[i])) throw new RangeError('heat accumulation overflow');
}
function capacityRate(capacities, sumG) {
  let maxRate = 0;
  for (let i = 0; i < capacities.length; i++) maxRate = Math.max(maxRate, finite(sumG[i] / capacities[i], 'node exchange rate', 0));
  return maxRate;
}

function validateGraph(graph) {
  object(graph, 'graph', GRAPH_KEYS);
  if (graph.version !== VERSION) throw new RangeError('unsupported graph version');
  finite(graph.h, 'graph.h', 0, true); finite(graph.beta, 'graph.beta', 0, true);
  const ns = integer(graph.surfaceCount, 'surfaceCount'), ng = integer(graph.gasCount, 'gasCount');
  const n = integer(ns + ng, 'node count');
  for (const key of ['ids', 'positions', 'measures', 'capacityPerMeasure', 'capacities', 'sumG']) array(graph[key], `graph.${key}`, n);
  identifiers(graph.ids);
  for (let i = 0; i < n; i++) {
    position(graph.positions[i], `graph.positions[${i}]`);
    finite(graph.measures[i], 'node measure', 0, true); finite(graph.capacityPerMeasure[i], 'capacity density', 0, true);
    finite(graph.capacities[i], 'node capacity', 0, true); finite(graph.sumG[i], 'node conductance sum', 0);
    if (graph.capacities[i] !== graph.measures[i] * graph.capacityPerMeasure[i]) throw new RangeError('node capacity differs from authored measure times capacity density');
  }
  array(graph.edges, 'graph.edges');
  const sums = Array(n).fill(0), pairs = new Set();
  for (const edge of graph.edges) {
    object(edge, 'edge', ['i', 'j', 'G']);
    integer(edge.i, 'edge.i', 0, ns - 1); integer(edge.j, 'edge.j', ns, n - 1); finite(edge.G, 'edge.G', 0, true);
    const key = `${edge.i},${edge.j}`;
    if (pairs.has(key)) throw new RangeError('duplicate exchange edge');
    pairs.add(key); sums[edge.i] += edge.G; sums[edge.j] += edge.G;
  }
  if (sums.some((x, i) => !Number.isFinite(x) || x !== graph.sumG[i])) throw new RangeError('graph conductance sums are inconsistent');
  if (graph.maxRate !== capacityRate(graph.capacities, sums)) throw new RangeError('graph maximum exchange rate is inconsistent');
}

function validateState(state, graph) {
  object(state, 'state', STATE_KEYS);
  if (state.version !== VERSION) throw new RangeError('unsupported state version');
  const n = graph.capacities.length;
  array(state.ids, 'state.ids', n); array(state.temperatures, 'state.temperatures', n);
  if (state.ids.some((id, i) => id !== graph.ids[i])) throw new RangeError('state identity/order does not match graph');
  state.temperatures.forEach((t, i) => finite(t, `temperature[${i}]`, 0));
  finite(state.time, 'state.time', 0); integer(state.steps, 'state.steps');
  object(state.cumulative, 'state.cumulative', CUMULATIVE_KEYS);
  finite(state.cumulative.netSurface, 'cumulative.netSurface'); finite(state.cumulative.netGas, 'cumulative.netGas');
  integer(state.cumulative.substeps, 'cumulative.substeps'); integer(state.cumulative.edgeEvaluations, 'cumulative.edgeEvaluations');
}

function energyUnchecked(temperatures, graph) {
  const sums = [0, 0], corrections = [0, 0];
  for (let i = 0; i < temperatures.length; i++) {
    const value = finite(graph.capacities[i] * temperatures[i], 'node energy', 0);
    add(sums, corrections, i < graph.surfaceCount ? 0 : 1, value);
  }
  return { surface: sums[0], gas: sums[1], total: finite(sums[0] + sums[1], 'total energy', 0) };
}

/** Return {surface, gas, total} sensible energy in J. No hidden source/reservoir. */
export function thermalEnergy(state, graph) {
  validateGraph(graph); validateState(state, graph);
  return energyUnchecked(state.temperatures, graph);
}

/** Build a fixed 3D cross-material graph and a separate initial state.
 * Surface: area [m²], capacityPerArea [J/(m² K)].
 * Gas: volume [m³], capacityPerVolume [J/(m³ K)].
 * Options: h [m], beta [W/(m² K)]; Kelvin temperatures are nonnegative.
 * G=beta*A*V*K_h has units W/K. K_h integrates to one in R³.
 */
export function buildThermalGraph(scene, options) {
  object(scene, 'scene', ['surface', 'gas']); array(scene.surface, 'surface'); array(scene.gas, 'gas');
  object(options, 'options', ['h', 'beta']);
  const h = finite(options.h, 'h', 0, true), beta = finite(options.beta, 'beta', 0, true);
  const normalization = finite(3 / (Math.PI * h * h * h), 'kernel normalization', 0, true);
  const graph = { version: VERSION, h, beta, surfaceCount: scene.surface.length, gasCount: scene.gas.length,
    ids: [], positions: [], measures: [], capacityPerMeasure: [], capacities: [], sumG: [], maxRate: 0, edges: [] };
  const temperatures = [];
  for (const [kind, nodes] of [['surface', scene.surface], ['gas', scene.gas]]) {
    const measure = kind === 'surface' ? 'area' : 'volume';
    const density = kind === 'surface' ? 'capacityPerArea' : 'capacityPerVolume';
    for (const node of nodes) {
      object(node, `${kind} node`, ['id', 'position', measure, density, 'temperature']);
      position(node.position, `${kind}.position`);
      const m = finite(node[measure], measure, 0, true), c = finite(node[density], density, 0, true);
      graph.ids.push(node.id); graph.positions.push([...node.position]); graph.measures.push(m); graph.capacityPerMeasure.push(c);
      graph.capacities.push(finite(m * c, 'node capacity', 0, true)); graph.sumG.push(0);
      temperatures.push(finite(node.temperature, 'temperature', 0));
    }
  }
  identifiers(graph.ids);
  for (let i = 0; i < graph.surfaceCount; i++) for (let j = graph.surfaceCount; j < graph.ids.length; j++) {
    const a = graph.positions[i], b = graph.positions[j];
    const distance = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
    if (!Number.isFinite(distance)) throw new RangeError('pair distance overflow');
    if (distance >= h) continue;
    const kernel = normalization * (1 - distance / h);
    const G = finite(beta * graph.measures[i] * graph.measures[j] * kernel, 'pair conductance', 0, true);
    graph.edges.push({ i, j, G });
    graph.sumG[i] = finite(graph.sumG[i] + G, 'surface conductance sum', 0);
    graph.sumG[j] = finite(graph.sumG[j] + G, 'gas conductance sum', 0);
  }
  graph.maxRate = capacityRate(graph.capacities, graph.sumG);
  const state = { version: VERSION, ids: [...graph.ids], temperatures, time: 0, steps: 0,
    cumulative: { netSurface: 0, netGas: 0, substeps: 0, edgeEvaluations: 0 } };
  // Reject finite temperatures/capacities whose physical energy is not representable.
  energyUnchecked(temperatures, graph);
  return { graph, state };
}

/** Synchronous explicit Euler exchange using the same signed Q on both sides.
 * Input graph/state are never changed. Every substep reads all old temperatures
 * before applying the accumulated energy deltas. No source, loss, clipping,
 * combustion, gas advection, material inference or renderer is present.
 */
export function stepThermalGraph(state, graph, dt, options = {}) {
  validateGraph(graph); validateState(state, graph); finite(dt, 'dt', 0);
  object(options, 'step options', ['safety', 'maxSubsteps']);
  const safety = options.safety === undefined ? .9 : finite(options.safety, 'safety', 0, true);
  if (safety > 1) throw new RangeError('safety must be <= 1');
  const maxSubsteps = options.maxSubsteps === undefined ? HARD_MAX_SUBSTEPS : integer(options.maxSubsteps, 'maxSubsteps', 1, HARD_MAX_SUBSTEPS);
  const requested = dt * graph.maxRate / safety;
  if (!Number.isFinite(requested)) throw new RangeError('requested substep count overflow');
  const substeps = Math.max(1, Math.ceil(requested));
  integer(substeps, 'substeps', 1, maxSubsteps);
  const substepDt = dt / substeps, maxCfl = substepDt * graph.maxRate;
  if (!Number.isFinite(maxCfl) || maxCfl > 1) throw new RangeError('substep violates the positivity bound');
  const edgeEvaluations = integer(substeps * graph.edges.length, 'edge evaluations');
  const Ebefore = energyUnchecked(state.temperatures, graph), n = graph.capacities.length;
  let temperatures = [...state.temperatures];
  const flux = [0, 0], fluxCorrection = [0, 0];
  for (let step = 0; step < substeps; step++) {
    const delta = Array(n).fill(0), correction = Array(n).fill(0);
    for (const { i, j, G } of graph.edges) {
      const Q = finite(substepDt * G * (temperatures[j] - temperatures[i]), 'pair heat');
      add(delta, correction, i, Q); add(delta, correction, j, -Q);
      add(flux, fluxCorrection, 0, Q); add(flux, fluxCorrection, 1, -Q);
    }
    temperatures = temperatures.map((t, i) => finite(t + delta[i] / graph.capacities[i], 'updated temperature', 0));
  }
  const Eafter = energyUnchecked(temperatures, graph);
  const next = { version: VERSION, ids: [...state.ids], temperatures,
    time: finite(state.time + dt, 'state.time', 0), steps: integer(state.steps + 1, 'state.steps'),
    cumulative: {
      netSurface: finite(state.cumulative.netSurface + flux[0], 'cumulative.netSurface'),
      netGas: finite(state.cumulative.netGas + flux[1], 'cumulative.netGas'),
      substeps: integer(state.cumulative.substeps + substeps, 'cumulative.substeps'),
      edgeEvaluations: integer(state.cumulative.edgeEvaluations + edgeEvaluations, 'cumulative.edgeEvaluations') } };
  const ledger = { dt, safety, maxRate: graph.maxRate, substeps, substepDt, maxCfl, edgeEvaluations,
    Ebefore, Eafter, netSurface: flux[0], netGas: flux[1],
    energyChangeSurface: Eafter.surface - Ebefore.surface, energyChangeGas: Eafter.gas - Ebefore.gas,
    energyResidual: Eafter.total - Ebefore.total };
  return { state: next, ledger };
}
