// T81 observation-side state. No particle/native state fields are added.
let t81Policy='per-layer',t81Enabled=false,t81Ids=new WeakMap(),t81NextId=0;
let t81FixedB=new Set(),t81NewB=new Set(),t81Offers=[],t81Current=null,t81HookMs=0;
let t81Cumulative={offers:0,blocked:0,randomRejected:0,emitted:0,blockedWithGlobalFree:0,nativeAttrition:0};
function t81CapacityFull(L,i,k){
  const begin=performance.now(),localFull=L.ps.length>=P.ppl;
  const total=layers.reduce((n,a)=>n+a.ps.length,0),full=t81Policy==='global'?total>=P.layers*P.ppl:localFull;
  if(!t81Enabled)throw Error('T81 observation must begin before stepping');
  t81Current={source:i,layer:k,localCount:L.ps.length,globalCount:total,localFull,full,
    fixedB:t81FixedB.has(i),newB:t81NewB.has(i),particleId:null};
  t81HookMs+=performance.now()-begin;
  return full;
}
function t81Admitted(p,i,k){
  const begin=performance.now();
  if(!t81Current||t81Current.source!==i||t81Current.layer!==k)throw Error('T81 offer mismatch');
  const id=++t81NextId;
  t81Ids.set(p,{id,emissionSource:i,emissionLayer:k,birthFrame:researchFrame+1,
    sourceInFixedB:t81FixedB.has(i),sourceNewlyIgnitedByB:t81NewB.has(i)});
  t81Current.particleId=id;t81HookMs+=performance.now()-begin;
}
function t81OfferEnd(){
  const begin=performance.now(),o=t81Current;
  if(!o)throw Error('T81 missing offer');
  const outcome=o.full?'blocked':o.particleId===null?'randomRejected':'emitted';
  t81Offers.push([o.source,o.layer,o.localCount,o.globalCount,+o.localFull,+o.full,
    outcome,o.particleId,+o.fixedB,+o.newB]);
  t81Cumulative.offers++;t81Cumulative[outcome]++;
  if(outcome==='blocked'&&o.globalCount<P.layers*P.ppl)t81Cumulative.blockedWithGlobalFree++;
  t81Current=null;t81HookMs+=performance.now()-begin;
}
function t81Particles(){return layers.flatMap(L=>L.ps.map(p=>({layer:L.idx,p,meta:t81Ids.get(p)})));}
function t81Finite(value,path='state'){
  if(typeof value==='number'&&!Number.isFinite(value))throw Error('Non-finite '+path);
  if(value&&typeof value==='object')for(const [k,v] of Object.entries(value))t81Finite(v,path+'.'+k);
}
function t81Export(){
  const s=__t42.state();
  const gas=layers.map(L=>({idx:L.idx,seed:L.seed,t:L.t,acc:L.acc,
    particles:L.ps.map(p=>{const meta=t81Ids.get(p);if(!meta)throw Error('Unattributed native particle');return {observation:meta,native:{...p}};})}));
  const value={schema:'t81-full-native-observation-v1',native:s,gas,policy:t81Policy,
    fixedBIndices:[...t81FixedB].sort((a,b)=>a-b),newlyBIndices:[...t81NewB].sort((a,b)=>a-b),
    observationCounters:{...t81Cumulative},nativeAuxiliary:{simSeed,simTime,researchFrame,researchRandomDraws,
      vpmTick,embers:JSON.parse(JSON.stringify(embers)),emberAcc,source:{...source},pointer:{...pointer}},
    attribution:'Emission source only; no unique ancestry is inferred for threshold-heated descendants.',
    checkpoint_scope:'Full recorded gas objects and material snapshot; renderer scratch buffers/RNG closure are not a restart API.'};
  t81Finite(value);return value;
}
window.__t81={
  begin({fixedBIndices}){
    if(researchFrame!==0||layers.some(L=>L.ps.length))throw Error('T81 begin needs zero-frame empty-gas reset');
    if(P.layers!==9||P.ppl!==600||P.spreadParticlePolicy!=='block'||P.spreadMeasureMode!=='legacy'||P.emitterOn||P.embers||P.filament)
      throw Error('T81 unsupported frozen recipe');
    t81Policy='per-layer';t81Enabled=true;t81Ids=new WeakMap();t81NextId=0;
    t81FixedB=new Set(fixedBIndices);t81NewB=new Set();t81Current=null;t81Offers=[];t81HookMs=0;
    t81Cumulative={offers:0,blocked:0,randomRejected:0,emitted:0,blockedWithGlobalFree:0,nativeAttrition:0};
    return {fixedBCount:t81FixedB.size,policy:t81Policy};
  },
  setPolicy(policy){
    if(researchFrame!==180||!['per-layer','global'].includes(policy))throw Error('T81 policy only at frame180');
    t81Policy=policy;return policy;
  },
  igniteB(pick,apply){
    if(researchFrame!==180)throw Error('T81 B operation only at frame180');
    const old=Array.from(sceneBurnState.state),lit=apply?igniteAt(...pick.world,pick.radius):0;
    const indices=[];for(let i=0;i<old.length;i++)if(old[i]!==1&&sceneBurnState.state[i]===1)indices.push(i);
    if(indices.length!==lit||indices.some(i=>!t81FixedB.has(i)))throw Error('T81 newly-B identity mismatch');
    t81NewB=new Set(indices);return {applied:apply,lit,indices};
  },
  frame(dt,capture=false){
    if(!t81Enabled||researchFrame>=360||dt!==1/60)throw Error('T81 step budget/recipe');
    const allStart=performance.now();researchParams({},P,true);
    const before=t81Particles(),beforeIds=new Set(before.map(x=>{if(!x.meta)throw Error('Missing particle ID');return x.meta.id;}));
    t81Offers=[];t81HookMs=0;const oldCounters={...spreadCounters},oldDraws=researchRandomDraws;
    const obsBeforeMs=performance.now()-allStart,paused=P.paused;P.paused=false;
    const stepStart=performance.now();
    try{updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;stepAll(dt);researchFrame++;}
    finally{P.paused=paused;}
    const stepMs=performance.now()-stepStart,renderStart=performance.now();render();gl.finish();
    const renderMs=performance.now()-renderStart,obsStart=performance.now();
    const after=t81Particles(),afterIds=new Set(after.map(x=>{if(!x.meta)throw Error('Unknown source particle');return x.meta.id;}));
    const removed=[...beforeIds].filter(id=>!afterIds.has(id));
    t81Cumulative.nativeAttrition+=removed.length;
    const emitted=spreadCounters.sceneSeedsEmitted-oldCounters.sceneSeedsEmitted;
    if(before.length+emitted-removed.length!==after.length)throw Error('T81 gas balance');
    if(t81Offers.length!==spreadCounters.sceneFeedAttempts-oldCounters.sceneFeedAttempts)throw Error('T81 source offer count');
    if(after.length>5400||(t81Policy==='per-layer'&&layers.some(L=>L.ps.length>600)))throw Error('T81 capacity exceeded');
    for(const [key,nativeKey] of [['emitted','sceneSeedsEmitted'],['blocked','sceneFeedCapacityBlocked'],['randomRejected','sceneFeedRandomRejected']])
      if(t81Offers.filter(o=>o[6]===key).length!==spreadCounters[nativeKey]-oldCounters[nativeKey])throw Error('T81 outcome mismatch '+key);
    if(t81Cumulative.nativeAttrition!==t81Cumulative.emitted-after.length)throw Error('T81 cumulative attrition balance');
    // Return GL diagnostics with the completed row/capture before the worker
    // qualifies them; otherwise a boundary failure would discard its evidence.
    const error=gl.getError(),lost=gl.isContextLost();
    const record={frame:researchFrame,time:simTime,policy:t81Policy,layerCounts:layers.map(L=>L.ps.length),
      counters:{...spreadCounters},observationCounters:{...t81Cumulative},randomDraws:researchRandomDraws,
      randomDrawsThisStep:researchRandomDraws-oldDraws,offers:t81Offers,nativeRemovedIds:removed,
      timing:{step_including_hooks_ms:stepMs,observation_hooks_inside_step_ms:t81HookMs,
        render_and_gpu_finish_ms:renderMs,step_plus_render_ms:stepMs+renderMs,observation_before_step_ms:obsBeforeMs},
      glError:error,contextLost:lost};
    t81Finite(record);for(const x of after)t81Finite(x.p,'gas');
    record.timing.observation_after_render_ms=performance.now()-obsStart;
    record.timing.frame_wrapper_ms=performance.now()-allStart;
    if(capture){
      const exportStart=performance.now();const png=cv.toDataURL('image/png');
      const pixels=new Uint8Array(cv.width*cv.height*4);gl.bindFramebuffer(gl.FRAMEBUFFER,null);
      gl.readPixels(0,0,cv.width,cv.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      let binary='';for(let i=0;i<pixels.length;i+=32768)binary+=String.fromCharCode(...pixels.subarray(i,i+32768));
      const state=t81Export();record.capture={state,png,rgbaBase64:btoa(binary),
        export_ms:performance.now()-exportStart,pixel_format:'RGBA8 bottom-left origin'};
    }
    return record;
  },
  export:t81Export,
  offerColumns:['sourceIndex','targetLayer','localCountBefore','globalCountBefore','localFull','policyFull','outcome','emittedParticleId','sourceInFixedB','sourceNewlyIgnitedByB']
};
