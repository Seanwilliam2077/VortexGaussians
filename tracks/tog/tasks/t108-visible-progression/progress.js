let t108Weights=null;

function t108Cache(count,pairs){
  if(t108Weights)throw Error('Weights already configured');
  const units=new Float64Array(count);
  units.fill(-1);
  for(const [id,weight] of pairs){
    const n=Math.round(weight*1e6);
    if(!Number.isInteger(id)||id<0||id>=count||units[id]!==-1||!Number.isSafeInteger(n)||n<0)throw Error('Invalid matte');
    units[id]=n;
  }
  t108Weights=units;
  return {bytes:units.byteLength,records:pairs.length};
}

function t108Progress(){
  const ids=[],sb=sceneBurnState,mask=new Uint8Array(sb.state.length);
  let total=0;
  for(const i of t90Shell.ids){
    if(sb.state[i]!==0 || sb.fuel[i]<=0)continue;
    const w=t108Weights[i];
    if(w<0 || !Number.isSafeInteger(w))throw Error('Missing eligible weight');
    total+=w;ids.push(i);mask[i]=1;
  }
  if(!Number.isSafeInteger(total))throw Error('Mass exceeds integer precision');
  return {ids,mask,total,target:Math.ceil(total/4),count:0,mass:0};
}

function t108Add(p,i){p.mass+=t108Weights[i];p.count++;}

// Full-state diagnostic includes every typed material value, ordered frontier,
// complete particle record, native clock and random position. It runs outside timing.
function t108Fingerprint(){
  const phys=t100Physical();
  const values=JSON.stringify(phys,(_,v)=>ArrayBuffer.isView(v)?Array.from(v):v);
  let hash=2166136261;
  for(let k=0;k<values.length;k++){hash^=values.charCodeAt(k);hash=Math.imul(hash,16777619);}
  return {length:values.length,fnv32:(hash>>>0).toString(16).padStart(8,'0'),marker:__t86.marker()};
}

function t108Answer(mode,p,h,dt,profile=false,auditFrames=[]){
  const origin=researchFrame, deadline=origin+h, phases={fork_ms:0,restore_ms:0,guard_ms:0,repair_ms:0};
  const work={guards:[],ordinary_steps:0,sliced_steps:0,repair_steps:0,repairs:0,restarts:0,log_bytes:0,
              peak_log_bytes:0,projected_material_bytes:0,logged_samples:0,active:[]};
  const curve=[],boundaries={};
  let first=null,atCount=0,atMass=0,live=null,previousCount=0;
  const begin=()=>{const t=performance.now();live=t90Fork();phases.fork_ms+=performance.now()-t;t102Start('active-anchor',dt);};
  const end=()=>{work.active.push(t102Stop());const t=performance.now();t90Restore(live);phases.restore_ms+=performance.now()-t;live=null;};
  function record(){
    if(profile)curve.push([researchFrame,p.count-previousCount,p.count,p.mass]);
    previousCount=p.count;
    if(first===null && p.mass>=p.target){first=researchFrame;atCount=p.count;atMass=p.mass;}
    if(profile && auditFrames.includes(researchFrame))boundaries[researchFrame]=t108Fingerprint();
    return !profile && first!==null;
  }
  const restart=()=>{
    end();begin();p.count=0;p.mass=0;first=null;atCount=0;atMass=0;previousCount=0;curve.length=0;
    mode='ordinary';work.restarts++;
  };
  begin();
  try {
    if(p.target>0)while(researchFrame<deadline){
      const remain=deadline-researchFrame;
      let plan=null;
      if(mode!=='ordinary'){
        const t=performance.now();plan=t100Plan(p.ids,p.mask,remain,dt);phases.guard_ms+=performance.now()-t;
        work.guards.push([researchFrame,plan?.remaining??0]);
      }
      if(!plan){
        if(mode==='restart' && researchFrame>origin){restart();continue;}
        if(mode==='restart')mode='ordinary';
        updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);
        t108Full(p,dt,!profile);researchFrame++;work.ordinary_steps++;
        if(record())break;continue;
      }
      const length=plan.remaining,full=sceneBurnState;
      const retain=mode==='repair' && length<remain;
      const logs=[];
      // The projection mutates only heat, monotone ignition flags and the emission cursor.
      // The copied state intentionally does not append local births to the old feed frontier.
      sceneBurnState={...full,h:full.h.slice(),state:full.state.slice()};
      work.projected_material_bytes+=sceneBurnState.h.byteLength+sceneBurnState.state.byteLength;
      for(let i=0;i<length;i++){
        const log=retain?t100FrameLog():null;
        if(log){logs.push(log);work.log_bytes+=log.values.byteLength;}
        t108Slice(plan,dt,log,p,!profile);researchFrame++;work.sliced_steps++;
        if(log)work.logged_samples+=log.count;
        if(record())break;
      }
      work.peak_log_bytes=Math.max(work.peak_log_bytes,logs.length*32*P.spreadSampleCap);
      if(!profile && first!==null || researchFrame===deadline)break;
      if(mode==='restart'){restart();continue;}
      const t=performance.now();sceneBurnState=full;
      for(const frame of logs)t100ReplayActive(frame,dt);
      phases.repair_ms+=performance.now()-t;work.repair_steps+=logs.length;work.repairs++;
      if(profile)boundaries[researchFrame]=t108Fingerprint();
    }
    return {defined:p.total>0,first_frame:first,total:p.total,target:p.target,eligible:p.ids.length,
            count:first===null?p.count:atCount,mass:first===null?p.mass:atMass,curve,boundaries,work,phases};
  } finally {end();}
}

function t108Click(mode,h,dt,pick,audit=false,auditFrames=[]){
  if(!['ordinary','restart','repair'].includes(mode)||h!==180||dt!==1/60)throw Error('Unregistered request');
  const start=performance.now(),stroke=__t86.ignite(pick,true),clicked=performance.now();
  __t90.configure(pick);const region=performance.now(),p=t108Progress(),ready=performance.now();
  const answer=t108Answer(mode,p,h,dt,audit,auditFrames);
  return {...answer,clicked:stroke.count,click_ms:clicked-start,shell_index_ms:region-clicked,
    denominator_ms:ready-region,total_browser_ms:performance.now()-start};
}
window.__t108={cache:t108Cache,click:t108Click};
