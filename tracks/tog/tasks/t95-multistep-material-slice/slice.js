// Executed on a disposable query branch. Sources are fixed only within this guard.
function t95Open(ids, mask, horizon, dt) {
  if (horizon<=1) return null;
  if (dt!==1/60 || P.solver!=='vpm' || P.dimMode!=='layer' || P.sliceMode!=='world' ||
      P.simLayers!==layers.length || P.emitterOn || P.embers || P.filament || P.interZ!==0 ||
      P.sceneScale!==1 || P.scenePitch!==0 || P.sceneYaw!==0 || P.spreadMeasureMode!=='legacy' ||
      P.spreadClockMode!=='elapsed' || P.spreadParticlePolicy!=='block' || !P.spreadSceneFeed ||
      !P.spreadOn || !P.spreadFlameHeat || !t86Global) return null;
  const sb=sceneBurnState, old=sb.burning, steps=horizon-1;
  if (old.length<P.spreadFrontierCap || old.length<P.spreadFeedCap || sb.emitCursor<0 ||
      sb.emitCursor+steps*P.spreadFeedCap >= old.length) return null;
  // Monotonicity of the exact per-step binary32 fuel update makes the smallest
  // initial fuel a lower bound for every old burner through the last feed.
  let minFuel=Infinity;
  for (const i of old) minFuel=Math.min(minFuel,sb.fuel[i]);
  for (let k=0;k<steps;k++) minFuel=Math.fround(minFuel-dt/P.spreadBurnT);
  if (!(minFuel>0)) return null;
  const cold=[], lo=[Infinity,Infinity,Infinity], hi=[-Infinity,-Infinity,-Infinity];
  for (const id of ids) {
    if (sb.state[id]!==0 || sb.fuel[id]<=0) continue;
    cold.push(id);
    const p=sceneGauss[id].p;
    for (let j=0;j<3;j++) {lo[j]=Math.min(lo[j],p[j]); hi[j]=Math.max(hi[j],p[j]);}
  }
  return {cold,mask,lo,hi,graph:null,remaining:steps};
}

function t95Overlaps(plan, p, r) {
  const pad=r+1e-9;
  return p[0]>=plan.lo[0]-pad && p[0]<=plan.hi[0]+pad &&
         p[1]>=plan.lo[1]-pad && p[1]<=plan.hi[1]+pad &&
         p[2]>=plan.lo[2]-pad && p[2]<=plan.hi[2]+pad;
}

function t95Graph(plan, dt) {
  const sb=sceneBurnState, r=P.spreadR;
  const edgeIds=[], deltas=[];
  for(let b=0;b<P.spreadFrontierCap;b++) {
    const donor=sb.burning[b], pi=sceneGauss[donor].p;
    if (!t95Overlaps(plan,pi,r)) continue;
    hashQuery(pi,r,(j,d)=>{
      if (!plan.mask[j] || sb.state[j]!==0 || sb.fuel[j]<=0) return;
      const dy=sceneGauss[j].p[1]-pi[1], up=Math.max(0,dy/Math.max(1e-4,r));
      edgeIds.push(j);
      deltas.push(dt*P.spreadRate*(1-d/r)*(1+2.2*up));
    },sb.state);
  }
  return {edgeIds,deltas};
}

function t95Advance(plan,dt) {
  if(plan.remaining--<=0) throw Error('T95 exceeded guarded prefix');
  updateCam(cv.width/Math.max(1,cv.height)); simTime+=dt;
  t95FullGas(dt);
  const sb=sceneBurnState, r=P.spreadIgnR, N=layers.length;
  let sampled=0;
  scan:for(const L of layers) {
    const z=(L.idx/(N-1)-.5)*P.sliceDepth;
    for(let i=0;i<L.ps.length;i+=7) {
      const p=L.ps[i];
      if(p.T<.55) continue;
      if(++sampled>P.spreadSampleCap) break scan;
      const s=worldToSrc(p.x,p.y,z);
      if(!t95Overlaps(plan,s,r)) continue;
      hashQuery(s,r,(j,d)=>{
        if(plan.mask[j] && sb.state[j]===0 && sb.fuel[j]>0) sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);
      });
    }
  }
  const decay=1-dt*.35;
  for (const id of plan.cold) {
    if(sb.h[id]>0) {
      sb.h[id]*=decay;
      if(sb.h[id]>=P.spreadIgnH) return id;
    }
  }
  // The fixed graph is materialized only if the query survives to its first post-scan phase.
  if(!plan.graph) plan.graph=t95Graph(plan,dt);
  const {edgeIds,deltas}=plan.graph;
  for (let i=0;i<edgeIds.length;i++) sb.h[edgeIds[i]]+=deltas[i];
  t95Feed(dt);
  return null;
}
