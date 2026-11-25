// Share the exact retained-state/guard loop; change only the full material backend.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';

const here=path.dirname(fileURLToPath(import.meta.url));
const sha=s=>createHash('sha256').update(s).digest('hex');
const base=await fs.readFile(path.join(here,'local/plugin.js'),'utf8');
const active=await fs.readFile(path.join(here,'../t102-active-recipients/local/plugin.js'),'utf8');
assert.equal(sha(base),'35ffeaccd926572685d1f1c0b7e3c3a785c953925762820400ce5735579bfb98');
assert.equal(sha(active),'3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474');
function section(a,b) {
  const i=base.indexOf(a),j=base.indexOf(b,i+1);
  assert(i>=0 && j>i);return base.slice(i,j);
}
let replay=section('function t100Replay(frame,dt) {','function t100Plan');
const graph=replay.indexOf('  const radius=P.spreadR;'), clock=replay.indexOf('  // Under the prefix proof');
assert(graph>0 && clock>graph);
replay=replay.slice(0,graph)+'  t102MaterialTail(sb,dt);\n'+replay.slice(clock);
replay=replay.replace('function t100Replay','function t100ReplayActive');
let full=section('function t100FullStep(q,dt)','const t100Ordinary=')
  .replace('function t100FullStep','function t100FullStepActive').replace('t97Spread(dt)','t102Spread(dt)');
let query=section('function t100Query(method,h,dt)','window.__t90.query=t100Query;');
query=query.replace('function t100Query','function t100ActiveQuery')
  .replaceAll('t100Ordinary(','t100BeforeActive(')
  .replaceAll('repair-cache','repair-active').replaceAll('restart-cache','restart-active')
  .replace('const stats=','let activeStats=null;\n  const stats=')
  .replace("t97Use('asset-cache');","t102Start('active-anchor',dt);")
  .replace('t100FullStep(q,dt)','t100FullStepActive(q,dt)')
  .replace('t100Replay(frame,dt)','t100ReplayActive(frame,dt)')
  .replace('beforeRestore=performance.now();t90Restore(live);','activeStats=t102Stop();beforeRestore=performance.now();t90Restore(live);')
  .replace("t100BeforeActive('asset-cache',h,dt)","t100BeforeActive('active-anchor',h,dt)")
  .replace('answer.repair_stats=stats;','answer.repair_stats=stats;answer.active_stats={prefix:activeStats,replay:answer.active_stats};')
  .replace('cache_build:t97Build,cache_rows:t97Graph?.size','active_stats:activeStats,cache_build:activeStats,cache_rows:activeStats.branch_rows');
let audit=section('function t100Audit(dt)','window.__t100={audit:t100Audit};')
  .replace('function t100Audit','function t100AuditActive')
  .replace("t97Use('asset-cache');","t102Start('active-anchor',dt);")
  .replace('t100Replay(frame,dt)','t100ReplayActive(frame,dt)')
  .replace('finally {t90Restore(first);}','finally {t102Stop();t90Restore(first);}');
const code=replay+'\n'+full+'\nconst t100BeforeActive=window.__t90.query;\n'+query+'\nwindow.__t90.query=t100ActiveQuery;\n'+audit+`
window.__t100.audit=dt=>{const native=t100Audit(dt);native.active_backend=t100AuditActive(dt);return native;};`;
new Script(code);await fs.writeFile(path.join(here,'local/active-repair.js'),code);console.log(sha(code));
