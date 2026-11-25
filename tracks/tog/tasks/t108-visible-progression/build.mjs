import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';
const here=path.dirname(fileURLToPath(import.meta.url));
async function read(name,hash){const s=await fs.readFile(path.join(here,name),'utf8');assert.equal(createHash('sha256').update(s).digest('hex'),hash);return s;}
function once(s,from,to){assert.equal(s.split(from).length,2,from);return s.replace(from,()=>to);}
const active=await read('../t102-active-recipients/local/plugin.js','3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474');
const repair=await read('../t100-material-repair/local/plugin.js','35ffeaccd926572685d1f1c0b7e3c3a785c953925762820400ce5735579bfb98');
const start=active.indexOf('function t102Spread(dt)'), end=active.indexOf('\n}\n',start);
assert(start>=0 && end>start);
let full=active.slice(start,end+3);
full=once(full,'function t102Spread(dt)','function t108Full(p,dt,stop)');
full=once(full,'if(q && q.mask[i]) {q.witness=i; return;}','if(p.mask[i]) t108Add(p,i);');
full=once(full,'  t102MaterialTail(sb,dt);','  if(stop && p.mass>=p.target)return;\n  t102MaterialTail(sb,dt);');
let sub=repair.slice(0,repair.indexOf('function t100Replay('));
sub=once(sub,'function t100Advance(plan,dt,log)','function t108Slice(plan,dt,log,p,stop)');
sub=once(sub,'if(sb.h[id]>0) {','if(sb.state[id]===0 && sb.h[id]>0) {');
sub=once(sub,'if(sb.h[id]>=P.spreadIgnH) return id;','if(sb.h[id]>=P.spreadIgnH) {sb.state[id]=1;t108Add(p,id);}');
sub=once(sub,'  if(!plan.graph)', '  if(stop && p.mass>=p.target)return;\n  if(!plan.graph)');
sub=once(sub,'sb.h[edgeIds[i]]+=deltas[i];','if(sb.state[edgeIds[i]]===0) sb.h[edgeIds[i]]+=deltas[i];');
const text=full+'\n'+sub+'\n'+await fs.readFile(path.join(here,'progress.js'),'utf8');
new Script(text);
await fs.mkdir(path.join(here,'local'),{recursive:true});await fs.writeFile(path.join(here,'local/plugin.js'),text);
console.log(createHash('sha256').update(text).digest('hex'));
