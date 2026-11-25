// Region queries share fixed dt, static positions, and the pinned legacy spread operator.
const t97AssetGraph = new Map();
let t97Graph = null;
let t97Build = null;

function t97Neighbours(i, r, dt) {
  const existing = t97Graph.get(i);
  if (existing) return existing;
  const start = performance.now(), ids = [], increments = [];
  const pi = sceneGauss[i].p;
  hashQuery(pi,r,(j,d) => {
    const up = Math.max(0,(sceneGauss[j].p[1]-pi[1])/Math.max(1e-4,r));
    ids.push(j);
    increments.push(dt*P.spreadRate*(1-d/r)*(1+2.2*up));
  });
  const row = {ids:Int32Array.from(ids), heat:Float64Array.from(increments)};
  t97Graph.set(i,row);
  t97Build.entries++;
  t97Build.bytes += row.ids.byteLength+row.heat.byteLength;
  t97Build.ms += performance.now()-start;
  return row;
}

function t97Spread(dt) {
  const sb=sceneBurnState, q=t90Query, N=layers.length, areaMode=false;
  const r=P.spreadIgnR;
  let sampled=0;
  outer: for(const layer of layers) {
    const depth=(layer.idx/(N-1)-.5)*P.sliceDepth;
    for(let k=0;k<layer.ps.length;k+=7) {
      const p=layer.ps[k];
      if(p.T<.55) continue;
      if(++sampled>P.spreadSampleCap) break outer;
      hashQuery(worldToSrc(p.x,p.y,depth),r,(j,d)=>{
        if(sb.state[j]===0) sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);
      });
    }
  }
  const decay=1-dt*.35;
  for(let i=0;i<sb.h.length;i++) if(sb.h[i]>0) {
    sb.h[i]*=decay;
    if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH) {
      sb.state[i]=1; sb.burning.push(i);
      if(q && q.mask[i]) {q.witness=i; return;}
    }
  }
  const radius=P.spreadR;
  const serviced=Math.min(sb.burning.length,P.spreadFrontierCap);
  for(let b=0;b<serviced;b++){
    const i=sb.burning[b];
    if(sb.state[i]!==1) continue;
    if(t97Graph) {
      const row=t97Neighbours(i,radius,dt);
      for(let k=0;k<row.ids.length;k++){
        const j=row.ids[k];
        if(sb.state[j]===0) sb.h[j]+=row.heat[k];
      }
    } else {
      const pi=sceneGauss[i].p;
      hashQuery(pi,radius,(j,d)=>{
        if(sb.state[j]!==0) return;
        const up=Math.max(0,(sceneGauss[j].p[1]-pi[1])/Math.max(1e-4,radius));
        sb.h[j]+=dt*P.spreadRate*(1-d/radius)*(1+2.2*up);
      },sb.state);
    }
  }
  for(const i of sb.burning) if(sb.state[i]===1) {
    sb.fuel[i]-=dt/P.spreadBurnT;
    if(sb.fuel[i]<0) sb.fuel[i]=0;
    sb.glow[i]=Math.min(1,sb.glow[i]+dt*3);
    sb.char_[i]=Math.min(1,sb.char_[i]+dt/(P.spreadBurnT*.85));
    if(sb.fuel[i]<=0) {sb.state[i]=2;sb.glow[i]=0;sb.char_[i]=1;}
  }
  if(sb.burning.length) sb.burning=sb.burning.filter(i=>sb.state[i]===1);
  /* NATIVE_EMISSION */
}

function t97Use(method) {
  if (P.sceneYaw!==0 || P.scenePitch!==0 || P.sceneScale!==1 || !P.spreadFlameHeat ||
      P.spreadClockMode!=='elapsed' || P.spreadMeasureMode!=='legacy' || P.spreadParticlePolicy!=='block' ||
      !t86Global) throw Error('Unsupported ordinary graph settings');
  t97Build={ms:0,entries:0,bytes:0};
  t97Graph=method==='asset-cache'?t97AssetGraph:method==='cold-cache'?new Map():null;
}
const t97NativeStepSpread=stepSpread;
const t97OriginalQuery=window.__t90.query;
window.__t90.query=function(method,h,dt){
  if(!['plain','cold-cache','asset-cache'].includes(method)) return t97OriginalQuery(method,h,dt);
  const start=performance.now();
  t97Use(method); stepSpread=t97Spread;
  try {
    const result=t97OriginalQuery('rank-only',h,dt);
    result.cache_build=t97Build;
    result.cache_rows=t97Graph?.size??0;
    result.browser_ms=performance.now()-start;
    return result;
  } finally {stepSpread=t97NativeStepSpread; t97Graph=null;}
};

window.__t97Audit=function(dt) {
  const fingerprints=[];
  const keys=['state','h','fuel','char_','glow','burning'];
  function capture() {
    const sb=sceneBurnState;
    const fields=keys.map(k=>sb[k].slice());
    return {fields, cursor:sb.emitCursor, draws:researchRandomDraws, particle:researchSnapshot().particleStateHash};
  }
  for(const method of ['native','plain','cold-cache']){
    const live=t90Fork();
    try {
      if(method!=='native') { t97Use(method); stepSpread=t97Spread; }
      for(let k=0;k<8;k++){
        updateCam(cv.width/Math.max(1,cv.height)); simTime+=dt;stepAll(dt);researchFrame++;
        const s=capture();
        if(method==='native') fingerprints.push(s);
        else {
          const prev=fingerprints[k];
          if(s.cursor!==prev.cursor || s.draws!==prev.draws || s.particle!==prev.particle) throw Error('RNG, gas or cursor diverged');
          keys.forEach((key,j)=>{
            const a=s.fields[j], b=prev.fields[j];
            if(a.length!==b.length || !a.every((v,i)=>Object.is(v,b[i]))) throw Error(method+' '+key+' '+researchFrame);
          });
        }
      }
    } finally {stepSpread=t97NativeStepSpread; t90Restore(live);t97Graph=null;}
  }
  return fingerprints.map(s=>({particle:s.particle,cursor:s.cursor,draws:s.draws,active:s.fields[5].length}));
};
