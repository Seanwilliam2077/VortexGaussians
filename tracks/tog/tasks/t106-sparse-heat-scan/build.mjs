import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';
const here=path.dirname(fileURLToPath(import.meta.url)),sha=s=>createHash('sha256').update(s).digest('hex');
const a=await fs.readFile(path.join(here,'../t102-active-recipients/local/plugin.js'),'utf8');
const b=await fs.readFile(path.join(here,'../t100-material-repair/local/active-repair.js'),'utf8');
assert.equal(sha(a),'3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474');
function between(s,lo,hi){
  const l=s.indexOf(lo),h=s.indexOf(hi,l+lo.length);assert(l>=0 && h>l,lo);return s.slice(l,h);
}
function replace(s,from,to){
  assert.equal(s.split(from).length,2,from);return s.replace(from,()=>to);
}
function scan(s){
  const from=between(s,'  const decay=1-dt*.35;','  t102MaterialTail(sb,dt);');
  return replace(s,from,'  if(t106Scan(sb,q,dt))return;\n').replace('t102MaterialTail(sb,dt)','t106MaterialTail(sb,dt)');
}
function mark(s,site,increment){
  return replace(s,increment,'{'+increment+'if(sb.h['+site+']>0)t106Index.words['+site+'>>>5]|=1<<('+site+'&31);}');
}
let apply=between(a,'function t102Apply','function t102Stop').replace('t102Apply','t106Apply');
apply=mark(apply,'j','sb.h[j]+=row.heat[k];');
let tail=between(a,'function t102MaterialTail','function t102Spread').replace('t102MaterialTail','t106MaterialTail').replace('t102Apply','t106Apply');
let spread=between(a,'function t102Spread','// Cache only geometry').replace('t102Spread','t106Spread');
spread=scan(spread).replace('  const r=P.spreadIgnR;', '  t106Ensure(sb);\n  const r=P.spreadIgnR;');
spread=mark(spread,'j','sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/r);');
let replay=between(b,'function t100ReplayActive','function t100FullStepActive').replace('t100ReplayActive','t106Replay');
replay=scan(replay).replace('  const data=frame.values;','  t106Ensure(sb);\n  const data=frame.values;');
replay=mark(replay,'id','sb.h[id]+=dt*P.spreadHeat*T*(1-d/r);');
const full=between(b,'function t100FullStepActive','const t100BeforeActive').replace('t100FullStepActive','t106Full').replace('t102Spread(dt)','t106Spread(dt)');
let hybrid=between(b,'function t100ActiveQuery','window.__t90.query=t100ActiveQuery');
hybrid=hybrid.replace('function t100ActiveQuery','function t106RepairQuery').replaceAll('t100BeforeActive','t106Ordinary')
  .replaceAll('repair-active','sparse-repair').replaceAll('restart-active','disabled-sparse-restart')
  .replace("t102Start('active-anchor',dt);","t106Start();t102Start('active-anchor',dt);")
  .replace('let activeStats=null;','let activeStats=null,sparseStats=null;')
  .replace('activeStats=t102Stop();','sparseStats=t106Stop();activeStats=t102Stop();')
  .replace('active_stats:activeStats,','sparse:sparseStats,active_stats:activeStats,')
  .replace('t100FullStepActive(q,dt)','t106Full(q,dt)').replace('t100ReplayActive(frame,dt)','t106Replay(frame,dt)');
let audit=between(b,'function t100AuditActive','window.__t100.audit').replace('t100AuditActive','t106RepairAudit')
 .replace("t102Start('active-anchor',dt);","t106Start();t102Start('active-anchor',dt);")
 .replace('t100ReplayActive(frame,dt)','t106Replay(frame,dt)').replace('finally {t102Stop();','finally {t106Stop();t102Stop();');
const ext=await fs.readFile(path.join(here,'sparse.js'),'utf8');
const checks=await fs.readFile(path.join(here,'audit.js'),'utf8');
const output=[apply,tail,spread,replay,full,ext,hybrid,'window.__t90.query=t106RepairQuery;',audit,checks].join('\n');
new Script(output);
const loc=path.join(here,'local');await fs.mkdir(loc,{recursive:true});await fs.writeFile(path.join(loc,'plugin.js'),output);
console.log(sha(output)+'  plugin.js');
