// Consumes a disposable branch. All preceding native frames are the caller's responsibility.
function t93Velocity(layer, pl, i) {
  /* NATIVE_FIELD */
}

function t93TerminalQuery(shellIds, dt, mode) {
  if (P.dimMode !== 'layer' || P.solver !== 'vpm' || P.sliceMode !== 'world' ||
      P.simLayers !== layers.length || dt !== 1/60 || P.sceneScale !== 1 ||
      P.scenePitch !== 0 || P.sceneYaw !== 0 || !P.spreadOn || !P.spreadFlameHeat ||
      P.embers || P.filament || layers.length < 2 || !sceneBurnState ||
      ![...sceneInfo.center,P.sceneOffX,P.sceneOffZ,P.sceneLift].every(v => Number.isFinite(v) && Math.abs(v)<32))
    throw Error('Unsupported T93 configuration');
  const sb = sceneBurnState;
  const eligible = new Uint8Array(sb.state.length);
  const low = [Infinity, Infinity, Infinity], high = [-Infinity, -Infinity, -Infinity];
  let active = 0;
  for (const id of shellIds) {
    if (sb.state[id] !== 0 || sb.fuel[id] <= 0) continue;
    eligible[id] = 1;
    active++;
    const position = sceneGauss[id].p;
    for (let j = 0; j < 3; j++) {
      low[j] = Math.min(low[j], position[j]);
      high[j] = Math.max(high[j], position[j]);
    }
  }
  const counts = {eligible:active, available:0, field_calls:0, uncertain_boundary:0,
    selected_hot:0, spatially_excluded:0, heat_queries:0};
  if (!active) return {decision:'no', witness:null, counts};

  updateCam(cv.width / Math.max(1,cv.height));
  simTime += dt;
  /* NATIVE_SOURCE_ADVANCE */
  const useSim = evenMask(layers.length, P.simLayers);
  vpmPrepare(dt, useSim, true);
  counts.available = layers.reduce((n, layer) => n + layer.ps.length, 0);
  const heatRadius = P.spreadIgnR;
  const move = 4.000002 * dt + 1e-9;  // two binary32 velocity stores after the native norm cap
  const reach = heatRadius + move + 1e-8;
  let sampled = 0;
  for (const layer of layers) {
    // Global hot cap suffices for the selective modes. The ablation pays for every field.
    if (sampled >= P.spreadSampleCap && mode !== 'all') break;
    const pl = vpmPools[layer.idx], particles = layer.ps;
    layer.t += dt;
    if (pl.n !== particles.length) throw Error('T93 Morton pool mismatch');
    const depth = (layer.idx/(layers.length-1)-.5) * P.sliceDepth;
    const offset = worldToSrc(0,0,depth);
    let rank = 0;
    for (let i = 0; i < particles.length; i++) {
      if (sampled >= P.spreadSampleCap && mode !== 'all') break;
      const p = particles[pl.ord[i]];
      let measured = false;
      let x = p.x, y = p.y;
      if (mode === 'all') {
        t93Velocity(layer, pl, i);
        counts.field_calls++;
        measured = true;
        x += dt*pl.UX[i]; y += dt*pl.UY[i];
      }
      const temp = p.T - dt*P.cool*p.T*p.T;
      if (!(temp > .04 && p.d*(1-dt*.3) > .03)) continue;
      // A surviving cold/non-sampled particle still changes the subsequent stride.
      if (p.y-move >= WY || Math.abs(p.x)-move >= WX*.7) continue;
      const uncertain = p.y+move >= WY || Math.abs(p.x)+move >= WX*.7;
      if (uncertain) {
        counts.uncertain_boundary++;
        if (!measured) {
          t93Velocity(layer, pl, i);
          counts.field_calls++;
          measured = true;
          x += dt*pl.UX[i]; y += dt*pl.UY[i];
        }
        if (!(y < WY && Math.abs(x) < WX*.7)) continue;
      }
      if (rank++ % 7 !== 0 || temp < .55 || sampled >= P.spreadSampleCap) continue;
      sampled++;
      counts.selected_hot++;
      // With unit scale and zero rotation, source/world displacement is a translation.
      // Reject only a separated coordinate. Exact sphere distances are tested by hashQuery.
      if (mode === 'spatial' && (p.x+offset[0]+reach < low[0] || p.x+offset[0]-reach > high[0] ||
          p.y+offset[1]+reach < low[1] || p.y+offset[1]-reach > high[1] ||
          offset[2]+heatRadius+1e-8 < low[2] || offset[2]-heatRadius-1e-8 > high[2])) {
        counts.spatially_excluded++;
        continue;
      }
      if (!measured) {
        t93Velocity(layer, pl, i);
        counts.field_calls++;
        x += dt*pl.UX[i]; y += dt*pl.UY[i];
      }
      counts.heat_queries++;
      hashQuery(worldToSrc(x,y,depth), heatRadius, (id,d) => {
        if (eligible[id]) sb.h[id] += dt*P.spreadHeat*temp*(1-d/heatRadius);
      });
    }
  }
  for (const id of shellIds) {
    if (eligible[id] && sb.h[id]>0 && Math.fround(sb.h[id]*(1-dt*.35))>=P.spreadIgnH)
      return {decision:'yes', witness:id, counts};
  }
  return {decision:'no', witness:null, counts};
}

function t93Terminal(shellIds, dt) { return t93TerminalQuery(shellIds, dt, 'spatial'); }
function t93RankTerminal(shellIds, dt) { return t93TerminalQuery(shellIds, dt, 'rank'); }
function t93AllTerminal(shellIds, dt) { return t93TerminalQuery(shellIds, dt, 'all'); }
