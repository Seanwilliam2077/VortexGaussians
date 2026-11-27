// Verbatim T119 cold indexed regional update and chronological material recovery.
function t116Slice(plan,dt,log,p,stop) {
  if(plan.remaining--<=0) throw Error('T95 exceeded guarded prefix');
  updateCam(cv.width/Math.max(1,cv.height)); simTime+=dt;
  t95FullGas(dt);
  const sb=sceneBurnState, r=P.spreadIgnR, N=layers.length;
  const grid=t116Grid(sb,plan.cold);let sampled=0;
  scan:for(const L of layers) {
    const z=(L.idx/(N-1)-.5)*P.sliceDepth;
    for(let i=0;i<L.ps.length;i+=7) {
      const p=L.ps[i];
      if(p.T<.55) continue;
      if(++sampled>P.spreadSampleCap) break scan;
      const s=worldToSrc(p.x,p.y,z);
      if(log){const j=4*log.count++;log.values[j]=s[0];log.values[j+1]=s[1];log.values[j+2]=s[2];log.values[j+3]=p.T;}
      if(!t95Overlaps(plan,s,r)) continue;
      grid.walk(grid,s,r,(j,d)=>{
        if(plan.mask[j] && sb.state[j]===0 && sb.fuel[j]>0) sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);
      });
    }
  }
  const decay=1-dt*.35;
  for (const id of plan.cold) {
    if(sb.state[id]===0 && sb.h[id]>0) {
      sb.h[id]*=decay;
      if(sb.h[id]>=P.spreadIgnH) {sb.state[id]=1;t116Remove(grid,id);t111Add(p,id);}
    }
  }
  // The fixed graph is materialized only if the query survives to its first post-scan phase.
  if(stop && p.mass>=p.target)return;
  if(!plan.graph) plan.graph=t95Graph(plan,dt);
  const {edgeIds,deltas}=plan.graph;
  for (let i=0;i<edgeIds.length;i++) if(sb.state[edgeIds[i]]===0) sb.h[edgeIds[i]]+=deltas[i];
  t95Feed(dt); if(log)log.cursor=sb.emitCursor;
  return null;
}



function t116Chronological(frame,dt) {
  const sb=sceneBurnState,q=null,r=P.spreadIgnR;
  const grid=t116Grid(sb,null),data=frame.values;
  for(let j=0;j<frame.count*4;j+=4) {
    const s=[data[j],data[j+1],data[j+2]], T=data[j+3];
    grid.walk(grid,s,r,(id,d)=>{if(sb.state[id]===0) sb.h[id]+=dt*P.spreadHeat*T*(1-d/r);});
  }
    const decay=1-dt*.35;
  for(let i=0;i<sb.h.length;i++) if(sb.h[i]>0) {
    sb.h[i]*=decay;
    if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH) {
      sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i);
      if(q && q.mask[i]) {q.witness=i; return;}
    }
  }
  t102MaterialTail(sb,dt);
  // Under the prefix proof the sliced feed and native feed visit the same ordered IDs.
  // Gas and the RNG are already at the end of this frame.
  sb.emitCursor=frame.cursor;
}
