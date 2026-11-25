function t100Plan(ids,mask,maximum,dt) {
  const sb=sceneBurnState,n=sb.burning.length,cap=P.spreadFeedCap;
  if(maximum<=0 || !cap || n<P.spreadFrontierCap || n<cap) return null;
  const limit=Math.min(maximum,Math.floor((n-1-sb.emitCursor)/cap));
  if(limit<=0) return null;
  let fuel=Infinity;
  for(const i of sb.burning)fuel=Math.min(fuel,sb.fuel[i]);
  let length=0;
  while(length<limit) {
    fuel=Math.fround(fuel-dt/P.spreadBurnT);
    if(fuel<=0)break;
    length++;
  }
  if(length===0)return null;
  // Its existing admission checks and state/clock constraints still apply.
  return t95Open(ids,mask,length+1,dt);
}

function t100FrameLog() {return {values:new Float64Array(4*P.spreadSampleCap),count:0,cursor:-1};}

function t100FullStep(q,dt) {
  q.full=false;q.last=false;q.regionOnly=false;q.witness=-1;
  updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;
  t95FullGas(dt);t97Spread(dt);researchFrame++;
  return q.witness<0?null:q.witness;
}

const t100Ordinary=window.__t90.query;
function t100Query(method,h,dt) {
  if(!['repair-cache','restart-cache'].includes(method))return t100Ordinary(method,h,dt);
  const start=performance.now(),origin=researchFrame;
  const live=t90Fork(),afterFork=performance.now();
  const stats={guards:[],ordinary_steps:0,sliced_steps:0,logged_samples:0,allocated_log_bytes:0,
    max_live_log_bytes:0,repairs:0,repair_steps:0,restart:false,repair_ms:0,guard_ms:0};
  let witness=null,first=null,restart=false,beforeRestore,totalForward=0;
  try {
    t97Use('asset-cache');
    const q=t90Query={mask:t90Shell.mask,ids:t90Shell.ids,witness:-1,full:false,last:false,regionOnly:false};
    while(researchFrame<origin+h) {
      const remain=origin+h-researchFrame;
      if(remain===1) {
        const terminal=t93RankTerminal(q.ids,dt);
        witness=terminal.witness;researchFrame++;
        break;
      }
      const t=performance.now(),plan=t100Plan(q.ids,q.mask,remain-1,dt);
      stats.guard_ms+=performance.now()-t;
      const len=plan?.remaining || 0;
      stats.guards.push({frame:researchFrame,length:len});
      if(!len) {
        if(method==='restart-cache'){restart=true;break;}
        witness=t100FullStep(q,dt);stats.ordinary_steps++;
        if(witness!==null)break;continue;
      }
      const full=sceneBurnState,logs=[];
      // Only heat and the scalar emission cursor mutate in a guarded, event-free slice.
      // Preserve the full initial material only for a prefix that may expire.
      const retain=method==='repair-cache' && len<remain-1;
      if(retain)sceneBurnState={...full,h:full.h.slice()};
      for(let k=0;k<len;k++) {
        const frame=retain?t100FrameLog():null;
        if(frame){logs.push(frame);stats.allocated_log_bytes+=frame.values.byteLength;}
        witness=t100Advance(plan,dt,frame);
        if(frame)stats.logged_samples+=frame.count;
        stats.sliced_steps++;researchFrame++;
        if(witness!==null)break;
      }
      if(retain)stats.max_live_log_bytes=Math.max(stats.max_live_log_bytes,logs.length*32*P.spreadSampleCap);
      if(witness!==null)break;
      if(len===remain-1)continue;
      if(method==='restart-cache'){restart=true;break;}
      const beforeRepair=performance.now();sceneBurnState=full;
      for(const frame of logs)t100Replay(frame,dt);
      stats.repair_ms+=performance.now()-beforeRepair;stats.repairs++;stats.repair_steps+=logs.length;
    }
    first=witness===null?null:researchFrame;
    totalForward=researchFrame-origin;
  } finally {beforeRestore=performance.now();t90Restore(live);}
  const afterRestore=performance.now();
  if(restart) {
    // Repeat from the original, post-click loaded cut. Include both branches in delivery.
    stats.restart=true;
    const answer=t100Ordinary('asset-cache',h,dt);
    answer.repair_stats=stats;
    answer.compute_ms+=beforeRestore-afterFork;
    answer.restore_ms+=afterRestore-beforeRestore;
    answer.prefix_steps+=totalForward;
    answer.fork_ms+=afterFork-start;
    answer.browser_ms=performance.now()-start;
    return answer;
  }
  return {yes:witness!==null,first_frame:first,witness,prefix_steps:totalForward,
    fork_ms:afterFork-start,restore_ms:afterRestore-beforeRestore,compute_ms:beforeRestore-afterFork,browser_ms:afterRestore-start,
    cache_build:t97Build,cache_rows:t97Graph?.size,repair_stats:stats};
}
window.__t90.query=t100Query;

function t100Physical() {
  const sb=sceneBurnState;
  function copy(p) {const keys=Object.keys(p).sort();return keys.map(k=>[k,p[k]]);}
  return {frame:researchFrame,simTime,seed:simSeed,draws:researchRandomDraws,tick:vpmTick,
    source:copy(source),pointer:copy(pointer),embers:embers.map(copy),emberAcc,
    material:[sb.h.slice(),sb.fuel.slice(),sb.glow.slice(),sb.char_.slice(),sb.state.slice()],
    frontier:sb.burning.slice(),cursor:sb.emitCursor,
    gas:layers.map(l=>[l.idx,l.seed,l.t,l.acc,l.ps.map(copy)])};
}
function t100Equal(a,b) {
  if(typeof a!=='object' || a===null)return Object.is(a,b);
  if(typeof b!=='object' || b===null)return false;
  if(ArrayBuffer.isView(a)) {
    if(a.constructor!==b.constructor || a.byteLength!==b.byteLength)return false;
    const x=new Uint8Array(a.buffer,a.byteOffset,a.byteLength), y=new Uint8Array(b.buffer,b.byteOffset,b.byteLength);
    for(let i=0;i<x.length;i++)if(x[i]!==y[i])return false;
    return true;
  }
  const keys=Object.keys(a);
  return keys.length===Object.keys(b).length && keys.every(k=>Object.hasOwn(b,k) && t100Equal(a[k],b[k]));
}
function t100Audit(dt) {
  const initial=researchFrame;
  const plan=t100Plan(t90Shell.ids,t90Shell.mask,179,dt);
  const len=plan?.remaining || 0;
  const result={cut:initial,length:len,status:'zero_guard'};
  if(!len || len===179)return result;
  let checkpoint,next;
  const first=t90Fork();
  try {
    t97Use('asset-cache');
    const full=sceneBurnState;sceneBurnState={...full,h:full.h.slice()};
    const logs=[];
    for(let k=0;k<len;k++) {
      const frame=t100FrameLog();logs.push(frame);
      const hit=t100Advance(plan,dt,frame);researchFrame++;
      if(hit!==null) {
        return {...result,status:'event_before_expiry',event:researchFrame,witness:hit};
      }
    }
    sceneBurnState=full;
    const gasEnd=layers,draws=researchRandomDraws;
    for(const frame of logs)t100Replay(frame,dt);
    if(layers!==gasEnd || draws!==researchRandomDraws)throw Error('Repair touched gas/RNG');
    checkpoint=t100Physical();
    t94StepFull(dt);next=t100Physical();
    result.sample_count=logs.reduce((n,f)=>n+f.count,0);
  } finally {t90Restore(first);}
  const second=t90Fork();
  try {
    for(let k=0;k<len;k++)t94StepFull(dt);
    if(!t100Equal(checkpoint,t100Physical()))throw Error('Full material and gas state differs at repair '+researchFrame);
    result.repair_frame=researchFrame;result.repair_hash=__t86.marker().hash;
    t94StepFull(dt);
    if(!t100Equal(next,t100Physical()))throw Error('Post-repair native continuation differs at '+researchFrame);
    result.next_hash=__t86.marker().hash;
  } finally {t90Restore(second);}
  result.status='matched_expiry_and_continuation';return result;
}
window.__t100={audit:t100Audit};
