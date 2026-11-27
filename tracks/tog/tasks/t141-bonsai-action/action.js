// Browser-side implementation in the closure of the pinned standalone Vortex renderer.
let t141HideGas=false;
let t141Rest=null;
let t141Eligible=null;
let t141Camera=null;
let t141Weights=null;
const t141dt=1/60;

async function digest141(view) {
  const bytes=view instanceof ArrayBuffer ? view : new Uint8Array(view.buffer,view.byteOffset,view.byteLength);
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  return Array.from(new Uint8Array(hash),x=>x.toString(16).padStart(2,'0')).join('');
}
async function state141() {
  const state=t100Physical();
  const arrays=state.material;
  delete state.material;
  const meta=new TextEncoder().encode(JSON.stringify(state,(k,v)=>{
    if(typeof v==='number' && !Number.isFinite(v))throw Error('Nonfinite physical state');
    return v;
  }));
  return {frame:researchFrame,draws:researchRandomDraws,time:simTime,cursor:sceneBurnState.emitCursor,
    particles:layers.reduce((s,l)=>s+l.ps.length,0),active:sceneBurnState.burning.length,
    gas_clocks_rng_frontier:await digest141(meta),material:await Promise.all(arrays.map(digest141))};
}
function native141(end) {
  const paused=P.paused; P.paused=false;
  try {
    while(researchFrame<end){
      updateCam(cv.width/cv.height);simTime+=t141dt;stepAll(t141dt);researchFrame++;
    }
  }finally{P.paused=paused;}
}
function indexed141(end) {
  const initial=researchFrame;
  t102Start('active-anchor',t141dt);
  try{
    while(researchFrame<end){
      updateCam(cv.width/cv.height);simTime+=t141dt;t95FullGas(t141dt);t116Full(null,t141dt,false);researchFrame++;
    }
  }finally{t102Stop();}
  return researchFrame-initial;
}
function installWeights141(result){
  const {eligible,width,height}=result;
  const positive=[];
  let total=0,x0=width,x1=-1,y0=height,y1=-1;
  for(let i=0;i<eligible.length;i++){
    const a=eligible[i];
    if(!Number.isFinite(a)||a<0)throw Error('Invalid native shell alpha');
    if(!a)continue;
    const x=i%width,y=Math.floor(i/width);
    x0=Math.min(x,x0);x1=Math.max(x,x1);y0=Math.min(y,y0);y1=Math.max(y,y1);
    positive.push(i);total+=a;
  }
  if(!total){t141Weights=null;return {nonzero_cells:0,total};}
  const box={x:2*x0,y:2*(height-1-y1),w:2*(x1-x0+1),h:2*(y1-y0+1)};
  t141Weights={box,indices:Int32Array.from(positive,i=>4*(2*(y1-Math.floor(i/width))*box.w+2*(i%width-x0))),
    weights:Float32Array.from(positive,i=>eligible[i]),total};
  return {nonzero_cells:positive.length,total,box,stats:result.stats};
}
async function image141(audit){
  if(!t141Weights)throw Error('Primary target has zero weight');
  const {box,indices,weights,total}=t141Weights;
  const images=[], hashes=[];
  for(const suppress of [false,true]){
    t141HideGas=suppress;
    try{
      const count=render();
      const image=new Uint8Array(box.w*box.h*4);
      gl.readPixels(box.x,box.y,box.w,box.h,gl.RGBA,gl.UNSIGNED_BYTE,image);
      if(gl.isContextLost() || gl.getError()!==gl.NO_ERROR)throw Error('Failed display read');
      if(audit){
        const full=new Uint8Array(cv.width*cv.height*4);
        gl.readPixels(0,0,cv.width,cv.height,gl.RGBA,gl.UNSIGNED_BYTE,full);
        if(gl.getError()!==gl.NO_ERROR)throw Error('Full audit display read failed');
        hashes.push({full_display_rgba_sha256:await digest141(full),dynamic_instances:count});
      }
      images.push(image);
    }finally{t141HideGas=false;}
  }
  const [a,b]=images;
  let changed=0;
  for(let i=0;i<indices.length;i++){
    const p=indices[i],q=p+4*box.w;
    for(let k=0;k<3;k++){
      const j=p+k,l=q+k;
      if(Math.abs(a[j]+a[j+4]+a[l]+a[l+4]-b[j]-b[j+4]-b[l]-b[l+4])>=64){changed+=weights[i];break;}
    }
  }
  return {mass:changed,denominator:total,fraction:changed/total,passes:4*changed>=total,hashes};
}
async function action141(method,picks,audit) {
  if(researchFrame!==180 || t86Global || !['ordinary-native','ordinary-indexed','transport'].includes(method))
    throw Error('Invalid live branch entry');
  const start=performance.now(),times={},branches=[];
  function work(name,fn){const at=performance.now();try{return fn();}finally{times[name]=(times[name]||0)+performance.now()-at;}}
  const make=()=>work('fork_restore_ms',()=>__t98.resetTrial());
  const done=()=>work('fork_restore_ms',()=>__t98.finishTrial());
  const click=p=>work('click_ms',()=>__t86.ignite(p,true).ids);
  const advance=end=>work('physics_ms',()=>method==='ordinary-native'?native141(end):indexed141(end));
  const parent=sceneBurnState;
  const stats=method==='ordinary-native'?null:t116Begin(false);
  let answer='none',k=0,reused=0,cp=null,fullIds;
  async function observe(name,ids){
    const physical=audit?await state141():null,at=performance.now();
    const result=await image141(audit);
    times.image_ms=(times.image_ms||0)+performance.now()-at;
    const record={name,clicked:ids.length,result};
    if(audit){
      const after=await state141();
      if(JSON.stringify(physical)!==JSON.stringify(after))throw Error('Rendering mutated physics');
      const endpoint=t90Fork();try{native141(271);record.successor=await state141();}finally{t90Restore(endpoint);}
      record.endpoint=physical;
      await window.__t141Report({method,branch:record});
    }
    branches.push(record);
    if(answer==='none' && result.passes)answer=name;
  }
  try{
    if(method==='transport'){make();try{fullIds=click(picks[1]);}finally{done();}}
    make();
    try{
      const light=click(picks[0]);
      if(method==='transport')k=work('guard_ms',()=>t119Guard(parent,light,fullIds,t141dt));
      if(k){
        advance(180+k);cp=work('checkpoint_ms',()=>t90Fork());
      }
      advance(270);
      await observe('L',light);
      if(audit || answer==='none'){
        if(k){
          work('fork_restore_ms',()=>t90Restore(cp));t116Session.full=null;
          work('transport_ms',()=>t119Materialize(parent,light,fullIds,k,t141dt));reused=k;
        }else{
          done();make();fullIds=click(picks[1]);
        }
        advance(270);await observe('F',fullIds);
      }
    }finally{if(t102Context)t102Stop();if(t98Original)done();}
  }finally{t116Session=null;t141HideGas=false;}
  return {method,audit,choice:answer,secondary:'undefined',shared_steps:k,reused_steps:reused,
    elapsed_ms:performance.now()-start,phases:times,branches,cold_index:stats};
}
window.__t141={
  hardware(){const ext=gl.getExtension('WEBGL_debug_renderer_info');return {renderer:gl.getParameter(ext?ext.UNMASKED_RENDERER_WEBGL:gl.RENDERER),
    float_color:!!extCBF,sh_degree:shDegAvail,width:cv.width,height:cv.height,scene_n:sceneGauss.length,
    depth_buckets:SCENE_BUCKETS,sh_texture_width:shTexW,texture_limit:gl.getParameter(gl.MAX_TEXTURE_SIZE),
    load_gl_error:gl.getError(),context_lost:gl.isContextLost(),center:sceneInfo.center.slice()};},
  registerRest(camera){t141Camera=camera;__t42.camera(camera);t141Rest=t90Fork();P.paused=true;},
  native(end){native141(end);return {frame:researchFrame,burning:sceneBurnState.burning.length,gas:layers.reduce((n,l)=>n+l.ps.length,0)};},
  state:state141,
  async shell(pick){
    const ids=t90Configure(pick);
    t141Eligible=ids.filter(i=>sceneBurnState.state[i]===0 && sceneBurnState.fuel[i]>0);
    return {geometric:ids.length,eligible:t141Eligible.length,
      geometric_hash:await digest141(Uint32Array.from(ids)),eligible_hash:await digest141(Uint32Array.from(t141Eligible))};
  },
  async matte(){
    const parent=t90Fork(),frozen=t90Shell;
    try{
      t90Restore(t141Rest);P.paused=true;__t42.camera(t141Camera);
      const capture=__nativeMatte.captureArrays(t141Eligible,{block:2});
      return {...installWeights141(capture),native_weight_sha256:await digest141(capture.eligible)};
    }finally{t90Restore(parent);t90Shell=frozen;t141Rest=null;}
  },
  cold(){t102Anchor=null;t116Geometry=null;},
  action:action141
};
