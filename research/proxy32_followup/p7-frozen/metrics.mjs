function kahanAdd(s,c,i,x){const y=x-c[i],next=s[i]+y;c[i]=(next-s[i])-y;s[i]=next;}
export function observe(state){
 const {a,T,definition,display}=state,n=definition.n,panelHeat=new Float64Array(2),pc=new Float64Array(2),regionHeat=new Float64Array(32),rc=new Float64Array(32),E=new Float64Array(2),ec=new Float64Array(2);let actualPeakRise=0,minimum=Infinity,maximum=-Infinity;
 for(let i=0;i<a.n;i++){const v=T[i];if(!Number.isFinite(v))throw new Error('nonfinite state');minimum=Math.min(minimum,v);maximum=Math.max(maximum,v);kahanAdd(E,ec,i<a.ns?0:1,a.capacity[i]*v);
  if(i<a.ns){const panel=Math.floor(i/(n*n)),local=i%(n*n),j=Math.floor(local/n),k=local%n,region=panel*16+Math.floor(4*j/n)*4+Math.floor(4*k/n),q=a.capacity[i]*(v-300);kahanAdd(panelHeat,pc,panel,q);kahanAdd(regionHeat,rc,region,q);actualPeakRise=Math.max(actualPeakRise,v-300);}}
 return {step:state.step,time:state.step/definition.rate,panelHeat:Array.from(panelHeat),regionHeat:Array.from(regionHeat),display:Array.from(display),gasTemperatures:Array.from(T.subarray(a.ns)),actualPeakRise,minimum,maximum,energy:{surface:E[0],gas:E[1],total:E[0]+E[1]}};
}
export function totalEnergy(state){const E=new Float64Array(2),c=new Float64Array(2);for(let i=0;i<state.a.n;i++)kahanAdd(E,c,i<state.a.ns?0:1,state.a.capacity[i]*state.T[i]);return E[0]+E[1];}
const ratio=(num,den)=>den>0?num/den:num===0?0:null;
export function compareObservations(candidate,reference){
 if(candidate.length!==121||reference.length!==121)throw new Error('comparison requires121 common observations');
 const panelDenominator=Math.max(...reference.flatMap(o=>o.panelHeat.map(Math.abs))),regionDenominator=Math.max(...reference.flatMap(o=>o.regionHeat.map(Math.abs)));
 const maxReferenceDisplayRise=Math.max(...reference.map(o=>Math.max(...o.display.map(T=>T-300))));
 const displayDenominator=Math.max(...reference.map(o=>Math.sqrt(o.display.reduce((s,T)=>s+(T-300)**2,0)/o.display.length)));
 const panelErrorByPanel=[0,0],regionErrorByRegion=Array(32).fill(0),timeSeries=[];let panelNumerator=0,regionNumerator=0,displayNumerator=0,peakAbsoluteError=0,gasMaxAbsoluteError=0,gasSumSquared=0,gasCount=0;
 for(let t=0;t<121;t++){const a=candidate[t],b=reference[t];if(a.time!==t/120||b.time!==t/120||a.display.length!==8192||b.display.length!==8192)throw new Error('comparison time/display shape mismatch');
  const panelDifference=a.panelHeat.map((x,i)=>x-b.panelHeat[i]),regionDifference=a.regionHeat.map((x,i)=>x-b.regionHeat[i]);
  panelDifference.forEach((x,i)=>{panelErrorByPanel[i]=Math.max(panelErrorByPanel[i],Math.abs(x));panelNumerator=Math.max(panelNumerator,Math.abs(x));});regionDifference.forEach((x,i)=>{regionErrorByRegion[i]=Math.max(regionErrorByRegion[i],Math.abs(x));regionNumerator=Math.max(regionNumerator,Math.abs(x));});
  let sse=0;for(let i=0;i<8192;i++){const d=a.display[i]-b.display[i];sse+=d*d;peakAbsoluteError=Math.max(peakAbsoluteError,Math.abs(d));}const displayRms=Math.sqrt(sse/8192);displayNumerator=Math.max(displayNumerator,displayRms);
  for(let i=0;i<32;i++){const d=a.gasTemperatures[i]-b.gasTemperatures[i];gasMaxAbsoluteError=Math.max(gasMaxAbsoluteError,Math.abs(d));gasSumSquared+=d*d;gasCount++;}
  timeSeries.push({time:t/120,panelDifference,regionDifference,displayRms,displayNormalizedRms:ratio(displayRms,displayDenominator)});
 }
 const primary={panel:ratio(panelNumerator,panelDenominator),regional:ratio(regionNumerator,regionDenominator),display:displayDenominator>0?displayNumerator/displayDenominator:null};
 return {primary,panelDenominator,regionDenominator,displayDenominator,displayDenominatorDefinition:'maximum over common times of area-weighted RMS reference display rise above300K',maxReferenceDisplayRise,peakNormalizedDisplayDiagnostic:ratio(displayNumerator,maxReferenceDisplayRise),panelNumerator,regionNumerator,displayNumerator,panelErrorByPanel,regionErrorByRegion,peakAbsoluteError,gasMaxAbsoluteError,gasRmsError:Math.sqrt(gasSumSquared/gasCount),timeSeries,valid:Object.values(primary).every(Number.isFinite)};
}
export const passes=(comparison,tolerance)=>comparison.valid&&Object.values(comparison.primary).every(x=>x<=tolerance);
export function referenceDecision(comparisons){
 const {R0_R1,R1_R2,R0_R2,R2_R3,R1_R3}=comparisons;
 if(!R0_R1||!R1_R2||!R0_R2)return {status:'INCOMPLETE',accepted:false,needR3:false};
 if(!passes(R1_R2,.005))return {status:'REFERENCE_INVALID',accepted:false,needR3:false};
 if(passes(R0_R1,.005)&&passes(R0_R2,.005))return {status:'REFERENCE_ACCEPTED',accepted:true,selectedRole:'R2',needR3:false};
 if(!R2_R3||!R1_R3)return {status:'R3_REQUIRED',accepted:false,needR3:true};
 return passes(R2_R3,.005)&&passes(R1_R3,.005)?{status:'REFERENCE_ACCEPTED',accepted:true,selectedRole:'R3',needR3:false}:{status:'REFERENCE_INVALID',accepted:false,needR3:false};
}
export function signalCheck(observations){const peak=Math.max(...observations.map(o=>Math.max(...o.display.map(T=>T-300)))),rms=Math.max(...observations.map(o=>Math.sqrt(o.display.reduce((s,T)=>s+(T-300)**2,0)/o.display.length))),panel=Math.max(...observations.flatMap(o=>o.panelHeat.map(Math.abs))),regional=Math.max(...observations.flatMap(o=>o.regionHeat.map(Math.abs)));return {passed:peak>=1&&rms>0&&panel>0&&regional>0,peakDisplayRise:peak,maximumRmsDisplayRise:rms,panelDenominator:panel,regionDenominator:regional};}
export function validateLedger(frame,initialEnergy){const l=frame.ledger,scale=Math.max(1,Math.abs(initialEnergy));if(![initialEnergy,l.maxCfl,l.Eafter.total,l.Ebefore.total,l.netSurface,l.netGas].every(Number.isFinite)||l.maxCfl>.9+1e-12||Math.abs(l.Eafter.total-initialEnergy)>1e-12*scale||Math.abs(l.netSurface+l.netGas)>1e-12*scale)throw new Error('CFL or energy invalid');}
export function validateFrame(frame,initialEnergy,T){if(T.some(t=>!Number.isFinite(t)||t<300-1e-9||t>600+1e-9))throw new Error('temperature extrema/finite invalid');validateLedger(frame,initialEnergy);}
export function costDecision(blocks,memory){
 if(blocks.length!==6)return {complete:false,passed:false};if(blocks.some(b=>!Number.isFinite(b.proxy)||!Number.isFinite(b.shared)||b.proxy<=0||b.shared<=0))throw new Error('invalid timing block');const ratios=blocks.map(b=>b.proxy/b.shared),sorted=[...ratios].sort((a,b)=>a-b),median=(sorted[2]+sorted[3])/2;
 const costPassed=median<=.8&&ratios.filter(r=>r<1).length>=5,allowance=3*8192*8;
 for(const arm of ['shared','proxy'])for(const key of ['persistentBytes','maximumAlgorithmOwnedArrayBytes'])if(!Number.isSafeInteger(memory[arm][key])||memory[arm][key]<0)throw new Error('invalid memory payload');
 if(memory.shared.packedSurfacePositionBytes!==allowance||memory.shared.packedPositionBytes<allowance)throw new Error('shared layout does not substantiate visual alias allowance');
 const adjustedShared={persistentBytes:memory.shared.persistentBytes-allowance,maximumAlgorithmOwnedArrayBytes:memory.shared.maximumAlgorithmOwnedArrayBytes-allowance};
 if(Object.values(adjustedShared).some(x=>!Number.isFinite(x)||x<0))throw new Error('invalid shared memory alias allowance');
 const persistentPassed=memory.proxy.persistentBytes<=adjustedShared.persistentBytes,maximumPassed=memory.proxy.maximumAlgorithmOwnedArrayBytes<=adjustedShared.maximumAlgorithmOwnedArrayBytes,memoryPassed=persistentPassed&&maximumPassed;
 return {complete:true,ratios,medianRatio:median,minRatio:sorted[0],maxRatio:sorted[5],fasterBlocks:ratios.filter(r=>r<1).length,costPassed,memoryPassed,memory:{actual:memory,adjustmentValid:true,sharedOptimisticVisualAliasAllowanceBytes:allowance,adjustedShared,persistentPassed,maximumPassed,interpretation:'Optimistic shared alias allowance is a lower-bound comparison, not an observed allocation or timing change.'},passed:costPassed&&memoryPassed};
}
