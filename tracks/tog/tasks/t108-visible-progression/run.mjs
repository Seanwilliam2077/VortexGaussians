import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),prior=path.resolve(here,'../t98-edit-to-answer');
const origin=pathToFileURL(path.join(prior,'run.mjs')),local=path.join(here,'local');
await fs.mkdir(local,{recursive:true});
const sha=s=>createHash('sha256').update(s).digest('hex'), portable=p=>p.split(path.sep).join('/');
let text=await fs.readFile(origin,'utf8');
assert.equal(sha(text),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function change(a,b){assert.equal(text.split(a).length,2,a);text=text.replace(a,()=>b);}
change("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
change("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];",
       "const specs=['ordinary','restart','repair'];");
change("schema:'t98-delivered-edit-to-answer-v1'","schema:'t108-visible-progression-v1'");
change("path.join(here,'REFERENCE.json')",JSON.stringify(path.join(here,'REFERENCE.json')));
const weight=path.join(here,'../t107-visible-burn-progression/evidence/weights-0.json.gz');
assert.equal(sha(await fs.readFile(weight)),'08aade341633cada213895141ae6bbfe0b36ebaa2e729b9227b9fb668caaf432');
const block=(await fs.readFile(path.join(here,'worker-block.js.txt'),'utf8')).replace('WEIGHT_PATH',JSON.stringify(portable(weight)));
const a=text.indexOf('source=source.slice(0,first)+'),b=text.indexOf('+source.slice(last);',a);
assert(a>0 && b>a);
text=text.slice(0,a)+'source=source.slice(0,first)+'+JSON.stringify(block+'\n')+text.slice(b);
change("'local/dispatch.js'",JSON.stringify(portable(path.relative(prior,path.join(local,'dispatch.js')))));
const extras=['../t100-material-repair/local/plugin.js','../t102-active-recipients/local/plugin.js',
  '../t100-material-repair/local/active-repair.js','click.js','../t108-visible-progression/local/plugin.js'];
change("'click.js'];",extras.map(s=>JSON.stringify(s)).join(',')+'];');
change("await input('T98_runner',","await input('T108_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T108_protocol',"+JSON.stringify(portable(path.join(here,'PROTOCOL.md')))+");await input('T98_runner',");
const flags=process.argv.slice(2);
assert(flags.length===0 || (flags.length===2 && flags[0]==='--out'),'Optional --out NEW_DIR');
process.argv=process.argv.slice(0,2).concat('--methods','ordinary,restart,repair','--repeats','3','--out',flags[1]||path.join(here,'evidence'));
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(error){console.error(String(error));process.exitCode=1;}
