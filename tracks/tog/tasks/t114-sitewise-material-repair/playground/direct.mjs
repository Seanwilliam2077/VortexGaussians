// After timing, add a direct full-array comparison to each visited sitewise boundary.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)),local=path.join(here,'local');
const sha=x=>createHash('sha256').update(x).digest('hex');
let source=await fs.readFile(path.join(here,'run.mjs'),'utf8');
assert.equal(sha(source),'d00b0f677800ae7ea5c98b48ca9bc229d3d0e2e159cc6df30244d7957fa6962e');
assert.equal(sha(await fs.readFile(path.join(here,'../direct-audit.js'))),'0932b85b47ee1e7b5e143ea7e54bab1e5a4b47a46cd7914d9a0e63f420006b25');
function change(a,b){assert.equal(source.split(a).length,2,a);source=source.replace(a,()=>b);}
change('const here=path.dirname(fileURLToPath(import.meta.url)), prior=','const here='+JSON.stringify(here)+', prior=');
change("t114-recovery-editorial-choice-v1","t114-direct-recovery-equality-v1");
change("'../t114-sitewise-material-repair/repair.js','../t114-sitewise-material-repair/playground/local/action.js'",
       "'../t114-sitewise-material-repair/repair.js','../t114-sitewise-material-repair/direct-audit.js','../t114-sitewise-material-repair/playground/local/action.js'");
const marker='edit("await fs.readFile(path.join(here,\'worker.txt\'),\'utf8\')",JSON.stringify(block));';
change(marker,`const start=block.indexOf('          for(const cams of'),end=block.indexOf('          for(const pick of picksLF)',start);
assert(start>=0 && end>start);block=block.slice(0,start)+block.slice(end);
block=changed(block,"['repair','sparse','sitewise','ordinary']","['sitewise']");
block=changed(block,"if(m!=='repair')assert.deepEqual(r.boundaries,reports.repair.boundaries,'Physical state at boundary and next native step');",
  "assert(r.work.recovery_blocks.length>0 && r.work.recovery_blocks.every(b=>b.direct_state.matched_boundary && b.direct_state.matched_next),'Direct native equality');");
`+marker);
await fs.mkdir(local,{recursive:true});
const program=path.join(local,'direct-driver.mjs');await fs.writeFile(program,source);
if(process.argv.length===2)process.argv.push('--out',path.join(here,'direct-evidence'));
await import(pathToFileURL(program));
