import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {PHASE,PARENT_ARCHIVE_SHA256,NEW_ARM,SHARED_ARM,REFERENCE_ID,INHERITED_IDS,SOURCE_FILES,CONFIG,TIMING_ORDER} from './design.mjs';
import {authoredInput} from './p7-frozen/design.mjs';
import {qualityArm,timedArm} from './p7-frozen/run.mjs';
import {compareObservations,passes,signalCheck,costDecision} from './p7-frozen/metrics.mjs';
const HERE=path.dirname(fileURLToPath(import.meta.url));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
export const sameHashes=(a,b)=>!!b&&Object.keys(a).length===Object.keys(b).length&&Object.keys(a).every(k=>a[k]===b[k]);
export const sourceHashes=()=>Object.fromEntries(SOURCE_FILES.map(f=>[f,sha(fs.readFileSync(path.join(HERE,f)))]));
export class ParentEvidenceError extends Error{}
export async function fileHash(file){const h=crypto.createHash('sha256');for await(const b of fs.createReadStream(file))h.update(b);return h.digest('hex');}
export async function verifyFile(file,pin){try{if(fs.statSync(file).size!==pin.bytes)throw new ParentEvidenceError(`size differs: ${file}`);const actual=await fileHash(file);if(actual!==pin.sha256)throw new ParentEvidenceError(`SHA differs: ${file}`);return {path:pin.path??path.basename(file),bytes:pin.bytes,sha256:actual};}catch(error){if(error instanceof ParentEvidenceError)throw error;throw new ParentEvidenceError(`unreadable parent dependency ${file}: ${error.message}`);}}
const load=file=>JSON.parse(fs.readFileSync(file,'utf8'));
function save(file,data){fs.writeFileSync(file,JSON.stringify(data,null,2)+'\n');return {file:path.basename(file),sha256:sha(fs.readFileSync(file)),bytes:fs.statSync(file).size};}
export async function authenticateParent(baselineRoot,archive){
 const pins=load(path.join(HERE,'baseline-pins.json'));
 if(pins.archive.sha256!==PARENT_ARCHIVE_SHA256)throw new ParentEvidenceError('unexpected parent archive identity');
 const archiveIdentity=await verifyFile(archive,pins.archive),verified=new Map();
 const check=async pin=>{if(verified.has(pin.path)){if(!same(verified.get(pin.path),{path:pin.path,bytes:pin.bytes,sha256:pin.sha256}))throw new ParentEvidenceError('conflicting pin');return;}
  const resolved=path.resolve(baselineRoot,pin.path);if(!resolved.startsWith(path.resolve(baselineRoot)+path.sep))throw new ParentEvidenceError('unsafe baseline pin path');verified.set(pin.path,await verifyFile(resolved,pin));};
 for(const pin of pins.files)await check(pin);
 const manifest=load(path.join(baselineRoot,'formal/manifest.json')),freeze=load(path.join(baselineRoot,'freeze.json')),audit=load(path.join(baselineRoot,'independent-audit.json'));
 if(manifest.phase!=='P7'||!manifest.protocolComplete||!manifest.executionValid||!manifest.sourcesUnchanged||manifest.decision!=='PROXY_QUALITY_STOP'||manifest.reference.selectedRole!=='R3'||!manifest.reference.accepted||!manifest.quality.shared.passed||manifest.quality.proxy.passed||manifest.timing.status!=='skipped'||audit.status!=='passed'||!audit.independentAuditPassed||audit.scientificDecision!=='PROXY_QUALITY_STOP'||audit.reference.selectedRole!=='R3')throw new ParentEvidenceError('parent certification/decision mismatch');
 for(const mapping of [manifest.sourceHashes,manifest.sourceHashesAfter,freeze.sourceHashes,audit.sourceHashes,audit.sourceHashesAfter])if(!sameHashes(pins.sourceHashes,mapping))throw new ParentEvidenceError('parent frozen source mapping differs');
 const localParentSources=Object.fromEntries(Object.keys(pins.sourceHashes).map(f=>[f,sha(fs.readFileSync(path.join(HERE,'p7-frozen',f)))]));if(!sameHashes(pins.sourceHashes,localParentSources))throw new ParentEvidenceError('imported parent source changed');
 for(const entry of manifest.cases){await check({path:'formal/'+entry.file,bytes:entry.bytes,sha256:entry.sha256});await check({path:'formal/'+entry.history.file,bytes:entry.history.compressedBytes,sha256:entry.history.compressedSHA256});}
 const reference=load(path.join(baselineRoot,'formal',REFERENCE_ID+'.json')),shared=load(path.join(baselineRoot,'formal',SHARED_ARM.id+'.json'));
 for(const [role,record] of [['reference',reference],['shared',shared]]){const p=pins.cases[role];if(record.id!==p.id||record.inputSHA256!==p.inputSHA256||!same(record.definition,p.definition)||!same(record.initialEndpoint,p.initialEndpoint)||!same(record.finalEndpoint,p.finalEndpoint)||!same(record.history,p.history)||!record.inputUnchanged)throw new ParentEvidenceError(`reused ${role} identity differs`);}
 const sharedComparison=compareObservations(shared.observations,reference.observations),signal=signalCheck(reference.observations);
 if(!passes(sharedComparison,.02)||!signal.passed||!same(sharedComparison.primary,manifest.quality.shared.comparison.primary))throw new ParentEvidenceError('reused shared/reference check differs');
 return {identity:{archive:archiveIdentity,archiveExpectedSHA256:PARENT_ARCHIVE_SHA256,files:[...verified.values()].sort((a,b)=>a.path.localeCompare(b.path)),sourceHashes:localParentSources,parentManifestSHA256:sha(fs.readFileSync(path.join(baselineRoot,'formal/manifest.json'))),parentAuditSHA256:sha(fs.readFileSync(path.join(baselineRoot,'independent-audit.json'))),parentDecision:manifest.decision,referenceId:REFERENCE_ID,sharedId:SHARED_ARM.id,certification:'Authenticated existing parent audit; independent P7b audit must still re-execute the frozen parent auditor.'},reference:{id:reference.id,definition:reference.definition,observations:reference.observations},shared:{id:shared.id,definition:shared.definition,observations:shared.observations,inputSHA256:shared.inputSHA256,initialEndpoint:shared.initialEndpoint,finalEndpoint:shared.finalEndpoint,memory:shared.memory},sharedComparison,signal};
}
export function qualityDecision(sharedComparison,proxyComparison){if(!passes(sharedComparison,.02))throw new ParentEvidenceError('inherited shared quality no longer passes');return {sharedPassed:true,proxyPassed:passes(proxyComparison,.02),timingAllowed:passes(proxyComparison,.02),decision:passes(proxyComparison,.02)?null:'PROXY32_QUALITY_STOP'};}
export function screenDecision(blocks,memory){const screen=costDecision(blocks,memory);return {screen,decision:screen.passed?'PROXY32_STRICT_FOLLOWUP_SCREEN':'QUALITY_PASS_NO_STRICT_DOMINANCE'};}
function parse(argv){const a={};for(let i=0;i<argv.length;i++){const flag=argv[i];if(flag==='--formal')a.formal=true;else if(['--out','--freeze','--baseline-root','--parent-archive'].includes(flag))a[flag.slice(2)]=argv[++i];else if(flag==='--help'){console.log('node --expose-gc run.mjs --formal --freeze FREEZE --baseline-root EXTRACTED_P7 --parent-archive P7.zip --out NEW_DIRECTORY');process.exit(0);}else throw new Error(`unknown option ${flag}`);}if(!a.formal||!a.out||!a.freeze||!a['baseline-root']||!a['parent-archive'])throw new Error('formal, freeze, parent archive, extracted baseline and fresh output required');return a;}
export async function main(argv=process.argv.slice(2)){
 const args=parse(argv);if(typeof global.gc!=='function'||os.endianness()!=='LE')throw new Error('requires --expose-gc and little-endian host');const hashes=sourceHashes(),freeze=load(args.freeze);if(!sameHashes(hashes,freeze.sourceHashes??freeze))throw new Error('new source freeze mismatch');
 const out=path.resolve(args.out);if(fs.existsSync(out)&&fs.readdirSync(out).length)throw new Error('output directory must be empty/new');fs.mkdirSync(out,{recursive:true});
 const manifest={phase:PHASE,version:1,formal:true,postResultFollowup:true,status:'running',protocolComplete:false,sourceHashes:hashes,config:CONFIG,planned:[NEW_ARM],inheritedQualityIds:INHERITED_IDS,newQualityIds:[NEW_ARM.id],newCases:[],completedIds:[],requiredExecutedIds:[NEW_ARM.id],skipped:[],baseline:null,reference:{inherited:true,id:REFERENCE_ID,selectedRole:'R3'},quality:{status:'not-run'},timing:{status:'not-run',order:TIMING_ORDER},timingContract:{clock:'performance.now CPU wall time; no renderer/GPU',freshStatePairedBlocks:6,warmupsPerArm:1,primaryIncludes:'packing, mapping setup, analytic path, exact graph, exchange including native P6 finite/energy checks, O(1) ledger/CFL/cumulative-energy validation, display mapping, phase bookkeeping',excluded:'authored input creation, hashes, archival observations/copies/range scans, compression, file IO, independent audit',gc:'forced before each trajectory outside enclosing interval; incidental GC inside included'},decision:null,executionValid:null,independentAudit:'pending-parent-reaudit-and-new-audit',host:{node:process.version,platform:process.platform,arch:process.arch,cpu:os.cpus()[0]?.model},startedAt:new Date().toISOString()};
 const write=()=>save(path.join(out,'manifest.json'),manifest);write();
 try{
  console.log('AUTHENTICATE P7 parent');const parent=await authenticateParent(args['baseline-root'],args['parent-archive']);manifest.baseline={before:parent.identity,after:null,unchanged:null};manifest.reference.signal=parent.signal;write();
  console.log(`START ${NEW_ARM.id}`);const authored=authoredInput(32),{result:proxy,record}=await qualityArm(NEW_ARM,authored,out,{onProgress:p=>console.log(`PROGRESS ${p.id} ${p.step}/${p.total}`)});
  manifest.newCases.push({id:NEW_ARM.id,role:'proxy',...record,history:proxy.history});manifest.completedIds.push(NEW_ARM.id);
  const comparison=compareObservations(proxy.observations,parent.reference.observations),gate=qualityDecision(parent.sharedComparison,comparison);
  manifest.quality={status:'completed',shared:{inherited:true,id:SHARED_ARM.id,passed:true,comparison:parent.sharedComparison},proxy:{inherited:false,id:NEW_ARM.id,passed:gate.proxyPassed,comparison}};write();
  if(!gate.timingAllowed){manifest.decision=gate.decision;manifest.timing={...manifest.timing,status:'skipped',reason:gate.decision};}
  else{manifest.timing={...manifest.timing,status:'running',warmups:[],runs:[],blocks:[]};write();const inputs={shared:authoredInput(64),proxy:authored},records={shared:parent.shared,proxy},definitions={shared:SHARED_ARM,proxy:NEW_ARM};
   for(const role of ['shared','proxy'])if(sha(JSON.stringify(inputs[role]))!==records[role].inputSHA256)throw new Error('timing input differs from quality');
   const runTimed=role=>{const t=timedArm(definitions[role],inputs[role]);if(!same(t.endpoint,records[role].finalEndpoint)||!same(t.memory,records[role].memory))throw new Error(`${role} fresh timing differs from authenticated quality`);return t;};
   for(const role of ['shared','proxy']){const t=runTimed(role);manifest.timing.warmups.push({role,endpoint:t.endpoint});}
   for(let block=0;block<6;block++){const b={block};for(const role of TIMING_ORDER[block]){const t=runTimed(role);manifest.timing.runs.push({block,role,...t});b[role]=t.wholeTrajectoryMs;}manifest.timing.blocks.push(b);write();console.log(`TIMING ${block+1}/6`);}
   for(const role of ['shared','proxy'])if(sha(JSON.stringify(inputs[role]))!==records[role].inputSHA256)throw new Error('timing authored input mutated');manifest.timing.authoredInputsUnchanged=true;
   const decision=screenDecision(manifest.timing.blocks,{shared:parent.shared.memory,proxy:proxy.memory});manifest.timing.status='completed';manifest.timing.screen=decision.screen;manifest.decision=decision.decision;
  }
  console.log('RECHECK P7 parent');const after=await authenticateParent(args['baseline-root'],args['parent-archive']);manifest.baseline.after=after.identity;manifest.baseline.unchanged=same(parent.identity,after.identity);if(!manifest.baseline.unchanged)throw new ParentEvidenceError('parent dependencies changed during run');
  manifest.protocolComplete=same(manifest.completedIds,manifest.requiredExecutedIds);if(!manifest.protocolComplete)throw new Error('new quality evidence incomplete');manifest.executionValid=true;manifest.status='completed-pending-independent-audit';
 }catch(error){manifest.executionValid=false;manifest.status='execution_failed';manifest.decision=error instanceof ParentEvidenceError?'PARENT_EVIDENCE_INVALID':'EXECUTION_INVALID';manifest.error=String(error.stack??error);throw error;}
 finally{manifest.sourceHashesAfter=sourceHashes();manifest.sourcesUnchanged=sameHashes(hashes,manifest.sourceHashesAfter);if(!manifest.sourcesUnchanged){manifest.executionValid=false;manifest.status='execution_failed';manifest.decision='EXECUTION_INVALID';}manifest.finishedAt=new Date().toISOString();write();}
 return manifest;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))await main();
