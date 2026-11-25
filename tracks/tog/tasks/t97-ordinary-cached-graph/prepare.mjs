import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url)), t90=path.join(here,'../t90-callable-regional-query');
const root=path.resolve(here,'../../../..');
const demo=await readFile(path.join(root,'demo/index.html'),'utf8');
const start=demo.indexOf('  let M=P.spreadSceneFeed?');
const end=demo.indexOf('\n}\n',start);
assert(start>0 && end>start);
function replaceOne(source,from,to){
  assert.equal(source.split(from).length,2,'Unique marker '+from);
  return source.replace(from,()=>to);
}
const tail=replaceOne(demo.slice(start,end),'const full=L.ps.length>=P.ppl;',
  'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl;');
const template=await readFile(path.join(here,'ordinary.js'),'utf8');
await writeFile(path.join(here,'.generated-plugin.js'),replaceOne(template,'/* NATIVE_EMISSION */',tail));
let profile=await readFile(path.join(t90,'profile.mjs'),'utf8');
profile=replaceOne(profile,"const specs=['full','trim','regional','t91','t93','all-carriers','rank-only'];",
  "const specs=['rank-only','plain','cold-cache','asset-cache'];");
profile=replaceOne(profile,"path.join(here,'query.js')","path.join(here,'../t90-callable-regional-query/query.js')");
profile=replaceOne(profile,"path.join(here,'JOINT_PROTOCOL.md')","path.join(here,'../t90-callable-regional-query/JOINT_PROTOCOL.md')");
profile=replaceOne(profile,"        const restored=await page.evaluate(()=>__t86.marker());",
  "        (shot.ordinary_state_audits ||= {})[stop]=await page.evaluate(dt=>__t97Audit(dt),cfg.dt);\n        const restored=await page.evaluate(()=>__t86.marker());");
await writeFile(path.join(here,'.generated-profile.mjs'),profile);
