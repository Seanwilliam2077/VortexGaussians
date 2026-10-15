import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import {createGzip,createGunzip} from 'node:zlib';
import {pipeline} from 'node:stream/promises';
import {CONFIG,CORE_SHA256,ARM_DEFINITIONS,TIMING_ORDER,authoredInput} from './design.mjs';
import {createState,advance,initialMemory,accumulateMemory} from './wrapper.mjs';
import {observe,compareObservations,passes,referenceDecision,signalCheck,validateFrame,validateLedger,costDecision} from './metrics.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url));
export const SOURCE_FILES=['design.mjs','wrapper.mjs','metrics.mjs','run.mjs','test.mjs','p6-core.mjs','PROTOCOL.md','audit.py'];
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export const sourceHashes=()=>Object.fromEntries(SOURCE_FILES.map(f=>[f,sha(fs.readFileSync(path.join(HERE,f)))]));
const sameHashes=(a,b)=>!!b&&Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>a[k]===b[k]);
function hashArrays(arrays){const h=crypto.createHash('sha256');for(const a of arrays)h.update(Buffer.from(a.buffer,a.byteOffset,a.byteLength));return h.digest('hex');}
async function fileHash(file){const h=crypto.createHash('sha256');for await(const chunk of fs.createReadStream(file))h.update(chunk);return h.digest('hex');}
function save(file,value){fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');return {file:path.basename(file),sha256:sha(fs.readFileSync(file)),bytes:fs.statSync(file).size};}
function endpoint(state){return {temperatureSHA256:hashArrays([state.T]),displaySHA256:hashArrays([state.display]),positionSHA256:hashArrays([state.a.p]),step:state.step,time:state.step/state.definition.rate,format:'sha256 raw float64 little-endian buffers'};}
export async function historyWriter(file,vectorLength){
 const gzip=createGzip({level:1}),done=pipeline(gzip,fs.createWriteStream(file)),rawHash=crypto.createHash('sha256');let rawBytes=0,count=0;
 // Attach error handling immediately; close still awaits and propagates failure.
 done.catch(()=>{});
 return {async write(values){if(values.length!==vectorLength||!(values instanceof Float64Array))throw new Error('history shape');const bytes=Buffer.from(Buffer.from(values.buffer,values.byteOffset,values.byteLength));rawHash.update(bytes);rawBytes+=bytes.length;count++;await new Promise((resolve,reject)=>gzip.write(bytes,e=>e?reject(e):resolve()));},
 async close(){gzip.end();await done;const uncompressedSHA256=rawHash.digest('hex'),roundtrip=crypto.createHash('sha256');let roundtripBytes=0;for await(const chunk of fs.createReadStream(file).pipe(createGunzip())){roundtrip.update(chunk);roundtripBytes+=chunk.length;}if(roundtrip.digest('hex')!==uncompressedSHA256||roundtripBytes!==rawBytes)throw new Error('gzip round-trip mismatch');return {file:path.basename(file),format:'float64-le',order:'surface panel/j/k ascending, then gas ix/iy/iz ascending',vectorCount:count,vectorLength,uncompressedBytes:rawBytes,uncompressedSHA256,compressedBytes:fs.statSync(file).size,compressedSHA256:await fileHash(file),gzipLevel:1,roundtripVerified:true};},async abort(error){gzip.destroy(error);try{await done;}catch{}}};
}
function validateInputUnchanged(input,before){const after=sha(JSON.stringify(input));if(after!==before)throw new Error('authored input mutated');return after;}
export async function qualityArm(definition,input,out,{steps=definition.rate,onProgress=()=>{}}={}){
 const inputSHA256=sha(JSON.stringify(input)),state=createState(definition,input),memory=initialMemory(state),initial=observe(state),observations=[initial],frames=[],writer=await historyWriter(path.join(out,`${definition.id}.temperatures.f64.gz`),state.a.n);
 try{
 await writer.write(state.T);const initialEndpoint=endpoint(state),auditSteps=new Set([1,definition.rate/4,definition.rate/2,3*definition.rate/4,definition.rate]);
 for(let k=1;k<=steps;k++){
  let frame=advance(state,{observePositions:true});validateFrame(frame,initial.energy.total,state.T);accumulateMemory(memory,frame);
  let g=frame.graph;frames.push({step:frame.step,time:frame.time,geometryTime:frame.geometryTime,acceptedTime:frame.time,geometryGasPositions:frame.geometryGasPositions,acceptedGasPositions:frame.acceptedGasPositions,graph:{edgeCount:g.edgeCount,maxRate:g.maxRate,work:g.work,memory:g.memory,topologySHA256:auditSteps.has(k)?hashArrays([g.rowOffsets,g.gasIndex]):null,topologyHashEncoding:'uint32LE rowOffsets then uint32LE local gasIndex',sumConductance:g.conductance.reduce((s,x)=>s+x,0)},ledger:frame.ledger});
  if(k%(definition.rate/120)===0)observations.push(observe(state));await writer.write(state.T);g=null;frame=null;
  if(k%Math.max(1,Math.floor(definition.rate/4))===0)onProgress({id:definition.id,step:k,total:steps});
 }
 const history=await writer.close(),finalEndpoint=endpoint(state),inputSHA256After=validateInputUnchanged(input,inputSHA256);
 const result={version:1,phase:'P7',id:definition.id,definition,config:CONFIG,input,inputSHA256,inputSHA256After,inputUnchanged:true,history,displayAreaWeights:{kind:'uniform',count:8192,weight:.36/4096,totalArea:.72},initialEndpoint,finalEndpoint,frames,observations,memory,executionValid:true};
 if(steps===definition.rate&&(history.vectorCount!==definition.rate+1||observations.length!==121))throw new Error('quality evidence incomplete');
 const record=save(path.join(out,`${definition.id}.json`),result);return {result,record};
 }catch(error){await writer.abort(error);throw error;}
}
export function timedArm(definition,input){
 global.gc?.();const start=performance.now(),state=createState(definition,input),setupEnd=performance.now(),memory=initialMemory(state),stages={setupMs:setupEnd-start,analyticPathMs:0,graphBuildMs:0,exchangeMs:0,mappingMs:0,validationMs:0};let initialEnergy=null;
 for(let k=0;k<definition.rate;k++){let frame=advance(state);for(const key of ['analyticPathMs','graphBuildMs','exchangeMs','mappingMs'])stages[key]+=frame.timing[key];const v0=performance.now();if(initialEnergy===null)initialEnergy=frame.ledger.Ebefore.total;validateLedger(frame,initialEnergy);stages.validationMs+=performance.now()-v0;accumulateMemory(memory,frame);frame=null;}
 const end=performance.now(),wholeTrajectoryMs=end-start;
 return {id:definition.id,wholeTrajectoryMs,stages,validationScope:'O(1) ledger/CFL/cumulative-energy checks; native P6 per-node checks remain in exchangeMs; no extra archival extrema scan',initialEnergy,unattributedMs:wholeTrajectoryMs-Object.values(stages).reduce((s,x)=>s+x,0),endpoint:endpoint(state),memory};
}
function parse(argv){const a={};for(let i=0;i<argv.length;i++){if(argv[i]==='--out')a.out=argv[++i];else if(argv[i]==='--freeze')a.freeze=argv[++i];else if(argv[i]==='--formal')a.formal=true;else if(argv[i]==='--help'){console.log('node --expose-gc run.mjs --formal --freeze FREEZE.json --out NEW_DIRECTORY');process.exit(0);}else throw new Error(`unknown option ${argv[i]}`);}if(!a.formal||!a.freeze||!a.out)throw new Error('formal, freeze and fresh out required');return a;}
export async function main(argv=process.argv.slice(2)){
 const args=parse(argv);if(typeof global.gc!=='function'||os.endianness()!=='LE')throw new Error('requires --expose-gc on little-endian host');const hashes=sourceHashes();if(hashes['p6-core.mjs']!==CORE_SHA256)throw new Error('P6 core provenance mismatch');const frozen=JSON.parse(fs.readFileSync(args.freeze,'utf8'));if(!sameHashes(hashes,frozen.sourceHashes??frozen))throw new Error('source freeze mismatch');
 const out=path.resolve(args.out);if(fs.existsSync(out)&&fs.readdirSync(out).length)throw new Error('output directory must be empty/new');fs.mkdirSync(out,{recursive:true});
 const manifest={phase:'P7',version:1,formal:true,status:'running',protocolComplete:false,sourceHashes:hashes,planned:ARM_DEFINITIONS,config:CONFIG,cases:[],reference:{status:'pending'},quality:{status:'not-run'},timing:{status:'not-run',order:TIMING_ORDER},decision:null,executionValid:null,independentAudit:'pending',host:{node:process.version,platform:process.platform,cpu:os.cpus()[0]?.model,arch:process.arch},timingContract:{clock:'performance.now CPU wall time; no renderer/GPU',freshStatePairedBlocks:6,warmupsPerArm:1,primaryIncludes:'packing, mapping setup, analytic path, exact graph, exchange, energy/finite/CFL validation, display mapping, phase bookkeeping',excluded:'authored input creation, hashes, history observations/copies, compression, file IO, independent audit',gc:'forced before each trajectory outside enclosing interval; incidental GC inside included'},startedAt:new Date().toISOString()};
 const records=new Map(),results=new Map(),writeManifest=()=>save(path.join(out,'manifest.json'),manifest);
 const run=async role=>{const d=ARM_DEFINITIONS.find(a=>a.role===role),input=authoredInput(d.n);console.log(`START ${d.id}`);const {result,record}=await qualityArm(d,input,out,{onProgress:p=>console.log(`PROGRESS ${p.id} ${p.step}/${p.total}`)});manifest.cases.push({id:d.id,role,...record,history:result.history});const summary={id:result.id,definition:result.definition,inputSHA256:result.inputSHA256,observations:result.observations,memory:result.memory,initialEndpoint:result.initialEndpoint,finalEndpoint:result.finalEndpoint};results.set(role,summary);records.set(role,record);writeManifest();console.log(`DONE ${d.id}`);return summary;};
 const cmp=(a,b)=>compareObservations(results.get(a).observations,results.get(b).observations);
 writeManifest();
 try{
  await run('R0');await run('R1');await run('R2');const comparisons={R0_R1:cmp('R0','R1'),R1_R2:cmp('R1','R2'),R0_R2:cmp('R0','R2')};let ref=referenceDecision(comparisons);
  if(ref.needR3){await run('R3');comparisons.R2_R3=cmp('R2','R3');comparisons.R1_R3=cmp('R1','R3');ref=referenceDecision(comparisons);}
  manifest.reference={...ref,comparisons};writeManifest();
  if(!ref.accepted){manifest.decision='REFERENCE_INVALID';manifest.quality={status:'skipped',reason:manifest.decision};manifest.timing={...manifest.timing,status:'skipped',reason:manifest.decision};}
  else{const reference=results.get(ref.selectedRole),signal=signalCheck(reference.observations);manifest.reference.signal=signal;
   if(!signal.passed){manifest.decision='INSUFFICIENT_SIGNAL';manifest.quality={status:'skipped',reason:manifest.decision};manifest.timing={...manifest.timing,status:'skipped',reason:manifest.decision};}
   else{await run('shared');await run('proxy');const shared=cmp('shared',ref.selectedRole),proxy=cmp('proxy',ref.selectedRole);manifest.quality={status:'completed',shared:{comparison:shared,passed:passes(shared,.02)},proxy:{comparison:proxy,passed:passes(proxy,.02)}};
    if(!manifest.quality.shared.passed||!manifest.quality.proxy.passed){manifest.decision=!manifest.quality.proxy.passed?'PROXY_QUALITY_STOP':'SHARED_QUALITY_STOP';manifest.timing={...manifest.timing,status:'skipped',reason:manifest.decision};}
    else{manifest.timing={...manifest.timing,status:'running',warmups:[],runs:[],blocks:[]};writeManifest();const authored=Object.fromEntries(['shared','proxy'].map(role=>[role,authoredInput(results.get(role).definition.n)]));for(const role of ['shared','proxy'])if(sha(JSON.stringify(authored[role]))!==results.get(role).inputSHA256)throw new Error('timing authored-input mismatch');
     for(const role of ['shared','proxy']){const r=timedArm(results.get(role).definition,authored[role]);if(!same(r.endpoint,results.get(role).finalEndpoint))throw new Error('warmup endpoint mismatch');manifest.timing.warmups.push({role,endpoint:r.endpoint});}
     for(let block=0;block<6;block++){const b={block};for(const role of TIMING_ORDER[block]){const r=timedArm(results.get(role).definition,authored[role]);if(!same(r.endpoint,results.get(role).finalEndpoint))throw new Error('timing endpoint mismatch');if(!same(r.memory,results.get(role).memory))throw new Error('timing memory accounting mismatch');manifest.timing.runs.push({block,role,...r});b[role]=r.wholeTrajectoryMs;}manifest.timing.blocks.push(b);writeManifest();console.log(`TIMING ${block+1}/6`);}
     for(const role of ['shared','proxy'])validateInputUnchanged(authored[role],results.get(role).inputSHA256);manifest.timing.authoredInputsUnchanged=true;
     manifest.timing.status='completed';manifest.timing.screen=costDecision(manifest.timing.blocks,{shared:results.get('shared').memory,proxy:results.get('proxy').memory});manifest.decision=manifest.timing.screen.passed?'PROXY_STRICT_FIRST_SCREEN':'QUALITY_PASS_NO_STRICT_DOMINANCE';
    }
   }
  }
  manifest.completedIds=manifest.cases.map(c=>c.id);manifest.skipped=ARM_DEFINITIONS.filter(d=>!manifest.completedIds.includes(d.id)).map(d=>({id:d.id,reason:d.role==='R3'?'reference rule did not request optional temporal refinement':manifest.quality.reason}));
  manifest.requiredExecutedIds=['R0','R1','R2',...(comparisons.R2_R3?['R3']:[]),...(manifest.quality.status==='completed'?['shared','proxy']:[])].map(role=>ARM_DEFINITIONS.find(d=>d.role===role).id);
  manifest.protocolComplete=same(manifest.completedIds,manifest.requiredExecutedIds);if(!manifest.protocolComplete)throw new Error('conditional evidence coverage mismatch');manifest.executionValid=true;manifest.status='completed-pending-independent-audit';
 }catch(error){manifest.status='execution_failed';manifest.executionValid=false;manifest.decision='EXECUTION_INVALID';manifest.error=String(error.stack??error);throw error;}
 finally{manifest.sourceHashesAfter=sourceHashes();manifest.sourcesUnchanged=sameHashes(hashes,manifest.sourceHashesAfter);if(!manifest.sourcesUnchanged){manifest.status='execution_failed';manifest.executionValid=false;manifest.decision='EXECUTION_INVALID';}manifest.finishedAt=new Date().toISOString();writeManifest();}
 return manifest;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
