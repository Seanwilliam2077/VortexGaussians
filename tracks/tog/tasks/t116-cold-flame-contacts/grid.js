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
