// Source snapshots for portable reproduction. Regenerate with extract-kernels.mjs.
let t90Query = null;
let t90Shell = null;

function t90Configure(pick) {
  if (P.solver !== 'vpm' || P.dimMode !== 'layer' || P.simLayers !== P.layers ||
      P.interZ !== 0 || P.embers || P.filament || P.emitterOn || P.sliceMode !== 'world' ||
      P.spreadMeasureMode !== 'legacy' || P.sceneScale !== 1 || pointer.active)
    throw Error('Unsupported fork or region controls');
  const mask = new Uint8Array(sceneGauss.length), ids = [];
  for (let i = 0; i < sceneGauss.length; i++) {
    const w = srcToWorld(sceneGauss[i].p);
    const d = Math.hypot(w[0]-pick.world[0], w[1]-pick.world[1], w[2]-pick.world[2]);
    if (d > pick.radius && d <= pick.radius + P.spreadIgnR) { mask[i] = 1; ids.push(i); }
  }
  t90Shell = {mask, ids};
  return ids;
}

function t90Fork() {
  const live = {layers, sceneBurnState, srand, researchFrame, researchRandomDraws,
    vpmTick, areaFeedCredit, source, pointer, simTime, embers, emberAcc, paused:P.paused,
    counters:{...spreadCounters}, regions:[...spreadRegionCounters]};
  // The selected VPM path rebuilds its scratch tree every step and leaves its VIC grids untouched.
  // Preserve the exact original live objects, including the RNG closure. The disposable RNG
  // resumes mulberry32 at the position of its recorded draw count (addition modulo 2^32).
  layers = live.layers.map(l => ({...l, ps:l.ps.map(p => ({...p}))}));
  const sb = live.sceneBurnState;
  sceneBurnState = {...sb, h:sb.h.slice(), fuel:sb.fuel.slice(), glow:sb.glow.slice(),
    char_:sb.char_.slice(), state:sb.state.slice(), burning:sb.burning.slice()};
  source = {...source}; pointer = {...pointer}; embers = embers.map(p=>({...p}));
  spreadRegionCounters.clear();
  for (const [k, c] of live.regions) spreadRegionCounters.set(k, {...c});
  const random = mulberry32((simSeed + Math.imul(researchRandomDraws, 0x6D2B79F5)) >>> 0);
  srand = () => {researchRandomDraws++; return random();};
  P.paused = false;
  return live;
}

function t90Restore(s) {
  layers=s.layers; sceneBurnState=s.sceneBurnState; srand=s.srand; researchFrame=s.researchFrame;
  researchRandomDraws=s.researchRandomDraws; vpmTick=s.vpmTick; areaFeedCredit=s.areaFeedCredit;
  source=s.source; pointer=s.pointer; simTime=s.simTime; embers=s.embers; emberAcc=s.emberAcc;
  P.paused=s.paused; Object.assign(spreadCounters,s.counters); spreadRegionCounters.clear();
  for(const [k,c] of s.regions) spreadRegionCounters.set(k,c);
  t90Query=null;
}

function t95FullGas(dt){
  if(researchP4State)throw new Error('P4 active: use researchP4.step or reset first');
  if(pointer.active){
    source.x=pointer.x; source.y=Math.max(0.02,pointer.y);
    source.vx=(pointer.x-pointer.px)*8; source.px=pointer.x; source.py=pointer.y;
  } else { source.x*=0.96; source.vx*=0.9; if(Math.abs(source.x)<0.005)source.x=0; source.y=0.04; }
  if(P.dimMode==='vol'){ step3D(dt); stepEmbers(dt); if(P.filament)updateTrails(); return; }   // Tier1: 真三维体模式
  if(P.dimMode==='vic3'){ emitSim3(dt); stepSimVIC3(dt); stepEmbers(dt); if(P.filament)updateTrails(); return; }  // 基线: 真 3D VIC
  if(P.dimMode==='vpm3'){ emitSim3(dt); stepSimVPM3(dt); stepEmbers(dt); if(P.filament)updateTrails(); return; }  // 基线: 真 3D Gaussian VPM (matched control)
  const N=layers.length, sc=Math.min(P.simLayers,N);
  const useSim=evenMask(N,sc);
  Tm.t0();
  if(P.solver==='vpm' && sc>0){
    // VPM: emit 全部层→打包→建树→导演簇 (pre), 再逐层 N-body。dt 大时 2 子步 (仅交互模式;
    //  __demo.step 恒 1/60 → 恒单步, 确定性回放不受影响)。
    const nsub=(dt>1/45)?2:1, sdt=dt/nsub;
    for(let s=0;s<nsub;s++){
      vpmPrepare(sdt, useSim, s===0);
      Tm.lap('prep');
      for(let k=0;k<N;k++) if(useSim[k]) stepSimVPM(layers[k],sdt);
      Tm.lap('step');
    }
    for(let k=0;k<N;k++) if(!useSim[k]) Sources.proc.step(layers[k],dt);
  } else {
    if(sc>0) stepCoarse(dt);        // ILM Level-1: 全局粗解算先跑一次, 驱动所有仿真层 (仅 VIC)
    Tm.lap('prep');
    for(let k=0;k<N;k++){
      if(useSim[k]) Sources.sim.step(layers[k],dt);
      else          Sources.proc.step(layers[k],dt);
    }
    Tm.lap('step');
  }
  stepEmbers(dt);
}

const t97AssetGraph = new Map();
let t97Graph = null;
let t97Build = null;

function t97Use(method) {
  if (P.sceneYaw!==0 || P.scenePitch!==0 || P.sceneScale!==1 || !P.spreadFlameHeat ||
      P.spreadClockMode!=='elapsed' || P.spreadMeasureMode!=='legacy' || P.spreadParticlePolicy!=='block' ||
      !t86Global) throw Error('Unsupported ordinary graph settings');
  t97Build={ms:0,entries:0,bytes:0};
  t97Graph=method==='asset-cache'?t97AssetGraph:method==='cold-cache'?new Map():null;
}

function t102MaterialTail(sb,dt){
  const radius=P.spreadR;
  const serviced=Math.min(sb.burning.length,P.spreadFrontierCap);
  for(let b=0;b<serviced;b++){
    const i=sb.burning[b];
    if(sb.state[i]!==1) continue;
    t102Apply(i,radius,dt,sb);
  }
  for(const i of sb.burning) if(sb.state[i]===1) {
    sb.fuel[i]-=dt/P.spreadBurnT;
    if(sb.fuel[i]<0) sb.fuel[i]=0;
    sb.glow[i]=Math.min(1,sb.glow[i]+dt*3);
    sb.char_[i]=Math.min(1,sb.char_[i]+dt/(P.spreadBurnT*.85));
    if(sb.fuel[i]<=0) {sb.state[i]=2;sb.glow[i]=0;sb.char_[i]=1;}
  }
  if(sb.burning.length) sb.burning=sb.burning.filter(i=>sb.state[i]===1);
}

let t102Anchor=null, t102Context=null;

function t102Index(states, r) {
  const next=new Int32Array(states.length), heads=new Map();
  let indexed=0;
  for(let i=0;i<states.length;i++) {
    if(states[i]!==0)continue;
    const p=sceneGauss[i].p;
    const key=Math.floor(p[0]/r)+','+Math.floor(p[1]/r)+','+Math.floor(p[2]/r);
    next[i]=heads.get(key)??-1;heads.set(key,i);indexed++;
  }
  return {next,heads,indexed};
}

function t102Row(donor,grid,states,r,dt) {
  const a=sceneGauss[donor].p, rr=r*r, ids=[],heat=[];
  const x0=Math.floor((a[0]-r)/r),x1=Math.floor((a[0]+r)/r);
  const y0=Math.floor((a[1]-r)/r),y1=Math.floor((a[1]+r)/r);
  const z0=Math.floor((a[2]-r)/r),z1=Math.floor((a[2]+r)/r);
  for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)for(let z=z0;z<=z1;z++){
    for(let j=grid.heads.get(x+','+y+','+z)??-1;j>=0;j=grid.next[j]) {
      if(states[j]!==0)continue;
      const b=sceneGauss[j].p, dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2],d2=dx*dx+dy*dy+dz*dz;
      if(d2>rr)continue;
      const up=Math.max(0,dy/Math.max(1e-4,r));
      ids.push(j);heat.push(dt*P.spreadRate*(1-Math.sqrt(d2)/r)*(1+2.2*up));
    }
  }
  return {ids:Int32Array.from(ids),heat:Float64Array.from(heat),n:ids.length};
}

function t102ValidAnchor(a,base,r,dt) {
  if(!a || a.scene!==sceneGauss || a.r!==r || a.dt!==dt || a.rate!==P.spreadRate ||
     a.states.length!==base.state.length || a.donors.length!==Math.min(base.burning.length,P.spreadFrontierCap))
    return false;
  for(let k=0;k<a.donors.length;k++)if(a.donors[k]!==base.burning[k])return false;
  // Charred and burning sites are equivalent for recipient exclusion.
  for(let i=0;i<a.states.length;i++)if((a.states[i]===0)!==(base.state[i]===0))return false;
  return true;
}

function t102Prepare(base,dt,stats) {
  const r=P.spreadR, clock=performance.now();
  const ok=t102ValidAnchor(t102Anchor,base,r,dt);
  stats.anchor_validation_ms+=performance.now()-clock;
  if(!ok) {
    const start=performance.now();
    const states=base.state.slice(), donors=Int32Array.from(base.burning.slice(0,P.spreadFrontierCap));
    const grid=t102Index(states,r), rows=new Map();
    let bytes=states.byteLength+donors.byteLength+grid.next.byteLength;
    let edges=0;
    for(const i of donors){
      const row=t102Row(i,grid,states,r,dt);
      rows.set(i,row);edges+=row.n;bytes+=row.ids.byteLength+row.heat.byteLength;
    }
    t102Anchor={scene:sceneGauss,r,dt,rate:P.spreadRate,states,donors,grid,rows,bytes,edges};
    stats.anchor_build_ms=performance.now()-start;stats.anchor_built=true;
  }
  const a=t102Anchor;
  stats.anchor_bytes=a.bytes;stats.anchor_edges=a.edges;stats.anchor_donors=a.rows.size;
  stats.anchor_cells=a.grid.heads.size;stats.anchor_indexed=a.grid.indexed;
  return a;
}

function t102Start(mode,dt) {
  if(t102Context || !['active-fresh','active-anchor'].includes(mode))throw Error('T102 nested/unknown session');
  t97Use('plain'); // identical native control guard
  const stats={ms:0,entries:0,bytes:0,anchor_built:false,anchor_validation_ms:0,anchor_build_ms:0,
    anchor_bytes:0,anchor_donors:0,anchor_edges:0,anchor_cells:0,anchor_indexed:0,
    fresh_index_ms:0,fresh_cells:0,fresh_indexed:0,local_rows_built:0,local_edges_built:0,
    copied_rows:0,pruned_edges:0,branch_bytes:0,branch_resets:0};
  const base=typeof t98Original!=='undefined' && t98Original ? t98Original.live.sceneBurnState : sceneBurnState;
  const anchor=mode==='active-anchor'?t102Prepare(base,dt,stats):null;
  t102Context={mode,anchor,grid:anchor?.grid??null,rows:new Map(),stats};
  return stats;
}

function t102Apply(i,r,dt,sb) {
  const c=t102Context, a=c.anchor, st=c.stats;
  let row=c.rows.get(i), owned=row!==undefined;
  if(!row && a)row=a.rows.get(i);
  if(!row){
    const start=performance.now();
    if(!c.grid){
      const t=performance.now();
      c.grid=t102Index(sb.state,r);st.fresh_index_ms=performance.now()-t;
      st.fresh_cells=c.grid.heads.size;st.fresh_indexed=c.grid.indexed;st.branch_bytes+=c.grid.next.byteLength;
    }
    row=t102Row(i,c.grid,sb.state,r,dt);owned=true;c.rows.set(i,row);
    st.local_rows_built++;st.local_edges_built+=row.n;
    st.branch_bytes+=row.ids.byteLength+row.heat.byteLength;st.ms+=performance.now()-start;
  }
  let count=0;
  for(let k=0;k<row.n;k++){
    const j=row.ids[k];
    if(sb.state[j]!==0)continue;
    sb.h[j]+=row.heat[k];
    if(owned && count<k){row.ids[count]=j;row.heat[count]=row.heat[k];}
    count++;
  }
  if(count===row.n)return;
  st.pruned_edges+=row.n-count;
  if(owned){row.n=count;return;}
  // An anchor row is shared across sibling futures, so never edit it in place.
  const kept={ids:new Int32Array(count),heat:new Float64Array(count),n:count};
  for(let k=0,n=0;k<row.n;k++){
    if(sb.state[row.ids[k]]!==0)continue;
    kept.ids[n]=row.ids[k];kept.heat[n++]=row.heat[k];
  }
  st.copied_rows++;st.branch_bytes+=kept.ids.byteLength+kept.heat.byteLength;
  c.rows.set(i,kept);
}

function t102Stop(){
  const c=t102Context;if(!c)throw Error('No T102 session');
  const st=c.stats;
  st.entries=st.local_rows_built+(st.anchor_built?st.anchor_donors:0);
  st.bytes=st.branch_bytes+st.anchor_bytes;
  st.ms+=st.anchor_build_ms;st.branch_rows=c.rows.size;
  t102Context=null;t97Graph=null;
  return st;
}

// The outer fork resets the benchmark to its pre-click starting state and is
// outside delivery timing. Each real preview still forks/restores inside its own query.
let t98Original = null;
window.__t98 = {
  eligibleAfterClick() {
    if(!t86Global || researchFrame!==180) throw Error('Expected post-click state');
    const sb=sceneBurnState;
    return t90Shell.ids.filter(i=>sb.state[i]===0 && sb.fuel[i]>0);
  },
  resetTrial() {
    if (t98Original || t86Global || researchFrame !== 180) throw Error('Invalid pre-click state');
    const oldShell=t90Shell;
    t98Original = {live:t90Fork(),oldShell};
  },
  click(method,h,dt,pick) {
    if (!t98Original) throw Error('Missing trial reset');
    const start=performance.now();
    const stroke=__t86.ignite(pick,true), afterClick=performance.now();
    __t90.configure(pick);
    const afterRegion=performance.now(), r=__t90.query(method,h,dt);
    return {yes:r.yes, first_frame:r.first_frame, witness:r.witness, prefix_steps:r.prefix_steps,
            fork_ms:r.fork_ms, restore_ms:r.restore_ms, compute_ms:r.compute_ms,
            plan_active:r.plan_active ?? null, cache_build:r.cache_build ?? null, cache_rows:r.cache_rows ?? null,
            shell_index_ms:afterRegion-afterClick, click_ms:afterClick-start, clicked:stroke.count,
            preview_browser_ms:r.browser_ms, total_browser_ms:performance.now()-start};
  },
  finishTrial() {
    if(!t98Original) throw Error('No trial');
    t90Restore(t98Original.live);
    t90Shell=t98Original.oldShell;
    t86Global=false;
    t98Original=null;
  }
};

let t116Geometry=null,t116Session=null;
function t116Begin(profile){
  if(t116Session)throw Error('Nested cold lookup');
  const stats={profile,geom_build_ms:0,geom_bytes:0,build_ms:0,builds:0,
    total_index_bytes:0,peak_index_bytes:0,removals:0,registrations:[],
    samples:0,distance_tests:0,within_radius:0,initially_noncold_in_bucket:0};
  t116Session={profile,stats,full:null,region:null};
  return stats;
}
function t116GetGeometry(r) {
  const stats=t116Session.stats;
  if(t116Geometry && t116Geometry.scene===sceneGauss && t116Geometry.r===r){stats.geom_bytes=t116Geometry.cells.byteLength;return t116Geometry;}
  const t=performance.now(),lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  for(const g of sceneGauss)for(let k=0;k<3;k++){
    const cell=Math.floor(g.p[k]/r);lo[k]=Math.min(lo[k],cell);hi[k]=Math.max(hi[k],cell);
  }
  const [nx,ny,nz]=lo.map((x,k)=>hi[k]-x+1);
  if(!Number.isSafeInteger(nx*ny*nz) || nx*ny*nz>4000000)throw Error('Input exceeds bounded-grid development allocation');
  const cells=new Int32Array(sceneGauss.length);
  for(let i=0;i<cells.length;i++){
    const p=sceneGauss[i].p;
    cells[i]=((Math.floor(p[0]/r)-lo[0])*ny+Math.floor(p[1]/r)-lo[1])*nz+Math.floor(p[2]/r)-lo[2];
  }
  t116Geometry={scene:sceneGauss,r,nx,ny,nz,lo,cells};
  stats.geom_bytes=cells.byteLength;stats.geom_build_ms+=performance.now()-t;
  return t116Geometry;
}
function t116Grid(sb,ids) {
  const s=t116Session,kind=ids?'region':'full',current=s[kind];
  if(current?.state===sb.state && (!ids || current.ids===ids))return current;
  const geom=t116GetGeometry(P.spreadIgnR),start=performance.now(),n=sb.state.length;
  const heads=new Int32Array(geom.nx*geom.ny*geom.nz).fill(-1);
  const next=new Int32Array(n).fill(-2),previous=new Int32Array(n);
  let members=0;
  function insert(i){
    if(sb.state[i]!==0)return;
    const cell=geom.cells[i],other=heads[cell];
    next[i]=other;previous[i]=-1;if(other>=0)previous[other]=i;heads[cell]=i;members++;
  }
  if(ids)for(const i of ids)insert(i);else for(let i=0;i<n;i++)insert(i);
  const bytes=heads.byteLength+next.byteLength+previous.byteLength;
  const g=s[kind]={state:sb.state,heads,next,previous,geom,ids,bytes,stats:s.stats,
    walk:s.profile?t116VisitTracked:t116VisitRaw};
  const st=s.stats;
  st.build_ms+=performance.now()-start;st.builds++;st.total_index_bytes+=bytes;
  st.peak_index_bytes=Math.max(st.peak_index_bytes,(s.full?.bytes??0)+(s.region?.bytes??0));
  st.registrations.push({kind,members,sites:ids?.length??n,bytes});
  return g;
}
function t116Remove(g,id){
  const next=g.next[id];if(next===-2)return;
  const prev=g.previous[id];
  if(prev<0)g.heads[g.geom.cells[id]]=next;else g.next[prev]=next;
  if(next>=0)g.previous[next]=prev;
  g.next[id]=-2;g.stats.removals++;
}
function t116VisitRaw(g,p,r,fn){
  const {lo,nx,ny,nz}=g.geom,rr=r*r;
  const x0=Math.max(0,Math.floor((p[0]-r)/r)-lo[0]), x1=Math.min(nx-1,Math.floor((p[0]+r)/r)-lo[0]);
  const y0=Math.max(0,Math.floor((p[1]-r)/r)-lo[1]), y1=Math.min(ny-1,Math.floor((p[1]+r)/r)-lo[1]);
  const z0=Math.max(0,Math.floor((p[2]-r)/r)-lo[2]), z1=Math.min(nz-1,Math.floor((p[2]+r)/r)-lo[2]);
  /* T116_SAMPLE */
  for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)for(let z=z0;z<=z1;z++){
    let id=g.heads[(x*ny+y)*nz+z];
    while(id>=0){
      const next=g.next[id];
      if(g.state[id]!==0){ /* T116_STALE */ t116Remove(g,id); }
      else{
        const b=sceneGauss[id].p,dx=b[0]-p[0],dy=b[1]-p[1],dz=b[2]-p[2];
        /* T116_CHECK */
        const d2=dx*dx+dy*dy+dz*dz;
        if(d2<=rr){ /* T116_HIT */ fn(id,Math.sqrt(d2));}
      }
      id=next;
    }
  }
}

function t116VisitTracked(g,p,r,fn){
  const {lo,nx,ny,nz}=g.geom,rr=r*r;
  const x0=Math.max(0,Math.floor((p[0]-r)/r)-lo[0]), x1=Math.min(nx-1,Math.floor((p[0]+r)/r)-lo[0]);
  const y0=Math.max(0,Math.floor((p[1]-r)/r)-lo[1]), y1=Math.min(ny-1,Math.floor((p[1]+r)/r)-lo[1]);
  const z0=Math.max(0,Math.floor((p[2]-r)/r)-lo[2]), z1=Math.min(nz-1,Math.floor((p[2]+r)/r)-lo[2]);
  g.stats.samples++;
  for(let x=x0;x<=x1;x++)for(let y=y0;y<=y1;y++)for(let z=z0;z<=z1;z++){
    let id=g.heads[(x*ny+y)*nz+z];
    while(id>=0){
      const next=g.next[id];
      if(g.state[id]!==0){ g.stats.initially_noncold_in_bucket++; t116Remove(g,id); }
      else{
        const b=sceneGauss[id].p,dx=b[0]-p[0],dy=b[1]-p[1],dz=b[2]-p[2];
        g.stats.distance_tests++;
        const d2=dx*dx+dy*dy+dz*dz;
        if(d2<=rr){ g.stats.within_radius++; fn(id,Math.sqrt(d2));}
      }
      id=next;
    }
  }
}

function t116Full(p,dt,stop) {
  const sb=sceneBurnState, q=t90Query, N=layers.length, areaMode=false;
  const r=P.spreadIgnR, grid=t116Grid(sb,null);
  let sampled=0;
  outer: for(const layer of layers) {
    const depth=(layer.idx/(N-1)-.5)*P.sliceDepth;
    for(let k=0;k<layer.ps.length;k+=7) {
      const p=layer.ps[k];
      if(p.T<.55) continue;
      if(++sampled>P.spreadSampleCap) break outer;
      grid.walk(grid,worldToSrc(p.x,p.y,depth),r,(j,d)=>{
        if(sb.state[j]===0) sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);
      });
    }
  }
  const decay=1-dt*.35;
  for(let i=0;i<sb.h.length;i++) if(sb.h[i]>0) {
    sb.h[i]*=decay;
    if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH) {
      sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i);

    }
  }
  if(stop && p.mass>=p.target)return;
  t102MaterialTail(sb,dt);
    let M=P.spreadSceneFeed?Math.min(sb.burning.length, P.spreadFeedCap):0, feedSources=null;
  if(areaMode){
    if(!sb.burning.length){
      spreadCounters.areaFeedCancelledCredits+=areaFeedCredit; areaFeedCredit=0; M=0;
    } else if(P.spreadSceneFeed){
      feedSources=areaSources(sb);
      const generated=dt*P.spreadAreaFeedRate*(feedSources.total/P.spreadReferenceArea);
      const credit=areaFeedCredit+generated;
      if(!Number.isFinite(credit) || credit<0 || credit>Number.MAX_SAFE_INTEGER-1)
        throw new RangeError('area feed event credit exceeds safe finite integer range');
      spreadCounters.areaFeedCreditsGenerated+=generated;
      const due=Math.floor(credit); M=Math.min(due,P.spreadFeedCap);
      areaFeedCredit=credit-due;
      // Service overflow is dropped, never transferred to later burners. A
      // capacity rejection also consumes its event. Only fractions carry over.
      spreadCounters.areaFeedServiceCapDropped+=due-M;
    }
  }
  for(let m=0;m<M;m++){
    let i,w;
    if(areaMode){
      const chosen=pickAreaSource(feedSources); i=chosen.index; w=chosen.position;
      spreadCounters.areaFeedAttempts++;
    } else {
      sb.emitCursor=(sb.emitCursor+1)%sb.burning.length;
      i=sb.burning[sb.emitCursor]; w=srcToWorld(sceneGauss[i].p);
    }
    let sx,sy,dep2;
    if(P.sliceMode==='view'){ const bx=cam.bx, fh=cam.fh;
      sx=w[0]*bx[0]+w[2]*bx[2]; sy=w[1]; dep2=w[0]*fh[0]+w[2]*fh[2]; }
    else { sx=w[0]; sy=w[1]; dep2=w[2]; }
    let k=Math.round((dep2/P.sliceDepth+0.5)*(N-1)); k=Math.max(0,Math.min(N-1,k));
    const L=layers[k]; if(!L||!L.vic){ if(areaMode) spreadCounters.areaFeedBlocked++; continue; }
    if(P.solver!=='vpm'){                 // VIC: 注入网格温度源 (VPM 无网格, 热量走热种子粒子进混合场)
      const gi2=Math.max(0,Math.min(NX-1,Math.round(gX(sx)))),
            gj2=Math.max(0,Math.min(NY-1,Math.round(gY(sy))));
      const id2=gj2*NX+gi2;
      L.vic.T[id2]=Math.min(1.6, L.vic.T[id2]+dt*P.spreadFeed);
    }
    spreadCounters.sceneFeedAttempts++;
    // P1 recycling is a lossy admission policy, not a conservation operation.
    // Only a full layer may offer a cold, sufficiently old slot. Minimize max(T,Tb)
    // so both temperatures count; exact ties keep the lowest current array index.
    // Discovering a slot does not remove it. The legacy 0.5 admission test must
    // succeed first; area events already encode that rate and have no coin.
    // Blocked legacy attempts consume no RNG, preserving the legacy path.
    const full=t86Global ? layers.reduce((n,l)=>n+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;
    if(full && P.spreadParticlePolicy==='recycle-cold'){
      let coldest=Infinity;
      for(let j=0;j<L.ps.length;j++){
        spreadCounters.sceneRecycleSlotsExamined++;
        const q=L.ps[j];
        if(q.T<0.55 && q.Tb<0.55 && q.life>=P.spreadRecycleMinAge){
          const score=Math.max(q.T,q.Tb);
          if(score<coldest){coldest=score; recycle=j;}
        }
      }
      if(recycle<0) spreadCounters.sceneFeedNoColdSlot++;
      else spreadCounters.sceneFeedRecycleCandidates++;
    }
    if(full && recycle<0){
      spreadCounters.sceneFeedCapacityBlocked++;
      if(areaMode) spreadCounters.areaFeedBlocked++;
    } else if(areaMode || srand()<0.5){
      const sp={ x:sx+(srand()-0.5)*0.04, y:sy+srand()*0.03, G:0,
        T:0.85+srand()*0.15, d:0.8+srand()*0.2, vx:0, vy:0.2, seedp:srand()*99, life:0, sxx:1,sxy:0,syy:1,
        sg:P.eps*0.7071067811865476 };
      sp.Tb=sp.T;
      if(recycle<0) L.ps.push(sp);
      else {
        const old=L.ps[recycle], absG=Math.abs(old.G), c=spreadCounters;
        c.sceneSeedsRecycled++; c.recycledDensitySum+=old.d; c.recycledCirculationSum+=old.G;
        c.recycledAbsCirculationSum+=absG; c.recycledMaxDensity=Math.max(c.recycledMaxDensity,old.d);
        c.recycledMaxAbsCirculation=Math.max(c.recycledMaxAbsCirculation,absG);
        c.recycledSmokeProxySum+=smokeProxy(old);
        c.recycledHotRemoved+=+(old.T>=0.55 || old.Tb>=0.55);
        c.recycledMaxTemperature=Math.max(c.recycledMaxTemperature,old.T);
        c.recycledMaxDynamicTemperature=Math.max(c.recycledMaxDynamicTemperature,old.Tb);
        c.recycledMinAge=c.recycledMinAge===null?old.life:Math.min(c.recycledMinAge,old.life);
        spreadRegion(i).sceneSeedsRecycled++;
        L.ps[recycle]=sp;
      }
      spreadCounters.sceneSeedsEmitted++; spreadRegion(i).sceneSeedsEmitted++;
      if(areaMode) spreadCounters.areaFeedAdmitted++;
    } else spreadCounters.sceneFeedRandomRejected++;
  }
}

function t119Materialize(sb,lightIds,fullIds,steps,dt){
const lightSet=new Set(lightIds), extra=fullIds.filter(id=>!lightSet.has(id)), extraSet=new Set(extra);
const current=sceneBurnState,parentOrder=sb.burning;
    for (const id of extra) {
      if (sb.state[id] !== 0) throw Error('Extra site was not cold at the parent');
      let heat=sb.h[id], fuel=sb.fuel[id], glow=sb.glow[id], char=sb.char_[id];
      for (let t=0; t<steps; ++t) {
        if (heat>0) heat=Math.fround(heat*(1-dt*0.35));
        fuel=Math.fround(fuel-dt/P.spreadBurnT);
        glow=Math.fround(Math.min(1,glow+dt*3));
        char=Math.fround(Math.min(1,char+dt/(P.spreadBurnT*0.85)));
      }
      if (fuel<=0) throw Error('Newly painted site has retired');
      current.h[id]=heat; current.fuel[id]=fuel; current.glow[id]=glow;
      current.char_[id]=char; current.state[id]=1;
    }
    const tail = current.burning.slice(parentOrder.length + lightIds.length);
    current.burning = parentOrder.concat(fullIds, tail.filter(id => !extraSet.has(id)));

}

function t119Guard(parent,lightIds,fullIds,dt) {
  const n=parent.burning.length, quota=P.spreadFeedCap;
  if(dt!==1/60 || P.spreadClockMode!=='elapsed' || P.spreadMeasureMode!=='legacy' || areaFeedCredit!==0 ||
     !P.spreadSceneFeed || !Number.isInteger(quota) || quota<=0 || n<P.spreadFrontierCap ||
     parent.emitCursor<0 || !Number.isInteger(parent.emitCursor))return 0;
  const k=Math.min(90,Math.floor((n-1-parent.emitCursor)/quota)),full=new Set(fullIds);
  if(k<1 || !lightIds.every(id=>full.has(id)) ||
     !fullIds.every(id=>!t90Shell.mask[id] && parent.state[id]===0 && parent.fuel[id]>0))return 0;
  let fuel=Infinity;
  for(const id of parent.burning)fuel=Math.min(fuel,parent.fuel[id]);
  for(const id of fullIds)fuel=Math.min(fuel,parent.fuel[id]);
  for(let i=0;i<k;i++)fuel=Math.fround(fuel-dt/P.spreadBurnT);
  return fuel>0?k:0;
}

function t100Physical() {
  const sb=sceneBurnState;
  function copy(p) {const keys=Object.keys(p).sort();return keys.map(k=>[k,p[k]]);}
  return {frame:researchFrame,simTime,seed:simSeed,draws:researchRandomDraws,tick:vpmTick,
    source:copy(source),pointer:copy(pointer),embers:embers.map(copy),emberAcc,
    material:[sb.h.slice(),sb.fuel.slice(),sb.glow.slice(),sb.char_.slice(),sb.state.slice()],
    frontier:sb.burning.slice(),cursor:sb.emitCursor,
    gas:layers.map(l=>[l.idx,l.seed,l.t,l.acc,l.ps.map(copy)])};
}

function t108Fingerprint(){
  const phys=t100Physical();
  const values=JSON.stringify(phys,(_,v)=>ArrayBuffer.isView(v)?Array.from(v):v);
  let hash=2166136261;
  for(let k=0;k<values.length;k++){hash^=values.charCodeAt(k);hash=Math.imul(hash,16777619);}
  return {length:values.length,fnv32:(hash>>>0).toString(16).padStart(8,'0'),marker:__t86.marker()};
}
