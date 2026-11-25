// Untimed validation from frame 180 before the second stroke. The anchor used
// here is isolated from the one used by the measured editor invocations.
window.__t102Audit=function(pick,dt){
  if(t102Context || t98Original || researchFrame!==180 || t86Global)throw Error('T102 audit requires pre-click state');
  const oldAnchor=t102Anchor, savedSpread=stepSpread;
  const fields=['h','state','fuel','glow','char_','burning'];
  const baseline=[], modes=['native','active-fresh','active-anchor','active-anchor'];
  const runs=[];
  const fail=(key,k)=>{throw Error('T102 exactness: '+key+' at offset '+(k+1));};
  try {
    t102Anchor=null;
    for(const [trial,method] of modes.entries()){
      __t98.resetTrial();
      let matchedFields=0,matchedParticles=0,matchedSites=0,stats=null,clonedRows=null;
      try {
        __t86.ignite(pick,true);
        t90Query=null;
        if(method!=='native'){
          stats=t102Start(method,dt);
          if(method==='active-anchor'){
            if(stats.anchor_built!==(trial===2))throw Error('T102 unexpected reuse');
            clonedRows=new Map([...t102Anchor.rows].map(([i,row])=>[i,{n:row.n,ids:row.ids.slice(),heat:row.heat.slice()}]));
          }
          stepSpread=t102Spread;
        }
        for(let k=0;k<8;k++){
          updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;stepAll(dt);researchFrame++;
          const sb=sceneBurnState;
          if(method==='native'){
            baseline.push({material:fields.map(key=>sb[key].slice()),cursor:sb.emitCursor,draws:researchRandomDraws,
              gas:layers.map(l=>({t:l.t,acc:l.acc,ps:l.ps.map(p=>({...p}))}))});
            continue;
          }
          const ref=baseline[k];
          if(sb.emitCursor!==ref.cursor || researchRandomDraws!==ref.draws)fail('cursor/RNG',k);
          fields.forEach((key,j)=>{
            const a=sb[key],b=ref.material[j];
            if(a.length!==b.length)fail(key,k);
            for(let i=0;i<b.length;i++)if(!Object.is(a[i],b[i]))fail(key,k);
            matchedSites+=b.length;
          });
          for(const [l,a] of layers.entries()){
            const b=ref.gas[l];
            if(!Object.is(a.t,b.t) || !Object.is(a.acc,b.acc) || a.ps.length!==b.ps.length)fail('layer',k);
            for(let i=0;i<a.ps.length;i++){
              const x=a.ps[i],y=b.ps[i],keys=Object.keys(y);
              if(Object.keys(x).length!==keys.length)fail('particle fields',k);
              for(const key of keys)if(!Object.hasOwn(x,key) || !Object.is(x[key],y[key]))fail(key,k);
              matchedParticles++;matchedFields+=keys.length;
            }
          }
        }
        if(clonedRows)for(const [donor,ref] of clonedRows){
          const row=t102Anchor.rows.get(donor);
          if(row.n!==ref.n || !ref.ids.every((v,i)=>v===row.ids[i]) ||
             !ref.heat.every((v,i)=>Object.is(v,row.heat[i])))throw Error('Speculative mutation escaped into anchor');
        }
        runs.push({method,matched_particles:matchedParticles,matched_particle_fields:matchedFields,
          matched_material_and_frontier_values:matchedSites,anchor_built:stats?.anchor_built??null,
          preserved_anchor_rows:clonedRows?.size??0});
      } finally {
        if(t102Context)t102Stop();
        stepSpread=savedSpread;__t98.finishTrial();
      }
    }
  } finally {
    t102Anchor=oldAnchor;stepSpread=savedSpread;
  }
  return {frames:8,runs};
};
