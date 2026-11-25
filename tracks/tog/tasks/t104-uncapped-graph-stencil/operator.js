let t104Index=null;
function t104Domain() {
  const n=sceneGauss.length,start=performance.now();
  let buildMs=0;
  if(!t104Index || t104Index.scene!==sceneGauss || t104Index.radius!==P.spreadR) {
    const xyz=new Float64Array(3*n);
    for(let i=0;i<n;i++)xyz.set(sceneGauss[i].p,i*3);
    const s=searchGraph(xyz,P.spreadR,{deadline:performance.now()+180000,limit:1e9,tests:0});
    const components=new Int32Array(n);
    let label=0;
    for(let i=0;i<n;i++)if(s.seen[i]<0) {
      for(const j of s.expand([i]).nodes)components[j]=label;
      label++;
    }
    t104Index={scene:sceneGauss,radius:P.spreadR,components,label};
    buildMs=performance.now()-start;
  }
  const {components,label}=t104Index, selected=new Uint8Array(label),inc=new Uint8Array(n), ids=[];
  for(const id of t90Shell.ids)selected[components[id]]=1;
  for(let i=0;i<n;i++)if(selected[components[i]]){inc[i]=1;ids.push(i);}
  return {ids,inc,buildMs,membershipMs:performance.now()-start-buildMs,indexBytes:components.byteLength};
}
function t104Plan(domain,h,dt) {
  const sb=sceneBurnState,n=sb.burning.length,cap=P.spreadFeedCap;
  if(P.spreadFrontierCap<sceneGauss.length || !cap || !t86Global)throw Error('Unexpected service configuration');
  if(n<cap)return {...domain,length:0,local:[]};
  let fuel=Infinity;
  for(const id of sb.burning)fuel=Math.min(fuel,sb.fuel[id]);
  const limit=Math.min(h,Math.floor((n-1-sb.emitCursor)/cap));
  let length=0;while(length<limit) {
    fuel=Math.fround(fuel-dt/P.spreadBurnT);
    if(fuel<=0)break;
    length++;
  }
  return {...domain,length,local:sb.burning.filter(i=>domain.inc[i])};
}
function t104ScopedStep(plan,dt,statistics,finish=false) {
  updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);
  const sb=sceneBurnState,N=layers.length,r=P.spreadIgnR,decay=1-dt*.35;
  let sampled=0;
  outer:for(const L of layers) {
    const z=(L.idx/(N-1)-.5)*P.sliceDepth;
    for(let i=0;i<L.ps.length;i+=7) {
      const p=L.ps[i];if(p.T<.55)continue;
      if(++sampled>P.spreadSampleCap)break outer;
      hashQuery(worldToSrc(p.x,p.y,z),r,(j,d)=>{
        if(plan.inc[j] && sb.state[j]===0)sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);
      });
    }
  }
  let witness=null;
  for(const i of plan.ids)if(sb.h[i]>0){
    sb.h[i]*=decay;
    if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH) {
      sb.state[i]=1;plan.local.push(i);statistics.new_local++;
      if(witness===null && t90Shell.mask[i]){
        witness=i;
        if(!finish){researchFrame++;return i;}
      }
    }
  }
  const oldSources=sb.burning;
  sb.burning=plan.local;
  statistics.local_donor_steps+=plan.local.length;
  t102MaterialTail(sb,dt);plan.local=sb.burning;sb.burning=oldSources;
  t95Feed(dt);researchFrame++;
  return witness;
}
function t104Full(h,dt,backend) {
  const live=t90Fork(),q=t90Query={mask:t90Shell.mask,witness:-1};
  let stats,k=0;
  try {
    t102Start(backend,dt);
    while(k<h && q.witness<0){
      updateCam(cv.width/Math.max(1,cv.height));simTime+=dt;t95FullGas(dt);
      t102Spread(dt);researchFrame++;k++;
    }
    return {first:q.witness<0?null:researchFrame,witness:q.witness<0?null:q.witness,steps:k};
  } finally {try{stats=t102Stop();}finally{t90Restore(live);}t104LastFull=stats;}
}
let t104LastFull=null;
function t104Measure(method,h,dt,pick) {
  const start=performance.now(),edit=__t86.ignite(pick,true),click=performance.now();
  __t90.configure(pick);const afterRegion=performance.now();
  const scoped=method.startsWith('component-'),backend=method.endsWith('-fresh')?'active-fresh':'active-anchor';
  const domain=scoped?t104Domain():null;
  const stats={click_ms:click-start,shell_ms:afterRegion-click,index_build_ms:domain?.buildMs||0,
    index_bytes:domain?.indexBytes||0,membership_ms:domain?.membershipMs||0,domain:domain?.ids.length??null,
    eligible:0,scoped_steps:0,new_local:0,local_donor_steps:0,fallback:null,guard_ms:0};
  let first=null,witness=null,ordinary=0;
  if(domain && domain.ids.length<sceneGauss.length) {
    const t=performance.now(),plan=t104Plan(domain,h,dt);
    stats.guard_ms=performance.now()-t;stats.eligible=plan.length;
    if(plan.length) {
      const live=t90Fork();
      try {
        t102Start(backend,dt);
        for(let k=0;k<plan.length;k++){
          witness=t104ScopedStep(plan,dt,stats);stats.scoped_steps++;
          if(witness!==null){first=researchFrame;break;}
        }
      } finally {try{stats.scoped_backend=t102Stop();}finally{t90Restore(live);}}
    }
    if(first===null && plan.length<h)stats.fallback=plan.length?'expired':'zero-guard';
  } else stats.fallback=scoped?'whole-component':'ordinary';
  if(stats.fallback) {
    const r=t104Full(h,dt,backend);first=r.first;witness=r.witness;ordinary=r.steps;stats.ordinary_backend=t104LastFull;
  }
  return {method,first,witness,ordinary,clicked:edit.count,stats,browser_ms:performance.now()-start};
}
function t104Capture(domain,local) {
  const sb=sceneBurnState;
  return {frame:researchFrame,draws:researchRandomDraws,cursor:sb.emitCursor,
    gas:layers.map(l=>({idx:l.idx,t:l.t,acc:l.acc,ps:l.ps.map(p=>({...p}))})),
    frontier:[...(local??sb.burning.filter(i=>domain.inc[i]))],
    material:['h','fuel','glow','char_','state'].map(k=>domain.ids.map(i=>sb[k][i]))};
}
function t104Assert(a,b,key='state') {
  if(typeof a!=='object'||a===null){if(!Object.is(a,b))throw Error('T104 mismatch '+key);return;}
  const keys=Object.keys(a);
  if(!b || keys.length!==Object.keys(b).length)throw Error('T104 length at '+key);
  for(const k of keys)t104Assert(a[k],b[k],key+'.'+k);
}
function t104Audit(pick,dt) {
  const edit=__t86.ignite(pick,true);__t90.configure(pick);
  const domain=t104Domain(),plan=t104Plan(domain,8,dt);
  if(domain.ids.length===sceneGauss.length || !plan.length)return {frames:0,domain:domain.ids.length,length:plan.length};
  const result={frames:0,domain:domain.ids.length,length:plan.length,particles:0,material_values:0,
    new_local:0,local_donor_steps:0,old_donors_above_1400:sceneBurnState.burning.slice(1400).filter(i=>domain.inc[i]).length};
  const saved=[],events=[],live=t90Fork();
  try{
    t102Start('active-anchor',dt);
    for(let k=0;k<plan.length;k++) {
      const id=t104ScopedStep(plan,dt,result,true);
      saved.push(t104Capture(domain,plan.local));events.push(id);
      if(id!==null)break;
    }
  } finally {try{t102Stop();}finally{t90Restore(live);}}
  for(let k=0;k<saved.length;k++){
    const [row]=__t86.frames(researchFrame+1,dt),native=t104Capture(domain);
    t104Assert(saved[k],native);
    const hits=row.new_ids.filter(i=>t90Shell.mask[i]);
    if((events[k]===null)!==(hits.length===0) || events[k]!==null && !hits.includes(events[k]))throw Error('Audit witness mismatch');
    result.frames++;result.particles+=row.gas_count;result.material_values+=5*domain.ids.length;
  }
  return result;
}
window.__t104={measure:t104Measure,audit:t104Audit};
