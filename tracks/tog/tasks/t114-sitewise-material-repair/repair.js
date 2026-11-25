// Closure plugin for T108/T111. Only called for complete certified blocks.
function t114Transpose(sb,dt) {
  const n=sb.state.length,counts=new Uint32Array(n+1),rows=[],ctx=t102Context,rr=P.spreadR;
  if(!ctx || sb.burning.length<P.spreadFrontierCap)throw Error('Missing qualified donor context');
  let grid=ctx.grid,edges=0,built=0,createdRowBytes=0;
  for(let k=0;k<P.spreadFrontierCap;k++) {
    const donor=sb.burning[k];
    let row=ctx.rows.get(donor)??ctx.anchor?.rows.get(donor);
    if(!row){
      if(!grid)grid=t102Index(sb.state,rr);
      row=t102Row(donor,grid,sb.state,rr,dt);built++;createdRowBytes+=row.ids.byteLength+row.heat.byteLength;
    }
    rows.push(row);
    for(let e=0;e<row.n;e++)if(sb.state[row.ids[e]]===0){counts[row.ids[e]+1]++;edges++;}
  }
  for(let i=1;i<=n;i++)counts[i]+=counts[i-1];
  const cursor=counts.slice(0,n),heat=new Float64Array(edges);
  for(const row of rows)for(let e=0;e<row.n;e++) {
    const id=row.ids[e];if(sb.state[id]===0)heat[cursor[id]++]=row.heat[e];
  }
  return {offset:counts,heat,built,edges,bytes:counts.byteLength+cursor.byteLength+heat.byteLength+createdRowBytes};
}

// Clock stores saturate independently. Equal initial binary32 values with the same
// step count have precisely the same final binary32 result.
function t114ClockCache(delta,decrease) {
  const caches=new Map();
  return function update(initial,n) {
    if(!n || (!decrease && initial===1))return initial;
    let map=caches.get(n);if(!map){map=new Map();caches.set(n,map);}
    if(map.has(initial))return map.get(initial);
    let current=initial;
    for(let k=0;k<n;k++) {
      current=decrease?Math.max(0,Math.fround(current-delta)):Math.fround(Math.min(1,current+delta));
      if(current===(decrease?0:1))break;
    }
    map.set(initial,current);return current;
  };
}

function t114Sitewise(logs,dt,profile) {
  const sb=sceneBurnState,n=sb.state.length,L=logs.length,r=P.spreadIgnR,decay=1-dt*.35;
  if(!L || L>180)throw Error('Unexpected block size');
  const start=performance.now(),graph=t114Transpose(sb,dt),afterGraph=performance.now();
  const ended=new Uint16Array(n),born=new Uint16Array(n),buckets=Array.from({length:L},()=>[]);
  const st={frames:L,sites:n,old_burning:sb.burning.length,graph_edges:graph.edges,noncached_donor_rows:graph.built,
    typed_scratch_bytes:graph.bytes+ended.byteLength+born.byteLength,graph_ms:afterGraph-start,
    samples:0,hit_calls:0,flame_writes:0,graph_writes:0,positive_decays:0,site_frames:0,
    old_positive:0,cold_only_flame_touched:0,clock_sites:0,added_sites:0};
  const touched=profile?new Uint8Array(n):null;
  if(profile)for(const heat of sb.h)if(heat>0)st.old_positive++;
  function advance(i,until) {
    const from=ended[i];if(until===from)return;
    const lo=graph.offset[i],hi=graph.offset[i+1];
    let heat=sb.h[i],state=sb.state[i];
    // With no heat or graph source, all skipped stores would leave zero unchanged.
    if(!heat && (lo===hi || state!==0)){ended[i]=until;return;}
    let graphWrites=0,decays=0;
    for(let frame=from;frame<until;frame++) {
      if(heat>0) {
        heat=Math.fround(heat*decay);decays++;
        if(state===0 && sb.fuel[i]>0 && heat>=P.spreadIgnH){state=1;born[i]=frame+1;}
      }
      if(state===0 && hi>lo){
        for(let j=lo;j<hi;j++)heat=Math.fround(heat+graph.heat[j]);graphWrites+=hi-lo;
      }
    }
    sb.h[i]=heat;sb.state[i]=state;ended[i]=until;
    if(profile){st.graph_writes+=graphWrites;st.positive_decays+=decays;st.site_frames+=until-from;}
  }
  for(let k=0;k<L;k++) {
    const frame=logs[k],data=frame.values;
    st.samples+=frame.count;
    for(let j=0;j<4*frame.count;j+=4) {
      const pos=[data[j],data[j+1],data[j+2]],T=data[j+3];
      hashQuery(pos,r,(id,d)=>{
        if(profile)st.hit_calls++;
        if(sb.state[id]!==0)return;
        advance(id,k);
        if(sb.state[id]!==0)return;
        sb.h[id]+=dt*P.spreadHeat*T*(1-d/r);
        if(profile){st.flame_writes++;if(!touched[id]){touched[id]=1;st.cold_only_flame_touched++;}}
      });
    }
  }
  const afterFlame=performance.now();
  const fuel=t114ClockCache(dt/P.spreadBurnT,true),glow=t114ClockCache(dt*3,false),
    charred=t114ClockCache(dt/(P.spreadBurnT*.85),false);
  const old=sb.burning;
  function clock(id,steps) {
    sb.fuel[id]=fuel(sb.fuel[id],steps);
    if(sb.fuel[id]<=0){sb.state[id]=2;sb.glow[id]=0;sb.char_[id]=1;}
    else {sb.glow[id]=glow(sb.glow[id],steps);sb.char_[id]=charred(sb.char_[id],steps);}
    st.clock_sites++;
  }
  for(const i of old)clock(i,L);
  for(let i=0;i<n;i++){
    if(sb.h[i]>0 || graph.offset[i]!==graph.offset[i+1])advance(i,L);
    const at=born[i];
    if(at){clock(i,L-at+1);if(sb.state[i]===1)buckets[at-1].push(i);st.added_sites++;}
  }
  // Existing donors survive by the guard, and new IDs are ordered exactly as the
  // native ascending threshold scan within each frame.
  if(old.some(id=>sb.state[id]!==1))throw Error('Old donor survival guard violated');
  for(const bucket of buckets)for(const id of bucket)old.push(id);
  sb.emitCursor=logs[L-1].cursor;
  st.flame_ms=afterFlame-afterGraph;st.finish_ms=performance.now()-afterFlame;
  st.profile_counts=profile;return st;
}

function t114Repair(mode,logs,dt,profile=false) {
  if(mode==='sitewise')return t114Sitewise(logs,dt,profile);
  if(mode==='sparse'){
    t106Start();
    try{for(const frame of logs)t106Replay(frame,dt);}
    finally{var sparse=t106Stop();}
    return {frames:logs.length,sparse};
  }
  if(mode!=='repair')throw Error('Unregistered reconstruction');
  for(const frame of logs)t100ReplayActive(frame,dt);
  return {frames:logs.length};
}
