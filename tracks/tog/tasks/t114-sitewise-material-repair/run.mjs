import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {Script} from 'node:vm';
const own=path.dirname(fileURLToPath(import.meta.url)),here=path.join(own,'../t108-visible-progression');
const portable=p=>p.split(path.sep).join('/'),sha=s=>createHash('sha256').update(s).digest('hex');
function once(s,a,b){assert.equal(s.split(a).length,2,a);return s.replace(a,()=>b);}
async function pinned(f,h){const raw=await fs.readFile(f,'utf8');if(h)assert.equal(sha(raw),h);return raw;}
const local=path.join(own,'local');await fs.mkdir(local,{recursive:true});
const extra='../t114-sitewise-material-repair/local/firewoods.js';
let plugin=await pinned(path.join(here,'local/plugin.js'),'5bdc5de90e92be04e84741b78329ad1cf563c27d79c8e750e3001f6548bb41e0');
plugin=once(plugin,"const retain=mode==='repair' && length<remain;","const retain=mode!=='restart' && length<remain;");
plugin=once(plugin,'for(const frame of logs)t100ReplayActive(frame,dt);','(work.recovery_blocks??=[]).push(t114Repair(mode,logs,dt,profile));');
plugin=once(plugin,"!['ordinary','restart','repair'].includes(mode)","!['ordinary','repair','sparse','sitewise'].includes(mode)");
plugin=plugin.replaceAll('boundaries[researchFrame]=t108Fingerprint()','boundaries[researchFrame]=t114Boundary(dt)');
plugin+='\nfunction t114Boundary(dt){const now=t108Fingerprint(),fork=t90Fork();try{t94StepFull(dt);return {now,next:t108Fingerprint()};}finally{t90Restore(fork);}}';
new Script(plugin);await fs.writeFile(path.join(local,'firewoods.js'),plugin);
let block=await pinned(path.join(here,'worker-block.js.txt'),'c43ff00cb21f73a41b27c6345aea9c3c6ab54f9674ca985dd7b78c17600d9902');
block=once(block,"['repair','ordinary','restart']","['repair','ordinary','sparse','sitewise']");
block=once(block,"if(m==='ordinary')assert.deepEqual(result.boundaries,shot.progress_audits.repair.boundaries,'Repair physical states');",
 "if(m!=='repair')assert.deepEqual(result.boundaries,shot.progress_audits.repair.boundaries,'Complete and one-step native continuation');");
const weight=path.join(here,'../t107-visible-burn-progression/evidence/weights-0.json.gz');
block=block.replace('WEIGHT_PATH',JSON.stringify(portable(weight)));
const prior=path.join(here,'../t98-edit-to-answer'),origin=pathToFileURL(path.join(prior,'run.mjs'));
let text=await pinned(fileURLToPath(origin),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function change(a,b){text=once(text,a,b);}
change("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
change("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];",
 "const specs=['ordinary','repair','sparse','sitewise'];");
change("schema:'t98-delivered-edit-to-answer-v1'","schema:'t114-sitewise-repair-v1'");
change("path.join(here,'REFERENCE.json')",JSON.stringify(path.join(here,'REFERENCE.json')));
const a=text.indexOf('source=source.slice(0,first)+'),b=text.indexOf('+source.slice(last);',a);
assert(a>0 && b>a);text=text.slice(0,a)+'source=source.slice(0,first)+'+JSON.stringify(block+'\n')+text.slice(b);
change("'local/dispatch.js'",JSON.stringify(portable(path.relative(prior,path.join(local,'dispatch.js')))));
const extras=['../t100-material-repair/local/plugin.js','../t102-active-recipients/local/plugin.js',
  '../t100-material-repair/local/active-repair.js','click.js','../t106-sparse-heat-scan/local/plugin.js',
  '../t114-sitewise-material-repair/repair.js',extra];
change("'click.js'];",extras.map(s=>JSON.stringify(s)).join(',')+'];');
change("await input('T98_runner',","await input('T114_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T114_protocol',"+JSON.stringify(portable(path.join(own,'PROTOCOL.md')))+");await input('T98_runner',");
const flags=process.argv.slice(2),check=flags.length===1&&flags[0]==='--check';
assert(check || flags.length===0 || flags.length===2&&flags[0]==='--out');
process.argv=process.argv.slice(0,2).concat('--methods','ordinary,repair,sparse,sitewise','--repeats','4','--out',flags[1]||path.join(own,'evidence/firewoods'));
if(check)process.argv.push('--check');
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}
