// Runs inside the original native renderer closure.
const t150dt=1/60;
let t150Target=null, t150Held=null;

function install150(pick,pairs) {
  const shell=t90Configure(pick), weights=new Float64Array(sceneGauss.length);
  weights.fill(-1);
  for(const [id,w] of pairs){
    if(weights[id]!==-1 || !Number.isFinite(w) || w<0)throw Error('Invalid source weight');
    weights[id]=Math.round(w*1e6);
  }
  const ids=shell.filter(i=>sceneBurnState.state[i]===0 && sceneBurnState.fuel[i]>0);
  const mask=new Uint8Array(weights.length); let total=0;
  for(const id of ids){if(weights[id]<0)throw Error('Missing shell weight');mask[id]=1;total+=weights[id];}
  if(!Number.isSafeInteger(total)||!total)throw Error('Invalid target');
  t150Target={ids,mask,weights,total,target:Math.ceil(total/4)};
  return {eligible:ids.length,total,shell};
}
function progress150(){return {...t150Target,count:0,mass:0,witness:null,first:null};}
function t111Add(p,id){
  p.count++;
  const w=p.weights[id];p.mass+=w;
  if(w>0 && (p.witness===null || id<p.witness))p.witness=id;
}
function finishStep150(p) {
  if(p.mass>=p.target){if(p.witness===null)throw Error('Missing crossing witness');p.first=researchFrame;}
  else p.witness=null;
}
function nativeStep150() {
  updateCam(cv.width/cv.height);simTime+=t150dt;stepAll(t150dt);researchFrame++;
}
function nativeQuery150(p) {
  const cold=p.ids.filter(i=>sceneBurnState.state[i]===0);
  nativeStep150();
  for(const id of cold)if(sceneBurnState.state[id]===1)t111Add(p,id);
  finishStep150(p);
}
function indexedStep150(p=null) {
  updateCam(cv.width/cv.height);simTime+=t150dt;t95FullGas(t150dt);
  t116Full(p,t150dt,false);researchFrame++;
  if(p)finishStep150(p);
}
function screen150(p,isRegional,work) {
  while(researchFrame<270 && p.first===null){
    const remaining=270-researchFrame;
    const plan=isRegional?t100Plan(p.ids,p.mask,remaining,t150dt):null;
    if(!plan){indexedStep150(p);work.full++;continue;}
    const full=sceneBurnState, logs=[],length=plan.remaining;
    sceneBurnState={...full,h:full.h.slice(),state:full.state.slice()};
    for(let i=0;i<length && p.first===null;i++){
      // The terminal disposable block needs no logs. A rare terminal acceptance
      // rebuilds this block from a saved branch if it must be kept.
      const frame=length<remaining?t100FrameLog():null;
      t116Slice(plan,t150dt,frame,p,false);researchFrame++;finishStep150(p);
      if(frame)logs.push(frame);
      work.projected++;
    }
    if(!logs.length)return p.first!==null;
    const at=performance.now();sceneBurnState=full;
    for(const frame of logs)t116Chronological(frame,t150dt);
    work.repair_ms+=performance.now()-at;work.repaired+=logs.length;
  }
}
function answer150(p,arm){
  return {arm,first:p.first,count:p.count,mass:p.mass,target:p.target,total:p.total,witness:p.witness};
}
async function digest150(){
  const s=t100Physical(), parts=s.material;delete s.material;
  async function hash(array) {
    const d=new Uint8Array(await crypto.subtle.digest('SHA-256',array));
    return Array.from(d,b=>b.toString(16).padStart(2,'0')).join('');
  }
  return {frame:s.frame,draws:s.draws,material:await Promise.all(parts.map(hash)),
    ordered:await hash(new TextEncoder().encode(JSON.stringify(s)))};
}

async function take150(method,picks,audit){
  if(t150Held || researchFrame!==180 || t98Original || !EMBED)throw Error('Unexpected take parent');
  const start=performance.now(),parent=sceneBurnState,answers=[],work={full:0,projected:0,repaired:0,repair_ms:0,shared:0,reused:0};
  if(!['native','ordinary','repair','hybrid','sibling'].includes(method))throw Error('Unknown method');
  const native=method==='native';
  let fullIds,checkpoint=null,saved=null,chosen=null,progress;
  const begin=()=>__t98.resetTrial();
  const rewind=()=>__t98.finishTrial();
  const open=()=>{if(!native)t102Start('active-anchor',t150dt);};
  const close=()=>{if(t102Context)t102Stop();};
  if(!native)t116Begin(false);
  try{
    if(method==='sibling'){begin();try{fullIds=__t86.ignite(picks[1],true).ids;}finally{rewind();}}
    for(const pick of picks){
      if(checkpoint && pick.name==='F'){
        t90Restore(checkpoint);t116Session.full=null;t116Session.region=null;
        t119Materialize(parent,saved.light,fullIds,work.shared,t150dt);work.reused=work.shared;
        progress={...saved.progress};
      }else{
        if(t98Original)rewind();
        begin();const clicked=__t86.ignite(pick,true).ids;
        progress=progress150();
        if(method==='sibling' && pick.name==='L'){
          work.shared=t119Guard(parent,clicked,fullIds,t150dt);
          saved={light:clicked};
        }
      }
      open();
      if(native){while(researchFrame<270 && progress.first===null)nativeQuery150(progress);}
      else {
        if(method==='sibling' && pick.name==='L' && work.shared){
          const cut=researchFrame+work.shared;
          while(researchFrame<cut && progress.first===null){indexedStep150(progress);work.full++;}
          if(progress.first===null){
            saved.progress={...progress};checkpoint=t90Fork();
          }
        }
        const regional=method==='repair' || (method==='hybrid' && pick.name==='L');
        if(screen150(progress,regional,work)){
          // A terminal projected acceptance needs complete state. Only this
          // contingency pays for reinitializing and replaying the kept stroke.
          close();rewind();begin();__t86.ignite(pick,true);open();
          while(researchFrame<progress.first){indexedStep150();work.full++;}
        }
      }
      answers.push(answer150(progress,pick.name));
      if(progress.first!==null){chosen=pick.name;break;}
      close();
    }
    const selected=performance.now(),crossing=audit?await digest150():null;
    if(!chosen)throw Error('Neither brush qualified for the registered continuation');
    const frameBytes=cv.width*cv.height*4,frameCount=30;
    const slab=new Uint8Array(frameBytes*frameCount);
    let advanceMs=0,drawMs=0;
    for(let i=0;i<frameCount;i++){
      let t=performance.now();if(native)nativeStep150();else indexedStep150();
      advanceMs+=performance.now()-t;t=performance.now();
      render();gl.readPixels(0,0,cv.width,cv.height,gl.RGBA,gl.UNSIGNED_BYTE,slab.subarray(i*frameBytes,(i+1)*frameBytes));
      if(gl.isContextLost() || gl.getError()!==gl.NO_ERROR)throw Error('Native take readback failed');
      drawMs+=performance.now()-t;
    }
    const t=performance.now();
    const response=await fetch('/take',{method:'POST',body:slab});
    if(response.status!==204)throw Error('Host did not receive playback bytes');
    const delivered=performance.now();close();t116Session=null;
    t150Held={frame:researchFrame,serial:++serial150};
    return {method,chosen,answers,crossing,handle:t150Held,work,selection_ms:selected-start,advance_ms:advanceMs,
      draw_read_ms:drawMs,upload_ms:delivered-t,browser_ms:performance.now()-start};
  } catch(error){close();t116Session=null;if(t98Original)rewind();throw error;}
}
let serial150=0;
window.__t150={install:install150,take:take150,digest:digest150,
  async consume(handle){
    if(!t150Held || t150Held.serial!==handle.serial || researchFrame!==handle.frame)throw Error('Invalid kept handle');
    try {
      const end=await digest150();nativeStep150();const next=await digest150();
      return {end,next};
    }finally{__t98.finishTrial();t150Held=null;}
  },
  cold(){t102Anchor=null;t116Geometry=null;},
  backend(){const e=gl.getExtension('WEBGL_debug_renderer_info');return gl.getParameter(e?e.UNMASKED_RENDERER_WEBGL:gl.RENDERER);}
};
