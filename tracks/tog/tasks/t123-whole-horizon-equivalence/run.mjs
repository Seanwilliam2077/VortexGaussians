import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';
import {build} from '../t119-cross-sibling-actions/build.mjs';

const self=fileURLToPath(import.meta.url), here=path.dirname(self),tasks=path.dirname(here);
const template=path.join(tasks,'t111-playground-shot-choice');
const config={
  lower:['t121-lower-band-joint-choice',[76,230]],
  firewoods:['t109-common-parent-choice',[0,124]],
  playground:['t111-playground-shot-choice',[0,153]]
};
const sha=x=>createHash('sha256').update(x).digest('hex');
const args=process.argv.slice(2);
if (!args.length) {
  for (const [scene,round] of [['lower',1],['lower',2],['firewoods',1],['playground',1]]) {
    const child=spawn(process.execPath,[self,scene,String(round)],{stdio:'inherit',windowsHide:true});
    const code=await new Promise((resolve,reject)=>{child.once('exit',resolve);child.once('error',reject);});
    if(code!==0)throw Error('Failed capture '+scene+' '+round);
  }
} else {
  const [scene,index,check]=args, round=Number(index);
  assert(Object.hasOwn(config,scene)&&[1,2].includes(round)&&[undefined,'--check','--selection'].includes(check));
  const [folder,views]=config[scene],study=path.join(tasks,folder);
  const local=path.join(here,'local',scene+'-'+round);
  const selection=check==='--selection';
  if(selection)assert(scene==='lower');
  const out=path.join(here,'evidence',selection?'selection-restoration':scene+'-'+round);
  const groups=scene==='lower' && !selection?['cold-ordinary','cold-repair','cold-sibling','equiv-ordinary','equiv-repair']:['equiv-ordinary','equiv-repair'];
  const order=round===1?groups:groups.slice().reverse(), repetitions=scene==='lower' && !selection?5:1;
  await fs.mkdir(local,{recursive:true});await fs.mkdir(path.dirname(out),{recursive:true});
  const plugin=await build(path.join(tasks,'t119-cross-sibling-actions'),local);
  assert.equal(sha(await fs.readFile(plugin)),'1505050a662c4d4d2561346eeff98d9a0d099485d78614a706cfb7a10a3ac0f1');
  let main=await fs.readFile(path.join(template,'run.mjs'),'utf8');
  let worker=await fs.readFile(path.join(template,'worker.txt'),'utf8');
  assert.equal(sha(main),'581693bc34568f0d8dc77fdddf18742cc336c9237c98d204d53fd5c355707ae5');
  assert.equal(sha(worker),'c55b1f29f056a6947fa438c1759b1a4a553ea744dcef3e660db6ecadd98dd400');
  function patch(s,old,value) {assert.equal(s.split(old).length,2,old);return s.replace(old,()=>value);}
  function change(a,b) {main=patch(main,a,b);}
  const cutoff=worker.indexOf('          for(const pick of picksLF){');
  const resume=worker.indexOf('        const b=await page.evaluate',cutoff);
  assert(cutoff>=0&&resume>cutoff);
  worker=worker.slice(0,cutoff)+'        }\n'+worker.slice(resume);
  worker=patch(worker,'for(const camera of [0,153])','for(const camera of '+JSON.stringify(views)+')');
  worker=patch(worker,'[[0],[153],[0,153]]',JSON.stringify([views]));
  worker=patch(worker,'__t111.cold()','__t119.cold()');
  worker=patch(worker,'__t111.action',selection?'__t123CheckSelection':'__t123');
  change('const here=path.dirname(fileURLToPath(import.meta.url)),prior=', 'const here='+JSON.stringify(study)+',prior=');
  change(",local=path.join(here,'local');",",local="+JSON.stringify(local)+";");
  change("const specs=['ordinary','restart','repair'];","const specs=['"+order.join("','")+"'];");
  change("'ordinary,restart,repair','--repeats','3'",JSON.stringify(order.join(','))+",'--repeats','"+repetitions+"'");
  change("schema:'t111-end-to-end-editorial-choice-v1'","schema:'t123-whole-horizon-equivalence'");
  change("for(const camera of [0,153])","for(const camera of "+JSON.stringify(views)+")");
  change("await fs.readFile(path.join(here,'worker.txt'),'utf8')",JSON.stringify(worker));
  change("path.join(here,'TIMING_PROTOCOL.md')",JSON.stringify(path.join(here,'PROTOCOL.md')));
  if (scene==='firewoods') {
    change("path.join(here,'weights-'+camera+'.json.gz')","path.join(here,'../t107-visible-burn-progression/evidence/weights-'+camera+'.json.gz')");
    change("path.join(here,'../t101-playground-holdout/local/scene.ply')","(process.env.T86_PLY||path.resolve(here,'../../../../../real-asset-ingest/foreground.ply'))");
  }
  const prior=path.join(tasks,'t98-edit-to-answer'), eq=path.join(here,'equivalence.js');
  const auditFiles=selection?[path.join(here,'selection-audit.js')]:[];
  const extras=[plugin,eq,...auditFiles].map(f=>JSON.stringify(path.relative(prior,f).split(path.sep).join('/')));
  change("'../t111-playground-shot-choice/local/action.js'];","'../t111-playground-shot-choice/local/action.js',"+extras.join(',')+"];");
  change('JSON.stringify(portable(fileURLToPath(import.meta.url)))','JSON.stringify('+JSON.stringify(self.split(path.sep).join('/'))+')');
  const staged=path.join(local,'run.mjs');
  await fs.writeFile(staged,main);
  process.argv=process.argv.slice(0,2).concat(check==='--check'?['--check']:['--out',out]);
  await import(pathToFileURL(staged));
}
