export const CORE_SHA256='8434987b77928c4346b73ecd9fee88cbbb4c7444d232f9cfd34c4f652019a5fc';
export const CONFIG=Object.freeze({h:.12,beta:2,safety:.9,maxSubsteps:100000,horizon:1,displayN:64,ambient:300,Omega:Math.PI/2,U:.4});
export const ARM_DEFINITIONS=Object.freeze([
 {id:'dev-ref128-r120',n:128,rate:120,role:'R0'},
 {id:'dev-ref128-r240',n:128,rate:240,role:'R1'},
 {id:'dev-ref256-r240',n:256,rate:240,role:'R2'},
 {id:'dev-ref256-r480',n:256,rate:480,role:'R3',conditional:true},
 {id:'dev-shared64-r120',n:64,rate:120,role:'shared'},
 {id:'dev-proxy16-r120',n:16,rate:120,role:'proxy'},
]);
export const TIMING_ORDER=Array.from({length:6},(_,i)=>i%2===0?['shared','proxy']:['proxy','shared']);
export function authoredInput(n){
 if(!Number.isSafeInteger(n)||n<1)throw new Error('invalid panel resolution');
 const nodes=[],area=.36/(n*n);
 for(let panel=0;panel<2;panel++)for(let j=0;j<n;j++)for(let k=0;k<n;k++){
  const y=.1+(j+.5)*.6/n,w=-.3+(k+.5)*.6/n;
  nodes.push({id:`p${panel}-j${j}-k${k}`,kind:'surface',position:panel===0?[.25,y,w]:[w,y,.25],measure:area,capacityPerMeasure:2,capacity:area*2,temperature:300});
 }
 const gasInitialPositions=[];
 for(let ix=0;ix<4;ix++)for(let iy=0;iy<2;iy++)for(let iz=0;iz<4;iz++){
  const p=[.2+(ix-1.5)*.05,.1+(iy-.5)*.05,(iz-1.5)*.05],v=.05**3;
  gasInitialPositions.push(p);
  nodes.push({id:`g-ix${ix}-iy${iy}-iz${iz}`,kind:'gas',position:p,measure:v,capacityPerMeasure:30,capacity:v*30,temperature:600});
 }
 return {surfaceCount:2*n*n,nodes,gasInitialPositions};
}
export function pathPosition(p,time,config=CONFIG){const c=Math.cos(config.Omega*time),s=Math.sin(config.Omega*time);return [p[0]*c-p[2]*s,p[1]+config.U*time,p[0]*s+p[2]*c];}
