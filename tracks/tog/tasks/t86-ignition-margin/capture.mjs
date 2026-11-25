import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {gunzipSync, gzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';

// Run from any directory. A full reproduction writes to a fresh directory
// supplied as argv[2]; the default is the task's ignored local/ directory.
const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../..');
const out = path.resolve(process.argv[2] || path.join(here, 'local'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const t42 = path.resolve(here, '../t42-firewoods-sequential-workflow');
const frozen = JSON.parse(await fs.readFile(path.resolve(here, '../t81-firewoods-capacity-causality/freeze.json'), 'utf8'));
const files = new Map(frozen.files.map(f => [f.path,f]));
const start = performance.now();
const report = {schema:'t86-native-reference-v1', status:'running', started_utc:new Date().toISOString(),
  sources:{}, runtime:{}, shots:{}, cuts:[], files:[], costs_ms:{}, errors:[],
  timing_scope:'Continuous native runs with no renders. step_ms includes camera update, clock and stepAll. Per-frame label scans, snapshot extraction/transport, packing, setup and teardown are reported separately; single-host measurements.'};
async function pinned(key, filename, expected) {
  const bytes = await fs.readFile(filename);
  assert.equal(sha(bytes), expected, 'Input changed '+key);
  report.sources[key] = {bytes:bytes.length, sha256:expected};
  return bytes;
}
async function packed(name, value) {
  const begin = performance.now();
  const bytes = Buffer.from(JSON.stringify(value)+'\n');
  const compressed = gzipSync(bytes,{level:6});
  await fs.writeFile(path.join(out,name),compressed,{flag:'wx'});
  const record = {name, bytes:compressed.length, sha256:sha(compressed),
    decoded_bytes:bytes.length, decoded_sha256:sha(bytes), pack_and_write_ms:performance.now()-begin};
  report.files.push(record);
  return record;
}
async function timed(obj,key,fn) {
  const begin = performance.now();
  try { return await fn(); } finally { obj[key] = performance.now()-begin; }
}
const numSort=(a,b)=>a-b;
function sameSet(actual, expected, label) {
  assert.deepEqual([...actual].sort(numSort),[...expected].sort(numSort),label);
}
function historical(bytes) {
  const csv = gunzipSync(bytes).toString('utf8').trimEnd().split('\n');
  assert.equal(csv.shift(),'policy,material_id,direct_B,A_onset_frame,A_status,AB_onset_frame,AB_status');
  const events = Array.from({length:361},()=>[]);
  const direct = [], prefix=[];
  for(const row of csv){
    const [policy,id,,,,frame,status] = row.split(',');
    if(policy!=='global' || status==='right_censored') continue;
    const n=Number(id.slice(4));
    if(status==='direct_stroke') direct.push(n);
    else if(status==='left_censored') prefix.push(n);
    else assert.equal(status,'observed');
    events[Number(frame)].push(n);
  }
  return {events,direct,prefix};
}
function verify(arm,shot,rows,truth) {
  assert.equal(rows.length,360);
  const active = new Set(shot.initial.ids);
  let observed = 0;
  for(const [j,row] of rows.entries()){
    assert.equal(row.frame,j+1);
    assert.equal(row.retired,0,'Endpoint consistency assumes no retirement in these 360 steps');
    for(const id of row.new_ids){ assert(!active.has(id)); active.add(id); observed++; }
    assert.equal(active.size,row.active_count);
    if(row.frame===180){
      if(arm==='AB') sameSet(active,truth.prefix,'T84 left-censored IDs');
      for(const id of shot.edit.ids){ assert(!active.has(id)); active.add(id); }
      if(arm==='AB') {
        sameSet(shot.edit.ids,truth.direct,'T84 direct stroke');
        sameSet(active,truth.events[180],'T84 edited start');
      }
    } else if(arm==='AB' && row.frame>180) sameSet(row.new_ids,truth.events[row.frame],'T84 exact onset frame '+row.frame);
  }
  assert.equal(active.size,shot.end.burning);
  assert.equal(shot.end.charred,0);
  assert.equal(rows.at(-1).gas_count,shot.end.gas_count);
  if(arm==='AB'){
    assert.equal(shot.pre_edit.hash,'24ba7dc9'); assert.equal(shot.post_edit.hash,'36e624bc');
    assert.equal(shot.end.hash,'491894ec'); assert.equal(shot.end.particle_hash,'2acba20a');
  }
  return {frames:rows.length, natural_ignitions:observed, endpoint_active:active.size,
    historical_per_ID_frames:arm==='AB'?181:0, total_retirements:0};
}

let browser, server;
await fs.mkdir(out,{recursive:true});
// Refuse to mix evidence from different attempts. A new output path is safe.
await fs.writeFile(path.join(out,'capture-start.json'),JSON.stringify({pid:process.pid,utc:report.started_utc}),{flag:'wx'});
try {
  const setup = performance.now();
  const src = (await pinned('demo',path.join(root,'demo/index.html'),files.get('work/VortexGaussians/demo/index.html').sha256)).toString('utf8');
  const camera = (await pinned('camera_adapter',path.join(t42,'adapter.js'),files.get('work/VortexGaussians/tracks/tog/tasks/t42-firewoods-sequential-workflow/adapter.js').sha256)).toString('utf8');
  const cfg = JSON.parse(await pinned('recipe',path.join(t42,'recipe.json'),files.get('work/VortexGaussians/tracks/tog/tasks/t42-firewoods-sequential-workflow/recipe.json').sha256));
  const asset = path.resolve(process.env.T86_PLY || path.join(root,'../real-asset-ingest/foreground.ply'));
  const ply = await pinned('Firewoods_foreground',asset,files.get('work/real-asset-ingest/foreground.ply').sha256);
  const truth = historical(await pinned('T84_onsets',path.resolve(here,'../t84-ignition-edit-footprint/material_onsets.csv.gz'),'e36931183a493693ad4ae438a135ab9570f769e55c94984d1e1d02cdcdd1f7bb'));
  const adapter = await fs.readFile(path.join(here,'native.js'),'utf8');
  for(const name of ['capture.mjs','native.js','PROTOCOL.md']) report.sources[name] = {sha256:sha(await fs.readFile(path.join(here,name)))};
  const marker = 'window.__demo = {', predicate = 'const full=L.ps.length>=P.ppl; let recycle=-1;';
  assert.equal(src.split(marker).length,2); assert.equal(src.split(predicate).length,2);
  const html = src.replace(predicate,'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;')
    .replace(marker,()=>camera+'\n'+adapter+'\n'+marker);
  for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) new vm.Script(script[1]);
  report.sources.staged_html = {sha256:sha(html)};
  const require = createRequire(import.meta.url);
  const pw = process.env.PLAYWRIGHT_MODULE || frozen.runtime.playwright_module;
  const executable = process.env.BROWSER_EXECUTABLE || frozen.runtime.browser_executable;
  const playwright = require(pw);
  server = await startServer(root);
  report.runtime = {node:process.version, node_sha256:sha(await fs.readFile(process.execPath)),
    browser_executable_sha256:sha(await fs.readFile(executable)),
    playwright_version:require(path.join(pw,'package.json')).version};
  report.costs_ms.input_stage_and_runtime_identity = performance.now()-setup;
  browser=await timed(report.costs_ms,'browser_launch',()=>playwright.chromium.launch({headless:true,executablePath:executable}));
  report.runtime.browser_version = browser.version();
  for(const arm of ['AB','BA']){
    const shot = {costs_ms:{}, cuts:[]};
    report.shots[arm] = shot;
    const page = await timed(shot.costs_ms,'new_page',()=>browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1}));
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const url=new URL(route.request().url());
      if(url.origin!==server.url) {report.errors.push('Unexpected origin '+url.origin); return route.abort();}
      if(url.pathname==='/t86/')return route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:html});
      if(url.pathname==='/firewoods.ply')return route.fulfill({status:200,contentType:'application/octet-stream',body:ply});
      return route.continue();
    });
    await timed(shot.costs_ms,'page_load',async()=>{
      await page.goto(server.url+'/t86/?embed=1&orbit=0',{waitUntil:'load'});
      await page.waitForFunction(()=>window.__t86 && window.__demo);
    });
    const picks = [...arm].map(c=>cfg.picks.find(p=>p.name===c));
    const init = await timed(shot.costs_ms,'load_reset_camera_first_stroke',()=>page.evaluate(async ({c,pick})=>{
      const d=__demo; d.P.paused=true; d.forceSize(c.width,c.height);
      const res=await fetch('/firewoods.ply'); if(!res.ok)throw Error('PLY unavailable');
      const load=d.loadPLY(await res.arrayBuffer()); d.research.reset(c.seed,c.params); __t42.camera(c.camera);
      const stroke=__t86.ignite(pick,false);
      return {load:{kept:load.kept,total:load.total},stroke};
    },{c:cfg,pick:picks[0]}));
    assert.deepEqual(init.load,{kept:34687,total:34687}); shot.initial=init.stroke;
    sameSet(shot.initial.ids,picks[0].initial_geometric_neighbors,'Initial contact');
    const rows = [];
    for(const frame of [180,210,240,300,360]){
      const batch = await timed(shot.costs_ms,'steps_through_'+frame,()=>page.evaluate(([end,dt])=>__t86.frames(end,dt),[frame,cfg.dt]));
      rows.push(...batch);
      if(frame===180){
        const marks=await timed(shot.costs_ms,'edit_markers_and_operation',()=>page.evaluate(pick=>{
          const pre=__t86.marker(), edit=__t86.ignite(pick,true), post=__t86.marker();
          return {pre,edit,post}; },picks[1]));
        shot.pre_edit=marks.pre;shot.post_edit=marks.post;shot.edit=marks.edit;
        const burning=new Set([...shot.initial.ids,...rows.flatMap(r=>r.new_ids)]);
        sameSet(shot.edit.ids,picks[1].initial_geometric_neighbors.filter(i=>!burning.has(i)),'Second contact');
        assert.equal(shot.edit.frame,180); assert.equal(shot.edit.count,shot.edit.ids.length);
        assert.equal(shot.pre_edit.burning+shot.edit.count,shot.post_edit.burning);
        assert.equal(shot.pre_edit.particle_hash,shot.post_edit.particle_hash);
      } else if(frame===360){
        shot.end=await timed(shot.costs_ms,'endpoint_marker',()=>page.evaluate(()=>__t86.marker()));
      } else {
        const cut=await timed(shot.costs_ms,'checkpoint_extract_and_bridge_'+frame,
          ()=>page.evaluate(([arm,dt])=>__t86.cut(arm,dt),[arm,cfg.dt]));
        assert.equal(cut.frame,frame); assert.equal(cut.state.length,34687);
        assert.equal(cut.frontier.length,rows.at(-1).active_count);
        assert.deepEqual(cut.scene_center,cfg.source_center);
        const record=await packed(arm+'-'+frame+'.json.gz',cut);
        shot.cuts.push({frame,file:record.name,native_hash:cut.native_hash,gas:rows.at(-1).gas_count,active:cut.frontier.length});
        await packed(arm+'-'+frame+'-eligibility.json.gz',{schema:'t86-public-eligibility-v1',arm,frame,
          threshold:cut.params.spreadIgnH, state:cut.state, fuel:cut.fuel, heat:cut.heat, native_hash:cut.native_hash});
      }
    }
    shot.checks=verify(arm,shot,rows,truth);
    shot.native_step_total_ms=rows.reduce((n,r)=>n+r.step_ms,0);
    shot.observer_total_ms=rows.reduce((n,r)=>n+r.observer_ms,0);
    await packed(arm+'-trace.json.gz',rows);
    await timed(shot.costs_ms,'close_page',()=>page.close());
    await fs.writeFile(path.join(out,arm+'-reference.json'),JSON.stringify(shot,null,2)+'\n',{flag:'wx'});
    assert.equal(report.errors.length,0);
  }
  report.status='validated';
} catch(e) {
  report.status='failed';report.errors.push(e.stack||String(e));process.exitCode=1;
} finally {
  await timed(report.costs_ms,'cleanup',async()=>{await browser?.close();await server?.close();});
  report.costs_ms.worker_before_receipt=performance.now()-start;
  report.finished_utc=new Date().toISOString();
  await fs.writeFile(path.join(out,'capture-report.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:report.status, wall_ms:report.costs_ms.worker_before_receipt, errors:report.errors}));
}
