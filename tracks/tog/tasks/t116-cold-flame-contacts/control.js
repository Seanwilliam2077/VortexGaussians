function t116DispatchRepair(mode,logs,dt,profile){
  let reference=null,next=null;
  if(profile){
    const keep=t102Context,oldGraph=t97Graph,oldBuild=t97Build,fork=t90Fork();
    t102Context=null;
    try{
      t102Start('active-fresh',dt);for(const f of logs)t100ReplayActive(f,dt);
      reference=t100Physical();t94StepFull(dt);next=t100Physical();
    }finally{
      if(t102Context)t102Stop();t102Context=keep;t97Graph=oldGraph;t97Build=oldBuild;t90Restore(fork);
    }
  }
  let info;
  if(mode==='sitewise')info=t116Sitewise(logs,dt,profile);
  else if(mode==='repair'){
    for(const f of logs)t116Chronological(f,dt);info={frames:logs.length};
  }else throw Error('Unexpected recovery mode');
  if(profile){
    if(!t100Equal(reference,t100Physical()))throw Error('Cold grid recovery differs at '+researchFrame);
    const fork=t90Fork();
    try{t94StepFull(dt);if(!t100Equal(next,t100Physical()))throw Error('Cold grid continuation differs at '+researchFrame);}
    finally{t90Restore(fork);}
    info.direct_equal={frame:researchFrame,frontier:reference.frontier.length,
      material_bytes:reference.material.reduce((s,a)=>s+a.byteLength,0)};
  }
  return info;
}
const t116PreviousClick=window.__t108.click;
window.__t108.click=function(mode,h,dt,pick,profile=false,frames=[]){
  if(!mode.endsWith('-cold'))return t116PreviousClick(mode,h,dt,pick,profile,frames);
  const stats=t116Begin(profile);
  try{const receipt=t116ClickCore(mode.slice(0,-5),h,dt,pick,profile,frames);receipt.work.flame_grid=stats;return receipt;}
  finally{t116Session=null;}
};
window.__t116FullAudit=function(pick,dt){
  const expected=[],rows=[];
  for(const native of [true,false]){
    __t98.resetTrial();
    try{
      __t86.ignite(pick,true);__t90.configure(pick);
      const p=t108Progress();
      if(!native){t116Begin(true);t102Start('active-anchor',dt);}
      for(let k=0;k<8;k++){
        if(native)t94StepFull(dt);
        else{
          updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);
          t116Full(p,dt,false);researchFrame++;
        }
        const now=t100Physical();
        if(native)expected.push(now);
        else{
          if(!t100Equal(now,expected[k]))throw Error('Cold ordinary full mismatch at '+researchFrame);
          rows.push({frame:researchFrame,frontier:now.frontier.length,gas:now.gas.reduce((s,l)=>s+l[4].length,0)});
        }
      }
    }finally{if(!native){if(t102Context)t102Stop();t116Session=null;}__t98.finishTrial();}
  }
  return rows;
};
