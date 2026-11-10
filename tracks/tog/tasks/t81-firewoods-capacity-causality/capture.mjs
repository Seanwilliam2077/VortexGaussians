import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {gzipSync} from 'node:zlib';
import {performance} from 'node:perf_hooks';
import {startServer} from '../../../../research/lib/runtime.mjs';
const start=performance.now(),root=process.cwd(),outer=path.dirname(path.dirname(root));
const here=path.join(root,'tracks/tog/tasks/t81-firewoods-capacity-causality');
const out=path.join(here,'local/run-01'),sha=b=>createHash('sha256').update(b).digest('hex');
const frozen=JSON.parse(await fs.readFile(path.join(here,'freeze.json'),'utf8'));
const cfg=JSON.parse(await fs.readFile(path.join(root,'tracks/tog/tasks/t42-firewoods-sequential-workflow/recipe.json'),'utf8'));
const invocation=JSON.parse(await fs.readFile(path.join(here,'invocation.json'),'utf8'));
if(invocation.freeze_sha256!==sha(await fs.readFile(path.join(here,'freeze.json')))||invocation.status!=='attempt_consumed')throw Error('T81 supervisor guard missing/mismatched');
let browser,server,page,timer,expired=false,completeSteps=0,activeRows=null,activeArm=null;const sizes=new Map();
const MAX=frozen.budget.max_output_bytes,DEADLINE=frozen.budget.worker_seconds*1000;
const report={schema:'t81-four-arm-causal-capture-v1',status:'running',started_utc:new Date().toISOString(),
  phases:[],files:[],arms:[],checks:[],page_errors:[],console_errors:[],blocked_requests:[],failures:[],
  interpretation:'Same seeded total policy intervention; conditional RNG diverges after admission changes. No new-method or perceptual-pass claim.'};
const elapsed=()=>performance.now()-start;
function deadline(){if(expired||elapsed()>=DEADLINE)throw Error('T81 whole-worker deadline');}
async function write(name,value,replace=false){
  const bytes=Buffer.isBuffer(value)?value:Buffer.from(value),old=sizes.get(name)||0;
  const total=[...sizes.values()].reduce((s,n)=>s+n,0)-old+bytes.length;
  if(total>MAX-1024*1024)throw Error('T81 output budget reserve reached');
  await fs.writeFile(path.join(out,name),bytes,replace?{}:{flag:'wx'});sizes.set(name,bytes.length);
  if(!replace)report.files.push({name,bytes:bytes.length,sha256:sha(bytes)});
}
async function persist(){await write('progress.json',JSON.stringify(report,null,2)+'\n',true);}
async function phase(name,fn){const t=elapsed();try{return await fn();}finally{report.phases.push({name,ms:elapsed()-t});}}
async function verifyInputs(){for(const f of frozen.files){const bytes=await fs.readFile(path.resolve(outer,f.path));if(bytes.length!==f.bytes||sha(bytes)!==f.sha256)throw Error('Frozen identity changed: '+f.path);}}
function same(x,y,label){
  const passed=JSON.stringify(x)===JSON.stringify(y);report.checks.push({label,observed:x,expected:y,passed});
  if(!passed)throw Error(label+' mismatch; observed='+JSON.stringify(x)+' expected='+JSON.stringify(y));
}
const counterKeys=['sceneFeedAttempts','sceneFeedCapacityBlocked','sceneSeedsEmitted'];
function historical(state,endpoint=false){
  const n=state.native;const expected=endpoint?{frame:360,hash:'cb784052',count:2433,counters:[17280,12379,2437]}:{frame:180,hash:'24ba7dc9',count:2394,counters:[8640,3826,2394]};
  same({frame:n.frame,hash:n.hash,count:n.particles.count,counters:counterKeys.map(k=>n.counters[k])},expected,'T42 historical '+(endpoint?'endpoint':'prefix'));
}
async function saveState(name,state){
  const raw=Buffer.from(JSON.stringify(state)+'\n');await write(name+'.json.gz',gzipSync(raw,{level:6}));
  Object.assign(report.files.at(-1),{decoded_bytes:raw.length,decoded_sha256:sha(raw)});
  const n=state.native;return {frame:n.frame,time:n.time,hash:n.hash,particleStateHash:n.particleStateHash,
    randomDraws:n.randomDraws,scene:n.scene,particles:n.particles,counters:n.counters,
    observationCounters:state.observationCounters,newlyBCount:state.newlyBIndices.length,
    glError:n.glError,contextLost:n.contextLost};
}
async function saveCapture(arm,label,capture){
  const t=elapsed();
  const summary=await saveState(arm+'-'+label,capture.state);
  const png=Buffer.from(capture.png.split(',')[1],'base64'),rgba=Buffer.from(capture.rgbaBase64,'base64');
  if(rgba.length!==cfg.width*cfg.height*4)throw Error('RGBA byte length');
  await write(arm+'-'+label+'.png',png);await write(arm+'-'+label+'.rgba.gz',gzipSync(rgba,{level:6}));
  Object.assign(report.files.at(-1),{decoded_bytes:rgba.length,decoded_sha256:sha(rgba)});
  return {...summary,capture_export_ms:capture.export_ms,compression_write_ms:elapsed()-t};
}
function qualifyGL(state,label){same({glError:state.native.glError,contextLost:state.native.contextLost},{glError:0,contextLost:false},label+' post-readback GL');}
async function flushRows(partial=false){
  if(!activeRows||!activeRows.length||!activeArm)return;
  const name=activeArm+'-'+(partial?'partial-':'')+'steps.jsonl.gz';
  if(sizes.has(name))return;
  const raw=Buffer.from(activeRows.map(r=>JSON.stringify(r)).join('\n')+'\n');
  await phase(activeArm+'_'+(partial?'partial_':'')+'step_log_compression_write',()=>write(name,gzipSync(raw,{level:6})));
  Object.assign(report.files.at(-1),{decoded_bytes:raw.length,decoded_sha256:sha(raw),completed_returned_rows:activeRows.length,partial});
}
try{
  await write('worker-start.json',JSON.stringify({pid:process.pid,utc:new Date().toISOString()})+'\n');
  timer=setTimeout(()=>{expired=true;browser?.close().catch(()=>{});},Math.max(0,DEADLINE-elapsed()));
  await phase('frozen_input_check',verifyInputs);deadline();
  const playwright=createRequire(import.meta.url)(frozen.runtime.playwright_module);
  server=await phase('server_start',()=>startServer(path.join(outer,'work')));
  browser=await phase('browser_launch',()=>playwright.chromium.launch({headless:true,executablePath:frozen.runtime.browser_executable}));
  report.runtime={node:process.version,browser:browser.version(),playwright:frozen.runtime.playwright_version};
  same(process.version,frozen.runtime.node_version,'Node version');same(browser.version(),frozen.runtime.browser_version,'Browser version');
  let prefixIdentity=null,prefixTraceIdentity=null;
  for(const arm of frozen.arms){
    deadline();const armStart=elapsed(),a={id:arm.id,policy:arm.policy,B:arm.B,steps:0};report.arms.push(a);
    const rows=[];activeRows=rows;activeArm=arm.id;page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.setDefaultTimeout(45000);
    page.on('pageerror',e=>report.page_errors.push({arm:arm.id,message:e.stack||e.message}));
    page.on('console',m=>{if(m.type()==='error')report.console_errors.push({arm:arm.id,message:m.text()});});
    await page.route('**/*',route=>{if(new URL(route.request().url()).origin===server.url)return route.continue();report.blocked_requests.push(route.request().url());return route.abort();});
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await phase(arm.id+'_page_load',()=>page.goto(server.url+'/VortexGaussians/tracks/tog/tasks/t81-firewoods-capacity-causality/local/site/demo/?embed=1&orbit=0',{waitUntil:'load'}));
    await page.waitForFunction(()=>!!window.__t81&&!!window.__demo);deadline();
    a.initial=await phase(arm.id+'_load_reset_camera_ignite_A',()=>page.evaluate(async c=>{
      const d=__demo;d.P.paused=true;d.forceSize(c.width,c.height);
      const response=await fetch('/real-asset-ingest/foreground.ply');if(!response.ok)throw Error('PLY load');
      const bytes=await response.arrayBuffer(),load=d.loadPLY(bytes);d.research.reset(c.seed,c.params);__t42.camera(c.camera);
      __t81.begin({fixedBIndices:c.picks[1].initial_geometric_neighbors});
      const lit=d.ignite(...c.picks[0].world,c.picks[0].radius),g=d.gl,e=g.getExtension('WEBGL_debug_renderer_info');
      return {bytes:bytes.byteLength,load,litA:lit,initial:d.research.snapshot(),
        graphics:{userAgent:navigator.userAgent,vendor:g.getParameter(e?e.UNMASKED_VENDOR_WEBGL:g.VENDOR),renderer:g.getParameter(e?e.UNMASKED_RENDERER_WEBGL:g.RENDERER)}};
    },cfg));
    if(a.initial.load.kept!==34687||a.initial.load.total!==34687)throw Error('Full Firewoods load required');
    for(let step=1;step<=360;step++){
      deadline();const bridgeStart=elapsed();const row=await page.evaluate(({dt,capture})=>__t81.frame(dt,capture),{dt:cfg.dt,capture:step===180||step===360});
      completeSteps++;a.steps++;const capture=row.capture;delete row.capture;row.node_bridge_ms=elapsed()-bridgeStart;
      rows.push(row);
      if(step===180){
        a.prefix=await phase(arm.id+'_prefix_save',()=>saveCapture(arm.id,'prefix',capture));
        if(row.glError!==0||row.contextLost)throw Error('Saved prefix frame GL failure; arm='+arm.id+' error='+row.glError+' lost='+row.contextLost);
        qualifyGL(capture.state,arm.id+' prefix');
        historical(capture.state,false);
        const identity=sha(Buffer.from(JSON.stringify(capture.state)));
        const trace=sha(Buffer.from(JSON.stringify(rows.map(({timing,node_bridge_ms,...r})=>r))));
        if(prefixIdentity===null){prefixIdentity=identity;prefixTraceIdentity=trace;}
        else {same(identity,prefixIdentity,'All-arm full prefix state');same(trace,prefixTraceIdentity,'All-arm prefix per-step trace');}
        a.prefixIdentity=identity;a.prefixTraceIdentity=trace;
        a.intervention=await phase(arm.id+'_zero_time_intervention',()=>page.evaluate(({policy,B,pick})=>{
          __t81.setPolicy(policy);const event=__t81.igniteB(pick,B);return {event,state:__t81.export()};
        },{policy:arm.policy,B:arm.B,pick:cfg.picks[1]}));
        const after=a.intervention.state;delete a.intervention.state;
        a.afterIntervention=await saveState(arm.id+'-after-intervention',after);
        qualifyGL(after,arm.id+' after intervention');
        if(arm.B)same(after.native.hash,'36e624bc','T42 zero-time B hash');
      }
      if(step===360){
        a.endpoint=await phase(arm.id+'_endpoint_save',()=>saveCapture(arm.id,'endpoint',capture));
        if(row.glError!==0||row.contextLost)throw Error('Saved endpoint frame GL failure; arm='+arm.id+' error='+row.glError+' lost='+row.contextLost);
        qualifyGL(capture.state,arm.id+' endpoint');
        if(arm.id==='per-layer-AB')historical(capture.state,true);
      }
      if(row.glError!==0||row.contextLost)throw Error('Frame GL failure; arm='+arm.id+' frame='+row.frame+' error='+row.glError+' lost='+row.contextLost);
      if(step%30===0){a.last_frame=row.frame;a.latest_counts=row.observationCounters;await persist();}
    }
    await flushRows(false);activeRows=null;activeArm=null;
    a.timing={};for(const key of Object.keys(rows[0].timing)){const values=rows.map(r=>r.timing[key]);a.timing[key]={sum:values.reduce((s,n)=>s+n,0),mean:values.reduce((s,n)=>s+n,0)/values.length,max:Math.max(...values)};}
    await phase(arm.id+'_page_cleanup',()=>page.close());page=null;a.whole_arm_ms=elapsed()-armStart;await persist();
    if(report.page_errors.length||report.console_errors.length||report.blocked_requests.length)throw Error('Browser errors/external requests');
  }
  same(completeSteps,1440,'Total native steps');
  await phase('final_frozen_input_check',verifyInputs);deadline();report.status='completed_capture_pending_saved_audit';
}catch(e){
  report.status='failed_execution';report.failures.push(e.stack||e.message);process.exitCode=1;
  // Preserve every completed row already returned by the browser. No new step
  // or browser read is performed; the existing byte cap remains in force.
  if(elapsed()<DEADLINE)try{await flushRows(true);}catch(saveError){report.failures.push('Partial row preservation: '+saveError.message);}
  else report.failures.push('Partial row preservation skipped after worker deadline; no new work authorized');
}
finally{
  for(const [name,close]of [['page',()=>page?.close()],['browser',()=>browser?.close()],['server',()=>server?.close()]]){
    try{await phase(name+'_cleanup',close);}catch(e){report.failures.push(name+' cleanup: '+e.message);report.status='failed_execution';process.exitCode=1;}
  }
  clearTimeout(timer);report.completed_native_steps=completeSteps;report.worker_total_ms=elapsed();
  report.deadline_expired=expired||report.worker_total_ms>DEADLINE;
  if(report.deadline_expired||report.page_errors.length||report.console_errors.length||report.blocked_requests.length){report.status='failed_execution';process.exitCode=1;}
  report.finished_utc=new Date().toISOString();report.output_bytes_before_final_receipts=[...sizes.values()].reduce((s,n)=>s+n,0);
  report.timing_scope='worker_total_ms: module start through cleanup, excluding imports and final receipts; external supervisor includes startup. Step includes hooks; GPU finish included in render. Observation, export, bridge, compression and IO retained separately; no optimized FPS claim.';
  try{await persist();await write('result.json',JSON.stringify(report,null,2)+'\n');}catch(e){process.exitCode=1;console.error('Final receipt failure: '+e.message);}
  console.log(JSON.stringify({status:report.status,completed_native_steps:completeSteps,worker_total_ms:report.worker_total_ms,failures:report.failures}));
}
