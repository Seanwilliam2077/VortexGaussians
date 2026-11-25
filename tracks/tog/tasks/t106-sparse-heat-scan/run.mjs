import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),prior=path.resolve(here,'../t98-edit-to-answer');
const origin=pathToFileURL(path.join(prior,'run.mjs')),local=path.join(here,'local');
const portable=s=>s.split(path.sep).join('/');
const sha=s=>createHash('sha256').update(s).digest('hex');
let text=await fs.readFile(origin,'utf8');
assert.equal(sha(text),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function replace(a,b){assert.equal(text.split(a).length,2,a);text=text.replace(a,()=>b);}
replace("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
replace("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];",
  "const specs=['active-anchor','sparse-active','repair-active','sparse-repair'];");
replace("schema:'t98-delivered-edit-to-answer-v1'","schema:'t106-sparse-heat-control-v1'");
replace('for(const horizon of [60,180])','for(const horizon of [60])');
replace("        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)",`        shot.sparse_audit=await page.evaluate(([p,dt])=>__t106Audit(p,dt),[picks[1],cfg.dt]);
        assert.deepEqual(await page.evaluate(()=>__t86.marker()),pre,'Restored sparse audit');
        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)`);
replace('shot.cut_hashes[stop]=marker.hash;',`shot.cut_hashes[stop]=marker.hash;
        if(asset==='firewoods' && arm==='AB' && stop===210){
          shot.repair_audit=await page.evaluate(dt=>__t106Expiry(dt),cfg.dt);
          assert.equal(shot.repair_audit.status,'matched_expiry_and_continuation');
          assert.deepEqual(await page.evaluate(()=>__t86.marker()),marker);
        }`);
replace("'local/dispatch.js'",JSON.stringify(portable(path.relative(prior,path.join(local,'dispatch.js')))));
const click0=await fs.readFile(path.join(prior,'click.js'),'utf8');
const mark='plan_active:r.plan_active ?? null,';
const click=click0.replace(mark,'sparse:r.sparse??null,repair_stats:r.repair_stats??null,active_stats:r.active_stats??null,'+mark);
assert.notEqual(click,click0);await fs.mkdir(local,{recursive:true});await fs.writeFile(path.join(local,'click.js'),click);
const extra=['../t100-material-repair/local/plugin.js','../t102-active-recipients/local/plugin.js',
  '../t100-material-repair/local/active-repair.js','../t106-sparse-heat-scan/local/click.js','../t106-sparse-heat-scan/local/plugin.js'];
replace("'click.js'];",extra.map(s=>JSON.stringify(s)).join(',')+'];');
replace("await input('T98_runner',","await input('T106_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T106_protocol',"+JSON.stringify(portable(path.join(here,'PROTOCOL.md')))+");await input('T98_runner',");
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}

