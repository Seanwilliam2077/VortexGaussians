// Optional registered query implementations share T90's already checked branch isolation.
const t94OriginalQuery=window.__t90.query;
function t94StepFull(dt) {
  updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;
  stepAll(dt);researchFrame++;
}

function t94Query(method,horizon,dt) {
  const sweep=method==='sweep-rank' || method==='sweep-spatial';
  const slice=method==='slice-rank' || method==='slice-regional';
  if(!sweep && !slice) return t94OriginalQuery(method,horizon,dt);
  if(!t90Shell || ![1,4,8].includes(horizon) || dt!==1/60) throw Error('Unsupported T94 query');
  const begin=performance.now(), startFrame=researchFrame, live=t90Fork(), afterFork=performance.now();
  const result={yes:false, first_frame:null,witness:null,prefix_steps:0,estimated:null,
    fork_ms:afterFork-begin,restore_ms:0,compute_ms:0,step_counts:[]};
  try {
    const q=t90Query={ids:t90Shell.ids,mask:t90Shell.mask,full:false,last:false,regionOnly:false,witness:-1};
    const plan=slice?t95Open(q.ids,q.mask,horizon,dt):null;
    if(slice)result.plan_active=plan!==null;
    for(let k=1;k<=horizon;k++) {
      result.prefix_steps++;q.last=k===horizon;
      let witness=null;
      if(sweep) {
        const a=t94Advance(q.ids,dt,method==='sweep-spatial'?'spatial':'rank',q.last,false);
        result.step_counts.push(a.counts);witness=a.witness;researchFrame++;
        if(a.empty)break;
      } else if(!q.last && plan!==null) {
        witness=t95Advance(plan,dt);researchFrame++;
      } else if(q.last && method==='slice-rank') {
        const a=t93RankTerminal(q.ids,dt);
        result.terminal_counts=a.counts;witness=a.witness;researchFrame++;
      } else {
        q.regionOnly=q.last && method==='slice-regional';
        t94StepFull(dt);witness=q.witness<0?null:q.witness;
      }
      if(witness!==null) {result.yes=true;result.witness=witness;result.first_frame=startFrame+k;break;}
    }
  } finally {
    const t=performance.now();t90Restore(live);
    result.compute_ms=t-afterFork;result.restore_ms=performance.now()-t;
    result.browser_ms=performance.now()-begin;
  }
  return result;
}
window.__t90.query=t94Query;

function t94Audit(dt) {
  const table={};
  for(const mode of ['native','rank','spatial']) {
    const states=[],live=t90Fork();
    try {
      for(let i=0;i<8;i++) {
        if(mode==='native')t94StepFull(dt);
        else {t94Advance(t90Shell.ids,dt,mode,false,true);researchFrame++;}
        const m=__t86.marker();
        states.push(m);
      }
    } finally {t90Restore(live);}
    table[mode]=states;
  }
  for(const mode of ['rank','spatial'])
    if(JSON.stringify(table[mode])!==JSON.stringify(table.native))
      throw Error('Resumed '+mode+' state differs from native after cut '+researchFrame+': '+JSON.stringify(table));
  return table.native.map(x=>({frame:x.frame,hash:x.hash,particle:x.particle_hash,burn:x.burn_hash}));
}
window.__t90.audit=dt=>({sweep:t94Audit(dt),slice:typeof t95Audit==='function'?t95Audit(t90Shell.ids,t90Shell.mask,dt):null});
