import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),t114=path.join(here,'../t114-sitewise-material-repair');
const file=path.join(t114,'run.mjs'),sha=s=>createHash('sha256').update(s).digest('hex');
let text=await fs.readFile(file,'utf8');
assert.equal(sha(text),'39e17201cd1d1bedf1332866cefb9ed678bcd9d86a48f5d9f968578eef348a39');
assert.equal(sha(await fs.readFile(path.join(t114,'local/firewoods.js'))),'5416fa11d880f222eb4979cbf9f64285a8c1a03d0bc7d223b540d0c134feaa9f');
assert.equal(sha(await fs.readFile(path.join(here,'local/plugin.js'))),'6144304de535350765f57e042c61fc206a73b35f5b54b01a25d546ffdc769e29');
function change(a,b){assert.equal(text.split(a).length,2,a);text=text.replace(a,()=>b);}
change('const own=path.dirname(fileURLToPath(import.meta.url))','const own='+JSON.stringify(t114));
change("const local=path.join(own,'local');","const local="+JSON.stringify(path.join(here,'local'))+";");
change("'../t114-sitewise-material-repair/repair.js',extra","'../t114-sitewise-material-repair/repair.js',extra,'../t116-cold-flame-contacts/local/plugin.js'");
change("const specs=['ordinary','repair','sparse','sitewise'];","const specs=['ordinary','repair','sitewise','ordinary-cold','repair-cold','sitewise-cold'];");
change("'ordinary,repair,sparse,sitewise','--repeats','4'","'ordinary,repair,sitewise,ordinary-cold,repair-cold,sitewise-cold','--repeats','6'");
change("schema:'t114-sitewise-repair-v1'","schema:'t116-cold-flame-contacts-v1'");
const edits=[
 ["['repair','ordinary','sparse','sitewise']","['repair','ordinary','sitewise','ordinary-cold','repair-cold','sitewise-cold']"],
 ["m==='ordinary'?auditFrames:[]","m.startsWith('ordinary')?auditFrames:[]"],
 ["        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)",
 "        shot.cold_ordinary_direct=await page.evaluate(([p,dt])=>__t116FullAudit(p,dt),[picks[1],cfg.dt]);\n        assert.deepEqual(await page.evaluate(()=>__t86.marker()),pre);\n        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true)"]
];
const addition=edits.map(([a,b])=>'block=once(block,'+JSON.stringify(a)+','+JSON.stringify(b)+');').join('\n');
change("block=block.replace('WEIGHT_PATH'",addition+"\nblock=block.replace('WEIGHT_PATH'");
change("portable(fileURLToPath(import.meta.url))","portable("+JSON.stringify(fileURLToPath(import.meta.url))+")");
change("path.join(own,'PROTOCOL.md')",JSON.stringify(path.join(here,'PROTOCOL.md')));
change("path.join(own,'evidence/firewoods')",JSON.stringify(path.join(here,'evidence/firewoods')));
text=text.replaceAll('T114_runner','T116_runner').replaceAll('T114_protocol','T116_protocol');
try{await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}
