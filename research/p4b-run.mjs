import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';
import { P4B, p4bCases, p4bConfig, parseP4bArgs } from './p4b-design.mjs';
import { hostMetadata, researchRoot, startServer, launchBrowser, openResearchPage } from './lib/runtime.mjs';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const requireTrue = (value, message) => { if (!value) throw new Error(message); };
const exact = isDeepStrictEqual;
const relative = (error, scale) => Math.abs(error) / Math.max(1, Math.abs(scale));
const FORBIDDEN_COUNTERS = ['nativeHeatApplications', 'nativeDynamicCoolingApplications',
  'nativeVisualCoolingApplications', 'nativeBirths', 'nativeDeaths', 'nativeDensityLossApplications',
  'mortonOutsideBefore', 'mortonOutsideAfter', 'domainZClamps', 'transportDomainExits', 'nativeWouldRetire'];
const FIELD_KEYS = ['UX', 'UY', 'UZ', 'TT', 'DTX', 'DTZ', 'SX', 'SY', 'SZ'];
const RAW_KEYS = ['ux', 'uy', 'uz', 'sx', 'sy', 'sz', 'S', 'sT', 'gx', 'gxx', 'gz', 'gzz', 'DTX', 'DTZ'];

function finite(value, label) { requireTrue(typeof value === 'number' && Number.isFinite(value), `Invalid number: ${label}`); }
function vector(value, label) { requireTrue(Array.isArray(value) && value.length === 3, `Missing vector: ${label}`); value.forEach((v, i) => finite(v, `${label}[${i}]`)); }
function finiteTree(value, label) {
  if (typeof value === 'number') finite(value, label);
  else if (Array.isArray(value)) value.forEach((v, i) => finiteTree(v, `${label}[${i}]`));
  else if (value && typeof value === 'object') for (const [k, v] of Object.entries(value)) finiteTree(v, `${label}.${k}`);
}
function canonicalConfig(config) {
  const out = structuredClone(config), compare = (a, b) => String(a.id) < String(b.id) ? -1 : String(a.id) > String(b.id) ? 1 : 0;
  out.surface.sort(compare); out.gas.sort(compare); return out;
}
const keyed = values => new Map(values.map(p => [String(p.id), p]));
const gasDynamics = values => values.map(({ displayT, ...p }) => p);

export function compareP4bReplay(reference, candidate, fullState = false) {
  requireTrue(reference.raw.length === candidate.raw.length, 'Replay is missing steps');
  let exactDynamics = true, exactNativeFields = true, exactSnapshots = true;
  for (let i = 0; i < reference.raw.length; i++) {
    const a = reference.raw[i], b = candidate.raw[i];
    requireTrue(a.frame === b.frame && a.time === b.time, 'Replay times differ');
    exactDynamics &&= a.dynamicsHash === b.dynamicsHash && exact(gasDynamics(a.gas), gasDynamics(b.gas))
      && exact(a.cloudOrder, b.cloudOrder) && exact(a.rng, b.rng);
    exactNativeFields &&= exact(a.last?.fields ?? null, b.last?.fields ?? null);
    exactSnapshots &&= exact(a, b);
  }
  return { reference: reference.definition.id, candidate: candidate.definition.id,
    states: reference.raw.length, exactDynamics, exactNativeFields, exactSnapshots, fullStateRequired: fullState,
    passed: exactDynamics && exactNativeFields && (!fullState || exactSnapshots) };
}

export function p4bStateDifference(a, b) {
  requireTrue(a.gas.length === b.gas.length && a.gas.length > 0, 'Gas comparison coverage differs');
  const right = keyed(b.gas); requireTrue(right.size === a.gas.length, 'Duplicate gas identities');
  let positionSquared = 0, positionMax = 0, velocitySquared = 0, vorticitySquared = 0;
  for (const p of a.gas) {
    const q = right.get(String(p.id)); requireTrue(q, 'Gas comparison identity missing');
    for (const key of ['position', 'velocity', 'G']) { vector(p[key], key); vector(q[key], key); }
    const p2 = p.position.reduce((s, v, i) => s + (v - q.position[i]) ** 2, 0);
    positionSquared += p2; positionMax = Math.max(positionMax, Math.sqrt(p2));
    velocitySquared += p.velocity.reduce((s, v, i) => s + (v - q.velocity[i]) ** 2, 0);
    vorticitySquared += p.G.reduce((s, v, i) => s + (v - q.G[i]) ** 2, 0);
  }
  const ai = a.thermalState.ids, bi = b.thermalState.ids, bt = new Map(bi.map((id, i) => [String(id), i]));
  requireTrue(ai.length === bi.length && bt.size === ai.length, 'Thermal comparison coverage differs');
  let thermalSquared = 0, capacity = 0, thermalMax = 0;
  for (let i = 0; i < ai.length; i++) {
    const j = bt.get(String(ai[i])); requireTrue(j !== undefined, 'Thermal comparison identity missing');
    const C = a.capacities[i]; finite(C, 'capacity'); requireTrue(C > 0 && C === b.capacities[j], 'Thermal comparison capacity differs');
    const x = a.thermalState.temperatures[i], y = b.thermalState.temperatures[j]; finite(x, 'temperature'); finite(y, 'temperature');
    const e = x - y; thermalSquared += C * e * e; capacity += C; thermalMax = Math.max(thermalMax, Math.abs(e));
  }
  return { gasCount: a.gas.length, thermalNodeCount: ai.length, positionSquared, positionRms: Math.sqrt(positionSquared / a.gas.length),
    positionMax, velocityRms: Math.sqrt(velocitySquared / a.gas.length), vorticityRms: Math.sqrt(vorticitySquared / a.gas.length),
    capacity, capacityWeightedTemperatureSquared: thermalSquared, capacityWeightedTemperatureRmse: Math.sqrt(thermalSquared / capacity), temperatureMax: thermalMax };
}

export function validateP4bRecord(record) {
  const { definition: d, config, raw } = record, canonical = canonicalConfig(config);
  requireTrue(raw.length === d.steps + 1 && raw[0].last === null, 'Missing complete initial-plus-step trajectory');
  requireTrue(record.browserErrors.length === 0, 'Browser reported an exception');
  const first = raw[0], ids = [...canonical.surface, ...canonical.gas].map(p => p.id), gasIds = canonical.gas.map(p => p.id);
  const initialT = ids.map((_, i) => [...canonical.surface, ...canonical.gas][i].temperature);
  const low = Math.min(...initialT), high = Math.max(...initialT), E0 = first.energy.total;
  const capacities = [...canonical.surface.map(p => p.area * p.capacityPerArea), ...canonical.gas.map(p => p.volume * p.capacityPerVolume)];
  let maxRelativeEnergyDrift = 0, maxLedgerResidual = 0, maxTemperatureChange = 0, maxPackedTemperatureDifference = 0, minEdges = Infinity, maxEdges = 0;
  let maxAbsVz = 0, minZ = Infinity, maxZ = -Infinity;
  for (let frame = 0; frame < raw.length; frame++) {
    const s = raw[frame]; finiteTree(s, `raw[${frame}]`);
    requireTrue(s.version === 1 && s.phase === 'P4b' && s.valid && s.invalidReasons.length === 0, 'Runtime invalidated the fixed-parcel experiment');
    requireTrue(s.frame === frame && Math.abs(s.time - frame * d.dt) < 1e-12
      && s.thermalState.steps === frame && s.thermalState.time === s.time, 'Step/time state mismatch');
    requireTrue(exact(canonicalConfig(s.config), canonical) && exact(s.thermalState.ids, ids) && exact(s.capacities, capacities), 'Canonical configuration/thermal identities changed');
    requireTrue(exact(s.gas.map(p => p.id), gasIds) && s.gas.length === canonical.gas.length
      && new Set(s.cloudOrder).size === gasIds.length && gasIds.every(id => s.cloudOrder.includes(id)), 'Fixed parcel identity coverage failed');
    requireTrue(s.rng.draws === 0 && exact(s.rng, first.rng), 'Source RNG must remain unused');
    for (const k of FORBIDDEN_COUNTERS) requireTrue(s.counters[k] === 0, `Forbidden native channel/domain event: ${k}`);
    for (const [k, value] of Object.entries(s.counters)) requireTrue(Number.isSafeInteger(value) && value >= 0, `Invalid counter ${k}`);
    requireTrue(s.counters.flowSteps === (d.transportMode === 'native-vpm3' ? frame : 0)
      && s.counters.staticSteps === (d.transportMode === 'static' ? frame : 0), 'Transport step counters differ');
    requireTrue(s.thermalState.temperatures.length === ids.length, 'Missing Kelvin values');
    let E = 0;
    s.thermalState.temperatures.forEach((T, i) => {
      finite(T, 'Kelvin'); requireTrue(T >= low - P4B.temperatureTolerance && T <= high + P4B.temperatureTolerance, 'Thermal maximum principle violated');
      E += T * capacities[i]; maxTemperatureChange = Math.max(maxTemperatureChange, Math.abs(T - initialT[i]));
    });
    maxRelativeEnergyDrift = Math.max(maxRelativeEnergyDrift, relative(E - E0, E0));
    requireTrue(relative(E - s.energy.total, E0) <= P4B.energyTolerance, 'Reported energy differs from Kelvin/capacity state');
    const ns = canonical.surface.length;
    s.gas.forEach((p, i) => {
      for (const k of ['position', 'velocity', 'G']) vector(p[k], `gas.${k}`);
      for (const k of ['sg', 'life', 'mappedTb', 'displayT', 'density']) finite(p[k], `gas.${k}`);
      const TK = s.thermalState.temperatures[ns + i], dynamicTK = d.thermalFeedback ? TK : canonical.gas[i].temperature;
      requireTrue(p.mappedTb === (dynamicTK - P4B.mapping.ambientK) / P4B.mapping.scaleK, 'Kelvin-to-dynamics mapping differs');
      requireTrue(p.displayT === Math.max(0, Math.min(1.6, (TK - 300) / 300)), 'Display-only temperature mapping differs');
      requireTrue(p.density === 1 && p.sg === canonical.gas[i].sg, 'Fixed display density/kernel changed');
      requireTrue(Math.abs(p.life - (d.transportMode === 'static' ? 0 : s.time)) < 1e-12, 'Transport lifetime mismatch');
      maxAbsVz = Math.max(maxAbsVz, Math.abs(p.velocity[2])); minZ = Math.min(minZ, p.position[2]); maxZ = Math.max(maxZ, p.position[2]);
    });
    if (!frame) { requireTrue(exact(s.thermalState.temperatures, initialT), 'Initial Kelvin differs from authored input'); continue; }
    const previous = raw[frame - 1], last = s.last;
    requireTrue(last && last.frame === frame && last.dt === d.dt && last.fieldTime === previous.time
      && last.fieldTemperatureTime === s.time && s.fieldTemperatureTime === s.time
      && last.forcingTime === s.time && s.fieldTime === previous.time && s.forcingTime === s.time, 'Missing/wrong split-phase times');
    requireTrue(exact(last.before.thermalState, previous.thermalState) && exact(last.before.gas, previous.gas), 'Step did not begin from prior full state');
    requireTrue(exact(last.afterThermal.thermalState, last.afterFlow.thermalState)
      && exact(last.afterFlow.thermalState, s.thermalState) && exact(last.afterFlow.gas, s.gas), 'Flow altered Kelvin or saved final state differs');
    requireTrue(exact(s.graph, last.graph) && exact(s.graph.ids, ids) && exact(s.graph.capacities, capacities), 'Thermal graph identities/capacity changed');
    const expectedPositions = [...canonical.surface.map(p => p.position), ...last.before.gas.map(p => p.position)];
    requireTrue(exact(s.graph.positions, expectedPositions), 'Heat graph did not use actual pre-integration positions');
    minEdges = Math.min(minEdges, s.graph.edges.length); maxEdges = Math.max(maxEdges, s.graph.edges.length);
    const l = last.thermalLedger;
    requireTrue(l.enabled === d.exchange && l.dt === d.dt && l.safety === P4B.thermal.safety, 'Thermal ledger mode/time differs');
    const expectedSubsteps = d.exchange ? Math.max(1, Math.ceil(d.dt * s.graph.maxRate / P4B.thermal.safety)) : 0;
    requireTrue(l.substeps === expectedSubsteps && l.edgeEvaluations === l.substeps * s.graph.edges.length
      && l.maxCfl <= P4B.thermal.safety + 1e-12, 'Thermal substeps/workload/CFL differ');
    for (const e of [l.netSurface + l.netGas, l.energyChangeSurface - l.netSurface, l.energyChangeGas - l.netGas,
      l.energyResidual, l.Ebefore.total - previous.energy.total, l.Eafter.total - s.energy.total]) maxLedgerResidual = Math.max(maxLedgerResidual, relative(e, E0));
    if (!d.exchange) requireTrue(exact(s.thermalState.temperatures, first.thermalState.temperatures), 'Disabled exchange changed Kelvin');
    for (const [k, value] of Object.entries(last.counters)) requireTrue(s.counters[k] === previous.counters[k] + value, `Cumulative counter mismatch ${k}`);
    requireTrue(last.counters.thermalSubsteps === l.substeps && last.counters.thermalEdgeEvaluations === l.edgeEvaluations, 'Thermal workload counter mismatch');
    requireTrue(last.fields.length === (d.transportMode === 'native-vpm3' ? gasIds.length : 0), 'Incomplete native fields');
    const beforeById = keyed(last.afterThermal.gas);
    requireTrue(new Set(last.fields.map(p => String(p.id))).size === last.fields.length, 'Duplicate native field IDs');
    last.fields.forEach((f, sortedIndex) => {
      requireTrue(f.sortedIndex === sortedIndex, 'Native sorted field order mismatch');
      const p = beforeById.get(String(f.id)); requireTrue(p, 'Native field identity missing');
      vector(f.packed.position, 'packed.position'); vector(f.packed.G, 'packed.G');
      requireTrue(exact(f.packed.position, p.position.map(Math.fround)) && exact(f.packed.G, p.G.map(Math.fround))
        && f.packed.sg === Math.fround(p.sg) && f.packed.Tb === Math.fround(p.mappedTb), 'Actual packed Float32 state mismatch');
      maxPackedTemperatureDifference = Math.max(maxPackedTemperatureDifference, Math.abs(f.packed.Tb - p.mappedTb));
      for (const k of RAW_KEYS) finite(f.raw[k], `raw.${k}`);
      for (const k of FIELD_KEYS) { finite(f.field[k], `field.${k}`); requireTrue(f.field[k] === Math.fround(f.field[k]), 'Native field is not recorded as actual Float32'); }
    });
  }
  requireTrue(maxRelativeEnergyDrift <= P4B.energyTolerance && maxLedgerResidual <= P4B.energyTolerance, 'Closed sensible heat/ledger drift');
  requireTrue(record.observations.length === (d.observe ? d.steps : 0), 'Incomplete observer history');
  for (let i = 0; i < record.observations.length; i++) {
    const observation = record.observations[i], s = raw[i + 1];
    const saved = { dynamicsHash: s.dynamicsHash, thermalStateHash: s.thermalStateHash, fullStateHash: s.fullStateHash };
    requireTrue(observation.frame === i + 1 && observation.exactSnapshots && exact(observation.before, observation.after)
      && exact(observation.before, saved) && observation.camera.dynamicsHash === s.dynamicsHash, 'Observation changed future simulation state');
  }
  return { states: raw.length, gasCount: gasIds.length, surfaceCount: canonical.surface.length,
    maxRelativeEnergyDrift, maxLedgerResidual, maxTemperatureChange, maxPackedTemperatureDifference,
    minEdges, maxEdges, maxAbsVz, observedZSpan: maxZ - minZ, finalCounters: raw.at(-1).counters,
    interpretation: 'Finite sensible heat invariant only; native force/damping model is not a total energy-conserving fluid.' };
}

export function singleP4bAnalytic(record) {
  const d = record.definition, c = record.config;
  requireTrue(d.fixture.kind === 'single' && record.raw.length === 2, 'One-step analytic fixture required');
  const s = c.surface[0], g = c.gas[0], Cs = s.area * s.capacityPerArea, Cg = g.volume * g.capacityPerVolume;
  const r = Math.hypot(...s.position.map((v, i) => v - g.position[i]));
  const G = c.thermal.beta * s.area * g.volume * 3 / (Math.PI * c.thermal.h ** 3) * Math.max(0, 1 - r / c.thermal.h);
  const substeps = Math.max(1, Math.ceil(d.dt * Math.max(G / Cs, G / Cg) / c.thermal.safety));
  let Ts = s.temperature, Tg = g.temperature;
  for (let i = 0; i < substeps; i++) { const Q = d.dt / substeps * G * (Tg - Ts); Ts += Q / Cs; Tg -= Q / Cg; }
  const mappedTb = (Tg - 300) / 300, packedTb = Math.fround(mappedTb), velocity = [0, c.transport.params.buoy * packedTb, 0];
  const position = g.position.map((v, i) => v + d.dt * velocity[i]), actual = record.raw[1];
  const temperatureMaxError = Math.max(...actual.thermalState.temperatures.map((T, i) => Math.abs(T - [Ts, Tg][i])));
  const velocityMaxError = Math.max(...actual.gas[0].velocity.map((v, i) => Math.abs(v - velocity[i])));
  const positionMaxError = Math.max(...actual.gas[0].position.map((v, i) => Math.abs(v - position[i])));
  return { G, substeps, temperatures: [Ts, Tg], mappedTb, packedTb, velocity, position,
    temperatureMaxError, velocityMaxError, positionMaxError,
    passed: temperatureMaxError <= P4B.temperatureTolerance && velocityMaxError <= 1e-12 && positionMaxError <= 1e-12,
    interpretation: 'One-step frozen-graph Euler/substep algebra plus native Float32 mapping and zero-vorticity buoyancy; not a continuous-time heat solution.' };
}

export function analyzeP4b(records, complete) {
  const byId = new Map(records.map(r => [r.definition.id, r])), replays = [], failures = [];
  const get = id => { const r = byId.get(id); requireTrue(r?.status === 'passed', `Missing/failed case ${id}`); return r; };
  const pairs = [
    ['main-no-exchange-no-feedback', 'main-no-exchange-feedback', false],
    ['main-no-exchange-no-feedback', 'main-exchange-no-feedback', false],
    ['main-coupled-dt60', 'main-coupled-observed', true],
    ['main-coupled-dt60', 'main-coupled-reordered', true],
    ['uniform-no-exchange', 'uniform-exchange', false]
  ];
  for (const [a, b, full] of pairs) {
    if (!complete && !byId.has(a) && !byId.has(b)) continue;
    try { const v = compareP4bReplay(get(a), get(b), full); replays.push(v); if (!v.passed) failures.push(`${a} / ${b} replay changed`); }
    catch (e) { failures.push(e.message); }
  }
  let analytic = null, feedbackExposure = null, geometryExposure = null;
  try { analytic = singleP4bAnalytic(get('single-step-analytic')); if (!analytic.passed) failures.push('Single-step interface algebra failed'); } catch (e) { failures.push(e.message); }
  try {
    const passive = get('main-exchange-no-feedback'), coupled = get('main-coupled-dt60'), fixed = get('main-static-exchange');
    feedbackExposure = { reference: passive.definition.id, candidate: coupled.definition.id, ...p4bStateDifference(coupled.raw.at(-1), passive.raw.at(-1)),
      criterion: 'final matched-gas 3D position RMS', threshold: P4B.feedbackPositionRmsExposure, requiredForProtocol: complete };
    feedbackExposure.passed = feedbackExposure.positionRms > feedbackExposure.threshold;
    geometryExposure = { reference: fixed.definition.id, candidate: passive.definition.id, ...p4bStateDifference(passive.raw.at(-1), fixed.raw.at(-1)),
      criterion: 'final all-node capacity-weighted Kelvin RMSE', threshold: P4B.movingGeometryTemperatureRmseExposure, requiredForProtocol: complete };
    geometryExposure.passed = geometryExposure.capacityWeightedTemperatureRmse > geometryExposure.threshold;
    if (complete && (!feedbackExposure.passed || !geometryExposure.passed)) failures.push('A preregistered causal interface was not exposed');
  } catch (e) { failures.push(e.message); }
  const temporalRefinement = [];
  if (complete) {
    for (const id of ['main-coupled-dt60', 'main-coupled-dt120']) {
      try {
        const coarse = get(id), fine = get('main-coupled-dt240'), ratio = Math.round(coarse.definition.dt / fine.definition.dt);
        requireTrue(ratio * fine.definition.dt === coarse.definition.dt, 'Nonmatching refinement schedule');
        const matched = coarse.raw.map((s, i) => ({ frame: s.frame, time: s.time, fineFrame: i * ratio, ...p4bStateDifference(s, fine.raw[i * ratio]) }));
        temporalRefinement.push({ candidate: id, reference: fine.definition.id, matched, final: matched.at(-1),
          interpretation: 'Time-resolution sensitivity against the finest recorded trajectory, not a true solution or hard monotonic-convergence gate.' });
      } catch (e) { failures.push(e.message); }
    }
  }
  return { replays, analytic, feedbackExposure, geometryExposure, temporalRefinement, failures,
    referenceStatus: 'pending-independent-audit',
    independentReferenceRequired: 'Rebuild each graph from actual x^n; independently integrate thermal substeps, reproduce Kelvin/Float32 mapping, and check the declared native force and Euler integration using saved raw/F32 fields. This does not independently reimplement every tree-field query.' };
}

export async function runP4bCase(browser, url, definition) {
  const config = p4bConfig(definition), record = { definition, config, status: 'running', raw: [], observations: [], browserErrors: [] };
  let opened;
  try {
    opened = await openResearchPage(browser, url); record.graphics = opened.graphics;
    const { page, errors } = opened;
    await page.waitForFunction(() => window.__demo?.researchP4?.reset);
    record.raw.push(await page.evaluate(async config => await window.__demo.researchP4.reset(config), config));
    for (let frame = 1; frame <= definition.steps; frame++) {
      record.raw.push(await page.evaluate(dt => window.__demo.researchP4.step(1, dt), definition.dt));
      if (definition.observe) {
        record.observations.push(await page.evaluate(frame => {
          const api = window.__demo.researchP4, before = api.snapshot({ detail: true });
          const yaw = .7 * Math.sin(frame * .17), camera = api.camera(yaw), after = api.snapshot({ detail: true });
          const hashes = s => ({ dynamicsHash: s.dynamicsHash, thermalStateHash: s.thermalStateHash, fullStateHash: s.fullStateHash });
          return { frame, yaw, camera, before: hashes(before), after: hashes(after), exactSnapshots: JSON.stringify(before) === JSON.stringify(after) };
        }, frame));
      }
    }
    record.browserErrors = [...errors]; record.summary = validateP4bRecord(record); record.status = 'passed';
  } catch (error) {
    record.status = 'failed'; record.error = { name: error.name, message: error.message, stack: error.stack };
    if (opened) record.browserErrors = [...opened.errors];
  } finally { if (opened) await opened.page.close(); }
  return record;
}

export async function mainP4b(argv = process.argv.slice(2)) {
  const args = parseP4bArgs(argv);
  if (args.help) { console.log('node research/p4b-run.mjs --suite all|quick --out research/runs/p4b-full [--browser-executable PATH]\nPlaywright browser interface test; every detailed step is retained. No render/performance benchmark. Existing results are never overwritten.'); return; }
  const out = args.out ? path.resolve(args.out) : path.join(researchRoot, 'runs', `p4b-${args.suite}-${Date.now()}`);
  await fs.mkdir(out, { recursive: true }); requireTrue((await fs.readdir(out)).length === 0, 'Refusing to overwrite an existing run');
  const metadata = hostMetadata(), definitions = p4bCases(args.suite);
  const requestedCompleteProtocol = args.suite === 'all';
  const manifest = { phase: 'P4b', version: 1, suite: args.suite, requestedCompleteProtocol, protocolComplete: false, exploratory: args.suite !== 'all',
    status: 'running', startedAt: new Date().toISOString(), args, metadata, sourceHashes: metadata.sourceHashes, protocol: P4B, planned: definitions,
    cases: [], interpretation: P4B.interpretation };
  const manifestPath = path.join(out, 'manifest.json'), save = () => fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  await save(); let server, launched; const records = [];
  try {
    server = await startServer(); launched = await launchBrowser(args.browserExecutable);
    manifest.browser = { version: launched.browser.version(), module: launched.module, launchOptions: launched.launchOptions }; await save();
    for (const definition of definitions) {
      const record = await runP4bCase(launched.browser, server.url, definition), bytes = Buffer.from(JSON.stringify(record)), file = `${definition.id}.json`;
      await fs.writeFile(path.join(out, file), bytes); records.push(record);
      manifest.cases.push({ id: definition.id, path: file, sha256: sha(bytes), bytes: bytes.length,
        status: record.status, summary: record.summary ?? null, error: record.error ?? null }); await save();
      console.log(`[${records.length}/${definitions.length}] ${definition.id}: ${record.status}${record.error ? ` - ${record.error.message}` : ''}`);
    }
    manifest.analysis = analyzeP4b(records, requestedCompleteProtocol);
  } catch (error) { manifest.executionError = { name: error.name, message: error.message, stack: error.stack }; }
  finally { if (launched) await launched.browser.close(); if (server) await server.close(); }
  const after = hostMetadata().sourceHashes, names = [...new Set([...Object.keys(metadata.sourceHashes), ...Object.keys(after)])];
  const changed = names.filter(k => metadata.sourceHashes[k] !== after[k]); manifest.sourceHashesAfter = after;
  manifest.sourceFreeze = { matched: changed.length === 0, fileCount: Object.keys(after).length, changed };
  manifest.protocolComplete = requestedCompleteProtocol && records.length === definitions.length
    && records.every((r, i) => r.definition.id === definitions[i].id && r.raw.length === definitions[i].steps + 1
      && r.raw.every((s, step) => s.frame === step));
  manifest.finishedAt = new Date().toISOString();
  manifest.status = !manifest.executionError && records.length === definitions.length && records.every(r => r.status === 'passed')
    && manifest.analysis.failures.length === 0 && manifest.sourceFreeze.matched ? 'passed' : 'failed';
  await save(); console.log(JSON.stringify({ out, status: manifest.status, cases: records.length, sourceFreeze: manifest.sourceFreeze,
    referenceStatus: manifest.analysis?.referenceStatus ?? null }));
  if (manifest.status !== 'passed') process.exitCode = 1;
  return manifest;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await mainP4b();
