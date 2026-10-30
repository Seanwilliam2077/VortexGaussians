/* Inserted inside the original demo IIFE. No simulation occurs at installation.
 * The one private load handshake starts the ordinary page flow. There is no
 * window bridge, public prepare/step/reset/restore function or message driver.
 */
(() => {
  'use strict';
  const N = 7500, COUNT = 15000, SEED = 20261031;
  const fields = ['h', 'fuel', 'glow', 'char_', 'state'];
  const require = (ok, message) => { if (!ok) throw Error('A48: ' + message); };
  const same = (a, b) => {
    if (Object.is(a, b)) return true;
    if (!a || !b || typeof a !== 'object' || typeof b !== 'object') return false;
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every(k => Object.hasOwn(b, k) && same(a[k], b[k]));
  };
  // Explicit typed-array/Map representations keep all values in JSON evidence.
  const pack = value => {
    if (ArrayBuffer.isView(value)) return { type: value.constructor.name, values: Array.from(value) };
    if (value instanceof Map) return { type: 'Map', entries: [...value].map(([k, v]) => [pack(k), pack(v)]) };
    if (Array.isArray(value)) return value.map(pack);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, pack(v)]));
    return value;
  };
  const overrides = {
    solver: 'vpm', dimMode: 'layer', layers: 1, simLayers: 1, ppl: 1,
    paused: true, orbit: false, yaw: 0, camElev: 0, camDist: 3.4, fov: .85, sliceMode: 'world',
    sceneOn: true, sceneMax: 16000, sceneScale: 1, sceneYaw: 0, scenePitch: 0,
    sceneLift: 0, sceneOffX: 0, sceneOffZ: 0, sceneSH: 0, box: false,
    spreadOn: true, spreadClockMode: 'elapsed', spreadMeasureMode: 'legacy', spreadParticlePolicy: 'block',
    spreadBurnT: 6, spreadRate: 0, spreadFlameHeat: false, spreadSceneFeed: false,
    emitterOn: false, embers: false
  };
  const expectedP = { ...RESEARCH_DEFAULTS, ...overrides };
  const report = { version: 1, calls: { setScene: 0, reset: 0, ignite: 0, stepAPI: 0, steps: 0, restore: 0 },
    seed: SEED, dt: 1 / 60, geometry: null, physicalStates: {}, stages: {},
    ignition: null, preparation: null, exchange: null, pngChecks: [], errors: [], timings: {},
    sourceLoop: 'Normal embed has an idle RAF: early return, no automatic step or render.' };
  let hooks, connected = false, geometryRefs, initialArrays, preparedArrays;
  const arrays = () => Object.fromEntries(fields.map(k => [k, Array.from(sceneBurnState[k])]));
  const allCounters = () => ({ counters: pack(spreadCounters), groups: pack(spreadRegionCounters), areaFeedCredit });
  const geometry = () => ({ authored: pack(researchScenePoints), gaussians: pack(sceneGauss),
    sceneInfo: pack(sceneInfo), hashGrid: pack(sceneHash) });
  const physics = () => pack({ frame: researchFrame, time: simTime, seed: simSeed, randomDraws: researchRandomDraws,
    vpmTick, orbitPhase, layers, embers, emberAcc, source, pointer, cloud, cloudAcc, cloudAcc3, vol_t,
    vic3, coarse, vpmPools, vpmInvTheta, vpmDir, vpmDirAcc, vpmDirAcc2, vpmDirN, vpmDirL, vpmDirOut,
    researchP3State, researchP4State, camera: cam });
  const roots = () => ({ srand, layers, embers, cloud, source, pointer, coarse, vic3,
    vpmPools, vpmDir, vpmDirAcc, vpmDirAcc2, vpmDirOut, cam, P,
    sceneGauss, researchScenePoints, sceneInfo, sceneHash, sceneBurnState, spreadCounters, spreadRegionCounters });
  // Save object links, not a second per-point audit log. Scalars are checked separately.
  function referenceGuard(selected = roots()) {
    const nodes = [], seen = new Set();
    function visit(v) {
      if (!v || typeof v !== 'object' || seen.has(v)) return;
      seen.add(v);
      if (ArrayBuffer.isView(v)) { nodes.push({ v, buffer: v.buffer, length: v.length, type: v.constructor }); return; }
      const entries = v instanceof Map ? [...v] : Object.entries(v);
      nodes.push({ v, entries, map: v instanceof Map });
      for (const [, child] of entries) visit(child);
    }
    Object.values(selected).forEach(visit);
    return current => {
      for (const k of Object.keys(selected)) require(current[k] === selected[k], 'root object/reference changed: ' + k);
      for (const node of nodes) {
        if (node.buffer) {
          require(node.v.buffer === node.buffer && node.v.length === node.length && node.v.constructor === node.type, 'typed array identity changed');
          continue;
        }
        const now = node.map ? [...node.v] : Object.entries(node.v);
        require(now.length === node.entries.length, 'object shape changed');
        now.forEach(([key, value], i) => {
          const [oldKey, oldValue] = node.entries[i];
          require(Object.is(key, oldKey), 'object keys or Map order changed');
          if (oldValue && (typeof oldValue === 'object' || typeof oldValue === 'function'))
            require(value === oldValue, 'nested object reference changed');
        });
      }
    };
  }
  function frontier() {
    const sb = sceneBurnState, seen = new Set();
    for (const i of sb.burning) {
      require(Number.isInteger(i) && i >= 0 && i < COUNT && !seen.has(i), 'invalid or duplicate frontier index');
      require(sb.state[i] === 1, 'frontier contains a non-burning point'); seen.add(i);
    }
    for (let i = 0; i < COUNT; i++) require((sb.state[i] === 1) === seen.has(i), 'state/frontier membership differs');
    return { indices: sb.burning.slice(), ids: sb.burning.map(i => researchScenePoints[i].id), emitCursor: sb.emitCursor };
  }
  function fixedGeometry() {
    require(same(geometry(), report.geometry.value), 'complete geometry/metadata/hash grid changed');
    geometryRefs({ sceneGauss, researchScenePoints, sceneInfo, sceneHash });
    require(same(P, expectedP), 'complete P differs from locked defaults plus overrides');
  }
  function saveStage(name) {
    fixedGeometry();
    const physical = physics();
    let physicalRef = Object.keys(report.physicalStates).find(k => same(report.physicalStates[k], physical));
    if (!physicalRef) { physicalRef = 'physical-' + Object.keys(report.physicalStates).length; report.physicalStates[physicalRef] = physical; }
    const evidence = { name, geometryRef: 'geometry-0', geometryEqual: true, physicalRef,
      material: researchAPI.snapshot({ detail: true }), arrays: arrays(), frontier: frontier(), ...allCounters() };
    report.stages[name] = evidence; hooks.publish(report); return evidence;
  }
  function active() { require(hooks.active(), 'page left or stopped'); }
  async function imageStage(name) {
    active();
    const stage = saveStage(name), refs = referenceGuard(), before = physics(), counters = allCounters();
    const started = performance.now();
    await hooks.capture(name, stage.arrays.char_);
    active(); fixedGeometry(); refs(roots());
    require(same(stage.arrays, arrays()) && same(stage.frontier, frontier()), 'material changed during PNG work');
    require(same(before, physics()) && same(counters, allCounters()), 'physical state/counters changed during PNG work');
    require(same(stage.material, researchAPI.snapshot({ detail: true })), 'raw snapshot changed during PNG work');
    report.pngChecks.push({ stage: name, unchanged: true, elapsedMs: performance.now() - started });
    hooks.publish(report);
  }
  function makePoints() {
    const points = [], a = 12 * Math.PI / 180, c = Math.cos(a), s = Math.sin(a);
    for (const group of ['F', 'B']) for (let j = 0; j < 100; j++) for (let i = 0; i < 75; i++) {
      const u = 2 + 4 * i, v = 2 + 4 * j;
      const X = group === 'F' ? 280 + u : 300 + c * (u - 150) + s * (v - 200);
      const Y = group === 'F' ? 80 + v : 390 - s * (u - 150) + c * (v - 200);
      points.push({ id: `${group}:${i}:${j}`, group, position: [(X - 360) / 100, (360 - Y) / 100, group === 'F' ? .5 : -.5],
        fuel: 1, opacity: 1, scale: .02, color: [228 / 255, 221 / 255, 204 / 255], areaWeight: .0016 });
    }
    return points;
  }
  function compareUnhit(initial, after, hits) {
    for (let i = 0; i < COUNT; i++) if (!hits.has(i))
      for (const key of fields) require(Object.is(initial[key][i], after[key][i]), 'unhit material changed: ' + i + '/' + key);
  }
  function noParticles() {
    require(layers.length === 1 && layers.every(L => L.ps.length === 0) && embers.length === 0 && cloud.length === 0 && vic3 === null,
      'unexpected particles/embers/cloud/3D state');
  }
  function fail(error) {
    if (!hooks.active()) return; // Leaving freezes the already published evidence.
    try {
      report.failure = { material: researchAPI.snapshot({ detail: true }), arrays: sceneBurnState ? arrays() : null,
        frontier: sceneBurnState ? { indices: sceneBurnState.burning.slice(), emitCursor: sceneBurnState.emitCursor } : null,
        physical: physics(), ...allCounters(), geometryRef: report.geometry ? 'geometry-0' : null };
      const actualGeometry = geometry();
      if (!report.geometry || !same(actualGeometry, report.geometry.value)) report.failure.actualGeometry = actualGeometry;
    } catch (captureError) { report.failureCaptureError = String(captureError.message || captureError); }
    report.errors.push(String(error.message || error)); hooks.publish(report);
    hooks.fail(error);
  }
  async function restore() {
    if (!hooks.active() || report.calls.restore !== 0) return;
    report.calls.restore++; hooks.phase('restoring'); hooks.disableRestore();
    const started = performance.now();
    report.exchange = { status: 'checking', passed: false, pairs: N, fields: fields.slice(), assertions: {} };
    try {
      active(); fixedGeometry(); noParticles();
      require(researchFrame === 360 && simSeed === SEED && Math.abs(simTime - 6) < 1e-8, 'wrong exchange frame/time/seed');
      require(same(preparedArrays, arrays()), 'material changed while awaiting the action');
      const before = arrays(), beforeFrontier = frontier(), beforePhysics = physics(), beforeCounters = allCounters();
      const refs = referenceGuard(), sb = sceneBurnState;
      // Only these assignments change material. No original API call occurs here.
      for (let i = 0; i < N; i++) for (const key of fields) {
        const value = sb[key][i]; sb[key][i] = sb[key][i + N]; sb[key][i + N] = value;
      }
      for (let k = 0; k < sb.burning.length; k++) {
        const i = sb.burning[k]; sb.burning[k] = i < N ? i + N : i - N;
      }
      for (let i = 0; i < N; i++) for (const key of fields)
        require(Object.is(sb[key][i], before[key][i + N]) && Object.is(sb[key][i + N], before[key][i]), 'pair tuple mismatch');
      const afterFrontier = frontier();
      require(same(afterFrontier.indices, beforeFrontier.indices.map(i => i < N ? i + N : i - N)), 'frontier order mapping differs');
      require(Object.is(afterFrontier.emitCursor, beforeFrontier.emitCursor), 'emitCursor changed');
      refs(roots()); fixedGeometry(); noParticles();
      require(same(beforePhysics, physics()), 'non-material physical values changed');
      require(same(beforeCounters, allCounters()), 'complete historical counters or area credit changed');
      report.exchange.assertions = { exactAllPairs: true, typedArraysAndAllObjectLinksPreserved: true,
        geometryMetadataAndParamsPreserved: true, frontierOrderMapped: true, cursorLiterallyPreserved: true,
        physicalValuesAndRngClosurePreserved: true, completeCountersAndMapPreserved: true,
        zeroResetIgniteSteps: report.calls.reset === 1 && report.calls.ignite === 1 && report.calls.stepAPI === 1 && report.calls.steps === 360 };
      require(report.exchange.assertions.zeroResetIgniteSteps, 'operation budget differs');
      report.exchange.status = 'passed'; report.exchange.passed = true;
      report.exchange.elapsedMs = performance.now() - started;
      await imageStage('swapped'); active(); hooks.phase('ended');
    } catch (error) { if (hooks.active()) { report.exchange.status = 'failed'; fail(error); } }
  }
  async function run() {
    const start = performance.now();
    try {
      active(); hooks.phase('preparing');
      const t0 = performance.now(), points = makePoints();
      require(points.length === COUNT, 'wrong scene size');
      report.calls.setScene++; researchAPI.setScene(points);
      report.calls.reset++; researchAPI.reset(SEED, overrides);
      require(same(P, expectedP), 'initial complete parameters differ');
      require(researchFrame === 0 && simTime === 0 && researchRandomDraws === 0, 'reset baseline differs');
      noParticles();
      report.geometry = { id: 'geometry-0', value: geometry(), pairing: { offset: N, order: 'F row-major, then B row-major', columns: 75, rows: 100 },
        canvas: { width: 720, height: 720, background: '#1D2320', paper: '#E4DDCC', line: '#4C514B',
          lineCenters: [34, 162, 234], lineWidth: 2, lineV: [20, 380], F: [430, 280, 0], B: [300, 390, -12],
          cellSize: 4, localSize: [300, 400], alpha: '1-clamp(char_,0,1), once per combined paper/line pixel' } };
      geometryRefs = referenceGuard({ sceneGauss, researchScenePoints, sceneInfo, sceneHash });
      initialArrays = arrays();
      for (let i = 0; i < COUNT; i++) for (const k of fields)
        require(initialArrays[k][i] === (k === 'fuel' ? 1 : 0), 'initial material not pristine');
      report.timings.sceneAndResetMs = performance.now() - t0;
      await imageStage('initial'); active();

      const expected = new Set();
      points.forEach((p, i) => {
        const [x, y, z] = p.position;
        if ((x + .72) ** 2 + (y - .30) ** 2 + (z - .5) ** 2 <= .36 ** 2) expected.add(i);
      });
      require(expected.size > 0 && [...expected].every(i => i < N), 'invalid planned hit set');
      const ti = performance.now(); report.calls.ignite++;
      const lit = window.__demo.ignite(-.72, .30, .5, .36), afterIgnite = arrays();
      const actual = new Set(afterIgnite.state.flatMap((state, i) => state === 1 ? [i] : []));
      require(lit === expected.size && actual.size === expected.size && [...expected].every(i => actual.has(i)), 'actual hit set differs');
      compareUnhit(initialArrays, afterIgnite, expected);
      for (const i of actual) for (const k of fields)
        require(afterIgnite[k][i] === (k === 'state' ? 1 : initialArrays[k][i]), 'ignite changed an unexpected material field');
      report.ignition = { center: [-.72, .30, .5], radius: .36, localCenter: [8, 250], localRadius: 36,
        expectedIndices: [...expected], actualIndices: [...actual], actualIds: [...actual].map(i => points[i].id), returnedLit: lit,
        exactMatch: true, elapsedMs: performance.now() - ti };
      saveStage('ignited'); active();
      const ts = performance.now(); report.calls.stepAPI++; report.stepRequested = 360;
      try { researchAPI.step(360, 1 / 60); }
      finally { report.calls.steps = researchFrame; report.timings.stepAPIMs = performance.now() - ts; }
      require(researchFrame === 360 && Math.abs(simTime - 6) < 1e-8, 'preparation did not end at frame 360');
      preparedArrays = arrays(); compareUnhit(initialArrays, preparedArrays, expected); noParticles();
      const changed = [], boundary = [];
      for (let i = 0; i < COUNT; i++) if (!Object.is(preparedArrays.char_[i], initialArrays.char_[i])) {
        require(i < N && expected.has(i), 'char changed outside the fixed F hit set');
        const col = i % 75, row = Math.floor(i / 75), u = col * 4, v = row * 4;
        require(u >= 0 && u + 4 <= 96 && v >= 205 && v + 4 <= 295, 'changed cell footprint outside W');
        require(Number.isFinite(preparedArrays.char_[i]) && preparedArrays.char_[i] > 0 && preparedArrays.char_[i] <= 1, 'invalid char');
        changed.push(i); if (col === 0) boundary.push(i);
      }
      require(changed.length > 0 && boundary.length > 0, 'no material loss touching the left edge');
      report.preparation = { passed: true, changedCharIndices: changed, boundaryIndices: boundary,
        BAndUnhitFPristine: true, withinWindow: true, particlesAbsent: true,
        floatFuelStateGlowRetained: true, elapsedMs: performance.now() - start };
      await imageStage('prepared'); active();
      report.timings.readyMs = performance.now() - start;
      hooks.bindRestore(restore); hooks.phase('prepared'); hooks.publish(report);
    } catch (error) { fail(error); }
  }
  window.addEventListener('load', () => {
    // A transient, single-use capability handed to this work's module, not an inspection API.
    parent.dispatchEvent(new parent.CustomEvent('a48-source-connect', { detail: { sourceWindow: window,
      connect(callbacks) {
        require(!connected, 'source connection is single-use'); connected = true; hooks = callbacks; void run();
      } } }));
  }, { once: true });
})();
