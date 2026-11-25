import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
// Remove these adapter arguments before handing the unmodified core CLI to T90.
function takeArg(flag) {
  const ix=process.argv.indexOf(flag);
  if(ix<0)return null;
  if(ix+1>=process.argv.length)throw Error('Missing '+flag);
  const value=process.argv[ix+1];process.argv.splice(ix,2);return value;
}
const external=takeArg('--external-targets');
const externalName=takeArg('--asset-name');
assert(Boolean(external)===Boolean(externalName),'Use --external-targets and --asset-name together');
const extra=takeArg('--active-plugin');
const activeAudit=takeArg('--active-audit');
const parent=path.resolve(here,'../t98-edit-to-answer'),origin=pathToFileURL(path.join(parent,'run.mjs'));
const sha=s=>createHash('sha256').update(s).digest('hex');
let text=await fs.readFile(origin,'utf8');
assert.equal(sha(text),'975ac9ef06387d041238452883dca01c22a03509403470558286b01744a6b8b9');
function replace(a,b){assert.equal(text.split(a).length,2,'T98 adapter marker: '+a);text=text.replace(a,()=>b);}
const local=path.join(here,'local');
await fs.mkdir(local,{recursive:true});
let click=await fs.readFile(path.join(parent,'click.js'),'utf8');
const marker='plan_active:r.plan_active ?? null,';
assert.equal(click.split(marker).length,2);
click=click.replace(marker,'active_stats:r.active_stats ?? null,repair_stats:r.repair_stats ?? null,'+marker);
await fs.writeFile(path.join(local,'click.js'),click);

// All generated files live under T100; T98 input artifacts remain byte-identical.
replace("const local=path.join(here,'local');",'const local='+JSON.stringify(local)+';');
text=text.replaceAll('fileURLToPath(import.meta.url)',JSON.stringify(fileURLToPath(origin)));
replace("const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];",
        "const specs=['asset-cache','restart-cache','repair-cache','active-anchor','active-fresh','restart-active','repair-active'];");
replace("schema:'t98-delivered-edit-to-answer-v1'","schema:'t100-material-repair-v1'");
const portable=p=>p.split(path.sep).join('/');
if(external) {
  assert(/^[a-z0-9-]+$/.test(externalName),'Invalid external dataset token');
  replace("path.join(here,'REFERENCE.json')",JSON.stringify(path.resolve(external)));
  replace("const asset=args.recipe?'dead-tree':'firewoods';","const asset='"+externalName+"';");
  replace("for(const horizon of [60,180])","for(const horizon of [30,60,180])");
  replace("![60,180].includes(horizon)","![30,60,180].includes(horizon)");
}
replace("await input('T98_runner',","await input('T100_runner',"+JSON.stringify(portable(fileURLToPath(import.meta.url)))+");await input('T100_protocol',"+JSON.stringify(portable(path.join(here,'PROTOCOL.md')))+");await input('T98_runner',");
replace("'local/dispatch.js'",JSON.stringify(path.relative(parent,path.join(local,'dispatch.js')).split(path.sep).join('/')));
const additional=[path.join(local,'plugin.js'),...(extra?[path.resolve(extra),path.join(local,'active-repair.js')]:[]),
  path.join(local,'click.js'),...(activeAudit?[path.resolve(activeAudit)]:[])];
replace("'click.js'];",additional.map(f=>JSON.stringify(portable(path.relative(parent,f)))).join(',')+"];");
replace("assert.deepEqual(b.edit,ref.edit);assert.deepEqual(b.post_edit,ref.post_edit);",
        `assert.deepEqual(b.edit,ref.edit);assert.deepEqual(b.post_edit,ref.post_edit);
        shot.repair_audits=[];
        shot.repair_audits.push(await timed(phase,'untimed_click_audit',()=>page.evaluate(dt=>__t100.audit(dt),cfg.dt)));
        assert.deepEqual(await page.evaluate(()=>__t86.marker()),ref.post_edit);`);
if(activeAudit)replace("        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)",`        shot.active_audit=await timed(phase,'untimed_preclick_active_audit',
          ()=>page.evaluate(([p,dt])=>__t102Audit(p,dt),[picks[1],cfg.dt]));
        assert.deepEqual(await page.evaluate(()=>__t86.marker()),pre);
        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)`);
replace("shot.cut_hashes[stop]=marker.hash;",`shot.cut_hashes[stop]=marker.hash;
        if(asset==='firewoods' && arm==='AB' && stop===210) {
          const audit=await timed(phase,'untimed_development_wrap_check',()=>page.evaluate(dt=>__t100.audit(dt),cfg.dt));
          shot.repair_audits.push(audit);
          assert.equal(audit.status,'matched_expiry_and_continuation','Expected natural A/B frame-210 expiry');
          assert.deepEqual(await page.evaluate(()=>__t86.marker()),marker,'Live state after audit');
        }`);
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}
