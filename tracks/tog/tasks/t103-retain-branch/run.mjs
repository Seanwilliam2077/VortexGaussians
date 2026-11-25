import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url)),prior=path.resolve(here,'../t98-edit-to-answer');
const origin=pathToFileURL(path.join(prior,'run.mjs')), local=path.join(here,'local');
await fs.mkdir(local,{recursive:true});
const sha=s=>createHash('sha256').update(s).digest('hex');
let text=await fs.readFile(origin,'utf8');
assert.equal(sha(text),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function replace(a,b){assert.equal(text.split(a).length,2,'T98 anchor '+a);text=text.replace(a,()=>b);}
replace("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
replace("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];",
  "const specs=['ordinary-discard','slice-discard','ordinary-keep','slice-keep'];");
replace("schema:'t98-delivered-edit-to-answer-v1'","schema:'t103-keep-edit-to-answer-v1'");
replace("for(const horizon of [60,180])","for(const horizon of [60])");
const adapter=`            const backend=method.startsWith('ordinary')?'ordinary':'slice';
            const t=performance.now();
            const preview=await page.evaluate(([m,h,dt,pick])=>__t103.begin(m,h,dt,pick),[backend,horizon,cfg.dt,picks[1]]);
            const preview_delivered_ms=performance.now()-t;
            const a=performance.now();
            const resolved=await page.evaluate(keep=>__t103.resolve(keep),method.endsWith('-keep'));
            const action_delivered_ms=performance.now()-a;
            const delivered_ms=preview_delivered_ms+action_delivered_ms;
            const result={...preview,...resolved,preview_delivered_ms,action_delivered_ms};`;
const first=text.indexOf('            const t=performance.now();'),last=text.indexOf('            await page.evaluate(()=>__t98.finishTrial());',first);
assert(first>=0 && last>first);text=text.slice(0,first)+adapter+'\n'+text.slice(last);
replace("        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)",`        const target=allTargets.find(q=>q.asset===asset&&q.arm===arm&&q.horizon===60);
        shot.keep_audit=await page.evaluate(([p,dt,frame])=>__t103.audit(p,dt,frame),[picks[1],cfg.dt,target.first_frame??240]);
        assert.deepEqual(await page.evaluate(()=>__t86.marker()),pre,'Restored audit');
        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)`);
const portable=p=>p.split(path.sep).join('/');
replace("'local/dispatch.js'",JSON.stringify(portable(path.relative(prior,path.join(local,'dispatch.js')))));
const extra=['../t100-material-repair/local/plugin.js','../t102-active-recipients/local/plugin.js',
  '../t100-material-repair/local/active-repair.js','click.js','../t103-retain-branch/local/plugin.js'];
replace("'click.js'];",extra.map(s=>JSON.stringify(s)).join(',')+'];');
replace("await input('T98_runner',","await input('T103_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T103_protocol',"+JSON.stringify(portable(path.join(here,'PROTOCOL.md')))+");await input('T98_runner',");
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}

