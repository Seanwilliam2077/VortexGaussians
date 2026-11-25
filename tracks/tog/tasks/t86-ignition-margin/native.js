// T86 observation inside the native demo closure. Only the T81 admission
// predicate changes after the second zero-time stroke. No rendering or RNG
// occurs in this observer. The native physics timer excludes label scans.
let t86Global = false;
window.__t86 = {
  ignite(pick, second) {
    if (researchFrame !== (second ? 180 : 0)) throw Error('Invalid stroke frame');
    t86Global = second;
    const sb = sceneBurnState;
    const previous = sb.burning.length;
    const count = igniteAt(...pick.world, pick.radius);
    const ids = sb.burning.slice(previous);
    if (ids.length !== count) throw Error('Lost native stroke IDs');
    return {name: pick.name, frame: researchFrame, count, ids};
  },
  frames(end, dt) {
    if (end > 360 || end <= researchFrame || end > 180 && !t86Global || dt !== 1/60)
      throw Error('Invalid native frame range');
    researchParams({}, P, true);
    const rows = [];
    const paused = P.paused;
    P.paused = false;
    try {
      while (researchFrame < end) {
        const sb = sceneBurnState;
        const start = performance.now();
        const old = sb.state.slice();
        const stepStart = performance.now();
        updateCam(cv.width / Math.max(1, cv.height));
        simTime += dt;
        stepAll(dt);
        researchFrame++;
        const done = performance.now();
        const new_ids = [];
        let retired = 0, active_count = 0;
        for (let i = 0; i < sb.state.length; i++) {
          const state = sb.state[i];
          if (old[i] === 0 && state !== 0) new_ids.push(i);
          if (old[i] === 1 && state === 2) retired++;
          if (state === 1) active_count++;
        }
        if (active_count !== sb.burning.length) throw Error('Native frontier count mismatch');
        rows.push({frame: researchFrame, new_ids, retired, active_count,
          gas_count: layers.reduce((n,L) => n + L.ps.length, 0), random_draws: researchRandomDraws,
          step_ms: done-stepStart, observer_ms: stepStart-start+performance.now()-done});
      }
    } finally {
      P.paused = paused;
    }
    return rows;
  },
  marker() {
    const s = researchSnapshot();
    return {frame: s.frame, hash: s.hash, particle_hash: s.particleStateHash,
      burn_hash: s.scene.burnHash, burning: s.scene.burning, charred: s.scene.charred,
      gas_count: s.particles.count, cursor: sceneBurnState.emitCursor, random_draws: s.randomDraws};
  },
  cut(arm, dt) {
    const s = researchSnapshot(), sb = sceneBurnState;
    return {schema: 't86-native-cut-v1', arm, frame: s.frame, time: s.time, dt,
      policy: t86Global ? 'global' : 'per-layer', params: s.params,
      scene_center: sceneInfo.center.slice(), seed: simSeed,
      heat: Array.from(sb.h), fuel: Array.from(sb.fuel), state: Array.from(sb.state),
      frontier: sb.burning.slice(), emit_cursor: sb.emitCursor,
      gas: layers.map(L => ({idx:L.idx, seed:L.seed, t:L.t, acc:L.acc,
        particles: L.ps.map(p => ({...p}))})), native_hash:s.hash,
      particle_hash:s.particleStateHash, random_draws:s.randomDraws, counters:s.counters};
  }
};
