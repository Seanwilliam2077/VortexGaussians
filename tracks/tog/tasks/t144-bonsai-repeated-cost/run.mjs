// Reuse the original T141 host and simulation without modifying the frozen files.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {registerHooks} from 'node:module';

const original = new URL('../t141-bonsai-action/run.mjs',import.meta.url);
const contrast = new URL('./contrast.mjs',import.meta.url);
const schedule = new URL('./schedule.mjs',import.meta.url);
const sha = x => createHash('sha256').update(x).digest('hex');
function one(source, needle, updated) {
  assert.equal(source.split(needle).length,2,needle);
  return source.replace(needle,()=>updated);
}
let text = readFileSync(original,'utf8').replaceAll('\r\n','\n');
assert.equal(sha(text),'7178c04b2dc40cb9a5bea941cfb57d2fb4d7adb5962d31471e2757c2bd9649ed');
text=one(text,"const action=await file('action.js');",`const action=instrumentAction(await file('action.js'));`);
text=one(text,"schema:'t141-bonsai-native-action-v1'","schema:'t144-bonsai-native-replication-v1'");
const begin=text.indexOf('  if(!report.matte.total){');
const end=text.indexOf('  assert.equal(report.errors.length,0);',begin);
assert(begin>0 && end>begin);
text=text.slice(0,begin)+`  assert(report.matte.total>0);
  const historical=await json('evidence/RUN.json');
  await runSchedule({page,cfg,historical,report,save,actual,rootState,compare},Number(process.argv[3]));
`+text.slice(end);
text=`import {instrumentAction} from ${JSON.stringify(contrast.href)};
import {runSchedule} from ${JSON.stringify(schedule.href)};
`+text;
// This single-module hook preserves the original task-relative paths and source guards.
const hook=registerHooks({load(url,context,next){
  if(url===original.href)return {format:'module',source:text,shortCircuit:true};
  return next(url,context);
}});
try { await import(original.href); } finally {hook.deregister();}
