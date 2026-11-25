let t103Pending=null;

function t103Gas(dt) {
  updateCam(cv.width/Math.max(1,cv.height));
  simTime+=dt;t95FullGas(dt);
}

function t103WholeStep(dt) {
  t90Query=null;t103Gas(dt);t102Spread(dt);researchFrame++;
}

function t103Repair(s,dt) {
  if(!s.block)return;
  const start=performance.now();
  const {full,logs,partial}=s.block;
  sceneBurnState=full;
  for(const log of logs){
    // A positive sliced scan stopped before feed. Its log still contains every
    // gas sample. Replay the full material scan, then perform its one live feed.
    if(log===partial)log.cursor=full.emitCursor;
    t100ReplayActive(log,dt);
    if(log===partial)t103Feed(full,dt);
    s.stats.repaired_steps++;
  }
  s.stats.repair_ms+=performance.now()-start;
  s.block=null;
}

function t103Begin(backend,h,dt,pick) {
  if(t103Pending || !['ordinary','slice'].includes(backend) || h!==60 || dt!==1/60)throw Error('Invalid preview request');
  const start=performance.now(),edit=__t86.ignite(pick,true);
  __t90.configure(pick);
  const origin=researchFrame,live=t90Fork();
  const q=t90Query={ids:t90Shell.ids,mask:t90Shell.mask,witness:-1,regionOnly:false,full:false,last:false};
  const stats={ordinary_steps:0,sliced_steps:0,guards:[],repaired_steps:0,repair_ms:0,
    allocated_log_bytes:0,peak_block_log_bytes:0,peak_held_heat_bytes:0,logged_samples:0,terminal:false};
  const s={backend,origin,live,stats,block:null,ordinaryStop:null,terminal:false,witness:null,dt};
  t103Pending=s;
  t102Start('active-anchor',dt);
  while(researchFrame<origin+h){
    const remain=origin+h-researchFrame;
    if(remain===1){
      s.witness=t93RankTerminal(q.ids,dt).witness;
      s.terminal=true;stats.terminal=true;
      break;
    }
    const plan=backend==='slice'?t100Plan(q.ids,q.mask,remain-1,dt):null;
    if(backend==='slice')stats.guards.push(plan?.remaining??0);
    if(!plan){
      q.witness=-1;
      t103Gas(dt);t102Spread(dt);researchFrame++;stats.ordinary_steps++;
      if(q.witness>=0){s.witness=q.witness;s.ordinaryStop=q.witness;break;}
      continue;
    }
    const count=plan.remaining,b={full:sceneBurnState,logs:[],partial:null};
    s.block=b;
    sceneBurnState={...b.full,h:b.full.h.slice()};
    stats.peak_held_heat_bytes=Math.max(stats.peak_held_heat_bytes,sceneBurnState.h.byteLength);
    for(let k=0;k<count;k++){
      const log=t100FrameLog();b.logs.push(log);
      stats.allocated_log_bytes+=log.values.byteLength;stats.peak_block_log_bytes=Math.max(stats.peak_block_log_bytes,b.logs.length*log.values.byteLength);
      const hit=t100Advance(plan,dt,log);researchFrame++;stats.sliced_steps++;stats.logged_samples+=log.count;
      if(hit!==null){s.witness=hit;b.partial=log;break;}
    }
    if(s.witness!==null)break;
    // The terminal rank evaluator only depends on current gas and eligible shell
    // heat/fuel. A nonexpired slice stays pending until the action arrives.
    if(count<remain-1)t103Repair(s,dt);
  }
  const first=s.witness===null?null:researchFrame+(s.terminal?1:0);
  s.decisionFrame=first??origin+h;
  return {yes:s.witness!==null,first_frame:first,witness:s.witness,clicked:edit.count,
    preview_ms:performance.now()-start,decision_frame:s.decisionFrame};
}

function t103Physical() {
  return {...t100Physical(),areaFeedCredit};
}

function t103Resolve(keep,audit=null) {
  const s=t103Pending;
  if(!s)throw Error('Missing unresolved preview');
  const {dt,stats}=s,start=performance.now();
  let crossing=null,next=null;
  if(keep){
    t103Repair(s,dt);
    if(s.terminal)t103WholeStep(dt);
    if(s.ordinaryStop!==null)t103FinishScan(sceneBurnState,dt,s.ordinaryStop+1);
    t90Query=null;
    if(researchFrame!==s.decisionFrame)throw Error('Incomplete crossing step');
    if(audit){
      if(!t100Equal(t103Physical(),audit.cross))throw Error('Full crossing state diverged');
      crossing=__t86.marker().hash;
    }
    const t=performance.now();
    t103WholeStep(dt);stats.following_step_ms=performance.now()-t;
    if(audit){
      if(!t100Equal(t103Physical(),audit.next))throw Error('Native subsequent state diverged');
      next=__t86.marker().hash;
    }
  }
  const committed=keep?researchFrame:null, active=t102Stop();
  if(!keep)t90Restore(s.live);
  t103Pending=null;
  return {keep,committed_frame:committed,decision_frame:s.decisionFrame,action_ms:performance.now()-start,
    active_stats:active,work:stats,crossing,next};
}

function t103Audit(pick,dt,frame){
  let reference;
  __t98.resetTrial();
  try {
    __t86.ignite(pick,true);t90Query=null;
    while(researchFrame<frame)t94StepFull(dt);
    const cross=t103Physical(),crossHash=__t86.marker().hash;
    t94StepFull(dt);
    reference={cross,next:t103Physical(),crossHash,nextHash:__t86.marker().hash};
  } finally {__t98.finishTrial();}
  const rows=[];
  for(const backend of ['ordinary','slice']){
    __t98.resetTrial();
    try {
      const preview=t103Begin(backend,60,dt,pick);
      if(preview.decision_frame!==frame)throw Error('Unexpected committed frame');
      const r=t103Resolve(true,reference);
      rows.push({backend,decision_frame:frame,commit_frame:r.committed_frame,cross_hash:r.crossing,next_hash:r.next,
        compared_material_sites:reference.cross.material[0].length,
        compared_gas_particles_at_cross:reference.cross.gas.reduce((n,l)=>n+l[4].length,0)});
    } finally {__t98.finishTrial();}
  }
  return {reference_cross_hash:reference.crossHash,reference_next_hash:reference.nextHash,rows};
}

window.__t103={begin:t103Begin,resolve:t103Resolve,audit:t103Audit};
