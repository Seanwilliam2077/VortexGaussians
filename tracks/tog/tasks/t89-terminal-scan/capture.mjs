import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {gunzipSync,gzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';

const started=performance.now(), here=path.dirname(fileURLToPath(import.meta.url));
const base=path.resolve(here,'../t86-ignition-margin'), root=path.resolve(here,'../../../..');
const sha=b=>createHash('sha256').update(b).digest('hex');
const json=async file=>JSON.parse(await fs.readFile(file));
const reference=await json(path.join(base,'public/capture-report.json'));
const frozen=await json(path.join(here,'../t81-firewoods-capacity-causality/freeze.json'));
const out=path.resolve(process.argv[2] || path.join(here,'evidence'));
const list=reference.files;
const report={schema:'t89-native-terminal-scan-v1',status:'running',started_utc:new Date().toISOString(),
  sources:{},runtime:{},phases_ms:{},shots:{},errors:[],steps:0};

async function input(name,file,expected) {
  const raw=await fs.readFile(file);
  const actual=sha(raw); if(expected)assert.equal(actual,expected,'Source identity '+name);
  report.sources[name]=actual;
  return raw;
}
function patch(source,before,after){
  assert.equal(source.split(before).length,2,'Nonunique source marker '+before);
  return source.replace(before,()=>after);
}
async function timed(cost,key,fn){
  const begin=performance.now();try{return await fn();}finally{cost[key]=performance.now()-begin;}
}
const source=(await input('demo',path.join(root,'demo/index.html'),reference.sources.demo.sha256)).toString();
const t42=path.join(here,'../t42-firewoods-sequential-workflow');
const camera=(await input('camera_adapter',path.join(t42,'adapter.js'),reference.sources.camera_adapter.sha256)).toString();
const observer=(await input('T86_observer',path.join(base,'native.js'),reference.sources['native.js'].sha256)).toString();
let html=patch(source,'const full=L.ps.length>=P.ppl; let recycle=-1;',
  'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
html=patch(html,'window.__demo = {',camera+'\n'+observer+'\nwindow.__demo = {');
assert.equal(sha(html),reference.sources.staged_html.sha256,'Must exactly reproduce T86 staged HTML');
report.sources.T86_staged=sha(html);

const ignitionScanEnd='  // Source-space world-up = Rx(pitch)^T Ry(yaw)^T [0,1,0].';
html=patch(html,ignitionScanEnd,'  t89ScanEnd = performance.now();\n'+ignitionScanEnd);
html=patch(html,'let t86Global = false;','let t86Global = false, t89ScanEnd = NaN;');
html=patch(html,'        const stepStart = performance.now();',
  '        t89ScanEnd = NaN;\n        const stepStart = performance.now();');
html=patch(html,'        const new_ids = [];',
  "        if (!(stepStart <= t89ScanEnd && t89ScanEnd <= done)) throw Error('Native scan missing');\n        const new_ids = [];");
html=patch(html,'step_ms: done-stepStart,','step_ms: done-stepStart, scan_ms: t89ScanEnd-stepStart,');
assert.equal([...html.matchAll(/t89ScanEnd = performance\.now\(\)/g)].length,1);
const scripts=[...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)];
assert(scripts.length>0);for(const script of scripts)new vm.Script(script[1]);
report.sources.T89_staged=sha(html);
const cfg=JSON.parse(await input('recipe',path.join(t42,'recipe.json'),reference.sources.recipe.sha256));
const ply=await input('Firewoods',process.env.T86_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply'),
                      reference.sources.Firewoods_foreground.sha256);
await input('T86_reference',path.join(base,'public/capture-report.json'));
await input('T89_protocol',path.join(here,'PROTOCOL.md'));
await input('T89_worker',fileURLToPath(import.meta.url));
const traces={};
for(const arm of ['AB','BA']){
  const file=arm+'-trace.json.gz';
  traces[arm]=JSON.parse(gunzipSync(await input(file,path.join(base,'public',file),list.find(r=>r.name===file).sha256)));
}
const require=createRequire(import.meta.url);
const pw=process.env.PLAYWRIGHT_MODULE || frozen.runtime.playwright_module;
const browserExe=process.env.BROWSER_EXECUTABLE || frozen.runtime.browser_executable;
const playwright=require(pw);
report.runtime={node:process.version,node_sha256:sha(await fs.readFile(process.execPath)),
  browser_executable_sha256:sha(await fs.readFile(browserExe)),playwright_version:require(path.join(pw,'package.json')).version};
for(const k of Object.keys(report.runtime))assert.equal(report.runtime[k],reference.runtime[k],'Runtime '+k);
report.phases_ms.preflight=performance.now()-started;
if (process.argv.includes('--check')){console.log('T86 staged digest, T89 scan marker, runtime, JS syntax and input identities matched.');process.exit(0);}

let browser,server;
await fs.mkdir(out,{recursive:true});
await fs.writeFile(path.join(out,'RUN.json'),JSON.stringify({started_utc:report.started_utc})+'\n',{flag:'wx'});
try{
  server=await startServer(root);
  browser=await timed(report.phases_ms,'browser_launch',()=>playwright.chromium.launch({headless:true,executablePath:browserExe}));
  report.runtime.browser_version=browser.version();assert.equal(browser.version(),reference.runtime.browser_version);
  for(const arm of ['AB','BA']){
    const shot=report.shots[arm]={phases_ms:{},markers:{}};
    const page=await timed(shot.phases_ms,'new_page',()=>browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1}));
    page.on('pageerror',err=>report.errors.push(String(err)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const url=new URL(route.request().url());
      if(url.origin!==server.url){report.errors.push('Unexpected origin '+url.origin);return route.abort();}
      if(url.pathname==='/t89/')return route.fulfill({status:200,body:html,contentType:'text/html; charset=utf-8'});
      if(url.pathname==='/firewoods.ply')return route.fulfill({status:200,body:ply,contentType:'application/octet-stream'});
      return route.continue();
    });
    await timed(shot.phases_ms,'load',async()=>{
      await page.goto(server.url+'/t89/?embed=1&orbit=0',{waitUntil:'load'});
      await page.waitForFunction(()=>window.__t86 && window.__demo);
    });
    const baseline=reference.shots[arm];
    const picks=[...arm].map(name=>cfg.picks.find(p=>p.name===name));
    const init=await timed(shot.phases_ms,'setup_reset_ignite',()=>page.evaluate(async ({c,pick})=>{
      const d=__demo;d.P.paused=true;d.forceSize(c.width,c.height);
      const res=await fetch('/firewoods.ply');if(!res.ok)throw Error('PLY load');
      const load=d.loadPLY(await res.arrayBuffer());d.research.reset(c.seed,c.params);__t42.camera(c.camera);
      return {count:load.kept,initial:__t86.ignite(pick,false)};
    },{c:cfg,pick:picks[0]}));
    assert.equal(init.count,34687);assert.deepEqual(init.initial,baseline.initial);
    const rows=[];
    for(const stop of [180,210,240,300,360]){
      const batch=await timed(shot.phases_ms,'native_and_observation_to_'+stop,
        ()=>page.evaluate(([end,dt])=>__t86.frames(end,dt),[stop,cfg.dt]));
      report.steps+=batch.length;
      for(const row of batch){
        const ref=traces[arm][row.frame-1];
        for(const k of ['frame','new_ids','retired','active_count','gas_count','random_draws'])assert.deepEqual(row[k],ref[k],arm+' '+row.frame+' '+k);
        assert(row.scan_ms>=0 && row.scan_ms<=row.step_ms);
        rows.push(row);
      }
      if(stop===180){
        const markers=await timed(shot.phases_ms,'fork_and_hash',()=>page.evaluate(pick=>{
          const pre_edit=__t86.marker(),edit=__t86.ignite(pick,true),post_edit=__t86.marker();
          return {pre_edit,edit,post_edit};
        },picks[1]));
        for(const k of Object.keys(markers))assert.deepEqual(markers[k],baseline[k],arm+' '+k);
        shot.markers.pre_edit=markers.pre_edit.hash;shot.markers.post_edit=markers.post_edit.hash;
      }else if(stop===360){
        const last=await timed(shot.phases_ms,'end_hash',()=>page.evaluate(()=>__t86.marker()));
        assert.deepEqual(last,baseline.end);shot.markers.end=last;
      }
    }
    assert.equal(rows.length,360);
    shot.native_ms=rows.reduce((n,r)=>n+r.step_ms,0);
    shot.observer_ms=rows.reduce((n,r)=>n+r.observer_ms,0);
    const raw=Buffer.from(JSON.stringify(rows)+'\n'),name=arm+'-frames.json.gz';
    await timed(shot.phases_ms,'event_timing_compress_and_write',async()=>{
      const data=gzipSync(raw);await fs.writeFile(path.join(out,name),data,{flag:'wx'});
      shot.frames={file:name,count:rows.length,sha256:sha(data),decoded_sha256:sha(raw)};
    });
    await timed(shot.phases_ms,'close',()=>page.close());assert.equal(report.errors.length,0);
  }
  assert.equal(report.steps,720);report.status='validated';
}catch(err){report.status='failed';report.errors.push(err.stack||String(err));process.exitCode=1;}
finally{
  await timed(report.phases_ms,'cleanup',async()=>{await browser?.close();await server?.close();});
  report.phases_ms.whole_before_receipt=performance.now()-started;
  await fs.writeFile(path.join(out,'CAPTURE.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:report.status,steps:report.steps,wall_ms:report.phases_ms.whole_before_receipt,errors:report.errors}));
}
