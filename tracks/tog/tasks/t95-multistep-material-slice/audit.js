// Untimed cross-check. This function restores the original live branch in both passes.
function t95Audit(ids, mask, dt) {
  const checks=[4,8].map(h=>({h,qualified:!!t95Open(ids,mask,h,dt)}));
  const horizons=checks.filter(x=>x.qualified).map(x=>x.h);
  const result={cut:researchFrame,checks,horizon:Math.max(0,...horizons),frames:[],event:null};
  if (!result.horizon) return result;
  const cold=ids.filter(id=>sceneBurnState.state[id]===0 && sceneBurnState.fuel[id]>0);
  const expected=[];
  const normal=t90Fork();
  try {
    // A full native step also does off-region graph, fuel and emission work.
    t90Query=null;
    for(let k=1;k<result.horizon;k++) {
      updateCam(cv.width/Math.max(1,cv.height)); simTime+=dt;
      stepAll(dt); researchFrame++;
      const sb=sceneBurnState, hit=cold.filter(i=>sb.state[i]!==0);
      if(hit.length) {expected.push({hit});break;}
      const gas=layers.map(l=>({idx:l.idx,t:l.t,acc:l.acc,ps:l.ps.map(p=>({...p}))}));
      expected.push({gas, heat:Float32Array.from(cold,i=>sb.h[i]), fuel:Float32Array.from(cold,i=>sb.fuel[i]),
        cursor:sb.emitCursor,draws:researchRandomDraws,offers:sb.burning.slice(sb.emitCursor-P.spreadFeedCap+1,sb.emitCursor+1)});
    }
  } finally {
    t90Restore(normal);
  }
  const sliced=t90Fork();
  try {
    const plan=t95Open(ids,mask,result.horizon,dt);
    if(!plan) throw Error('T95 guard changed on fork');
    for(const [idx,ref] of expected.entries()) {
      const hit=t95Advance(plan,dt); researchFrame++;
      if(ref.hit) {
        if(hit===null || !ref.hit.includes(hit)) throw Error('T95 regional witness mismatch');
        result.event={offset:idx+1,witness:hit};
        break;
      }
      if(hit!==null) throw Error('T95 unexpected regional event');
      const sb=sceneBurnState;
      if(sb.emitCursor!==ref.cursor || researchRandomDraws!==ref.draws) throw Error('T95 cursor or RNG');
      const offers=sb.burning.slice(sb.emitCursor-P.spreadFeedCap+1,sb.emitCursor+1);
      if(offers.length!==P.spreadFeedCap || ref.offers.length!==P.spreadFeedCap ||
          offers.some((id,i)=>id!==ref.offers[i])) throw Error('T95 ordered emitter offers');
      for(const [i,id] of cold.entries()) {
        if(sb.state[id]!==0 || !Object.is(ref.heat[i],sb.h[id]) || !Object.is(ref.fuel[i],sb.fuel[id]))
          throw Error('T95 cold heat/fuel/state diverged at site '+id);
      }
      let particles=0, fields=0;
      for(const [k,l] of layers.entries()) {
        const target=ref.gas[k];
        if(l.idx!==target.idx || !Object.is(l.t,target.t) || !Object.is(l.acc,target.acc) ||
            l.ps.length!==target.ps.length) throw Error('T95 layer or population mismatch');
        for(let n=0;n<l.ps.length;n++) {
          const p=l.ps[n], q=target.ps[n], names=Object.keys(q);
          if(Object.keys(p).length!==names.length) throw Error('T95 particle fields missing');
          for(const key of names) if(!Object.hasOwn(p,key) || !Object.is(p[key],q[key]))
            throw Error('T95 particle disagreement '+k+'/'+n+'/'+key);
          particles++; fields+=names.length;
        }
      }
      result.frames.push({offset:idx+1,particles,particle_fields:fields,recipient_states:cold.length,
        cursor:ref.cursor,random_draws:ref.draws,ordered_offers:offers.length});
    }
  } finally {
    t90Restore(sliced);
  }
  return result;
}
