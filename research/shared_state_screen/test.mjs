import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import crypto from 'node:crypto';
import {CONFIG,authoredInput,pathPosition} from './design.mjs';
import {createState,makeMap,mapDisplay,uniqueBytes,advance,updatePath,initialMemory} from './wrapper.mjs';
import {buildGraph,exchange} from './p6-core.mjs';
import {observe,totalEnergy,compareObservations,passes,referenceDecision,signalCheck,validateFrame,costDecision} from './metrics.mjs';
import {historyWriter,timedArm} from './run.mjs';
test('bilinear map preserves constants, interior linear fields, and boundary clamping',()=>{
 const n=4,map=makeMap(n),T=new Float64Array(2*n*n),out=new Float64Array(8192);T.fill(321);mapDisplay(T,n,map,out);assert.ok(out.every(x=>x===321));assert.equal(map.lower.byteLength+map.fraction.byteLength,768);
 for(let p=0;p<2;p++)for(let j=0;j<n;j++)for(let k=0;k<n;k++)T[p*n*n+j*n+k]=300+10*p+2*j+3*k;
 mapDisplay(T,n,map,out);assert.equal(out[0],T[0]);assert.equal(out[4095],T[15]);const j=16,k=32,qj=(j+.5)*n/64-.5,qk=(k+.5)*n/64-.5;assert.equal(out[j*64+k],300+2*qj+3*qk);
});
test('shared display aliases current state; owned-buffer accounting counts aliases once',()=>{
 const s=createState({n:64,rate:120},authoredInput(64));assert.equal(s.display.buffer,s.T.buffer);assert.equal(s.a.initial.buffer,s.T.buffer);assert.equal(s.display.length,8192);assert.equal(initialMemory(s).mappingBytes,0);assert.equal(uniqueBytes([s.T,s.T.subarray(1),s.display]),s.T.byteLength);assert.equal(initialMemory(s).packedSurfacePositionBytes,196608);
});
test('region and panel heat preserve authored capacity and area',()=>{
 const s=createState({n:4,rate:120},authoredInput(4));for(let i=0;i<s.a.ns;i++)s.T[i]=310;mapDisplay(s.T,4,s.map,s.display);const o=observe(s);assert.ok(Math.abs(o.panelHeat[0]-7.2)<1e-12);assert.ok(o.regionHeat.every(x=>Math.abs(x-.45)<1e-12));assert.ok(Math.abs(o.energy.total-518.4)<1e-10);assert.equal(o.actualPeakRise,10);
});
test('analytic path agrees at common times across rates and preserves radial distance',()=>{
 const p=[.125,.075,-.075];for(const t of [0,.25,.5,1]){const q=pathPosition(p,t);assert.ok(Math.abs(q[0]**2+q[2]**2-p[0]**2-p[2]**2)<1e-16);assert.equal(q[1],p[1]+.4*t);assert.deepEqual(pathPosition(p,(t*120)/120),pathPosition(p,(t*240)/240));}
});
test('moving wrapper matches all-pairs old-temperature schedule and retains heat across steps',()=>{
 const definition={n:4,rate:120},input=authoredInput(4),a=createState(definition,input),b=createState(definition,input),before=JSON.stringify(input),E=totalEnergy(a);let previousHeat=0;
 for(let k=0;k<4;k++){let actual=advance(a,{observePositions:true});updatePath(b,k/120);const g=buildGraph(b.a,'allpairs');exchange(b.a,g,b.T,{...CONFIG,dt:1/120});updatePath(b,(k+1)/120);mapDisplay(b.T,4,b.map,b.display);b.step++;
  assert.deepEqual(a.T,b.T);assert.deepEqual(a.a.p,b.a.p);assert.deepEqual(a.display,b.display);assert.deepEqual(actual.geometryGasPositions,input.gasInitialPositions.map(p=>pathPosition(p,k/120)));assert.deepEqual(actual.acceptedGasPositions,input.gasInitialPositions.map(p=>pathPosition(p,(k+1)/120)));validateFrame(actual,E,a.T);const heat=observe(a).panelHeat[0];assert.ok(heat>previousHeat);previousHeat=heat;actual=null;
 }assert.equal(JSON.stringify(input),before);
});
const fake=(rise=2)=>Array.from({length:121},(_,i)=>({time:i/120,panelHeat:[1,2],regionHeat:Array(32).fill(.1),display:Array(8192).fill(300+rise),gasTemperatures:Array(32).fill(500)}));
test('metrics use response RMS, reject zero display denominator, and catch errors',()=>{
 const r=fake(),a=fake();a[120].display[0]+=1;const c=compareObservations(a,r);assert.equal(c.displayDenominator,2);assert.ok(Math.abs(c.primary.display-1/Math.sqrt(8192)/2)<1e-15);assert.ok(passes(c,.02));assert.ok(!compareObservations(fake(0),fake(0)).valid);assert.ok(!signalCheck(fake(.5)).passed);assert.throws(()=>compareObservations([],r));
});
test('reference rule permits exactly the declared conditional refinement and never rescues spatial failure',()=>{
 const good={valid:true,primary:{panel:.001,regional:.002,display:.003}},bad={valid:true,primary:{panel:.006,regional:.002,display:.003}};
 assert.equal(referenceDecision({R0_R1:good,R1_R2:good,R0_R2:good}).selectedRole,'R2');assert.equal(referenceDecision({R0_R1:bad,R1_R2:good,R0_R2:bad}).needR3,true);assert.equal(referenceDecision({R0_R1:bad,R1_R2:good,R0_R2:bad,R2_R3:good,R1_R3:good}).selectedRole,'R3');assert.equal(referenceDecision({R0_R1:good,R1_R2:bad,R0_R2:good}).status,'REFERENCE_INVALID');
});
test('cost screen enforces paired ratios and both optimistic shared memory bounds',()=>{
 const blocks=Array.from({length:6},()=>({shared:100,proxy:79})),memory={shared:{persistentBytes:300000,maximumAlgorithmOwnedArrayBytes:1000000,packedSurfacePositionBytes:196608,packedPositionBytes:197376},proxy:{persistentBytes:100000,maximumAlgorithmOwnedArrayBytes:500000}};
 assert.ok(costDecision(blocks,memory).passed);const worse=structuredClone(memory);worse.proxy.persistentBytes=110000;assert.ok(!costDecision(blocks,worse).memoryPassed);const b=structuredClone(blocks);b[0].proxy=101;b[1].proxy=101;assert.ok(!costDecision(b,memory).costPassed);const invalid=structuredClone(memory);invalid.shared.persistentBytes=1;assert.throws(()=>costDecision(blocks,invalid));
});
test('streamed gzip history round-trips exact Float64 values and vector framing',async()=>{
 const root=path.dirname(fileURLToPath(import.meta.url)),dir=fs.mkdtempSync(path.join(root,'.tiny-history-')),file=path.join(dir,'test.gz');
 try{const w=await historyWriter(file,4),a=Float64Array.from([0,-0,Math.PI,600]);await w.write(a);await w.write(a);const m=await w.close(),raw=gunzipSync(fs.readFileSync(file));assert.equal(m.vectorCount,2);assert.equal(m.uncompressedBytes,64);assert.equal(m.roundtripVerified,true);assert.deepEqual(raw.subarray(0,32),Buffer.from(a.buffer));}
 finally{if(path.dirname(dir)!==root||!path.basename(dir).startsWith('.tiny-history-'))throw new Error('unsafe cleanup path');fs.rmSync(dir,{recursive:true});}
});
test('tiny timed path preserves exact endpoint without an extra per-state audit scan',()=>{
 const definition={id:'tiny-timing-wiring',n:4,rate:4},input=authoredInput(4),original=Float64Array.prototype.some;let scans=0,actual;
 try{Float64Array.prototype.some=function(...args){scans++;return original.apply(this,args);};actual=timedArm(definition,input);}finally{Float64Array.prototype.some=original;}
 assert.equal(scans,definition.rate);const reference=createState(definition,input);for(let i=0;i<4;i++){const frame=advance(reference);validateFrame(frame,504,reference.T);}
 assert.equal(actual.endpoint.temperatureSHA256,crypto.createHash('sha256').update(Buffer.from(reference.T.buffer)).digest('hex'));assert.ok(actual.wholeTrajectoryMs>=0);assert.ok(actual.unattributedMs>=-1e-9);assert.ok(Object.values(actual.stages).every(x=>Number.isFinite(x)&&x>=0));
});
