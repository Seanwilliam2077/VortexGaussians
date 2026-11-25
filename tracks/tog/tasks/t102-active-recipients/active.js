// Cache only geometry/operators from the known immutable base, never speculative state.
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

function t102ResetBranch(){
  const c=t102Context;if(!c)throw Error('No T102 session');
  c.rows=new Map();c.grid=c.anchor?.grid??null;c.stats.branch_resets++;
}

const t102Previous=window.__t90.query;
window.__t90.query=function(method,h,dt){
  if(method!=='active-fresh' && method!=='active-anchor')return t102Previous(method,h,dt);
  const start=performance.now(),previous=stepSpread;
  t102Start(method,dt);stepSpread=t102Spread;
  let result;
  try {result=t102Previous('rank-only',h,dt);}
  finally {
    stepSpread=previous;
    const stats=t102Stop();
    if(result){result.cache_build=stats;result.active_stats=stats;result.cache_rows=stats.branch_rows;}
  }
  result.browser_ms=performance.now()-start;
  return result;
};
