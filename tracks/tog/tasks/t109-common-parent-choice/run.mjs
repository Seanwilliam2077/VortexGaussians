import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),prior=path.resolve(here,'../t98-edit-to-answer');
const origin=pathToFileURL(path.join(prior,'run.mjs')),local=path.join(here,'local');
await fs.mkdir(local,{recursive:true});
const sha=s=>createHash('sha256').update(s).digest('hex'),portable=s=>s.split(path.sep).join('/');
let text=await fs.readFile(origin,'utf8');
assert.equal(sha(text),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function change(a,b){assert.equal(text.split(a).length,2,a);text=text.replace(a,()=>b);}
change("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
change("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];","const specs=['ordinary','restart','repair'];");
change("schema:'t98-delivered-edit-to-answer-v1'","schema:'t109-common-parent-choice-v1'");
change("path.join(here,'REFERENCE.json')",JSON.stringify(path.join(here,'REFERENCE.json')));
const stat=JSON.parse(await fs.readFile(path.join(here,'STATIC.json')));
const files={};
for(const cam of [0,124]){
  files[cam]=portable(path.join(here,'../t107-visible-burn-progression/evidence/weights-'+cam+'.json.gz'));
  assert.equal(sha(await fs.readFile(files[cam])),stat.cameras[cam].sha256);
}
const operator=path.join(here,'../t108-visible-progression/local/plugin.js');
assert.equal(sha(await fs.readFile(operator)),'5bdc5de90e92be04e84741b78329ad1cf563c27d79c8e750e3001f6548bb41e0','Validated T108 original operator');
const block=(await fs.readFile(path.join(here,'worker.txt'),'utf8')).replace('FILES[camera]','('+JSON.stringify(files)+')[camera]');
const a=text.indexOf('source=source.slice(0,first)+'),b=text.indexOf('+source.slice(last);',a);
assert(a>0 && b>a);
text=text.slice(0,a)+'source=source.slice(0,first)+'+JSON.stringify(block+'\n')+text.slice(b);
change("'local/dispatch.js'",JSON.stringify(portable(path.relative(prior,path.join(local,'dispatch.js')))));
const extras=['../t100-material-repair/local/plugin.js','../t102-active-recipients/local/plugin.js',
  '../t100-material-repair/local/active-repair.js','click.js','../t108-visible-progression/local/plugin.js','../t109-common-parent-choice/wrapper.js'];
change("'click.js'];",extras.map(s=>JSON.stringify(s)).join(',')+'];');
change("await input('T98_runner',","await input('T109_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T109_protocol',"+JSON.stringify(portable(path.join(here,'PROTOCOL.md')))+");await input('T98_runner',");
const shell=JSON.stringify(portable(path.join(here,'shell.json.gz')));
const checkShell=JSON.stringify("assert.deepEqual(ids,JSON.parse(gunzipSync(await input('frozen_static_shell',"+shell+"))));const idSet=new Set(ids);");
change("try {await import",`assert(source.split("['AB','BA']").length===3);
source=source.replaceAll("['AB','BA']","['AL','AF']");
change("p=>__t90.configure(p),picks[1]", "p=>__t90.configure({...p,radius:.12}),picks[1]");
change("const idSet=new Set(ids);", ${checkShell});
try {await import`);
const args=process.argv.slice(2);
assert(args.length===0 || args.join()==='--check' || args.length===2&&args[0]==='--out');
const native=path.join(here,'evidence/native');
process.argv=process.argv.slice(0,2).concat('--methods','ordinary,restart,repair','--repeats','3','--out',args[1]||path.join(here,'evidence/timing'),
  '--recipe',path.join(here,'recipe.json'),'--asset',process.env.T86_PLY||path.resolve(here,'../../../../../real-asset-ingest/foreground.ply'),
  '--reference',path.join(native,'capture-report.json'),'--traces',native);
if(args[0]==='--check')process.argv.push('--check');
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(error){console.error(String(error));process.exitCode=1;}
