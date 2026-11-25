// Stage only the extension points of the pinned T90 runner. No historical source file is changed.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const t90=path.join(here,'../t90-callable-regional-query');
const origin=pathToFileURL(path.join(t90,'profile.mjs'));
const sha=b=>createHash('sha256').update(b).digest('hex');
let source=await fs.readFile(origin,'utf8');
assert.equal(sha(source),'a8e5cb3e4420945cb7d102d70e3c47d8a85148c503b46edace1bf493147c4915');
function change(a,b) {assert.equal(source.split(a).length,2,'T90 source marker');source=source.replace(a,()=>b);}
const runtime=pathToFileURL(path.resolve(t90,'../../../../research/lib/runtime.mjs')).href;
change("'../../../../research/lib/runtime.mjs'",JSON.stringify(runtime));
source=source.replaceAll('import.meta.url',JSON.stringify(origin.href));
change("'all-carriers','rank-only'];","'all-carriers','rank-only','sweep-rank','sweep-spatial','slice-rank','slice-regional'];");
change("schema:'t90-callable-native-regional-v1'","schema:'t94-joint-multistep-v1'");
change("report.sources.staged_html=sha(html);",`report.sources.staged_html=sha(html);
  await input('T94_runner',${JSON.stringify(fileURLToPath(import.meta.url))});
  await input('T94_protocol',${JSON.stringify(path.join(here,'PROTOCOL.md'))});
  await input('joint_followup_protocol',${JSON.stringify(path.join(here,'JOINT_PROTOCOL.md'))});`);
change("const marker=await page.evaluate(()=>__t86.marker());",`const marker=await page.evaluate(()=>__t86.marker());
        shot.resume_checks ||= {};
        shot.resume_checks[stop]=await timed(phase,'untimed_continuation_audit_'+stop,
          ()=>page.evaluate(dt=>__t90.audit(dt),cfg.dt));`);
change("report.errors.push(String(error.stack||error))","report.errors.push(String(error))");
process.argv.push('--plugin',path.join(here,'dispatch.js'));
try {await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));}
catch(error) {console.error(String(error));process.exitCode=1;}
