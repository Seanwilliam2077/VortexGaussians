// Inject in the pinned native solver closure. No simulation state is changed.
function t91Estimate(shellIds, dt = 1/60, useSampling = true) {
  if (dt !== 1/60 || P.solver !== 'vpm' || P.dimMode !== 'layer' ||
      P.simLayers !== layers.length || P.layers !== layers.length || P.sliceMode !== 'world' ||
      P.emitterOn || !P.spreadOn || !P.spreadFlameHeat ||
      P.sceneScale !== 1 || P.sceneYaw !== 0 || P.scenePitch !== 0 ||
      !(P.cool >= 0 && P.spreadHeat >= 0 && P.spreadIgnR > 0 && P.spreadIgnH > 0) ||
      !Number.isSafeInteger(P.spreadSampleCap) || P.spreadSampleCap < 1) {
    throw Error('T91 operator outside its one-step contract');
  }
  const sb = sceneBurnState, radius = P.spreadIgnR, decay = 1-dt*.35;
  const cap = P.spreadSampleCap, pad = 1e-9;
  const travel = dt*4.000002 + pad;
  const ids = [], low = [], high = [];
  const x = [], y = [], z = [], lowerBox = [Infinity,Infinity,Infinity], upperBox = [-Infinity,-Infinity,-Infinity];
  for (const i of shellIds) {
    if (sb.state[i] !== 0 || sb.fuel[i] <= 0) continue;
    if (Math.fround(sb.h[i]*decay) >= P.spreadIgnH) return {decision:'yes', witness:i};
    const q = sceneGauss[i].p;
    for (let j=0;j<3;j++) {
      if (!(Math.abs(q[j]) < 1024)) throw Error('T91 scene coordinates outside padding contract');
      lowerBox[j] = Math.min(lowerBox[j],q[j]);
      upperBox[j] = Math.max(upperBox[j],q[j]);
    }
    ids.push(i); x.push(q[0]); y.push(q[1]); z.push(q[2]);
    low.push(sb.h[i]); high.push(sb.h[i]);
  }
  if (!ids.length) return {decision:'no',witness:null};
  // Apply contributions in native layer and stable Morton order. In no-rank
  // mode only the upper sum is used, so an arbitrary order would not in
  // general bound the native sequence of binary32 writes.
  function deposit(p, temperature, depth, guaranteed) {
    const center = worldToSrc(p.x,p.y,depth), [cx,cy,cz] = center;
    const support = radius+travel+pad;
    if (cx < lowerBox[0]-support || cx > upperBox[0]+support ||
        cy < lowerBox[1]-support || cy > upperBox[1]+support ||
        cz < lowerBox[2]-radius-pad || cz > upperBox[2]+radius+pad) return null;
    const gain = dt*P.spreadHeat*temperature;
    for (let j=0;j<ids.length;j++) {
      const dx=x[j]-cx, dy=y[j]-cy, dz=z[j]-cz;
      if (Math.abs(dz)>radius+pad || Math.abs(dx)>support || Math.abs(dy)>support) continue;
      const xy=Math.sqrt(dx*dx+dy*dy);
      const nearestXY=Math.max(0,xy-travel);
      const near=Math.max(0,Math.sqrt(nearestXY*nearestXY+dz*dz)-pad);
      if (near>radius) continue;
      high[j] = Math.fround(high[j]+Math.max(0,gain*(1-near/radius))+pad);
      if (guaranteed) {
        const farXY=xy+travel, far=Math.sqrt(farXY*farXY+dz*dz)+pad;
        if (far<radius) {
          low[j]=Math.fround(low[j]+Math.max(0,gain*(1-far/radius)-pad));
          if (Math.fround(low[j]*decay) >= P.spreadIgnH) return ids[j];
        }
      }
    }
    return null;
  }
  let minEarlier=0, maxEarlier=0;
  for (const layer of layers) {
    if (minEarlier>=cap && useSampling) break;
    const ps = layer.ps, n=ps.length;
    const order={code:new Uint32Array(n), ord:new Uint32Array(n), tmp:new Uint32Array(n), cnt256:new Uint32Array(256)};
    for (let i=0;i<n;i++) order.code[i]=vpmMorton(ps[i].x,ps[i].y);
    vpmSort(order,n);
    // Cell r bounds previous hot samples over all paths with r survivors
    // modulo seven in this layer. At layer boundaries only heat count carries.
    let min=new Float64Array(7).fill(Infinity), max=new Float64Array(7).fill(-Infinity);
    let nextMin=new Float64Array(7), nextMax=new Float64Array(7);
    min[0]=minEarlier; max[0]=maxEarlier;
    const depth = (layers.length>1 ? layer.idx/(layers.length-1)-.5 : 0)*P.sliceDepth;
    for (const index of order.ord) {
      const p=ps[index], temp=p.T-dt*P.cool*p.T*p.T, density=p.d*(1-dt*.3);
      if (!(Math.abs(p.x)<1024 && Math.abs(p.y)<1024 && temp>=0 && temp<=1)) throw Error('T91 carrier range');
      if (temp<=.04 || density<=.03 || p.y-travel>=WY || Math.abs(p.x)-travel>=WX*.7) continue;
      const survives=p.y+travel<WY && Math.abs(p.x)+travel<WX*.7;
      const hot=temp>=.55;
      if (hot && (!useSampling || min[0]<cap)) {
        let certain=useSampling && survives && max[0]<cap;
        for (let r=1;certain && r<7;r++) if (min[r]!==Infinity) certain=false;
        const hit=deposit(p,temp,depth,certain);
        if (hit!==null) return {decision:'yes',witness:hit};
      }
      if (!useSampling) continue;
      nextMin.fill(Infinity); nextMax.fill(-Infinity);
      for (let r=0;r<7;r++) {
        if (min[r]===Infinity) continue;
        const s=(r+1)%7, extra=(r===0 && hot) ? 1 : 0;
        nextMin[s]=Math.min(nextMin[s],min[r]+extra);
        nextMax[s]=Math.max(nextMax[s],max[r]+extra);
        if (!survives) {
          nextMin[r]=Math.min(nextMin[r],min[r]);
          nextMax[r]=Math.max(nextMax[r],max[r]);
        }
      }
      [min,nextMin]=[nextMin,min]; [max,nextMax]=[nextMax,max];
    }
    minEarlier=Math.min(...min); maxEarlier=Math.max(...max);
  }
  for (const upper of high) if (Math.fround(upper*decay)>=P.spreadIgnH) return {decision:'abstain',witness:null};
  return {decision:'no',witness:null};
}
