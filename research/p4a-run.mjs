import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { P4A, p4aCases, makeP4aFixture, parseP4aArgs } from './p4a-design.mjs';
import { buildThermalGraph, stepThermalGraph, thermalEnergy } from './lib/p4-thermal.mjs';
import { hostMetadata, researchRoot } from './lib/runtime.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireTrue = (condition, message) => { if (!condition) throw new Error(message); };
const relative = (difference, scale) => Math.abs(difference) / Math.max(1, Math.abs(scale));

function compensatedSum(values) {
  let total = 0, correction = 0;
  for (const value of values) { const y = value - correction, next = total + y; correction = (next - total) - y; total = next; }
  return total;
}

// Deliberately wrong model: same fixed graph, synchronous staging and CFL rule,
// but only the surface gets Q. This diagnoses energy creation/loss; it is never
// included in a conservative-method accuracy comparison.
export function stepUndebited(state, graph, dt, { safety, maxSubsteps }) {
  const substeps = Math.max(1, Math.ceil(dt * graph.maxRate / safety));
  requireTrue(Number.isSafeInteger(substeps) && substeps <= maxSubsteps, 'Negative control substep overflow');
  const substepDt = dt / substeps, Ebefore = thermalEnergy(state, graph);
  let temperatures = [...state.temperatures], netSurface = 0, fluxCorrection = 0;
  for (let substep = 0; substep < substeps; substep++) {
    const delta = Array(temperatures.length).fill(0), correction = Array(temperatures.length).fill(0);
    for (const { i, j, G } of graph.edges) {
      const Q = substepDt * G * (temperatures[j] - temperatures[i]);
      const y = Q - correction[i], next = delta[i] + y; correction[i] = (next - delta[i]) - y; delta[i] = next;
      const fy = Q - fluxCorrection, fn = netSurface + fy; fluxCorrection = (fn - netSurface) - fy; netSurface = fn;
    }
    temperatures = temperatures.map((T, i) => T + delta[i] / graph.capacities[i]);
  }
  const edgeEvaluations = substeps * graph.edges.length;
  const next = { ...state, ids: [...state.ids], temperatures, time: state.time + dt, steps: state.steps + 1,
    cumulative: { netSurface: state.cumulative.netSurface + netSurface, netGas: state.cumulative.netGas,
      substeps: state.cumulative.substeps + substeps, edgeEvaluations: state.cumulative.edgeEvaluations + edgeEvaluations } };
  const Eafter = thermalEnergy(next, graph);
  return { state: next, ledger: { dt, safety, maxRate: graph.maxRate, substeps, substepDt,
    maxCfl: substepDt * graph.maxRate, edgeEvaluations, Ebefore, Eafter, netSurface, netGas: 0,
    energyChangeSurface: Eafter.surface - Ebefore.surface, energyChangeGas: Eafter.gas - Ebefore.gas,
    energyResidual: Eafter.total - Ebefore.total } };
}

function snapshot(state, graph, ledger) {
  return { step: state.steps, time: state.time, temperatures: [...state.temperatures],
    capacities: [...graph.capacities], cumulative: { ...state.cumulative }, ledger };
}

export function validateP4aRecord(record) {
  const { definition, graph, raw, initialEnergy } = record;
  requireTrue(raw.length === definition.steps + 1, 'Missing outer-step snapshots');
  const low = Math.min(...raw[0].temperatures), high = Math.max(...raw[0].temperatures), initial = raw[0].temperatures;
  const conservative = definition.model === 'conservative';
  let maxRelativeEnergyDrift = 0, maxLedgerResidual = 0, maxDebitCreditResidual = 0, maxCfl = 0;
  let minimumTemperature = Infinity, maximumTemperature = -Infinity, minSubsteps = Infinity, maxSubsteps = 0;
  for (let step = 0; step < raw.length; step++) {
    const sample = raw[step];
    requireTrue(sample.step === step && Math.abs(sample.time - step * definition.dt) < 1e-12, 'Step/time mismatch');
    requireTrue(sample.temperatures.length === graph.ids.length && sample.capacities.length === graph.ids.length, 'Missing state or capacity');
    for (let i = 0; i < graph.ids.length; i++) {
      const T = sample.temperatures[i];
      requireTrue(Number.isFinite(T), 'Nonfinite temperature');
      requireTrue(sample.capacities[i] === graph.capacities[i], 'Capacity changed during exchange');
      requireTrue(T >= low - P4A.temperatureTolerance && T <= high + P4A.temperatureTolerance, 'Discrete maximum principle failed');
      if (graph.sumG[i] === 0) requireTrue(T === initial[i], 'Isolated node changed');
      minimumTemperature = Math.min(minimumTemperature, T); maximumTemperature = Math.max(maximumTemperature, T);
    }
    const energy = compensatedSum(sample.temperatures.map((T, i) => T * graph.capacities[i]));
    maxRelativeEnergyDrift = Math.max(maxRelativeEnergyDrift, relative(energy - initialEnergy.total, initialEnergy.total));
    if (step === 0) { requireTrue(sample.ledger === null, 'Initial ledger must be null'); continue; }
    const l = sample.ledger;
    requireTrue(l && Object.values(l).every(value => typeof value === 'object' || Number.isFinite(value)), 'Invalid ledger');
    requireTrue(l.substeps === Math.max(1, Math.ceil(definition.dt * graph.maxRate / definition.options.safety)), 'Incorrect substep count');
    requireTrue(l.edgeEvaluations === l.substeps * graph.edges.length, 'Edge workload mismatch');
    requireTrue(l.maxCfl <= definition.options.safety + 1e-12, 'CFL safety violated');
    if (definition.family === 'cfl-control') requireTrue(l.substeps > 1, 'CFL stress not exposed');
    minSubsteps = Math.min(minSubsteps, l.substeps); maxSubsteps = Math.max(maxSubsteps, l.substeps); maxCfl = Math.max(maxCfl, l.maxCfl);
    for (const error of [l.energyChangeSurface - l.netSurface, l.energyChangeGas - l.netGas,
      l.energyResidual - (l.netSurface + l.netGas)]) maxLedgerResidual = Math.max(maxLedgerResidual, relative(error, initialEnergy.total));
    maxDebitCreditResidual = Math.max(maxDebitCreditResidual, relative(l.netSurface + l.netGas, initialEnergy.total));
    requireTrue(sample.cumulative.substeps === raw[step - 1].cumulative.substeps + l.substeps, 'Cumulative substeps mismatch');
    requireTrue(sample.cumulative.edgeEvaluations === raw[step - 1].cumulative.edgeEvaluations + l.edgeEvaluations, 'Cumulative workload mismatch');
  }
  requireTrue(maxLedgerResidual <= P4A.energyTolerance, 'Heat ledger does not explain state change');
  if (conservative) {
    requireTrue(maxRelativeEnergyDrift <= P4A.energyTolerance, 'Closed-system energy drift exceeded tolerance');
    requireTrue(maxDebitCreditResidual <= P4A.energyTolerance, 'Exchange debits and credits do not balance');
  } else requireTrue(maxRelativeEnergyDrift > P4A.energyTolerance, 'Undebited negative control did not expose an energy defect');
  const last = raw.at(-1), weightedMean = (start, end) => {
    const capacity = compensatedSum(graph.capacities.slice(start, end));
    return compensatedSum(last.temperatures.slice(start, end).map((T, k) => T * graph.capacities[start + k])) / capacity;
  };
  return { conservative, nodeCount: graph.ids.length, surfaceCount: graph.surfaceCount, gasCount: graph.gasCount,
    edgeCount: graph.edges.length, isolatedCount: graph.sumG.filter(x => x === 0).length,
    maximumRate: graph.maxRate, minSubsteps, maxSubsteps, maxCfl, edgeEvaluations: last.cumulative.edgeEvaluations,
    maxRelativeEnergyDrift, maxLedgerResidual, maxDebitCreditResidual, minimumTemperature, maximumTemperature,
    finalSurfaceMean: weightedMean(0, graph.surfaceCount), finalGasMean: weightedMean(graph.surfaceCount, graph.ids.length),
    referenceInterpretation: 'Endpoint means here include explicit time-discretization error. Spatial-refinement assessment uses independently computed continuous-time finite-graph solutions.' };
}

export function runP4aCase(definition) {
  const { input, metadata } = makeP4aFixture(definition.fixture);
  const record = { definition, input, fixture: metadata, options: { ...definition.options }, status: 'running', raw: [] };
  try {
    const built = buildThermalGraph(input, { h: definition.options.h, beta: definition.options.beta });
    record.graph = built.graph; let state = built.state;
    record.initialEnergy = thermalEnergy(state, built.graph); record.raw.push(snapshot(state, built.graph, null));
    const step = definition.model === 'conservative' ? stepThermalGraph : stepUndebited;
    for (let i = 0; i < definition.steps; i++) {
      const result = step(state, built.graph, definition.dt, { safety: definition.options.safety, maxSubsteps: definition.options.maxSubsteps });
      state = result.state; record.raw.push(snapshot(state, built.graph, result.ledger));
    }
    record.summary = validateP4aRecord(record); record.status = 'passed';
  } catch (error) { record.status = 'failed'; record.error = { name: error.name, message: error.message, stack: error.stack }; }
  return record;
}

export function compareP4aAnchors(reference, candidate) {
  requireTrue(reference.status === 'passed' && candidate.status === 'passed', 'Cannot compare failed cases');
  requireTrue(reference.raw.length === candidate.raw.length, 'Comparison checkpoint count differs');
  const byId = new Map(candidate.fixture.anchors.map(a => [a.id, a.anchorId]));
  const refIndex = new Map(reference.graph.ids.map((id, i) => [id, i]));
  const capacities = new Map();
  let maxTemperatureDifference = 0, maxRelativeEnergyDifference = 0, maxRelativeCapacityDifference = 0;
  for (let i = 0; i < candidate.graph.ids.length; i++) {
    const id = byId.get(candidate.graph.ids[i]); requireTrue(refIndex.has(id), 'Unmatched physical anchor');
    capacities.set(id, (capacities.get(id) ?? 0) + candidate.graph.capacities[i]);
  }
  requireTrue(capacities.size === reference.graph.ids.length, 'Physical anchor missing from candidate');
  for (const [id, C] of capacities) {
    const referenceCapacity = reference.graph.capacities[refIndex.get(id)];
    maxRelativeCapacityDifference = Math.max(maxRelativeCapacityDifference, Math.abs(C - referenceCapacity) / referenceCapacity);
  }
  for (let step = 0; step < reference.raw.length; step++) {
    const a = reference.raw[step], b = candidate.raw[step]; requireTrue(Math.abs(a.time - b.time) < 1e-12, 'Comparison times differ');
    for (let i = 0; i < candidate.graph.ids.length; i++) maxTemperatureDifference = Math.max(maxTemperatureDifference,
      Math.abs(b.temperatures[i] - a.temperatures[refIndex.get(byId.get(candidate.graph.ids[i]))]));
    const ea = compensatedSum(a.temperatures.map((T, i) => T * a.capacities[i]));
    const eb = compensatedSum(b.temperatures.map((T, i) => T * b.capacities[i]));
    maxRelativeEnergyDifference = Math.max(maxRelativeEnergyDifference, relative(eb - ea, ea));
  }
  return { reference: reference.definition.id, candidate: candidate.definition.id, type: candidate.definition.comparison.type,
    checkpointCount: reference.raw.length, maxTemperatureDifference, maxRelativeEnergyDifference, maxRelativeCapacityDifference,
    passed: maxTemperatureDifference <= P4A.temperatureTolerance && maxRelativeEnergyDifference <= P4A.energyTolerance && maxRelativeCapacityDifference <= P4A.energyTolerance };
}

export function pairAnalytic(record) {
  requireTrue(record.graph.ids.length === 2, 'Analytic pair requires two reservoirs');
  const [Cs, Cg] = record.graph.capacities, [Ts, Tg] = record.raw[0].temperatures;
  const G = record.graph.edges.reduce((a, e) => a + e.G, 0), time = record.raw.at(-1).time;
  const mean = (Cs * Ts + Cg * Tg) / (Cs + Cg), difference = (Ts - Tg) * Math.exp(-G * (1 / Cs + 1 / Cg) * time);
  const exact = [mean + Cg / (Cs + Cg) * difference, mean - Cs / (Cs + Cg) * difference];
  const final = record.raw.at(-1).temperatures;
  const error = Math.sqrt((Cs * (final[0] - exact[0]) ** 2 + Cg * (final[1] - exact[1]) ** 2) / (Cs + Cg));
  return { id: record.definition.id, time, exact, capacityWeightedRmse: error,
    interpretation: 'Continuous-time two-reservoir solution on this fixed conductance graph; not a calibrated physical experiment.' };
}

export function analyzeP4a(records, complete) {
  const byId = new Map(records.map(r => [r.definition.id, r])), comparisons = [], failures = [];
  for (const r of records) if (r.definition.comparison) {
    try { const c = compareP4aAnchors(byId.get(r.definition.comparison.reference), r); comparisons.push(c); if (!c.passed) failures.push(`${r.definition.id}: representation invariance failed`); }
    catch (error) { failures.push(`${r.definition.id}: ${error.message}`); }
  }
  const pair = records.filter(r => r.status === 'passed' && r.definition.fixture.kind === 'pair').map(pairAnalytic);
  const errors = [30, 60, 120].map(n => pair.find(p => p.id === `pair-dt${n}`)?.capacityWeightedRmse);
  const pairComplete = errors.every(Number.isFinite), temporalPair = { complete: pairComplete, dt: [1 / 30, 1 / 60, 1 / 120],
    finalCapacityWeightedRmse: errors.map(e => e ?? null), passed: pairComplete ? errors[1] < errors[0] && errors[2] < errors[1] : null };
  if (complete && (!pairComplete || !temporalPair.passed)) failures.push('Analytic pair temporal convergence failed or is incomplete');
  const negative = byId.get('corner-undebited-negative');
  return { comparisons, pairAnalytic: pair, temporalPair,
    negativeControl: negative ? { id: negative.definition.id, status: negative.status, maxRelativeEnergyDrift: negative.summary?.maxRelativeEnergyDrift ?? null,
      interpretation: 'Energy-defect exposure only; excluded from conservative accuracy comparisons.' } : null,
    referenceStatus: 'pending-independent-audit',
    independentReferenceRequired: 'Rebuild G and capacities from inputs; compare all explicit substeps and the continuous-time symmetric generalized-Laplacian exponential. Require pair/corner final capacity-weighted RMSE to decrease across dt30/dt60/dt120. Report exact-discrete-space refinement means without claiming general convergence.',
    failures };
}

export async function mainP4a(argv = process.argv.slice(2)) {
  const args = parseP4aArgs(argv);
  if (args.help) { console.log('node research/p4a-run.mjs --suite all|quick --out research/runs/p4a-full\nPure Node; no browser, rendering, or timing benchmark. Existing output directories must be empty.'); return; }
  const out = args.out ? path.resolve(args.out) : path.join(researchRoot, 'runs', `p4a-${args.suite}-${Date.now()}`);
  await fs.mkdir(out, { recursive: true }); requireTrue((await fs.readdir(out)).length === 0, 'Refusing to overwrite an existing run');
  const definitions = p4aCases(args.suite), metadata = hostMetadata();
  const manifest = { phase: 'P4a', version: 1, suite: args.suite, protocolComplete: args.suite === 'all', exploratory: args.suite !== 'all',
    status: 'running', startedAt: new Date().toISOString(), metadata, sourceHashes: metadata.sourceHashes,
    protocol: P4A, planned: definitions, cases: [], interpretation: P4A.interpretation };
  const manifestPath = path.join(out, 'manifest.json'), records = [];
  const save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2)); await save();
  for (const definition of definitions) {
    const record = runP4aCase(definition), bytes = Buffer.from(JSON.stringify(record)), file = `${definition.id}.json`;
    await fs.writeFile(path.join(out, file), bytes); records.push(record);
    manifest.cases.push({ id: definition.id, path: file, sha256: sha(bytes), bytes: bytes.length, status: record.status,
      summary: record.summary ?? null, error: record.error ?? null }); await save();
    console.log(`[${records.length}/${definitions.length}] ${definition.id}: ${record.status}${record.error ? ` - ${record.error.message}` : ''}`);
  }
  manifest.analysis = analyzeP4a(records, manifest.protocolComplete);
  const after = hostMetadata().sourceHashes, names = [...new Set([...Object.keys(metadata.sourceHashes), ...Object.keys(after)])];
  const changed = names.filter(k => metadata.sourceHashes[k] !== after[k]);
  manifest.sourceHashesAfter = after; manifest.sourceFreeze = { matched: changed.length === 0, fileCount: Object.keys(after).length, changed };
  manifest.finishedAt = new Date().toISOString();
  manifest.status = records.every(r => r.status === 'passed') && manifest.analysis.failures.length === 0 && manifest.sourceFreeze.matched ? 'passed' : 'failed';
  await save(); console.log(JSON.stringify({ out, status: manifest.status, cases: records.length, sourceFreeze: manifest.sourceFreeze,
    referenceStatus: manifest.analysis.referenceStatus }));
  if (manifest.status !== 'passed') process.exitCode = 1;
  return manifest;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await mainP4a();
