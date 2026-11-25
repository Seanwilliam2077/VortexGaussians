import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Script} from 'node:vm';
import {startServer} from '../../../../research/lib/runtime.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),tasks=path.dirname(here),root=path.resolve(here,'../../../..');
const [asset,dir,mode]=process.argv.slice(2);
assert(['firewoods','playground'].includes(asset) && dir);
const read=async f=>JSON.parse(await fs.readFile(f)),sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const methods=['active-fresh','active-anchor','component-fresh','component-anchor'];
const report={schema:'t104-uncapped-coupled-v1',asset,sources:{},status:'running',methods,arms:{},errors:[]};
async function source(k,p,hash){const bytes=await fs.readFile(p);report.sources[k]=sha(bytes);if(hash)assert.equal(sha(bytes),hash);return bytes;}
const origin=await read(path.join(tasks,'t86-ignition-margin/public/capture-report.json'));
const geometry=await read(path.join(here,'GEOMETRY.json'));
const dataset=asset==='firewoods'?'t42-firewoods-sequential-workflow':'t101-playground-holdout';
const cfg=JSON.parse(await source('recipe',path.join(tasks,dataset,'recipe.json')));
assert.equal(cfg.params.spreadFrontierCap,1400);cfg.params.spreadFrontierCap=1000000;
const ply=await source('asset',asset==='firewoods'?process.env.T86_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply'):
  path.join(tasks,dataset,'local/scene.ply'),geometry.assets[asset].sha256);
const t86=path.join(tasks,'t86-ignition-margin'),demo=await source('demo',path.join(root,'demo/index.html'),origin.sources.demo.sha256);
const camera=await source('camera',path.join(tasks,'t42-firewoods-sequential-workflow/adapter.js'),origin.sources.camera_adapter.sha256);
const observer=await source('observer',path.join(t86,'native.js'),origin.sources['native.js'].sha256);
const needle='const full=L.ps.length>=P.ppl; let recycle=-1;';
assert.equal(demo.toString().split(needle).length,2);
let html=demo.toString().replace(needle,'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;')
  .replace('window.__demo = {',()=>camera+'\n'+observer+'\nwindow.__demo = {');
assert.equal(sha(html),origin.sources.staged_html.sha256);
const plugins=[
  ['t90','t90-callable-regional-query/query.js','0e0cd4cecba197fb109e61cdd522f591bfc4d22722f3ff43a0923d35b3f27036'],
  ['t95','t95-multistep-material-slice/local/plugin.js','5782263e00c896e983614799332480c0abff925c83b1faaf6920b8c827af74c2'],
  ['t97','t97-ordinary-cached-graph/.generated-plugin.js','36a19010dfda87a3c27e2f458a529e14537eda16a5f6055e681c025fdbca3e59'],
  ['t102','t102-active-recipients/local/plugin.js','3311852d29e7c1ee2b6f9b615235174ece6550c79b0c889e6e7b3b7f4c1e8474'],
  ['t98','t98-edit-to-answer/click.js'],
  ['t102audit','t102-active-recipients/audit.js','8011178b2d71699d05e3d38eaa617cd428bef3e8e440c7133f9b20c4d3d7efbf']
];
let parts=[];
for(const [name,file,hash] of plugins)parts.push(await source(name,path.join(tasks,file),hash));
const graph=(await source('graph',path.join(here,'geometry.mjs'))).toString();
parts.push(graph.slice(graph.indexOf('export function searchGraph'),graph.indexOf('export function selfCheck')).replace('export ','')
  .replaceAll('assert(','t104Require(').replaceAll('assert.equal(seen[i],-1)','t104Require(seen[i]===-1)'));
parts.push('function t104Require(x){if(!x)throw Error("Invalid graph input");}'+await source('operator',path.join(here,'operator.js')));
html=html.replace('window.__demo = {',()=>parts.join('\n')+'\nwindow.__demo = {');
for(const m of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new Script(m[1]);
report.sources.stage=sha(html);
const frozen=await read(path.join(tasks,'t81-firewoods-capacity-causality/freeze.json')),require=createRequire(import.meta.url);
const pw=process.env.PLAYWRIGHT_MODULE || frozen.runtime.playwright_module,exe=process.env.BROWSER_EXECUTABLE || frozen.runtime.browser_executable;
report.runtime={node:process.version,browser_executable_sha256:sha(await fs.readFile(exe)),playwright_version:require(path.join(pw,'package.json')).version};
for(const [k,v] of Object.entries(report.runtime))assert.equal(v,origin.runtime[k]);
if(mode==='--check'){console.log('validated staging');process.exit(0);}
const out=path.resolve(dir);await fs.mkdir(out,{recursive:true});
await fs.writeFile(path.join(out,'RUN.json'),JSON.stringify({start:new Date(),asset,methods})+'\n',{flag:'wx'});
const started=performance.now();let browser,server;
function save(){return fs.writeFile(path.join(out,'CAPTURE.json'),JSON.stringify(report,null,2)+'\n');}
const watchdog=setTimeout(async()=>{report.errors.push('900s budget');report.status='failed';await save();process.exit(1);},900000);
try{
  server=await startServer(root);
  browser=await require(pw).chromium.launch({headless:true,executablePath:exe});
  assert.equal(browser.version(),origin.runtime.browser_version);
  for(const [order,arm] of ['AB','BA'].entries()){
    const shot=report.arms[arm]={trials:[],contract_h:60},picks=[...arm].map(a=>cfg.picks.find(p=>p.name===a));
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.origin!==server.url)return route.abort();
      if(u.pathname==='/query/')return route.fulfill({status:200,body:html,contentType:'text/html; charset=utf-8'});
      if(u.pathname==='/scene.ply')return route.fulfill({status:200,body:ply,contentType:'application/octet-stream'});
      return route.continue();
    });
    await page.goto(server.url+'/query/?embed=1&orbit=0',{waitUntil:'load'});
    await page.waitForFunction(()=>window.__t104 && window.__demo);
    shot.initial=await page.evaluate(async([cfg,pick])=>{
      __demo.P.paused=true;__demo.forceSize(cfg.width,cfg.height);
      __demo.loadPLY(await (await fetch('/scene.ply')).arrayBuffer());__demo.research.reset(cfg.seed,cfg.params);
      __t42.camera(cfg.camera);return __t86.ignite(pick,false);
    },[cfg,picks[0]]);
    const t=performance.now();
    shot.pre=await page.evaluate(dt=>{__t86.frames(180,dt);return __t86.marker();},cfg.dt);
    shot.native_to_cut_ms=performance.now()-t;
    const native=await page.evaluate(([p,dt])=>{
      __t98.resetTrial();
      try{
        const edit=__t86.ignite(p,true),shell=new Set(__t90.configure(p)),after=__t86.marker();
        const eligible=__t98.eligibleAfterClick().length,rows=__t86.frames(240,dt);
        return {edit,after,eligible,end:__t86.marker(),frames:rows.map(r=>({frame:r.frame,ids:r.new_ids.filter(i=>shell.has(i)),
          new_sites:r.new_ids.length,active:r.active_count,gas:r.gas_count,draws:r.random_draws}))};
      } finally{__t98.finishTrial();}
    },[picks[1],cfg.dt]);
    shot.native=native;const onset=native.frames.find(f=>f.ids.length);
    for(let rep=0;rep<5;rep++)for(let j=0;j<methods.length;j++){
      const method=methods[(j+rep+order)%methods.length];
      await page.evaluate(()=>__t98.resetTrial());
      const start=performance.now(),r=await page.evaluate(([m,p,dt])=>__t104.measure(m,60,dt,p),[method,picks[1],cfg.dt]);
      const delivered_ms=performance.now()-start;
      await page.evaluate(()=>__t98.finishTrial());
      shot.trials.push({...r,rep,delivered_ms});
      assert.equal(r.clicked,native.edit.count);assert.equal(r.first,onset?.frame??null);
      assert(onset?onset.ids.includes(r.witness):r.witness===null);
    }
    await page.evaluate(()=>__t98.resetTrial());
    shot.audit=await page.evaluate(([p,dt])=>__t104.audit(p,dt),[picks[1],cfg.dt]);
    await page.evaluate(()=>__t98.finishTrial());
    shot.ordinary_audit=await page.evaluate(([p,dt])=>__t102Audit(p,dt),[picks[1],cfg.dt]);
    assert.deepEqual(await page.evaluate(()=>__t86.marker()),shot.pre);
    shot.stored_pre_restored=true;
    await page.close();await save();
  }
  assert.deepEqual(report.errors,[]);report.status='validated';
}catch(e){report.status='failed';report.errors.push(String(e.stack||e));process.exitCode=1;}
finally{await browser?.close();await server?.close();clearTimeout(watchdog);report.total_ms=performance.now()-started;await save();}
console.log(JSON.stringify({status:report.status,ms:report.total_ms,errors:report.errors}));
