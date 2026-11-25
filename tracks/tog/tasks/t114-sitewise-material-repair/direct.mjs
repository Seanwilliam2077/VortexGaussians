import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const own=path.dirname(fileURLToPath(import.meta.url)),file=path.join(own,'run.mjs');
const sha=x=>createHash('sha256').update(x).digest('hex');
let worker=await fs.readFile(file,'utf8');
assert.equal(sha(await fs.readFile(path.join(own,'direct-audit.js'))),'0932b85b47ee1e7b5e143ea7e54bab1e5a4b47a46cd7914d9a0e63f420006b25');
function change(a,b){assert.equal(worker.split(a).length,2,a);worker=worker.replace(a,()=>b);}
change('const own=path.dirname(fileURLToPath(import.meta.url))','const own='+JSON.stringify(own));
change("'../t114-sitewise-material-repair/repair.js',extra","'../t114-sitewise-material-repair/repair.js','../t114-sitewise-material-repair/direct-audit.js',extra");
change("block=block.replace('WEIGHT_PATH'",'block=once(block,"for(let rep=0;rep<=repeats;rep++)","for(let rep=0;rep<0;rep++)");\nblock=block.replace(\'WEIGHT_PATH\'');
change("portable(fileURLToPath(import.meta.url))","portable("+JSON.stringify(file)+")");
change("path.join(own,'evidence/firewoods')","path.join(own,'evidence/firewoods-direct')");
try{await import('data:text/javascript;base64,'+Buffer.from(worker).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}
