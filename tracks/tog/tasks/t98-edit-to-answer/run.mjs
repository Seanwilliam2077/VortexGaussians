import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url)), t90=path.join(here,'../t90-callable-regional-query');
const origin=pathToFileURL(path.join(t90,'profile.mjs'));
const sha=x=>createHash('sha256').update(x).digest('hex');
let source=await fs.readFile(origin,'utf8');
assert.equal(sha(source),'a8e5cb3e4420945cb7d102d70e3c47d8a85148c503b46edace1bf493147c4915');
const local=path.join(here,'local');
await fs.mkdir(local,{recursive:true});
function changeOnce(s,a,b) { assert.equal(s.split(a).length,2,'Unique source anchor '+a.slice(0,50)); return s.replace(a,()=>b); }
function change(a,b) {source=changeOnce(source,a,b);}
const t94=path.join(here,'../t94-resumable-gas-query');
const q=await fs.readFile(path.join(t90,'query.js'),'utf8');
const dispatch=await fs.readFile(path.join(t94,'dispatch.js'),'utf8');
const horizonGuard='![1,4,8].includes(horizon)';
assert.equal(sha(q),'0e0cd4cecba197fb109e61cdd522f591bfc4d22722f3ff43a0923d35b3f27036');
assert.equal(sha(dispatch),'abb1277c97fae61654f9cb87fa69bdc080919041b781f6f700f2287f7f057a1c');
const extended=q=>changeOnce(q,horizonGuard,'![60,180].includes(horizon)');
const qPath=path.join(local,'query.js'), dispatchPath=path.join(local,'dispatch.js');
await fs.writeFile(qPath,extended(q)); await fs.writeFile(dispatchPath,extended(dispatch));
const runtime=pathToFileURL(path.resolve(t90,'../../../../research/lib/runtime.mjs')).href;
change("'../../../../research/lib/runtime.mjs'",JSON.stringify(runtime));
source=source.replaceAll('import.meta.url',JSON.stringify(origin.href));
change("path.join(here,'query.js')",JSON.stringify(qPath));
change("const specs=['full','trim','regional','t91','t93','all-carriers','rank-only'];",
     "const specs=['regional','rank-only','sweep-spatial','sweep-rank','slice-rank','asset-cache','cold-cache'];");
change("schema:'t90-callable-native-regional-v1'","schema:'t98-delivered-edit-to-answer-v1'");
change("report.sources.staged_html=sha(html);",`report.sources.staged_html=sha(html);
  await input('T98_runner',${JSON.stringify(fileURLToPath(import.meta.url))});await input('T98_protocol',${JSON.stringify(path.join(here,'PROTOCOL.md'))});
  const allTargets=JSON.parse(await input('T98_targets',${JSON.stringify(path.join(here,'REFERENCE.json'))})).queries;
  const asset=args.recipe?'dead-tree':'firewoods';`);
change("const ids=await timed(phase,'build_region_and_export_ids'", "const ids=await timed(phase,'untimed_reference_region'");
const first=source.indexOf('      if(stop===180){'), last=source.indexOf('    assert.equal(shot.verified_frames,360);',first);
assert(first>0 && last>first);
source=source.slice(0,first)+`
      if(stop===180){
        const pre=await page.evaluate(()=>__t86.marker()); assert.deepEqual(pre,ref.pre_edit);
        for(const horizon of [60,180]){
          const expected=allTargets.find(r=>r.asset===asset&&r.arm===arm&&r.horizon===horizon);
          assert(expected && ids.length===expected.shell_size);
          const query={arm,cut:180,horizon,first_frame:expected.first_frame,expected_ids:expected.ids,trials:[]};
          report.queries.push(query);
          for(let rep=0;rep<=repeats;rep++)for(let j=0;j<methods.length;j++){
            const method=methods[(j+rep+report.queries.length-1)%methods.length];
            await page.evaluate(()=>__t98.resetTrial());
            const t=performance.now();
            const result=await page.evaluate(([m,h,dt,pick])=>__t98.click(m,h,dt,pick),[method,horizon,cfg.dt,picks[1]]);
            const delivered_ms=performance.now()-t;
            await page.evaluate(()=>__t98.finishTrial());
            assert.equal(result.clicked,ref.edit.count,'Fresh second stroke');
            assert.equal(result.yes,expected.first_frame!==null);
            assert.equal(result.first_frame,expected.first_frame);
            assert(expected.first_frame!==null ? expected.ids.includes(result.witness) : result.witness===null);
            query.trials.push({...result,method,rep,delivered_ms});
          }
          assert.deepEqual(await page.evaluate(()=>__t86.marker()),pre,'Pre-edit reset');
        }
        const b=await page.evaluate(p=>({edit:__t86.ignite(p,true),post_edit:__t86.marker()}),picks[1]);
        assert.deepEqual(b.edit,ref.edit);assert.deepEqual(b.post_edit,ref.post_edit);
        const ineligible=new Set([...ref.initial.ids,...ref.edit.ids,...trace.slice(0,180).flatMap(f=>f.new_ids)]);
        const expectedEligible=ids.filter(i=>!ineligible.has(i));
        const observed=await page.evaluate(()=>__t98.eligibleAfterClick());
        assert.deepEqual(observed,expectedEligible,'Fresh post-click eligibility');
        shot.post_click_eligible={count:observed.length,sha256:sha(JSON.stringify(observed))};
      } else if(stop===360) {
        shot.endpoint=await page.evaluate(()=>__t86.marker());assert.deepEqual(shot.endpoint,ref.end);
      } else {
        const marker=await page.evaluate(()=>__t86.marker());
        assert.equal(marker.hash,ref.cuts.find(c=>c.frame===stop).native_hash);
        shot.cut_hashes[stop]=marker.hash;
      }
    }
`+source.slice(last);
change("report.errors.push(String(error.stack||error))","report.errors.push(String(error))");
const paths=['../t93-exact-terminal-gas/local/plugin.js','../t94-resumable-gas-query/local/plugin.js',
  '../t95-multistep-material-slice/local/plugin.js','local/dispatch.js',
  '../t97-ordinary-cached-graph/.generated-plugin.js','click.js'];
const expectedHashes={
  [paths[0]]:'568ad31b48d449ea07eab9f6bcee93315ded72893fe47b4559ec8745f2a3e638',
  [paths[1]]:'51184fc640c22aa0ab30ceb4c5ae26f3a4dda66ffef20a33fff3bddc7b54b608',
  [paths[2]]:'5782263e00c896e983614799332480c0abff925c83b1faaf6920b8c827af74c2',
  [paths[4]]:'36a19010dfda87a3c27e2f458a529e14537eda16a5f6055e681c025fdbca3e59'};
for(const [name,expected] of Object.entries(expectedHashes))
  assert.equal(sha(await fs.readFile(path.join(here,name))),expected,name);
for(const name of paths)process.argv.push('--plugin',path.join(here,name));
try {await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));}
catch(e){console.error(String(e));process.exitCode=1;}
