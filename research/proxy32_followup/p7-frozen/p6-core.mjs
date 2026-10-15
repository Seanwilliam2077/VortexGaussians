// Standard exact compact-support neighbor enumeration; no approximation.
import {performance} from 'node:perf_hooks';
const positive=x=>Number.isFinite(x)&&x>0;
export function pack(input,params){
  if(!Number.isInteger(input.surfaceCount)||input.surfaceCount<0||input.surfaceCount>input.nodes.length)throw new Error('surfaceCount');
  if(!positive(params.h)||!positive(params.beta))throw new Error('kernel parameters');
  const n=input.nodes.length,p=new Float64Array(3*n),measure=new Float64Array(n),capacity=new Float64Array(n),initial=new Float64Array(n),ids=new Set();
  input.nodes.forEach((v,i)=>{if(typeof v.id!=='string'||!v.id.trim()||ids.has(v.id)||!Array.isArray(v.position)||v.position.length!==3||v.position.some(x=>!Number.isFinite(x)||!Number.isSafeInteger(Math.floor(x/params.h))||Math.abs(Math.floor(x/params.h))>=Number.MAX_SAFE_INTEGER)||!positive(v.measure)||!positive(v.capacityPerMeasure)||!positive(v.capacity)||v.capacity!==v.measure*v.capacityPerMeasure||!Number.isFinite(v.temperature)||v.temperature<0||v.kind!==(i<input.surfaceCount?'surface':'gas'))throw new Error('invalid node');ids.add(v.id);p.set(v.position,3*i);measure[i]=v.measure;capacity[i]=v.capacity;initial[i]=v.temperature;});
  return {n,ns:input.surfaceCount,ng:n-input.surfaceCount,p,measure,capacity,initial,h:params.h,beta:params.beta};
}
const key=(x,y,z)=>`${x},${y},${z}`;
function makeIndex(a){const buckets=new Map();for(let j=0;j<a.ng;j++){const p=3*(a.ns+j),k=key(Math.floor(a.p[p]/a.h),Math.floor(a.p[p+1]/a.h),Math.floor(a.p[p+2]/a.h));let b=buckets.get(k);if(!b){b=[];buckets.set(k,b);}b.push(j);}return buckets;}
export function buildGraph(a,method){
  if(!['allpairs','hash'].includes(method))throw new Error('unknown builder');
  const start=performance.now(),buckets=method==='hash'?makeIndex(a):null,indexEnd=performance.now();
  const rowOffsets=new Uint32Array(a.ns+1),candidate=new Uint32Array(a.ng),cellCandidates=new Map();
  let candidateCacheEntries=0,candidateCacheHits=0;
  let candidatePairsPerPass=0,boundaryPairs=0,boundaryConductance=0,edgeCount=0;
  const normalization=3/(Math.PI*a.h*a.h*a.h);
  if(!positive(normalization))throw new Error('kernel normalization overflow');
  if(!buckets)for(let j=0;j<a.ng;j++)candidate[j]=j;
  function candidates(i){if(!buckets)return candidate;
    const p=3*i,cx=Math.floor(a.p[p]/a.h),cy=Math.floor(a.p[p+1]/a.h),cz=Math.floor(a.p[p+2]/a.h),cell=key(cx,cy,cz),cached=cellCandidates.get(cell);if(cached){candidateCacheHits++;return cached;}let count=0;
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){const b=buckets.get(key(cx+x,cy+y,cz+z));if(b)for(const j of b)candidate[count++]=j;}
    const list=candidate.slice(0,count);list.sort();cellCandidates.set(cell,list);candidateCacheEntries+=count;return list;
  }
  function distance(i,j){const s=3*i,g=3*(a.ns+j),dx=a.p[s]-a.p[g],dy=a.p[s+1]-a.p[g+1],dz=a.p[s+2]-a.p[g+2];return Math.sqrt((dx*dx+dy*dy)+dz*dz);}
  for(let i=0;i<a.ns;i++){const list=candidates(i);candidatePairsPerPass+=list.length;for(const j of list)if(distance(i,j)<a.h)edgeCount++;if(edgeCount>0xffffffff)throw new Error('CSR edge index overflow; no truncation');rowOffsets[i+1]=edgeCount;}
  const countEnd=performance.now(),gasIndex=new Uint32Array(edgeCount),conductance=new Float64Array(edgeCount),sumG=new Float64Array(a.n),neighborCount=new Uint32Array(a.n);
  let e=0;
  for(let i=0;i<a.ns;i++){const list=candidates(i);for(const j of list){const g=a.ns+j,r=distance(i,j),band=Math.abs(r-a.h)<=8*Number.EPSILON*Math.max(a.h,r);if(band)boundaryPairs++;if(r>=a.h)continue;
      const G=a.beta*a.measure[i]*a.measure[g]*(normalization*(1-r/a.h));if(!positive(G))throw new Error('invalid conductance');
      gasIndex[e]=j;conductance[e++]=G;sumG[i]+=G;sumG[g]+=G;neighborCount[i]++;neighborCount[g]++;if(band)boundaryConductance+=G;
  }}
  if(e!==edgeCount)throw new Error('two-pass edge mismatch');let maxRate=0;for(let i=0;i<a.n;i++){maxRate=Math.max(maxRate,sumG[i]/a.capacity[i]);if(!Number.isFinite(maxRate))throw new Error('rate overflow');}
  const end=performance.now();
  return {rowOffsets,gasIndex,conductance,sumG,neighborCount,maxRate,edgeCount,
    work:{candidatePairsPerPass,distanceEvaluations:2*candidatePairsPerPass,conductanceEvaluations:edgeCount,indexedGasNodes:buckets?a.ng:0,occupiedBuckets:buckets?.size??0,bucketLookups:cellCandidates.size*27,candidateCacheCells:cellCandidates.size,candidateCacheEntries,candidateCacheHits,boundaryPairs,boundaryConductance},
    memory:{graphTypedArrayBytes:rowOffsets.byteLength+gasIndex.byteLength+conductance.byteLength+sumG.byteLength+neighborCount.byteLength,candidateScratchBytes:candidate.byteLength,candidateCacheTypedArrayBytes:candidateCacheEntries*4,indexEntries:buckets?a.ng:0,indexBuckets:buckets?.size??0,indexHeapBytes:null,scope:'Exact owned typed-array payloads, not process peak memory; Map/string/object allocator overhead is not estimated.'},
    timing:{indexBuildMs:indexEnd-start,countPassMs:countEnd-indexEnd,fillAndDegreeMs:end-countEnd,buildMs:end-start}};
}
function add(sum,c,i,value){const y=value-c[i],next=sum[i]+y;c[i]=(next-sum[i])-y;sum[i]=next;}
function energy(a,T){const sums=[0,0],c=[0,0];for(let i=0;i<a.n;i++)add(sums,c,i<a.ns?0:1,a.capacity[i]*T[i]);return {surface:sums[0],gas:sums[1],total:sums[0]+sums[1]};}
export function exchange(a,graph,temperatures,params){
  const {dt,safety,maxSubsteps}=params;if(!Number.isFinite(dt)||dt<0||!positive(safety)||safety>1||!Number.isSafeInteger(maxSubsteps)||maxSubsteps<1)throw new Error('step parameters');
  if(!(temperatures instanceof Float64Array)||temperatures.length!==a.n||temperatures.some(x=>!Number.isFinite(x)||x<0))throw new Error('temperatures');
  const substeps=Math.max(1,Math.ceil(dt*graph.maxRate/safety));if(!Number.isSafeInteger(substeps)||substeps>maxSubsteps)throw new Error('substep overflow');
  const substepDt=dt/substeps,delta=new Float64Array(a.n),correction=new Float64Array(a.n),flux=[0,0],fluxCorrection=[0,0],Ebefore=energy(a,temperatures);
  for(let s=0;s<substeps;s++){delta.fill(0);correction.fill(0);for(let i=0;i<a.ns;i++)for(let e=graph.rowOffsets[i];e<graph.rowOffsets[i+1];e++){const j=a.ns+graph.gasIndex[e],Q=substepDt*graph.conductance[e]*(temperatures[j]-temperatures[i]);add(delta,correction,i,Q);add(delta,correction,j,-Q);add(flux,fluxCorrection,0,Q);add(flux,fluxCorrection,1,-Q);}
    for(let i=0;i<a.n;i++){temperatures[i]+=delta[i]/a.capacity[i];if(!Number.isFinite(temperatures[i])||temperatures[i]<0)throw new Error('updated temperature invalid');}
  }
  const Eafter=energy(a,temperatures);if(!Number.isFinite(Eafter.total))throw new Error('energy overflow');
  return {dt,safety,maxRate:graph.maxRate,substeps,substepDt,maxCfl:substepDt*graph.maxRate,edgeEvaluations:substeps*graph.edgeCount,Ebefore,Eafter,netSurface:flux[0],netGas:flux[1],energyChangeSurface:Eafter.surface-Ebefore.surface,energyChangeGas:Eafter.gas-Ebefore.gas,energyResidual:Eafter.total-Ebefore.total,workspaceTypedArrayBytes:delta.byteLength+correction.byteLength};
}
export function edgeTriples(a,g){const edges=[];for(let i=0;i<a.ns;i++)for(let e=g.rowOffsets[i];e<g.rowOffsets[i+1];e++)edges.push([i,a.ns+g.gasIndex[e],g.conductance[e]]);return edges;}
