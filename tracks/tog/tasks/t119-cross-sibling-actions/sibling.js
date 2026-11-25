// Runs inside the pinned T111 native closure. The build imports the T118
// material transport verbatim into t119Materialize(parent, lightIds, fullIds, steps, dt).
function t119Cold(use, audit, action) {
  if (!use) return action();
  const full=t111Full, slice=t111Slice, chronological=t100ReplayActive;
  const stats=t116Begin(audit);
  t111Full=t116Full;t111Slice=t116Slice;t100ReplayActive=t116Chronological;
  try {const r=action();r.cold_lookup=stats;return r;}
  finally {t111Full=full;t111Slice=slice;t100ReplayActive=chronological;t116Session=null;}
}
function t119Result(p,pick,clicked) {
  return {pick,clicked,views:p.views.map(v=>({camera:v.camera,defined:v.total>0,total:v.total,target:v.target,
    eligible:p.ids.length,first_frame:v.first_frame,count:v.first_frame===null?p.count:v.first_count,
    mass:v.first_frame===null?v.mass:v.first_mass,witness:v.witness,curve:v.curve}))};
}
function t119Guard(parent,lightIds,fullIds,dt) {
  const n=parent.burning.length, quota=P.spreadFeedCap;
  if(dt!==1/60 || P.spreadClockMode!=='elapsed' || P.spreadMeasureMode!=='legacy' || areaFeedCredit!==0 ||
     !P.spreadSceneFeed || !Number.isInteger(quota) || quota<=0 || n<P.spreadFrontierCap ||
     parent.emitCursor<0 || !Number.isInteger(parent.emitCursor))return 0;
  const k=Math.min(90,Math.floor((n-1-parent.emitCursor)/quota)),full=new Set(fullIds);
  if(k<1 || !lightIds.every(id=>full.has(id)) ||
     !fullIds.every(id=>!t90Shell.mask[id] && parent.state[id]===0 && parent.fuel[id]>0))return 0;
  let fuel=Infinity;
  for(const id of parent.burning)fuel=Math.min(fuel,parent.fuel[id]);
  for(const id of fullIds)fuel=Math.min(fuel,parent.fuel[id]);
  for(let i=0;i<k;i++)fuel=Math.fround(fuel-dt/P.spreadBurnT);
  return fuel>0?k:0;
}
function t119Run(dt,picks,cameras,audit) {
  const parent=sceneBurnState,start=performance.now(),origin=researchFrame;
  if(origin!==180 || picks[0].name!=='L' || picks[1].name!=='F')throw Error('Unsupported edit');
  let fullIds;
  __t98.resetTrial();
  try {fullIds=__t86.ignite(picks[1],true).ids;}finally{__t98.finishTrial();}
  const work={prepared_full_sites:fullIds.length,prepare_full_ms:performance.now()-start,
    guard_ms:0,fork_at_boundary_ms:0,restore_at_boundary_ms:0,transport_ms:0,light_steps:0,full_steps:0,
    checkpointed:false,checkpoint_material_bytes:0,checkpoint_particles:0,reused_steps:0,active:[],fallback:false};
  const tried=[],choices={},boundaries={};let supported=false,inner=null;
  __t98.resetTrial();
  try {
    const light=__t86.ignite(picks[0],true),lightIds=light.ids;
    __t90.configure({...picks[0],radius:.12});
    const p=t111Progress(cameras,audit),beforeGuard=performance.now();
    const steps=t119Guard(parent,lightIds,fullIds,dt);
    work.steps=steps;work.guard_ms=performance.now()-beforeGuard;
    if(steps>0 && p.total>0) {
      supported=true;
      const end=origin+90,cut=origin+steps,checks=[cut,cut+1,origin+44,end];
      let checkpoint=null,heldViews=null,heldCount=0;
      inner=t90Fork();t102Start('active-anchor',dt);
      const advance=(stop,branch)=>{
        updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);
        t111Full(p,dt,stop);researchFrame++;t111Record(p,researchFrame);work[branch+'_steps']++;
      };
      while(researchFrame<end && (audit || !p.mass)){
        advance(!audit && researchFrame+1>cut,'light');
        if(researchFrame===cut){
          const t=performance.now();checkpoint=t90Fork();
          heldViews=p.views.map(v=>({...v,curve:v.curve.slice()}));heldCount=p.count;
          work.fork_at_boundary_ms=performance.now()-t;work.checkpointed=true;
          work.checkpoint_material_bytes=parent.h.byteLength+parent.fuel.byteLength+
            parent.char_.byteLength+parent.glow.byteLength+parent.state.byteLength;
          work.checkpoint_particles=checkpoint.layers.reduce((s,l)=>s+l.ps.length,0);
        }
      }
      work.active.push(t102Stop());
      const lightResult=t119Result(p,'L',lightIds.length);tried.push(lightResult);
      const pending=new Set();
      for(const v of lightResult.views){
        choices[v.camera]=!v.defined?'undefined':v.first_frame!==null?'L':'none';
        if(v.defined && v.first_frame===null)pending.add(v.camera);
      }
      if(pending.size || audit){
        if(!checkpoint)throw Error('Incomplete light checkpoint');
        const t=performance.now();t90Restore(checkpoint);
        if(t116Session){t116Session.full=null;t116Session.region=null;}
        p.views=heldViews.filter(v=>audit||pending.has(v.camera));p.count=heldCount;
        work.restore_at_boundary_ms=performance.now()-t;
        const m=performance.now();t119Materialize(parent,lightIds,fullIds,steps,dt);
        work.transport_ms=performance.now()-m;work.reused_steps=steps;
        if(audit)boundaries[researchFrame]=t108Fingerprint();
        t102Start('active-anchor',dt);
        while(researchFrame<end && (audit||!p.mass)){
          advance(!audit,'full');
          if(audit && checks.includes(researchFrame))boundaries[researchFrame]=t108Fingerprint();
        }
        work.active.push(t102Stop());
        const result=t119Result(p,'F',fullIds.length);tried.push(result);
        for(const v of result.views)if(pending.has(v.camera))choices[v.camera]=!v.defined?'undefined':v.first_frame!==null?'F':'none';
      }
    }
  } finally {
    if(t102Context)t102Stop();
    if(inner)t90Restore(inner);
    __t98.finishTrial();
  }
  if(!supported){
    if(audit)throw Error('Uncertified sibling during complete-curve audit');
    const baseline=t111Action('ordinary',dt,picks,cameras);work.fallback=true;
    return {...baseline,work,total_browser_ms:performance.now()-start};
  }
  return {tried,choices,work,boundaries,total_browser_ms:performance.now()-start};
}
window.__t119={
  cold(){__t111.cold();t116Geometry=null;},
  action(method,dt,picks,cameras,audit=false){
    const cold=method.startsWith('cold-'),backend=method.replace(/^cold-/,'');
    return t119Cold(cold,audit,()=>backend==='sibling'?t119Run(dt,picks,cameras,audit):t111Action(backend,dt,picks,cameras));
  },
  one(method,dt,pick,cameras,frames){
    const cold=method.startsWith('cold-'),backend=method.replace(/^cold-/,'');
    return t119Cold(cold,true,()=>t111Sibling(backend,dt,pick,cameras,true,frames));
  }
};
