/* A42 local-build bridge. Inserted inside the original IIFE, before __demo.
 * This file only installs closures. It does not initialize, step, render or reset.
 * The parent calls handover once, synchronously, after the normal iframe load.
 */
(() => {
  'use strict';
  const copy = value => JSON.parse(JSON.stringify(value));
  const same = (a, b) => {
    if (typeof a !== typeof b) return false;
    if (a === null || b === null || typeof a !== 'object') return Object.is(a, b);
    if (Array.isArray(a) !== Array.isArray(b)) return false;
    const ka = Object.keys(a), kb = Object.keys(b);
    return ka.length === kb.length && ka.every(k => Object.hasOwn(b, k) && same(a[k], b[k]));
  };
  const require = (condition, message) => { if (!condition) throw new Error('A42 bridge: ' + message); };
  const freeze = value => {
    if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
    return value;
  };
  const valuesAt = i => ({ h: sceneBurnState.h[i], fuel: sceneBurnState.fuel[i],
    glow: sceneBurnState.glow[i], char_: sceneBurnState.char_[i], state: sceneBurnState.state[i] });
  const allRegions = () => [...spreadRegionCounters.entries()].map(([group, counters]) => ({ group, counters: copy(counters) }));
  const frontierIds = () => sceneBurnState.burning.map(i => {
    require(Number.isInteger(i) && i >= 0 && i < researchScenePoints.length, 'frontier index outside scene');
    return researchScenePoints[i].id;
  });
  let attempted = false, report = null;

  function inspect() {
    const material = researchAPI.snapshot({ detail: true });
    const authored = researchScenePoints ? copy(researchScenePoints) : [];
    const materialValues = sceneBurnState ? authored.map((p, i) => ({ id: p.id, group: p.group, ...valuesAt(i) })) : [];
    return freeze({ material, evidence: {
      authoredPoints: authored,
      metadataHash: researchHash(authored),
      completeGeometryHash: researchHash(sceneGauss),
      materialValuesHash: researchHash(materialValues),
      apologyMetadataHash: researchHash(authored.filter(p => p.group === 'apology')),
      apologyMaterialHash: researchHash(materialValues.filter(p => p.group === 'apology')),
      frontierIds: sceneBurnState ? frontierIds() : [],
      emitCursor: sceneBurnState ? sceneBurnState.emitCursor : 0,
      areaFeedCredit, vpmTick,
      random: { seed: simSeed, draws: researchRandomDraws,
        preservationMethod: 'same srand closure identity and unchanged draw count; no probing draw' },
      countersAllGroups: allRegions(),
      handoverAttempted: attempted,
      handoverReport: report ? copy(report) : null
    } });
  }

  function handover(nextPoints) {
    require(!attempted, 'handover is single-use');
    attempted = true;
    report = { version: 1, status: 'checking', passed: false, errors: [],
      permittedChange: 'remove release, add initially unburned request, retain apology',
      pointChecks: [], assertions: {}, removedReleaseIds: [], removedFrontierIds: [],
      retainedFrontierIdsBefore: [], frontierIdsAfter: [] };
    try {
      require(researchFrame === 180 && simSeed === 20261031, 'requires fixed seed and frame 180');
      require(Math.abs(simTime - 3) < 1e-8, 'requires first three simulated seconds');
      const expectedParams = { ...RESEARCH_DEFAULTS, solver: 'vpm', dimMode: 'layer',
        layers: 9, simLayers: 9, ppl: 160, paused: true, orbit: false,
        yaw: 0, camElev: 0, camDist: 3.4, fov: .85, sliceMode: 'world',
        emitterOn: false, spreadOn: true, spreadFlameHeat: true, spreadSceneFeed: true,
        spreadClockMode: 'elapsed', spreadParticlePolicy: 'block', spreadMeasureMode: 'legacy',
        spreadFrontierCap: 1400, spreadSampleCap: 160, spreadFeedCap: 48,
        sceneOn: true, sceneMax: 16000, sceneScale: 1, sceneSH: 0,
        sceneYaw: 0, scenePitch: 0, sceneLift: 0, sceneOffX: 0, sceneOffZ: 0, box: false };
      require(same(P, expectedParams), 'complete parameters differ from fixed A39 inheritance');
      require(areaFeedCredit === 0, 'legacy areaFeedCredit must be zero');
      require(Array.isArray(researchScenePoints) && sceneBurnState, 'authored scene and burn state required');
      require(Array.isArray(nextPoints) && nextPoints.length <= 16000, 'invalid next scene');
      require(sceneGauss.length === researchScenePoints.length, 'metadata and geometry count mismatch');

      const oldById = new Map(), nextById = new Map();
      researchScenePoints.forEach((p, i) => {
        require(!oldById.has(p.id), 'duplicate current id');
        require(['apology', 'release'].includes(p.group), 'unexpected current group');
        oldById.set(p.id, { index: i, metadata: copy(p), geometry: copy(sceneGauss[i]), values: valuesAt(i) });
      });
      nextPoints.forEach(p => {
        require(p && typeof p.id === 'string' && !nextById.has(p.id), 'duplicate or invalid next id');
        require(['apology', 'request'].includes(p.group), 'unexpected next group');
        // The complete normalized schema is explicit; extra/missing fields are rejected.
        require(same(Object.keys(p).sort(), ['id', 'group', 'position', 'fuel', 'opacity', 'scale', 'color', 'areaWeight'].sort()),
          'next metadata schema differs');
        nextById.set(p.id, p);
      });
      const oldApology = researchScenePoints.filter(p => p.group === 'apology');
      const oldRelease = researchScenePoints.filter(p => p.group === 'release');
      const nextApology = nextPoints.filter(p => p.group === 'apology');
      const nextRequest = nextPoints.filter(p => p.group === 'request');
      require(oldApology.length > 0 && oldRelease.length > 0 && nextRequest.length > 0, 'empty required group');
      require(same(oldApology, nextApology), 'apology metadata/order differs before handover');
      for (const p of nextRequest) require(!oldById.has(p.id) && p.fuel === 1, 'request must be new with fuel 1');
      for (const p of oldRelease) require(!nextById.has(p.id), 'release id retained');
      require(nextById.size === oldApology.length + nextRequest.length, 'scene change exceeds group replacement');
      const beforeFrontier = frontierIds();
      require(new Set(beforeFrontier).size === beforeFrontier.length, 'duplicate current frontier id');
      for (const id of beforeFrontier) require(oldById.get(id).values.state === 1, 'frontier contains a non-burning point');
      const retainedFrontier = beforeFrontier.filter(id => oldById.get(id).metadata.group === 'apology');
      const removedFrontier = beforeFrontier.filter(id => oldById.get(id).metadata.group === 'release');
      const oldBurn = sceneBurnState;
      const beforeMaterial = researchAPI.snapshot({ detail: true });
      const before = { frame: researchFrame, time: simTime, seed: simSeed, vpmTick, vol_t,
        randomDraws: researchRandomDraws, counters: copy(spreadCounters), countersAllGroups: allRegions(),
        params: copy(P), areaFeedCredit, emitCursor: oldBurn.emitCursor,
        particleStateHash: beforeMaterial.particleStateHash,
        particles: copy(beforeMaterial.particles), hash: beforeMaterial.hash };
      const refs = { srand, layers, layerParticles: layers.map(L => L.ps),
        particles: layers.map(L => L.ps.slice()), embers, cloud, source, pointer };
      report.before = copy(before);
      report.removedReleaseIds = oldRelease.map(p => p.id);
      report.addedRequestIds = nextRequest.map(p => p.id);
      report.frontierIdsBefore = beforeFrontier;
      report.removedFrontierIds = removedFrontier;
      report.retainedFrontierIdsBefore = retainedFrontier;

      // The only scene construction. No reset, step, ignite, render, await or RNG draw.
      researchAPI.setScene(nextPoints);
      const afterIndex = new Map(researchScenePoints.map((p, i) => [p.id, i]));
      for (const p of oldApology) {
        const previous = oldById.get(p.id), i = afterIndex.get(p.id);
        require(i !== undefined, 'apology id lost during setScene');
        for (const key of ['h', 'fuel', 'glow', 'char_', 'state']) sceneBurnState[key][i] = previous.values[key];
      }
      sceneBurnState.burning = retainedFrontier.map(id => afterIndex.get(id));
      // Preserve the number literally, even if it exceeds the filtered frontier length.
      sceneBurnState.emitCursor = before.emitCursor;

      for (const p of oldApology) {
        const old = oldById.get(p.id), i = afterIndex.get(p.id);
        const current = { metadata: copy(researchScenePoints[i]), geometry: copy(sceneGauss[i]), values: valuesAt(i) };
        const check = { id: p.id, metadataBefore: old.metadata, metadataAfter: current.metadata,
          geometryBefore: old.geometry, geometryAfter: current.geometry,
          materialBefore: old.values, materialAfter: current.values,
          metadataEqual: same(old.metadata, current.metadata), geometryEqual: same(old.geometry, current.geometry),
          valuesEqual: same(old.values, current.values) };
        report.pointChecks.push(check);
        require(check.metadataEqual && check.geometryEqual && check.valuesEqual, 'apology point changed: ' + p.id);
      }
      for (const p of researchScenePoints.filter(p => p.group === 'request')) {
        const i = afterIndex.get(p.id);
        require(same(p, nextById.get(p.id)), 'request metadata changed');
        require(same(valuesAt(i), { h: 0, fuel: 1, glow: 0, char_: 0, state: 0 }), 'request is not pristine');
      }
      const afterMaterial = researchAPI.snapshot({ detail: true });
      const after = { frame: researchFrame, time: simTime, seed: simSeed, vpmTick, vol_t,
        randomDraws: researchRandomDraws, counters: copy(spreadCounters), countersAllGroups: allRegions(),
        params: copy(P), areaFeedCredit, emitCursor: sceneBurnState.emitCursor,
        particleStateHash: afterMaterial.particleStateHash,
        particles: copy(afterMaterial.particles), hash: afterMaterial.hash };
      report.after = copy(after);
      report.frontierIdsAfter = frontierIds();
      report.assertions = {
        allApologyMetadataAndGeometryEqual: report.pointChecks.every(p => p.metadataEqual && p.geometryEqual),
        allApologyMaterialsEqual: report.pointChecks.every(p => p.valuesEqual),
        apologyCountEqual: report.pointChecks.length === oldApology.length,
        requestPristine: nextRequest.every(p => same(valuesAt(afterIndex.get(p.id)), { h: 0, fuel: 1, glow: 0, char_: 0, state: 0 })),
        onlyReleaseRemovedAndRequestAdded: same(researchScenePoints, nextPoints),
        retainedFrontierOrderEqual: same(retainedFrontier, report.frontierIdsAfter),
        emitCursorEqual: same(before.emitCursor, after.emitCursor),
        timeFrameSeedTickEqual: ['frame', 'time', 'seed', 'vpmTick', 'vol_t'].every(k => same(before[k], after[k])),
        rngClosureIdentityEqual: refs.srand === srand,
        randomDrawsEqual: before.randomDraws === after.randomDraws,
        particleStateHashEqual: before.particleStateHash === after.particleStateHash,
        particleSummaryEqual: same(before.particles, after.particles),
        particleObjectIdentityEqual: refs.layers === layers && refs.embers === embers && refs.cloud === cloud
          && refs.source === source && refs.pointer === pointer && layers.every((L, k) =>
            refs.layerParticles[k] === L.ps && refs.particles[k].length === L.ps.length
            && L.ps.every((p, j) => p === refs.particles[k][j])),
        countersEqual: same(before.counters, after.counters),
        allRegionCountersEqual: same(before.countersAllGroups, after.countersAllGroups),
        allParamsEqual: same(before.params, after.params),
        legacyAreaFeedCreditZero: before.areaFeedCredit === 0 && after.areaFeedCredit === 0,
        zeroSteps: before.frame === after.frame
      };
      for (const [name, ok] of Object.entries(report.assertions)) require(ok, name);
      report.apologyPointCount = oldApology.length;
      report.requestPointCount = nextRequest.length;
      report.passed = true; report.status = 'passed';
      return freeze(copy(report));
    } catch (error) {
      report.status = 'failed'; report.errors.push(String(error.message || error));
      // A failed assertion is terminal; no rollback, retry or weaker reconstruction.
      throw error;
    }
  }
  Object.defineProperty(window, '__a42LocalBridge', {
    value: Object.freeze({ inspect, handover }), writable: false, configurable: false
  });
})();
