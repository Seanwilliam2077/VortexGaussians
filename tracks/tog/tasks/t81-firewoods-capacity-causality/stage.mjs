// Static source preparation only: no browser, simulation or numerical import.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const root=process.cwd(),here=path.join(root,'tracks/tog/tasks/t81-firewoods-capacity-causality');
const sha=b=>createHash('sha256').update(b).digest('hex');
const source=await fs.readFile(path.join(root,'demo/index.html'),'utf8');
if(sha(source)!=='e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0')throw Error('Original demo identity mismatch');
const camera=await fs.readFile(path.join(root,'tracks/tog/tasks/t42-firewoods-sequential-workflow/adapter.js'),'utf8');
const adapter=await fs.readFile(path.join(here,'adapter.js'),'utf8');
const patches=[
  ['const full=L.ps.length>=P.ppl; let recycle=-1;','const full=t81CapacityFull(L,i,k); let recycle=-1;'],
  ['spreadCounters.sceneSeedsEmitted++; spreadRegion(i).sceneSeedsEmitted++;','t81Admitted(sp,i,k);\n      spreadCounters.sceneSeedsEmitted++; spreadRegion(i).sceneSeedsEmitted++;'],
  ['} else spreadCounters.sceneFeedRandomRejected++;','} else spreadCounters.sceneFeedRandomRejected++;\n    t81OfferEnd();'],
  ['window.__demo = {','// T81 EXTENSION BEGIN\n'+camera+'\n'+adapter+'\n// T81 EXTENSION END\nwindow.__demo = {']
];
let candidate=source;
for(const [from,to]of patches){if(candidate.split(from).length!==2)throw Error('Patch marker not unique: '+from);candidate=candidate.replace(from,to);}
let reversed=candidate;for(const [from,to]of [...patches].reverse()){if(reversed.split(to).length!==2)throw Error('Reverse marker not unique');reversed=reversed.replace(to,from);}
if(reversed!==source)throw Error('Patch reversal is not exact');
let scripts=0;for(const m of candidate.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)){new vm.Script(m[1]);scripts++;}
if(!scripts)throw Error('No inline scripts compiled');
const out=path.join(here,'local/site/demo/index.html');await fs.mkdir(path.dirname(out),{recursive:true});
try{const old=await fs.readFile(out,'utf8');if(old!==candidate){
  if(!process.argv.includes('--refresh-unconsumed'))throw Error('Existing staged source differs; use explicit --refresh-unconsumed after review');
  try{await fs.access(path.join(here,'invocation.json'));throw Error('Consumed attempt cannot refresh');}catch(e){if(e.code!=='ENOENT')throw e;}
  const archive=path.join(here,'local/preparation-history');await fs.mkdir(archive,{recursive:true});
  const previous=path.join(archive,sha(old)+'.html');
  try{await fs.writeFile(previous,old,{flag:'wx'});}catch(e){if(e.code!=='EEXIST')throw e;else if(await fs.readFile(previous,'utf8')!==old)throw Error('Previous candidate archive differs');}
  await fs.writeFile(out,candidate);
  await fs.appendFile(path.join(archive,'revisions.jsonl'),JSON.stringify({old_sha256:sha(old),new_sha256:sha(candidate),reason:'Pre-execution independent-review corrections; no scientific invocation'})+'\n');
}}
catch(e){if(e.code==='ENOENT')await fs.writeFile(out,candidate,{flag:'wx'});else throw e;}
const receipt={schema:'t81-static-staging-v1',source_sha256:sha(source),candidate_sha256:sha(candidate),
  camera_adapter_sha256:sha(camera),observation_adapter_sha256:sha(adapter),reverse_exact:true,
  inline_scripts_syntax_checked:scripts,scientific_executions:0,
  changed_native_expressions:['admission full predicate'],observational_hooks:['emitted particle identity','completed offer observation'],
  source_path:'demo/index.html',candidate_path:'tracks/tog/tasks/t81-firewoods-capacity-causality/local/site/demo/index.html'};
await fs.writeFile(path.join(here,'staging.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
