import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(here,'../../../..');
const sourceDir=path.resolve(process.argv[2] || path.join(root,'../real-asset-ingest'));
const target=process.argv[3] && path.resolve(process.argv[3]), receipt=process.argv[4] && path.resolve(process.argv[4]);
assert(target && receipt, 'Supply source directory, fresh private image directory and fresh capture JSON path.');
assert(!target.startsWith(root+path.sep),'Keep source-appearance images outside checkout.');
const read=(file)=>fs.readFile(path.resolve(here,file));
const json=async(file)=>JSON.parse(await read(file));
const sha=(bytes)=>createHash('sha256').update(bytes).digest('hex');
const report={schema:'t127-woodpile-native-camera-v1',started_utc:new Date().toISOString(),sources:{},runtime:{},arms:{},phases:[],errors:[]};
async function pinned(file,expected){
  const bytes=await read(file);
  assert.equal(sha(bytes),expected,path.basename(file));
  report.sources[path.basename(file)]=expected;
  return bytes;
}
const t109='../t109-common-parent-choice';
const prior=await json(t109+'/evidence/native/capture-report.json');
const nativeReference=(await json('../t119-cross-sibling-actions/evidence/firewoods-1/CAPTURE.json')).full_audits.sibling.physical;
const cfg=JSON.parse(await pinned(t109+'/recipe.json',prior.sources.recipe.sha256));
const {runtime}=await json('../t81-firewoods-capacity-causality/freeze.json');
const require=createRequire(import.meta.url),modulePath=process.env.PLAYWRIGHT_MODULE||runtime.playwright_module;
const pw=require(modulePath),executablePath=process.env.BROWSER_EXECUTABLE||runtime.browser_executable;
function uniqueReplace(text,key,value){
  assert.equal(text.split(key).length,2,key);
  return text.replace(key,()=>value);
}
function extract(text,first,next){
  const a=text.indexOf(first),b=text.indexOf(next,a);
  assert(a>=0&&b>a);return text.slice(a,b);
}
async function phase(stage,fn){
  const start=performance.now();
  try{return await fn();}finally{report.phases.push({stage,ms:performance.now()-start});}
}
function withoutTimings({step_ms,observer_ms,...physical}){return physical;}
const started=performance.now();
let server,browser,watchdog;
await fs.mkdir(target);await fs.mkdir(path.dirname(receipt),{recursive:true});await fs.writeFile(receipt,JSON.stringify(report),{flag:'wx'});
try{
  const demo=(await pinned(path.join(root,'demo/index.html'),prior.sources.demo.sha256)).toString();
  const camera=(await pinned('../t42-firewoods-sequential-workflow/adapter.js',prior.sources.camera.sha256)).toString();
  const adapter=(await pinned('../t86-ignition-margin/native.js',prior.sources.observer.sha256)).toString();
  const repair=(await pinned('../t100-material-repair/repair.js','941b4158868850ab59ffea796e8d9a15a2ee5fb609dbb4b6ae6df4d71b9e544f')).toString();
  const progression=(await pinned('../t108-visible-progression/progress.js','a83dd58ba02700210d202db95cf9920ce21c4abb7c5907c0ec02d1732c3beab3')).toString();
  const asset=await pinned(path.join(sourceDir,'foreground.ply'),cfg.asset_sha256);
  const allCameras=JSON.parse(await pinned(path.join(sourceDir,'cameras.json'),'5cdd4605b0bf11970357c26e66ce3affb6c25ab2823171488fa41288ceb4a5c5'));
  const cameras=[0,124].map(id=>allCameras.find(c=>c.id===id));assert.deepEqual(cameras[0],cfg.camera);
  assert.equal(cameras[1].img_name,'00124');
  report.cameras=cameras;
  const marker='window.__demo = {';
  let html=uniqueReplace(demo,'const full=L.ps.length>=P.ppl; let recycle=-1;',
    'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
  html=uniqueReplace(html,marker,camera+'\n'+adapter+'\n'+marker);
  assert.equal(sha(html),prior.staged_sha256);
  const physical=extract(repair,'function t100Physical()', 'function t100Equal(');
  const fingerprint=extract(progression,'function t108Fingerprint()', 'function t108Answer(');
  const observer=(await read('observer.js')).toString();
  html=uniqueReplace(html,marker,[physical,fingerprint,observer,marker].join('\n'));
  html=uniqueReplace(html,'function drawPartRange(start,count){ if(count<=0) return;',
    'function drawPartRange(start,count){ if(count<=0) return; if(t127Drawing){t127Drawing.instances+=count;if(t127Drawing.wood)return;}');
  report.staged_html_sha256=sha(html);report.worker_sha256=sha(await read('capture.mjs'));report.observer_sha256=sha(observer);
  watchdog=setTimeout(()=>{report.expired=true;browser?.close().catch(()=>{});},240000-(performance.now()-started));
  server=await startServer(root);
  browser=await phase('launch_browser',()=>pw.chromium.launch({executablePath,headless:true}));
  report.runtime={node:process.version,playwright:require(path.join(modulePath,'package.json')).version,browser:browser.version()};
  for(const [pick,name] of [['L','light'],['F','full']]){
    const arm='A'+pick,expected=prior.shots[arm];
    const record={frames:{},trace_ranges:[],images:[],renders:[]};report.arms[arm]=record;
    const trace=JSON.parse(gunzipSync(await read(t109+'/evidence/native/'+arm+'-trace.json.gz')));
    assert.equal(sha(await read(t109+'/evidence/native/'+arm+'-trace.json.gz')),prior.files.find(f=>f.name===arm+'-trace.json.gz').sha256);
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.origin!==server.url)return route.abort();
      if(u.pathname==='/t127/')return route.fulfill({contentType:'text/html',body:html});
      if(u.pathname==='/woodpile.ply')return route.fulfill({contentType:'application/octet-stream',body:asset});
      return route.continue();
    });
    const initial=await phase(arm+'_load_reset',async()=>{
      await page.goto(server.url+'/t127/?embed=1&orbit=0',{waitUntil:'load'});
      return page.evaluate(async c=>{
        const d=__demo;d.P.paused=true;d.forceSize(c.width,c.height);
        const r=await fetch('/woodpile.ply'),loaded=d.loadPLY(await r.arrayBuffer());
        if(!r.ok||loaded.kept!==c.material_count || loaded.total!==c.material_count)throw Error('Invalid fitted material count');
        d.research.reset(c.seed,c.params);__t42.camera(c.camera);
        return {stroke:__t86.ignite(c.picks[0],false),backend:__t127.backend()};
      },cfg);
    });
    assert.deepEqual(initial.stroke,expected.initial);report.runtime.graphics=initial.backend;
    for(const end of [180,224,270]){
      const rows=await phase(arm+'_native_through_'+end,()=>page.evaluate(([end,dt])=>__t86.frames(end,dt),[end,cfg.dt]));
      const start=end-rows.length;
      const clean=rows.map(withoutTimings);
      assert.deepEqual(clean,trace.slice(start,end).map(withoutTimings),'ordered native trace, including all random draws and counts');
      record.trace_ranges.push({first:start+1,last:end,sha256:sha(JSON.stringify(clean))});
      if(end===180){
        const fork=await page.evaluate(p=>{const pre=__t86.marker(),edit=__t86.ignite(p,true);return {pre,edit,post:__t86.marker()};},cfg.picks.find(p=>p.name===pick));
        assert.deepEqual(fork,{pre:expected.pre_edit,edit:expected.edit,post:expected.post_edit});
        record.fork={pre:fork.pre,post:fork.post,stroke_count:fork.edit.count};continue;
      }
      const state=await page.evaluate(()=>__t127.fingerprint());
      record.frames[end]=state;
      if(pick==='F')assert.deepEqual(state, nativeReference[end], 'independent native full-brush field fingerprint '+end);
      let originalPrimary;
      const draw=async (camera,mode,save,expectedBytes)=>{
        const value=await phase(arm+'_'+end+'_c'+camera.id+'_'+mode,()=>page.evaluate(([camera,mode])=>__t127.draw(camera,mode==='wood'),[camera,mode]));
        const bytes=Buffer.from(value.png.split(',')[1],'base64');
        const {png,...info}=value;
        assert.deepEqual(info.before,state);
        assert.deepEqual(info.after,state);
        assert.equal(info.error,0);assert.equal(info.lost,false);
        assert.deepEqual(info.size,[cfg.width,cfg.height]);
        assert.equal(info.dynamic_instances,state.marker.gas_count);assert.equal(info.total,state.marker.gas_count);
        if(expectedBytes)assert(bytes.equals(expectedBytes),'Returned image must match at repeated camera and state.');
        const key=name+'-c'+camera.id+'-h'+(end-180)+'-'+mode+'.png';
        record.renders.push({frame:end,camera:camera.id,mode,repeat:!!expectedBytes,dynamic_instances:info.dynamic_instances,gl_error:info.error,
          before_state_hash:state.marker.hash,after_state_hash:info.after.marker.hash,sha256:sha(bytes)});
        if(save){await fs.writeFile(path.join(target,key),bytes,{flag:'wx'});record.images.push({name:key,bytes:bytes.length,sha256:sha(bytes)});}
        return bytes;
      };
      for(const c of cameras){
        const bytes=await draw(c,'full',true);
        if(c.id===0)originalPrimary=bytes;
        await draw(c,'wood',true);await draw(c,'full',false,bytes);
      }
      await draw(cameras[0],'full',false,originalPrimary);
      await fs.writeFile(receipt,JSON.stringify(report,null,2)+'\n');
    }
    await page.close();
  }
  assert.equal(report.errors.length,0);
  assert.equal(Object.values(report.arms).flatMap(a=>a.renders).length,28);
  assert.equal(Object.values(report.arms).flatMap(a=>a.images).length,16);
  report.status='validated_native_capture';
}catch(e){
  report.status='failed_native_capture';report.errors.push(e.stack || String(e));process.exitCode=1;
}finally{
  await browser?.close();await server?.close();clearTimeout(watchdog);
  report.wall_ms=performance.now()-started;report.finished_utc=new Date().toISOString();
  if(report.expired||report.wall_ms>240000){report.status='failed_native_capture';report.errors.push('240 s budget exceeded');process.exitCode=1;}
  await fs.writeFile(receipt,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,wall_ms:report.wall_ms,errors:report.errors}));
}

