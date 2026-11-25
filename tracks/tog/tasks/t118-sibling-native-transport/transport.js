// Runs inside the pinned demo closure and uses the pre-existing native fork and equality checker.
window.__transport = function (cfg, expectedFrames) {
  const dt = cfg.dt, sb = sceneBurnState, parent = __t86.marker();
  const pick = name => cfg.picks.find(p => p.name === name);
  const quota = P.spreadFeedCap;
  const steps = Math.min(90, Math.floor((sb.burning.length - 1 - sb.emitCursor) / quota));
  if (steps !== expectedFrames || sb.burning.length < P.spreadFrontierCap ||
      P.spreadClockMode !== 'elapsed' || P.spreadMeasureMode !== 'legacy' || areaFeedCredit !== 0) {
    throw Error('Unsupported parent or service schedule');
  }
  let minFuel = Infinity;
  for (const id of sb.burning) minFuel = Math.min(minFuel, sb.fuel[id]);
  for (let t=0; t<steps; ++t) minFuel = Math.fround(minFuel - dt / P.spreadBurnT);
  if (minFuel <= 0) throw Error('Retirement before the shared prefix');
  function fork(action) {
    const policy = t86Global, snap = t90Fork();
    try { return action(); } finally { t90Restore(snap); t86Global = policy; }
  }
  const fullIds = fork(() => __t86.ignite(pick('F'), true).ids);
  const parentOrder = sb.burning.slice();
  const samples = [180 + steps, 181 + steps, 224, 270];
  const states = new Map(), stats = [], predictedOnsets = [];
  const footprint = fork(() => {
    const lightIds = __t86.ignite(pick('L'), true).ids;
    const lightSet = new Set(lightIds), fullSet = new Set(fullIds);
    if (!lightIds.every(id => fullSet.has(id))) throw Error('Brushes not nested');
    const extra = fullIds.filter(id => !lightSet.has(id)), extraSet = new Set(extra);
    const prefix = __t86.frames(samples[0], dt);
    const current = sceneBurnState;
    for (const row of prefix) {
      if (row.retired) throw Error('Unexpected retirement');
      predictedOnsets.push(row.new_ids.filter(id => !extraSet.has(id)));
    }
    for (const id of extra) {
      if (sb.state[id] !== 0) throw Error('Extra site was not cold at the parent');
      let heat=sb.h[id], fuel=sb.fuel[id], glow=sb.glow[id], char=sb.char_[id];
      for (let t=0; t<steps; ++t) {
        if (heat>0) heat=Math.fround(heat*(1-dt*0.35));
        fuel=Math.fround(fuel-dt/P.spreadBurnT);
        glow=Math.fround(Math.min(1,glow+dt*3));
        char=Math.fround(Math.min(1,char+dt/(P.spreadBurnT*0.85)));
      }
      if (fuel<=0) throw Error('Newly painted site has retired');
      current.h[id]=heat; current.fuel[id]=fuel; current.glow[id]=glow;
      current.char_[id]=char; current.state[id]=1;
    }
    const tail = current.burning.slice(parentOrder.length + lightIds.length);
    current.burning = parentOrder.concat(fullIds, tail.filter(id => !extraSet.has(id)));
    for (const end of samples) {
      if (end>researchFrame) {
        for (const row of __t86.frames(end,dt)) predictedOnsets.push(row.new_ids);
      }
      states.set(end,t100Physical());
    }
    return {light_sites:lightIds.length,full_sites:fullIds.length,extra_sites:extra.length};
  });
  if (!t100Equal(__t86.marker(),parent)) throw Error('Candidate parent restoration');
  fork(() => {
    const actual = __t86.ignite(pick('F'),true);
    if (!t100Equal(actual.ids,fullIds)) throw Error('Direct-brush order changed');
    for (const end of samples) {
      for (const row of __t86.frames(end,dt)) {
        if (!t100Equal(row.new_ids,predictedOnsets[row.frame-181])) throw Error('Onsets at '+row.frame);
      }
      const native = t100Physical(), candidate = states.get(end);
      for (const field of Object.keys(native)) {
        if (!t100Equal(candidate[field],native[field])) throw Error('Physical mismatch at '+end+' in '+field);
      }
      const mark = __t86.marker();
      stats.push({frame:end,material_bytes:native.material.reduce((n,v)=>n+v.byteLength,0),
        frontier:native.frontier.length,particles:mark.gas_count,draws:mark.random_draws,
        particle_hash:mark.particle_hash,burn_hash:mark.burn_hash,field_count:Object.keys(native).length});
    }
  });
  if (!t100Equal(__t86.marker(),parent) || predictedOnsets.length!==90) throw Error('Native parent restoration');
  return {parent,steps,...footprint,checks:stats,onsets:predictedOnsets};
};
