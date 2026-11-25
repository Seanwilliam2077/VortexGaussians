// Keep the same complete action, inputs and coupled particle solver as T111.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Script} from 'node:vm';
const here=path.dirname(fileURLToPath(import.meta.url)), prior=path.join(here,'../../t111-playground-shot-choice');
const local=path.join(here,'local'),sha=x=>createHash('sha256').update(x).digest('hex');
async function pin(file,expected){
  const raw=await fs.readFile(file);assert.equal(sha(raw),expected,file);return raw.toString('utf8');
}
function changed(src,a,b){assert.equal(src.split(a).length,2,a);return src.replace(a,()=>b);}
const heat=path.join(here,'../../t106-sparse-heat-scan/local/plugin.js'), kernel=path.join(here,'../repair.js');
await pin(heat,'0cf15b19d7b284faff0e80b4523795b02ab199dca0f3e868196f4adc3197fc78');
await pin(kernel,'89fa0f7e380d03875c7c0cac9c24a8d2fee88d48c878de09bbe1bcf54235b682');
let acts=await pin(path.join(prior,'local/action.js'),'a5da0325a4e99dab95ef7463cc456b212b3cb5b75add2161ec4738b1741b0aad');
acts=changed(acts,"['ordinary','restart','repair'].includes(mode)","['ordinary','repair','sparse','sitewise'].includes(mode)");
acts=changed(acts,"const retain=mode==='repair' && length<remain;","const retain=mode!=='ordinary' && length<remain;");
acts=changed(acts,"const work={guards:[],","const work={recovery_blocks:[],guards:[],");
acts=changed(acts,"for(const frame of logs)t100ReplayActive(frame,dt);","work.recovery_blocks.push(t114Repair(mode,logs,dt,profile));");
assert.equal(acts.split('=t108Fingerprint();').length,3);
acts=acts.replaceAll('=t108Fingerprint();','=t114StateNext(dt);');
const audit=`
function t114StateNext(dt){
  const state=t108Fingerprint();
  const saved=t90Fork();let next;
  try{t94StepFull(dt);next=t108Fingerprint();}finally{t90Restore(saved);}
  return {state,next};
}
`;
acts+=audit;new Script(acts);
await fs.mkdir(local,{recursive:true});await fs.writeFile(path.join(local,'action.js'),acts);
let main=await pin(path.join(prior,'run.mjs'),'581693bc34568f0d8dc77fdddf18742cc336c9237c98d204d53fd5c355707ae5');
const edit=(a,b)=>{main=changed(main,a,b);};
edit('const here=path.dirname(fileURLToPath(import.meta.url)),prior=','const here='+JSON.stringify(prior)+',prior=');
edit(",local=path.join(here,'local');",",local="+JSON.stringify(local)+";");
edit("schema:'t111-end-to-end-editorial-choice-v1'","schema:'t114-recovery-editorial-choice-v1'");
edit("const specs=['ordinary','restart','repair'];","const specs=['ordinary','repair','sparse','sitewise'];");
edit("'ordinary,restart,repair','--repeats','3'","'ordinary,repair,sparse,sitewise','--repeats','4'");
edit("'../t111-playground-shot-choice/local/action.js'","'../t106-sparse-heat-scan/local/plugin.js','../t114-sitewise-material-repair/repair.js','../t114-sitewise-material-repair/playground/local/action.js'");
edit("path.join(here,'evidence/timing')",JSON.stringify(path.join(here,'evidence')));
edit("path.join(here,'TIMING_PROTOCOL.md')",JSON.stringify(path.join(here,'../PROTOCOL.md')));
edit('JSON.stringify(portable(fileURLToPath(import.meta.url)))','JSON.stringify('+JSON.stringify(fileURLToPath(import.meta.url).split(path.sep).join('/'))+')');
let block=await pin(path.join(prior,'worker.txt'),'c55b1f29f056a6947fa438c1759b1a4a553ea744dcef3e660db6ecadd98dd400');
block=changed(block,"['repair','ordinary','restart']","['repair','sparse','sitewise','ordinary']");
block=changed(block,"if(m==='ordinary')assert.deepEqual(r.boundaries,reports.repair.boundaries,'Physical material repair state');",
                    "if(m!=='repair')assert.deepEqual(r.boundaries,reports.repair.boundaries,'Physical state at boundary and next native step');");
edit("await fs.readFile(path.join(here,'worker.txt'),'utf8')",JSON.stringify(block));
const dest=path.join(local,'driver.mjs');await fs.writeFile(dest,main);
console.log('Action SHA256',sha(acts));await import(pathToFileURL(dest));
