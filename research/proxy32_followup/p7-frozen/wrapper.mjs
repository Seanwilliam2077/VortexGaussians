import {performance} from 'node:perf_hooks';
import {pack,buildGraph,exchange} from './p6-core.mjs';
import {CONFIG} from './design.mjs';
export function makeMap(n,displayN=64){
 if(n===displayN)return null;
 const lower=new Uint32Array(displayN),fraction=new Float64Array(displayN);
 for(let a=0;a<displayN;a++){const q=(a+.5)*n/displayN-.5;if(q<=0){lower[a]=0;fraction[a]=0;}else if(q>=n-1){lower[a]=n-1;fraction[a]=0;}else{lower[a]=Math.floor(q);fraction[a]=q-lower[a];}}
 return {lower,fraction};
}
export function mapDisplay(T,n,map,output,displayN=64){
 if(!map)return T.subarray(0,2*n*n);
 for(let p=0;p<2;p++)for(let j=0;j<displayN;j++)for(let k=0;k<displayN;k++){
  const j0=map.lower[j],j1=Math.min(j0+1,n-1),k0=map.lower[k],k1=Math.min(k0+1,n-1),fj=map.fraction[j],fk=map.fraction[k],base=p*n*n;
  const a0=(1-fk)*T[base+j0*n+k0]+fk*T[base+j0*n+k1],a1=(1-fk)*T[base+j1*n+k0]+fk*T[base+j1*n+k1];
  output[p*displayN*displayN+j*displayN+k]=(1-fj)*a0+fj*a1;
 }
 return output;
}
export function uniqueBytes(arrays){return [...new Set(arrays.filter(Boolean).map(a=>a.buffer))].reduce((s,b)=>s+b.byteLength,0);}
export function createState(definition,input,config=CONFIG){
 const a=pack(input,config),T=a.initial,map=makeMap(definition.n,config.displayN),origins=Float64Array.from(input.gasInitialPositions.flat()),display=map?new Float64Array(2*config.displayN**2):T.subarray(0,a.ns);
 const state={definition,config,a,T,map,origins,display,step:0};mapDisplay(T,definition.n,map,display,config.displayN);
 state.persistentBytes=uniqueBytes([a.p,a.measure,a.capacity,a.initial,T,origins,display,map?.lower,map?.fraction]);
 return state;
}
export function updatePath(state,time){
 const {a,origins,config}=state,c=Math.cos(config.Omega*time),s=Math.sin(config.Omega*time);
 for(let j=0;j<a.ng;j++){const i=3*j,p=3*(a.ns+j),x=origins[i],z=origins[i+2];a.p[p]=x*c-z*s;a.p[p+1]=origins[i+1]+config.U*time;a.p[p+2]=x*s+z*c;}
}
export function advance(state,{observePositions=false}={}){
 const before=performance.now(),geometryTime=state.step/state.definition.rate,acceptedTime=(state.step+1)/state.definition.rate;
 updatePath(state,geometryTime);const geometryGasPositions=observePositions?Array.from({length:state.a.ng},(_,j)=>Array.from(state.a.p.subarray(3*(state.a.ns+j),3*(state.a.ns+j+1)))):null;
 const pathBeforeEnd=performance.now(),graph=buildGraph(state.a,'hash'),buildEnd=performance.now();
 const ledger=exchange(state.a,graph,state.T,{...state.config,dt:1/state.definition.rate}),exchangeEnd=performance.now();
 updatePath(state,acceptedTime);const acceptedGasPositions=observePositions?Array.from({length:state.a.ng},(_,j)=>Array.from(state.a.p.subarray(3*(state.a.ns+j),3*(state.a.ns+j+1)))):null;
 const pathAfterEnd=performance.now();mapDisplay(state.T,state.definition.n,state.map,state.display,state.config.displayN);const mappingEnd=performance.now();state.step++;
 const memory={persistentBytes:state.persistentBytes,graphBytes:graph.memory.graphTypedArrayBytes,candidateScratchBytes:graph.memory.candidateScratchBytes,candidateCacheBytes:graph.memory.candidateCacheTypedArrayBytes,exchangeScratchBytes:ledger.workspaceTypedArrayBytes};
 memory.buildPhaseBytes=memory.persistentBytes+memory.graphBytes+memory.candidateScratchBytes+memory.candidateCacheBytes;
 memory.exchangePhaseBytes=memory.persistentBytes+memory.graphBytes+memory.exchangeScratchBytes;
 return {step:state.step,time:acceptedTime,geometryTime,geometryGasPositions,acceptedGasPositions,graph,ledger,memory,timing:{analyticPathMs:(pathBeforeEnd-before)+(pathAfterEnd-exchangeEnd),graphBuildMs:buildEnd-pathBeforeEnd,exchangeMs:exchangeEnd-buildEnd,mappingMs:mappingEnd-pathAfterEnd,stepMs:mappingEnd-before}};
}
export function initialMemory(state){return {persistentBytes:state.persistentBytes,maximumBuildPhaseBytes:state.persistentBytes,maximumExchangePhaseBytes:state.persistentBytes,maximumAlgorithmOwnedArrayBytes:state.persistentBytes,packedPositionBytes:state.a.p.byteLength,packedSurfacePositionBytes:state.a.ns*3*8,packedGasPositionBytes:state.a.ng*3*8,measureBytes:state.a.measure.byteLength,capacityBytes:state.a.capacity.byteLength,currentTemperatureBytes:state.T.byteLength,originBytes:state.origins.byteLength,displayOwnedBytes:state.map?state.display.byteLength:0,mappingBytes:state.map?state.map.lower.byteLength+state.map.fraction.byteLength:0,displayAliasesCurrentState:state.display.buffer===state.T.buffer,initialAliasesCurrentState:state.a.initial.buffer===state.T.buffer,commonVisualGeometry:'implicit panel metadata; no separate visual-position typed array allocated',unknownHeapBytes:null,scope:'Unique owned ArrayBuffer payload and maximum live algorithm phases; excludes archival buffers/input JSON; not RSS or garbage awaiting collection.'};}
export function accumulateMemory(target,frame){target.maximumBuildPhaseBytes=Math.max(target.maximumBuildPhaseBytes,frame.memory.buildPhaseBytes);target.maximumExchangePhaseBytes=Math.max(target.maximumExchangePhaseBytes,frame.memory.exchangePhaseBytes);target.maximumAlgorithmOwnedArrayBytes=Math.max(target.maximumBuildPhaseBytes,target.maximumExchangePhaseBytes);}
