import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {registerHooks} from 'node:module';

const host=new URL('../t141-bonsai-action/run.mjs',import.meta.url);
const crop=new URL('./crop.mjs',import.meta.url), schedule=new URL('./schedule.mjs',import.meta.url);
let text=readFileSync(host,'utf8').replaceAll('\r\n','\n');
assert.equal(createHash('sha256').update(text).digest('hex'),'7178c04b2dc40cb9a5bea941cfb57d2fb4d7adb5962d31471e2757c2bd9649ed');
function replace(needle,newText){assert.equal(text.split(needle).length,2,needle);text=text.replace(needle,()=>newText);}
replace("const action=await file('action.js');","const action=instrumentAction(await file('action.js'));");
replace("for(const marker of html.matchAll","html=instrumentRenderer(html);\nfor(const marker of html.matchAll");
replace("schema:'t141-bonsai-native-action-v1'","schema:'t145-bonsai-scalar-scissor-v1'");
replace("assert.deepEqual(branch.result.hashes,expected.result.hashes,'paired full RGB buffers '+branch.name);",
  "if(row.method==='ordinary-native')assert.deepEqual(branch.result.hashes,expected.result.hashes,'full RGB '+branch.name);else assert.equal(branch.result.hashes.length,0);");
// Keep a last-good receipt even when Windows temporarily holds the target file.
replace("await fs.rename(temp,receipt);", `for(let retry=0;;retry++){
  try{await fs.rename(temp,receipt);break;}catch(e){
    if(retry>=24 || !['EBUSY','EPERM','EACCES'].includes(e.code))throw e;
    await new Promise(resolve=>setTimeout(resolve,80));
  }}`);
const begin=text.indexOf('  if(!report.matte.total){'), end=text.indexOf('  assert.equal(report.errors.length,0);',begin);
assert(begin>0 && end>begin);
text=text.slice(0,begin)+`  const historical=await json('evidence/RUN.json');
  await schedule145({page,report,save,actual,rootState,compare,historical},Number(process.argv[3]));
`+text.slice(end);
text=`import {instrumentAction,instrumentRenderer} from ${JSON.stringify(crop.href)};
import {schedule145} from ${JSON.stringify(schedule.href)};
`+text;
const hook=registerHooks({load(url,context,next){
  return url===host.href?{format:'module',source:text,shortCircuit:true}:next(url,context);
}});
try {await import(host.href);} finally {hook.deregister();}
