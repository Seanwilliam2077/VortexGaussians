window.__t106Audit=function(pick,dt){
  const fields=[];
  for(const method of ['native','sparse']){
    __t98.resetTrial();
    try{
      __t86.ignite(pick,true);t90Query=null;
      if(method==='sparse'){t106Start();t102Start('active-anchor',dt);}
      for(let k=0;k<9;k++){
        if(method==='native')t94StepFull(dt);
        else{
          if(k<8){updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);t106Spread(dt);researchFrame++;}
          else t94StepFull(dt);
        }
        const state=t100Physical();
        if(method==='native')fields.push({state,marker:__t86.marker().hash});
        else if(!t100Equal(state,fields[k].state))throw Error('Sparse full state differs at '+researchFrame);
      }
    }finally{if(t102Context)t102Stop();if(t106Stats)t106Stop();__t98.finishTrial();}
  }
  return {matched_frames:fields.length,native_hashes:fields.map(x=>x.marker)};
};
window.__t106Expiry=dt=>{
  const a=t100AuditActive(dt),b=t106RepairAudit(dt);
  if(!t100Equal(a,b))throw Error('Different material repair or next native state');
  return b;
};
