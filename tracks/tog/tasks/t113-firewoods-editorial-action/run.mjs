import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url)),study=path.join(here,'../t109-common-parent-choice');
const frozen=path.join(here,'../t111-playground-shot-choice'),local=path.join(here,'local');
const sha=x=>createHash('sha256').update(x).digest('hex');
async function read(file,digest){
  const data=await fs.readFile(file);
  assert.equal(sha(data),digest,path.basename(file));
  return data.toString();
}
await fs.mkdir(local,{recursive:true});
let s=await read(path.join(frozen,'run.mjs'),'581693bc34568f0d8dc77fdddf18742cc336c9237c98d204d53fd5c355707ae5');
const worker=await read(path.join(frozen,'worker.txt'),'c55b1f29f056a6947fa438c1759b1a4a553ea744dcef3e660db6ecadd98dd400');
await read(path.join(frozen,'local/action.js'),'a5da0325a4e99dab95ef7463cc456b212b3cb5b75add2161ec4738b1741b0aad');
await read(path.join(study,'REFERENCE.json'),'1931f2697447bae9fd0b5a55c7dfeab1815638e33ccb8b46bbb582dfaa6a010b');
await read(path.join(study,'recipe.json'),'221d92f20fec0c6b5bba3b730d054948dc55cd2226e9ed4df02a1be695209eb4');
function replace(a,b){assert.equal(s.split(a).length,2,a);s=s.replace(a,()=>b);}
replace('const here=path.dirname(fileURLToPath(import.meta.url)),prior=','const here='+JSON.stringify(here)+',prior=');
replace("JSON.stringify(path.join(here,'REFERENCE.json'))","JSON.stringify("+JSON.stringify(path.join(study,'REFERENCE.json'))+")");
for(const name of ['STATIC.json','shell.json.gz','recipe.json','evidence/native']){
  replace("path.join(here,'"+name+"')",JSON.stringify(path.join(study,name)));
}
replace("path.join(here,'TIMING_PROTOCOL.md')","path.join(here,'PROTOCOL.md')");
replace("path.join(here,'weights-'+camera+'.json.gz')","path.join(here,'../t107-visible-burn-progression/evidence/weights-'+camera+'.json.gz')");
replace("path.join(here,'../t101-playground-holdout/local/scene.ply')","(process.env.T86_PLY||path.resolve(here,'../../../../../real-asset-ingest/foreground.ply'))");
replace('for(const camera of [0,153])','for(const camera of [0,124])');
replace("await fs.readFile(path.join(here,'worker.txt'),'utf8')",JSON.stringify(worker.replaceAll('153','124')));
replace("schema:'t111-end-to-end-editorial-choice-v1'","schema:'t113-retrospective-editorial-choice-v1'");
replace('JSON.stringify(portable(fileURLToPath(import.meta.url)))','JSON.stringify('+JSON.stringify(fileURLToPath(import.meta.url).split(path.sep).join('/'))+')');
const target=path.join(local,'run.mjs');await fs.writeFile(target,s);
await import(pathToFileURL(target));
