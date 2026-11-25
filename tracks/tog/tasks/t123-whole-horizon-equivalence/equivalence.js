// The query asks only for the exterior outcome. Equal exterior trajectories need no physical fork at H.
window.__t123 = function (method, dt, picks, cameras) {
  if (!method.startsWith('equiv-')) return __t119.action(method, dt, picks, cameras);
  const mode=method.slice('equiv-'.length);
  if (!['ordinary','repair'].includes(mode)) throw Error('Unknown equivalence backend');
  const start=performance.now(), parent=sceneBurnState, deadline=90;
  const upper=Math.floor((parent.burning.length-1-parent.emitCursor)/P.spreadFeedCap);
  let certified=0, nfull=0;
  const centered=picks[0].world.every((v,i)=>v===picks[1].world[i]);
  if (upper>=deadline && centered && picks[0].radius<=picks[1].radius) {
    const footprint=pick=>{
      __t98.resetTrial();
      try { return __t86.ignite(pick,true).ids; }
      finally { __t98.finishTrial(); }
    };
    const full=footprint(picks[1]), light=footprint(picks[0]);
    __t90.configure({...picks[1],radius:.12});
    nfull=full.length;certified=t119Guard(parent,light,full,dt);
  }
  const proof_ms=performance.now()-start;
  if (certified<deadline) {
    const r=__t119.action('cold-'+mode,dt,picks,cameras);
    r.equivalence={admitted:false,upper,proof_ms,physical_attempts:r.tried.length,inferred:[]};
    r.total_browser_ms=performance.now()-start;
    return r;
  }
  const light=t119Cold(true,false,()=>t111Sibling(mode,dt,picks[0],cameras));
  const tried=[light], choices={}, remaining=[];
  for (const v of light.views) {
    choices[v.camera]=!v.defined?'undefined':v.first_frame!==null?'L':'none';
    if (v.defined && v.first_frame===null) remaining.push({...v});
  }
  if (remaining.length) tried.push({pick:'F',clicked:nfull,inferred:true,views:remaining});
  return {tried,choices,total_browser_ms:performance.now()-start,
    equivalence:{admitted:true,upper,certified,proof_ms,physical_attempts:1,inferred:remaining.map(v=>v.camera)}};
};
