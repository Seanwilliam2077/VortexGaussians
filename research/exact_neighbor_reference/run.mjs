import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {performance} from 'node:perf_hooks';
import {PARAMS,METHODS,ORDER,fixture,definitions} from './design.mjs';
import {pack,buildGraph,exchange,edgeTriples} from './core.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url));
export const SOURCE_FILES=['design.mjs','core.mjs','run.mjs','test.mjs','PROTOCOL.md','audit.py','p4-thermal-reference.mjs'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
export function sourceHashes(){return Object.fromEntries(SOURCE_FILES.map(f=>[f,sha(fs.readFileSync(path.resolve(HERE,f)))]));}
function typedHash(arrays){const h=crypto.createHash('sha256');for(const a of arrays)h.update(Buffer.from(a.buffer,a.byteOffset,a.byteLength));return h.digest('hex');}
function graphHash(g){return typedHash([g.rowOffsets,g.gasIndex,g.conductance]);}
function save(file,value){fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');return {path:path.basename(file),sha256:sha(fs.readFileSync(file)),bytes:fs.statSync(file).size};}
const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export const sameSources=(a,b)=>!!b&&Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>a[k]===b[k]);
const percentile=(xs,p)=>{const a=[...xs].sort((x,y)=>x-y);return a[Math.floor((a.length-1)*p)];};
function execute(a,method){
  // Authored state reset is excluded identically; all exchange scratch is inside.
  const temperatures=new Float64Array(a.initial);global.gc?.();
  const start=performance.now(),graph=buildGraph(a,method==='allpairs-rebuild'?'allpairs':'hash'),buildEnd=performance.now();
  const ledger=exchange(a,graph,temperatures,PARAMS),end=performance.now();
  return {graph,temperatures,ledger,timing:{...graph.timing,buildSetupMs:buildEnd-start,exchangeMs:end-buildEnd,totalWithSetupMs:end-start,applicationMs:method==='hash-cached'?end-buildEnd:end-start,scope:method==='hash-cached'?'one application of a prebuilt static graph; setup separately recorded':'complete graph rebuild plus one exchange step'}};
}
export function runCase(definition,{measured=true}={}){
  const input=fixture(definition.surfaceCount,definition.pattern),a=pack(input,PARAMS),inputSHA256=sha(JSON.stringify(input));
  const result={version:1,id:definition.id,definition,params:PARAMS,input,inputSHA256,inputHashEncoding:'sha256 UTF-8 JSON.stringify(input), property/insertion order preserved',methods:[],executionValid:true};
  // Warm every method with this case; no measurements retained or interpreted.
  if(measured)for(const method of METHODS){let r=execute(a,method);r=null;global.gc?.();}
  const outputs=new Map();
  for(let repeat=0;repeat<(measured?5:1);repeat++)for(const method of ORDER[repeat]){
    let r=execute(a,method);const hash=graphHash(r.graph),topologySHA256=typedHash([r.graph.rowOffsets,r.graph.gasIndex]),temperatureSHA256=typedHash([r.temperatures]);
    let output=outputs.get(method);
    if(!output){output={id:method,graph:{edgeCount:r.graph.edgeCount,neighborCount:Array.from(r.graph.neighborCount),sumG:Array.from(r.graph.sumG),maxRate:r.graph.maxRate,work:r.graph.work,memory:r.graph.memory,sha256:hash,topologySHA256,topologyHashEncoding:'sha256 concatenated rowOffsets:uint32LE[ns+1], gasIndex:uint32LE[E] (local gas index); excludes conductance',hashEncoding:'sha256 concatenated rowOffsets:uint32LE[ns+1], gasIndex:uint32LE[E] (local gas index), conductance:float64LE[E]; rows i ascending, local gas j ascending',edges:definition.surfaceCount===500?edgeTriples(a,r.graph):null},finalTemperatures:Array.from(r.temperatures),temperatureSHA256,ledger:r.ledger,repeats:[]};outputs.set(method,output);}
    else if(hash!==output.graph.sha256||topologySHA256!==output.graph.topologySHA256||temperatureSHA256!==output.temperatureSHA256||!equal(r.ledger,output.ledger))throw new Error(`${method}: nondeterministic fresh-state trial`);
    output.repeats.push({repeat,orderIndex:ORDER[repeat].indexOf(method),timing:measured?r.timing:null,graphSHA256:hash,topologySHA256,temperatureSHA256,ledger:r.ledger});r=null;global.gc?.();
  }
  for(const method of METHODS){const o=outputs.get(method);o.timingSummary=measured?Object.fromEntries(['applicationMs','buildSetupMs','exchangeMs','totalWithSetupMs'].map(k=>[k,{median:percentile(o.repeats.map(r=>r.timing[k]),.5),p95FloorIndex:percentile(o.repeats.map(r=>r.timing[k]),.95),min:Math.min(...o.repeats.map(r=>r.timing[k])),max:Math.max(...o.repeats.map(r=>r.timing[k]))}])):null;result.methods.push(o);}
  const reference=result.methods[0];result.crossMethodExact=result.methods.every(m=>m.graph.sha256===reference.graph.sha256&&m.graph.topologySHA256===reference.graph.topologySHA256&&m.temperatureSHA256===reference.temperatureSHA256&&equal(m.ledger,reference.ledger));
  if(!result.crossMethodExact)throw new Error('exact enumeration methods disagree');result.inputSHA256After=sha(JSON.stringify(input));result.inputUnchanged=result.inputSHA256After===inputSHA256;if(!result.inputUnchanged)throw new Error('authored input mutated');return result;
}
function parse(argv){const args={out:null,formal:false,freeze:null};for(let i=0;i<argv.length;i++){if(argv[i]==='--out')args.out=argv[++i];else if(argv[i]==='--freeze')args.freeze=argv[++i];else if(argv[i]==='--formal')args.formal=true;else if(argv[i]==='--help'){console.log('node --expose-gc run.mjs --formal --freeze freeze.json --out NEW_DIRECTORY\nFormal only: all nine cases. For tiny wiring use node --test test.mjs.');process.exit(0);}else throw new Error(`unknown argument ${argv[i]}`);}if(!args.out||!args.formal||!args.freeze)throw new Error('formal flag, freeze file, and fresh output directory required');return args;}
export function main(argv=process.argv.slice(2)){
  const args=parse(argv);if(typeof global.gc!=='function')throw new Error('formal requires Node --expose-gc');if(os.endianness()!=='LE')throw new Error('binary hash format requires little-endian host');
  const out=path.resolve(args.out);if(fs.existsSync(out)&&fs.readdirSync(out).length)throw new Error('output directory must be empty or new');
  const hashes=sourceHashes(),freeze=JSON.parse(fs.readFileSync(args.freeze,'utf8'));if(!sameSources(hashes,freeze.sourceHashes??freeze))throw new Error('frozen sources differ');fs.mkdirSync(out,{recursive:true});
  const planned=definitions(),manifest={phase:'P6-exact-neighbor-cost',version:1,status:'running',formal:true,protocolComplete:false,executionValid:null,independentAudit:'pending',sourceHashes:hashes,planned,params:PARAMS,cases:[],startedAt:new Date().toISOString(),host:{node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model,logicalCpus:os.cpus().length,endianness:os.endianness()},timing:{repeats:5,warmupsPerMethodPerCase:1,order:ORDER,gc:'forced outside each trial, after input clone and after releasing prior graph',inputPacking:'outside',inputTemperatureReset:'outside',exchangeScratchAllocation:'inside',buildAllocation:'inside buildSetupMs',hashesAndSerialization:'outside',clock:'performance.now CPU wall time; no GPU/render/full-system measurement',cachedMeaning:'Each trial measures fresh preprocessing separately, then one application; static edges can be reused but no amortization or moving-geometry claim.'}};
  save(path.join(out,'manifest.json'),manifest);
  try{for(const definition of planned){console.log(`START ${definition.id}`);const result=runCase(definition);manifest.cases.push({id:definition.id,...save(path.join(out,`${definition.id}.json`),result)});save(path.join(out,'manifest.json'),manifest);console.log(`DONE ${definition.id} (${manifest.cases.length}/${planned.length})`);}manifest.sourceHashesAfter=sourceHashes();if(!sameSources(hashes,manifest.sourceHashesAfter))throw new Error('source changed during run');manifest.protocolComplete=manifest.cases.length===planned.length;manifest.executionValid=true;manifest.status='completed-pending-independent-audit';}
  catch(error){manifest.status='execution_failed';manifest.executionValid=false;manifest.error=String(error.stack??error);throw error;}
  finally{manifest.sourceHashesAfter=sourceHashes();manifest.sourcesUnchanged=sameSources(hashes,manifest.sourceHashesAfter);if(!manifest.sourcesUnchanged){manifest.status='execution_failed';manifest.executionValid=false;}manifest.finishedAt=new Date().toISOString();save(path.join(out,'manifest.json'),manifest);}
  return manifest;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main();

