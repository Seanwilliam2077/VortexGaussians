// This source is injected in the native closure after T86's unchanged observer.
let t90Query = null;
let t90Shell = null;

function t90Configure(pick) {
  if (P.solver !== 'vpm' || P.dimMode !== 'layer' || P.simLayers !== P.layers ||
      P.interZ !== 0 || P.embers || P.filament || P.emitterOn || P.sliceMode !== 'world' ||
      P.spreadMeasureMode !== 'legacy' || P.sceneScale !== 1 || pointer.active)
    throw Error('Unsupported fork or region controls');
  const mask = new Uint8Array(sceneGauss.length), ids = [];
  for (let i = 0; i < sceneGauss.length; i++) {
    const w = srcToWorld(sceneGauss[i].p);
    const d = Math.hypot(w[0]-pick.world[0], w[1]-pick.world[1], w[2]-pick.world[2]);
    if (d > pick.radius && d <= pick.radius + P.spreadIgnR) { mask[i] = 1; ids.push(i); }
  }
  t90Shell = {mask, ids};
  return ids;
}

function t90Fork() {
  const live = {layers, sceneBurnState, srand, researchFrame, researchRandomDraws,
    vpmTick, areaFeedCredit, source, pointer, simTime, embers, emberAcc, paused:P.paused,
    counters:{...spreadCounters}, regions:[...spreadRegionCounters]};
  // The selected VPM path rebuilds its scratch tree every step and leaves its VIC grids untouched.
  // Preserve the exact original live objects, including the RNG closure. The disposable RNG
  // resumes mulberry32 at the position of its recorded draw count (addition modulo 2^32).
  layers = live.layers.map(l => ({...l, ps:l.ps.map(p => ({...p}))}));
  const sb = live.sceneBurnState;
  sceneBurnState = {...sb, h:sb.h.slice(), fuel:sb.fuel.slice(), glow:sb.glow.slice(),
    char_:sb.char_.slice(), state:sb.state.slice(), burning:sb.burning.slice()};
  source = {...source}; pointer = {...pointer}; embers = embers.map(p=>({...p}));
  spreadRegionCounters.clear();
  for (const [k, c] of live.regions) spreadRegionCounters.set(k, {...c});
  const random = mulberry32((simSeed + Math.imul(researchRandomDraws, 0x6D2B79F5)) >>> 0);
  srand = () => {researchRandomDraws++; return random();};
  P.paused = false;
  return live;
}

function t90Restore(s) {
  layers=s.layers; sceneBurnState=s.sceneBurnState; srand=s.srand; researchFrame=s.researchFrame;
  researchRandomDraws=s.researchRandomDraws; vpmTick=s.vpmTick; areaFeedCredit=s.areaFeedCredit;
  source=s.source; pointer=s.pointer; simTime=s.simTime; embers=s.embers; emberAcc=s.emberAcc;
  P.paused=s.paused; Object.assign(spreadCounters,s.counters); spreadRegionCounters.clear();
  for(const [k,c] of s.regions) spreadRegionCounters.set(k,c);
  t90Query=null;
}

function t90Run(method, horizon, dt) {
  if (!t90Shell || ![1,4,8].includes(horizon) || dt!==1/60) throw Error('Unknown query inputs');
  const begin = performance.now(), startFrame = researchFrame;
  const result = {yes:false, first_frame:null, witness:null, prefix_steps:0, estimated:null,
    fork_ms:0, restore_ms:0, compute_ms:0};
  const resolve = (id,frame) => {result.yes=true;result.witness=id;result.first_frame=frame;};
  if (method === 't91') {
    // Pure causal estimate. A positive first scan is decisive at any horizon.
    const guess=t91Estimate(t90Shell.ids,dt);
    result.estimated=guess.decision;
    if (guess.decision==='yes' || guess.decision==='no' && horizon===1) {
      if (guess.decision==='yes') resolve(guess.witness,startFrame+1);
      result.compute_ms=performance.now()-begin;
      result.browser_ms=performance.now()-begin;
      return result;
    }
  }
  const prep=performance.now(), live=t90Fork(), afterFork=performance.now();
  result.fork_ms=afterFork-prep;
  const mode=method==='t91'?'regional':method;
  try {
    const q=t90Query={mask:t90Shell.mask, ids:t90Shell.ids, witness:-1, full:mode==='full', last:false, regionOnly:false};
    for (let k=1;k<=horizon;k++) {
      result.prefix_steps++;
      q.last=k===horizon; q.regionOnly=q.last && mode==='regional';
      if(q.last && ['t93','all-carriers','rank-only'].includes(mode)) {
        const terminal=mode==='t93' ? t93Terminal : mode==='rank-only' ? t93RankTerminal : t93AllTerminal;
        const answer=terminal(q.ids,dt);
        if(answer.counts) result.terminal_counts=answer.counts;
        if(answer.decision!=='yes' && answer.decision!=='no') throw Error('Expected exact terminal decision');
        if(answer.decision==='yes') resolve(answer.witness,startFrame+k);
        break;
      }
      updateCam(cv.width / Math.max(1, cv.height)); simTime+=dt;
      stepAll(dt); researchFrame++;
      if(q.witness>=0) {resolve(q.witness,researchFrame);break;}
    }
  } finally {
    const beforeRestore=performance.now(); t90Restore(live); const end=performance.now();
    result.restore_ms=end-beforeRestore;
    result.compute_ms=(prep-begin)+(beforeRestore-afterFork);
    result.browser_ms=end-begin;
  }
  return result;
}
window.__t90 = {configure:t90Configure, query:t90Run};
