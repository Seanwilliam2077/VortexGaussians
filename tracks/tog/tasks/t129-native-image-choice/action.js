// Browser closure operating directly on the native RGB display buffer.
const t129Images=new Map();
let t129Camera0=null, t129Wood=false;
function t129Install(camera,bytes) {
  const weights=new Float64Array(bytes);
  if(weights.length!==470*264)throw Error('Unexpected calibrated shell shape');
  let x0=470,y0=264,x1=-1,y1=-1,total=0;
  const ids=[];
  for(let i=0;i<weights.length;i++){
    const w=weights[i];if(!Number.isFinite(w)||w<0)throw Error('Invalid reference opacity');
    if(!w)continue;
    const x=i%470,y=Math.floor(i/470);
    x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
    total+=w;ids.push(i);
  }
  if(!total)throw Error('Zero reference mass');
  const width=2*(x1-x0+1),height=2*(y1-y0+1);
  const offsets=Int32Array.from(ids,i=>4*(2*(y1-Math.floor(i/470))*width+2*(i%470-x0)));
  const r={x:2*x0,y:2*(263-y1),width,height};
  t129Images.set(camera.id,{camera,weights:Float64Array.from(ids,i=>weights[i]),offsets,r,total,
    full:new Uint8Array(width*height*4),wood:new Uint8Array(width*height*4)});
  if(camera.id===0)t129Camera0=camera;
  return {camera:camera.id,roi_gl:r,positive_pixels:ids.length,total};
}
function t129Pixels(id,audit,phases) {
  const cache=t129Images.get(id),{r,full,wood,weights,offsets}=cache;
  __t42.camera(cache.camera);
  const images={};
  for(const mode of ['full','wood']){
    t129Wood=mode==='wood';
    const t=performance.now();
    try {
      render();
      gl.readPixels(r.x,r.y,r.width,r.height,gl.RGBA,gl.UNSIGNED_BYTE,t129Wood?wood:full);
      if(audit){
        if(gl.getError()!==0 || gl.isContextLost())throw Error('Native rendering failed');
        images[mode]=cv.toDataURL('image/png').split(',')[1];
      }
    } finally {t129Wood=false;}
    phases.render_read_ms+=performance.now()-t;
  }
  const start=performance.now();let changed=0;
  for(let i=0;i<offsets.length;i++){
    const p=offsets[i],q=p+4*r.width;
    for(let k=0;k<3;k++){
      const a=p+k,b=q+k;
      const delta=full[a]+full[a+4]+full[b]+full[b+4]-wood[a]-wood[a+4]-wood[b]-wood[b+4];
      if(Math.abs(delta)>=64){changed+=weights[i];break;}
    }
  }
  phases.score_ms+=performance.now()-start;
  return {camera:id,changed_shell_mass:changed,shell_mass:cache.total,fraction:changed/cache.total,
    passes_quarter:4*changed>=cache.total,...(audit?{images}:{})};
}
function t129Action(method,picks,cams,dt,audit=false) {
  if(!['ordinary','sibling'].includes(method) || dt!==1/60 || researchFrame!==180 || t86Global)throw Error('Invalid editing state');
  const begin=performance.now(),phases={fork_restore_ms:0,pick_ms:0,guard_ms:0,physics_ms:0,transport_ms:0,render_read_ms:0,score_ms:0};
  const strokes=[],choices=Object.fromEntries(cams.map(c=>[c,'none']));
  function measure(k,fn){const t=performance.now();try{return fn();}finally{phases[k]+=performance.now()-t;}}
  function fork(){measure('fork_restore_ms',()=>__t98.resetTrial());}
  function restore(){measure('fork_restore_ms',()=>__t98.finishTrial());}
  const ignite=p=>measure('pick_ms',()=>__t86.ignite(p,true).ids);
  function advance(end){
    const start=researchFrame;
    measure('physics_ms',()=>{
      while(researchFrame<end){
        updateCam(cv.width/cv.height);simTime+=dt;t95FullGas(dt);
        t116Full(null,dt,false);researchFrame++;
      }
    });
    return end-start;
  }
  const startSolver=()=>measure('physics_ms',()=>t102Start('active-anchor',dt));
  const stopSolver=()=>measure('physics_ms',()=>t102Stop());
  function observe(pick,ids,steps,cameras){
    const state=audit?t108Fingerprint():null;
    const views=cameras.map(c=>t129Pixels(c,audit,phases));
    __t42.camera(t129Camera0);
    if(audit && JSON.stringify(t108Fingerprint())!==JSON.stringify(state))throw Error('Rendering altered physical state');
    for(const v of views)if(choices[v.camera]==='none' && v.passes_quarter)choices[v.camera]=pick;
    strokes.push({pick,clicked:ids.length,steps,views,...(audit?{state}:{})});
  }
  const parent=sceneBurnState,stats=t116Begin(false);
  let fullIds,checkpoint=null,shared=0,reused=0;
  try {
    if(method==='sibling'){
      fork();try{fullIds=ignite(picks[1]);}finally{restore();}
    }
    fork();
    try{
      const lightIds=ignite(picks[0]);
      if(method==='sibling'){
        shared=measure('guard_ms',()=>t119Guard(parent,lightIds,fullIds,dt));
        if(shared<=0)throw Error('Prior prospective guard no longer qualified');
      }
      startSolver();
      if(shared){
        advance(180+shared);
        checkpoint=measure('fork_restore_ms',()=>t90Fork());
      }
      advance(270);stopSolver();observe('L',lightIds,90,cams);
      const need=audit?cams:cams.filter(c=>choices[c]==='none');
      if(need.length){
        if(method==='sibling'){
          measure('fork_restore_ms',()=>t90Restore(checkpoint));
          t116Session.full=null;
          measure('transport_ms',()=>t119Materialize(parent,lightIds,fullIds,shared,dt));
          reused=shared;
        }else{
          restore();fork();fullIds=ignite(picks[1]);
        }
        startSolver();const steps=advance(270);stopSolver();observe('F',fullIds,steps,need);
      }
    }finally{if(t102Context)stopSolver();if(t98Original)restore();}
  }finally{t116Session=null;t129Wood=false;__t42.camera(t129Camera0);}
  return {method,cameras:cams,choices,strokes,shared_steps:shared,reused_steps:reused,index:stats,phases_ms:phases,browser_ms:performance.now()-begin};
}
window.__t129={
  install:t129Install,
  configure(pick){return t90Configure(pick);},
  action:t129Action,
  cold(){t116Geometry=null;t102Anchor=null;},
  backend(){const e=gl.getExtension('WEBGL_debug_renderer_info');return gl.getParameter(e?e.UNMASKED_RENDERER_WEBGL:gl.RENDERER);}
};

