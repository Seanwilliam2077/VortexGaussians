import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {build} from '../t119-cross-sibling-actions/build.mjs';

const self=fileURLToPath(import.meta.url), here=path.dirname(self), t111=path.join(here,'../t111-playground-shot-choice');
const sha=x=>createHash('sha256').update(x).digest('hex');
const methods=['cold-ordinary','cold-repair','cold-sibling'];
const orders=[[0,1,2],[2,1,0],[1,2,0],[0,2,1]].map(row=>row.map(i=>methods[i]));
const args=process.argv.slice(2);
async function source(name,file,expected){
  const bytes=await fs.readFile(file);
  if(expected)assert.equal(sha(bytes),expected,name);
  return bytes.toString('utf8');
}
if(args.length===0) {
  for(let round=1;round<=4;round++){
    const child=spawn(process.execPath,[self,'--block',String(round)],{stdio:'inherit',windowsHide:true});
    const status=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});
    if(status!==0)throw Error('Failed process block '+round);
  }
} else {
  assert(['--block','--stage','--verify'].includes(args[0]) && /^[1-4]$/.test(args[1]) && args.length===2);
  const verifying=args[0]==='--verify';
  const round=Number(args[1]), local=path.join(here,'local','block-'+round);
  await fs.mkdir(local,{recursive:true});
  const plugin=await build(path.join(here,'../t119-cross-sibling-actions'),local);
  await source('unchanged T119 complete three-way kernel',plugin,'1505050a662c4d4d2561346eeff98d9a0d099485d78614a706cfb7a10a3ac0f1');
  let main=await source('T111 driver',path.join(t111,'run.mjs'),'581693bc34568f0d8dc77fdddf18742cc336c9237c98d204d53fd5c355707ae5');
  let block=await source('T111 worker',path.join(t111,'worker.txt'),'c55b1f29f056a6947fa438c1759b1a4a553ea744dcef3e660db6ecadd98dd400');
  const patch=(s,from,to)=>{assert.equal(s.split(from).length,2,from);return s.replace(from,()=>to);};
  const change=(a,b)=>{main=patch(main,a,b);};
  block=patch(block,'for(const camera of [0,153])','for(const camera of [76,230])');
  block=patch(block,'for(const cams of [[0],[153],[0,153]])',
    'report.common_parent_successor=await page.evaluate(dt=>__t121.parent(dt),cfg.dt);\n          for(const cams of [[76,230]])');
  block=patch(block,'__t111.action','__t119.action');
  block=patch(block,'__t111.cold()','__t119.cold()');
  block=patch(block,"for(const k of fields)assert.equal(r[k],e[k],pick+' view '+r.camera+' '+k);",
    "for(const k of fields)if(e.defined || k!=='count')assert.equal(r[k],e[k],pick+' view '+r.camera+' '+k);");
  const start=block.indexOf('          for(const pick of picksLF){'),end=block.indexOf('        const b=await page.evaluate',start);
  assert(start>0 && end>start);
  block=block.slice(0,start)+await source('audit',path.join(here,'audit-worker.txt'))+'\n        }\n'+block.slice(end);
  change('const here=path.dirname(fileURLToPath(import.meta.url)),prior=', 'const here='+JSON.stringify(here)+',prior=');
  change(",local=path.join(here,'local');",",local="+JSON.stringify(local)+";");
  change("const specs=['ordinary','restart','repair'];","const specs=['"+methods.join("','")+"'];");
  change("'ordinary,restart,repair','--repeats','3'",JSON.stringify(orders[round-1].join(','))+",'--repeats','"+(verifying?1:6)+"'");
  change("schema:'t111-end-to-end-editorial-choice-v1'",verifying?"schema:'t121-physical-precheck-v1'":"schema:'t121-new-lower-band-playground-v1'");
  change('for(const camera of [0,153])','for(const camera of [76,230])');
  change("await fs.readFile(path.join(here,'worker.txt'),'utf8')",JSON.stringify(block));
  change("path.join(here,'TIMING_PROTOCOL.md')",JSON.stringify(path.join(here,'PROTOCOL.md')));
  const prior=path.join(here,'../t98-edit-to-answer');
  const extras=[plugin,path.join(here,'audit.js')].map(f=>JSON.stringify(path.relative(prior,f).split(path.sep).join('/')));
  change("'../t111-playground-shot-choice/local/action.js'];","'../t111-playground-shot-choice/local/action.js',"+extras.join(',')+"];");
  change('JSON.stringify(portable(fileURLToPath(import.meta.url)))','JSON.stringify('+JSON.stringify(self.split(path.sep).join('/'))+')');
  const dest=path.join(local,'run.mjs');await fs.writeFile(dest,main);
  console.log('T121',round,orders[round-1].join(','),sha(block),sha(await fs.readFile(plugin)));
  if(args[0]==='--block'||verifying){
    const destination=verifying?path.join(here,'evidence','physical-precheck'):path.join(here,'evidence','corrected','block-'+round);
    process.argv=process.argv.slice(0,2).concat('--out',destination);
    await import(pathToFileURL(dest));
  }
}
