import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';

const here=path.dirname(fileURLToPath(import.meta.url));
const demo=await readFile(path.resolve(here,'../../../../demo/index.html'),'utf8');
const sha=s=>createHash('sha256').update(s).digest('hex');
assert.equal(sha(demo),'e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0');
function between(src,first,last) {
  const i=src.indexOf(first), j=src.indexOf(last,i+1);
  assert(i>=0 && j>i && src.indexOf(first,i+1)<0);
  return src.slice(i,j);
}
const fullGas=between(demo,'function stepAll(dt){','  stepSpread(dt);').replace('function stepAll(dt){','function t95FullGas(dt){')+'}\n';
const rawFeed=between(demo,'  for(let m=0;m<M;m++){','\n}\n');
const ordinary='const full=L.ps.length>=P.ppl; let recycle=-1;';
assert.equal(rawFeed.split(ordinary).length,2);
const globalAdmission='const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;';
const feed='function t95Feed(dt){\nconst sb=sceneBurnState, N=layers.length, areaMode=false, feedSources=null, M=P.spreadFeedCap;\n'+rawFeed.replace(ordinary,globalAdmission)+'\n}\n';
const result=fullGas+feed+await readFile(path.join(here,'slice.js'),'utf8');
new Script(result);
const output=path.resolve(process.argv[2]||path.join(here,'local/plugin.js'));
await mkdir(path.dirname(output),{recursive:true});
await writeFile(output,result);
console.log(sha(result)+'  '+path.basename(output));
