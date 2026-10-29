import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {gzipSync} from 'node:zlib';
import {performance} from 'node:perf_hooks';
import {startServer} from '../../../../research/lib/runtime.mjs';
const begin=performance.now();
const root=process.cwd(),here=path.join(root,'tracks/tog/tasks/t42-firewoods-sequential-workflow');
const outer=path.dirname(path.dirname(root)),out=process.argv[2];
if(!out)throw Error('output directory required');
const cfg=JSON.parse(await fs.readFile(path.join(here,'recipe.json'),'utf8'));
const frozen=JSON.parse(await fs.readFile(path.join(here,'freeze.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
let browser,server,timer,expired=false;
const report={schema:'t42-one-workflow-run-v1',status:'running',started_utc:new Date().toISOString(),
 phases:[],files:[],events:[],progress:[],render_checks:[],page_errors:[],console_errors:[],blocked_requests:[],failures:[]};
const elapsed=()=>performance.now()-begin;
async function save(name,b){b=Buffer.isBuffer(b)?b:Buffer.from(b);await fs.writeFile(path.join(out,name),b,{flag:'wx'});report.files.push({name,bytes:b.length,sha256:sha(b)});}
async function persist(){await fs.writeFile(path.join(out,'progress.json'),JSON.stringify(report,null,2)+'\n');}
async function phase(name,fn){const s=elapsed();try{return await fn();}finally{report.phases.push({name,ms:elapsed()-s});await persist();}}
async function verifyFrozen(){for(const f of frozen.files){const b=await fs.readFile(path.join(outer,f.path));if(b.length!==f.bytes||sha(b)!==f.sha256)throw Error('frozen input changed: '+f.path);}}
try{
 await fs.writeFile(path.join(out,'worker-start.json'),JSON.stringify({pid:process.pid,utc:new Date().toISOString()})+'\n',{flag:'wx'});
 timer=setTimeout(()=>{expired=true;browser?.close().catch(()=>{});},Math.max(0,cfg.internal_deadline_ms-elapsed()));
 await phase('frozen_input_check',verifyFrozen);
 const modulePath='C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
 const playwright=createRequire(import.meta.url)(modulePath);
 server=await phase('server_start',()=>startServer(path.join(outer,'work')));
 browser=await phase('browser_launch',()=>playwright.chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'}));
 if(expired)throw Error('internal deadline elapsed at launch');
 const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
 page.setDefaultTimeout(45000);
 page.on('pageerror',e=>report.page_errors.push(e.stack||e.message));
 page.on('console',m=>{if(m.type()==='error')report.console_errors.push(m.text());});
 await page.route('**/*',route=>{if(new URL(route.request().url()).origin===server.url)return route.continue();report.blocked_requests.push(route.request().url());return route.abort();});
 await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
 await phase('page_load',()=>page.goto(server.url+'/VortexGaussians/tracks/tog/tasks/t42-firewoods-sequential-workflow/local/site/demo/?embed=1&orbit=0',{waitUntil:'load'}));
 await page.waitForFunction(()=>!!window.__t42&&!!window.__demo);
 report.runtime={node:process.version,browser:browser.version(),module:modulePath,
  graphics:await page.evaluate(()=>{const g=__demo.gl,e=g.getExtension('WEBGL_debug_renderer_info');return {userAgent:navigator.userAgent,vendor:g.getParameter(e?e.UNMASKED_VENDOR_WEBGL:g.VENDOR),renderer:g.getParameter(e?e.UNMASKED_RENDERER_WEBGL:g.RENDERER)};})};
 report.load=await phase('load_place_reset',()=>page.evaluate(async c=>{
  const d=window.__demo;d.P.paused=true;d.forceSize(c.width,c.height);
  const resp=await fetch('/real-asset-ingest/foreground.ply');if(!resp.ok)throw Error('PLY fetch failed');
  const b=await resp.arrayBuffer(),loaded=d.loadPLY(b);
  const initial=d.research.reset(c.seed,c.params);__t42.camera(c.camera);
  return {bytes:b.byteLength,loaded,initial};
 },cfg));
 if(report.load.loaded.kept!==34687||report.load.loaded.total!==34687)throw Error('not complete Firewoods load');
 let checkpoints=0;
 async function checkpoint(name){
  const state=await phase(name+'_state_export',()=>page.evaluate(()=>__t42.state()));
  const raw=Buffer.from(JSON.stringify(state)+'\n');if(raw.length>cfg.max_checkpoint_bytes)throw Error('checkpoint size cap');
  await phase(name+'_state_write',()=>save(name+'.json.gz',gzipSync(raw,{level:6})));
  report.files.at(-1).raw_bytes=raw.length;report.files.at(-1).raw_sha256=sha(raw);
  const png=await phase(name+'_render_export',()=>page.evaluate(()=>{__demo.render();const data=__t42.canvas();return {data,count:__t42.renderCount(),glError:__demo.gl.getError(),contextLost:__demo.gl.isContextLost()};}));
  await phase(name+'_png_write',()=>save(name+'.png',Buffer.from(png.data.split(',')[1],'base64')));
  report.render_checks.push({checkpoint:name,glError:png.glError,contextLost:png.contextLost});
  report.progress.push({checkpoint:name,frame:state.frame,time:state.time,scene:state.scene,particles:state.particles,counters:state.counters,hash:state.hash,draw_count:png.count});
  checkpoints++;await persist();
  if(png.glError!==0||png.contextLost)throw Error(name+' post-render GL failure');
 }
 async function ignite(p){const event=await phase('ignite_'+p.name,()=>page.evaluate(p=>({name:p.name,lit:__demo.ignite(...p.world,p.radius),frame:__demo.research.snapshot().frame,time:__demo.research.snapshot().time}),p));report.events.push(event);await persist();}
 async function advance(label){for(let j=0;j<6;j++){
  if(expired||elapsed()>=cfg.internal_deadline_ms)throw Error('internal deadline');
  const s=await phase(label+'_steps_'+(j*30+1)+'_'+((j+1)*30),()=>page.evaluate(dt=>__demo.research.step(30,dt),cfg.dt));
  report.progress.push({step_completed:s.frame,time:s.time,scene:s.scene,particles:s.particles,counters:s.counters,hash:s.hash});await persist();
 }}
 await checkpoint('00-initial');await ignite(cfg.picks[0]);await checkpoint('01-after-A');
 await advance('A');await checkpoint('02-before-B');await ignite(cfg.picks[1]);await checkpoint('03-after-B');
 await advance('AB');await checkpoint('04-endpoint');
 await phase('reset_same_controls',()=>page.evaluate(c=>__demo.research.reset(c.seed,c.params),cfg));await checkpoint('05-reset');
 report.completed_checkpoints=checkpoints;
 await phase('final_frozen_input_check',verifyFrozen);
 if(expired||report.page_errors.length||report.blocked_requests.length||report.console_errors.length)throw Error('deadline/browser errors/blocked requests');
 report.status='completed_capture_pending_saved_audit';
}catch(e){report.status='failed_execution';report.failures.push(e.stack||e.message);process.exitCode=1;}
finally{
 try{if(browser)await phase('browser_cleanup',()=>browser.close());}catch(e){report.failures.push('cleanup: '+e.message);report.status='failed_execution';process.exitCode=1;}
 try{if(server)await phase('server_cleanup',()=>server.close());}catch(e){report.failures.push('server cleanup: '+e.message);report.status='failed_execution';process.exitCode=1;}
 clearTimeout(timer);report.worker_total_ms=elapsed();
 expired=expired||report.worker_total_ms>cfg.internal_deadline_ms;report.internal_deadline_expired=expired;
 if(expired||report.page_errors.length||report.blocked_requests.length||report.console_errors.length){report.status='failed_execution';process.exitCode=1;}
 report.timing_scope='worker_total_ms: module entry through cleanup and error checks, before final progress/result receipts; phase ms excludes the following progress-file write';
 report.finished_utc=new Date().toISOString();await persist();await save('result.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,events:report.events,worker_total_ms:report.worker_total_ms,failures:report.failures}));
}
