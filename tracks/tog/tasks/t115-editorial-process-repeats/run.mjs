import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const self=fileURLToPath(import.meta.url),here=path.dirname(self),outDir=path.join(here,'evidence');
const frozen=path.join(here,'../t111-playground-shot-choice'),sha=x=>createHash('sha256').update(x).digest('hex');
const args=process.argv.slice(2);
if(args[0]!=='--block'){
  assert(args.length===0 || args.join()==='--check');
  for(let round=1;round<=4;round++){
    // Reversing scene order every round also reverses which dataset starts the experiment.
    const scenes=round%2?['firewoods','playground']:['playground','firewoods'];
    for(const scene of scenes){
      const child=spawn(process.execPath,[self,'--block',scene,String(round),...args],{stdio:'inherit',windowsHide:true});
      const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});
      if(code!==0)throw Error('Block failed: '+scene+' / '+round+', exit '+code);
    }
    if(args.length)break;
  }
}else{
  const [_,scene,num,check]=args;
  const round=Number(num);
  assert(['playground','firewoods'].includes(scene)&&round>=1&&round<=4&&[undefined,'--check'].includes(check));
  const wood=scene==='firewoods',study=wood?path.join(here,'../t109-common-parent-choice'):frozen;
  const camera=wood?124:153,name=scene+'-'+round;
  const local=path.join(here,'local',name), out=path.join(outDir,name);
  const methodOrder=round===1 || round===4?['ordinary','repair']:['repair','ordinary'];
  await fs.mkdir(local,{recursive:true});
  async function pinned(p,hash){const b=await fs.readFile(p);assert.equal(sha(b),hash,p);return b.toString('utf8');}
  await pinned(path.join(frozen,'local/action.js'),'a5da0325a4e99dab95ef7463cc456b212b3cb5b75add2161ec4738b1741b0aad');
  let main=await pinned(path.join(frozen,'run.mjs'),'581693bc34568f0d8dc77fdddf18742cc336c9237c98d204d53fd5c355707ae5');
  let block=await pinned(path.join(frozen,'worker.txt'),'c55b1f29f056a6947fa438c1759b1a4a553ea744dcef3e660db6ecadd98dd400');
  const change=(a,b)=>{assert.equal(main.split(a).length,2,a);main=main.replace(a,()=>b);};
  block=block.replace('[[0],[153],[0,153]]','[[0],[0,153]]').replaceAll('153',String(camera));
  const a=block.indexOf('          for(const pick of picksLF){'),b=block.indexOf('        const b=await page.evaluate',a);
  assert(a>0&&b>a);block=block.slice(0,a)+'        }\n'+block.slice(b);
  change('const here=path.dirname(fileURLToPath(import.meta.url)),prior=','const here='+JSON.stringify(study)+',prior=');
  change(",local=path.join(here,'local');",",local="+JSON.stringify(local)+";");
  change("const specs=['ordinary','restart','repair'];","const specs=['ordinary','repair'];");
  change("'ordinary,restart,repair','--repeats','3'",JSON.stringify(methodOrder.join(','))+",'--repeats','2'");
  change('schema:\'t111-end-to-end-editorial-choice-v1\'',"schema:'t115-process-repeats-v1'");
  change("await fs.readFile(path.join(here,'worker.txt'),'utf8')",JSON.stringify(block));
  change("path.join(here,'TIMING_PROTOCOL.md')",JSON.stringify(path.join(here,'PROTOCOL.md')));
  if(wood)change("for(const camera of [0,153])","for(const camera of [0,"+camera+"])");
  if(wood){
    change("path.join(here,'weights-'+camera+'.json.gz')","path.join(here,'../t107-visible-burn-progression/evidence/weights-'+camera+'.json.gz')");
    change("path.join(here,'../t101-playground-holdout/local/scene.ply')","(process.env.T86_PLY||path.resolve(here,'../../../../../real-asset-ingest/foreground.ply'))");
  }
  change('JSON.stringify(portable(fileURLToPath(import.meta.url)))','JSON.stringify('+JSON.stringify(self.split(path.sep).join('/'))+')');
  const dest=path.join(local,'run.mjs');await fs.writeFile(dest,main);
  process.argv=process.argv.slice(0,2).concat(check?['--check']:['--out',out]);
  console.log(name,methodOrder.join(','),check?'preflight':'timing');
  await import(pathToFileURL(dest));
}
