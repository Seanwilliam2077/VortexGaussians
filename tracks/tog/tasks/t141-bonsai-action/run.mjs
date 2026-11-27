import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {startServer} from '../../../../research/lib/runtime.mjs';
import {instrumentNativeMatte} from '../t140-native-shell-sensitivity/native-matte.mjs';
import {instrumentPickAudit,auditPickPixels} from './pick-audit.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../../..');
const read=name=>fs.readFile(path.resolve(here,name),'utf8'),json=async name=>JSON.parse(await read(name));
const hash=data=>createHash('sha256').update(data).digest('hex');
const results=await json('../t139-native-brush-projection/RESULTS.json'),cfg=results.native_input;
const cameras=await json('../t136-bonsai-shot/local/t139-cameras.json');
const t109=await json('../t109-common-parent-choice/evidence/native/capture-report.json');
const rt=(await json('../t81-firewoods-capacity-causality/freeze.json')).runtime;
const primary=cameras.find(c=>c.id===0);
function replace(text,needle,newText){
  assert.equal(text.split(needle).length,2,needle);
  return text.replace(needle,()=>newText);
}
const sources={};
async function file(name,identity){
  const text=await read(name),sha=hash(text);
  if(identity)assert.equal(sha,identity,name);
  sources[name]=sha;return text;
}
const demo=await file('../../../../demo/index.html',t109.sources.demo.sha256);
const t42=await file('../t42-firewoods-sequential-workflow/adapter.js',t109.sources.camera.sha256);
const t86=await file('../t86-ignition-margin/native.js',t109.sources.observer.sha256);
let kernels=await file('../t129-native-image-choice/native-kernels.js');
for(const [old,updated] of [
  ['P.sceneScale !== 1 || pointer.active','!(P.sceneScale > 0) || pointer.active'],
  ['P.sceneScale!==1 || !P.spreadFlameHeat','!(P.sceneScale>0) || !P.spreadFlameHeat'],
  ['const radius=P.spreadR;','const radius=P.spreadR/P.sceneScale;'],
  ['const r=P.spreadR, clock=performance.now();','const r=P.spreadR/P.sceneScale, clock=performance.now();'],
  ['t116GetGeometry(P.spreadIgnR),start=','t116GetGeometry(P.spreadIgnR/P.sceneScale),start='],
  ['const r=P.spreadIgnR, grid=','const r=P.spreadIgnR/P.sceneScale, grid='],
  ['nx*ny*nz>4000000','nx*ny*nz>16000000']])kernels=replace(kernels,old,updated);
const action=await file('action.js');
let html=replace(demo,'const full=L.ps.length>=P.ppl; let recycle=-1;',
  'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
html=replace(html,'window.__demo = {',t42+'\n'+t86+'\nwindow.__demo = {');
assert.equal(hash(html),t109.staged_sha256);
html=instrumentPickAudit(instrumentNativeMatte(html));
html=replace(html,'function drawPartRange(start,count){ if(count<=0) return;',
  'function drawPartRange(start,count){ if(count<=0 || t141HideGas) return;');
html=replace(html,'window.__demo = {',kernels+'\n'+action+'\nwindow.__demo = {');
for(const marker of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi))new Function(marker[1]);
if(process.argv[2]==='--check-staging'){console.log('Native HTML staged',hash(html));process.exit(0);}
assert(process.argv[2],'Supply a new private worker evidence directory via supervisor');
const out=path.resolve(process.argv[2]), receipt=path.join(out,'RUN.json');
const report={schema:'t141-bonsai-native-action-v1',status:'running',sources,staged_html_sha256:hash(html),
  phase:null,phases:[],actions:[],finished_audit_branches:[],warnings:[],errors:[],start_utc:new Date().toISOString()};
const start=performance.now();
let browser,server,page;
const save=async()=>{const temp=receipt+'.tmp';await fs.writeFile(temp,JSON.stringify(report,null,2)+'\n');await fs.rename(temp,receipt);};
async function phase(name,fn){
  report.phase=name;await save();const t=performance.now();
  try{return await fn();}
  finally{report.phases.push({name,ms:performance.now()-t});await save();}
}
async function actual(method,audit){
  const record=await phase(method+(audit?'-audit':'-requested-choice'),()=>{
    const begin=performance.now();
    return page.evaluate(({method,picks,audit})=>__t141.action(method,picks,audit),{method,picks:cfg.picks.slice(1),audit})
      .then(r=>({...r,host_ms:performance.now()-begin}));
  });
  report.actions.push(record);await save();return record;
}
async function rootState(){return page.evaluate(()=>__t141.state());}
function compare(ref,row){
  assert.equal(row.choice,ref.choice);
  for(const branch of row.branches){
    const expected=ref.branches.find(b=>b.name===branch.name);
    assert(expected);
    for(const key of ['mass','denominator','passes'])assert.equal(branch.result[key],expected.result[key],branch.name+' '+key);
    if(row.audit){
      assert.deepEqual(branch.endpoint,expected.endpoint,'endpoint '+branch.name);
      assert.deepEqual(branch.successor,expected.successor,'successor '+branch.name);
      assert.deepEqual(branch.result.hashes,expected.result.hashes,'paired full RGB buffers '+branch.name);
    }
  }
}
try{
  const module=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||rt.playwright_module);
  server=await startServer(root);
  browser=await phase('launch',()=>module.chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE||rt.browser_executable}));
  page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
  await page.exposeBinding('__t141Report',async(_,value)=>{report.finished_audit_branches.push(value);await save();});
  page.on('pageerror',e=>report.errors.push(String(e)));
  await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
  await page.route('**/*',route=>{
    const u=new URL(route.request().url());
    if(u.origin!==server.url)return route.abort();
    if(u.pathname==='/t141/')return route.fulfill({body:html,contentType:'text/html'});
    return route.continue();
  });
  await phase('open',()=>page.goto(server.url+'/t141/?embed=1&orbit=0',{waitUntil:'load'}));
  report.load=await phase('load_and_check_all_splats',()=>page.evaluate(async({c,camera})=>{
    __demo.P.paused=true;__demo.forceSize(c.width,c.height);__demo.P.sceneMax=c.decode_cap;
    const response=await fetch('/tracks/tog/tasks/t136-bonsai-shot/local/scene.ply');
    if(!response.ok)throw Error('Original fit unavailable');
    const bytes=await response.arrayBuffer(),actual=await crypto.subtle.digest('SHA-256',bytes);
    const digest=Array.from(new Uint8Array(actual),v=>v.toString(16).padStart(2,'0')).join('');
    if(digest!=='a16af6d8815498ffbf9eb5d5ee93f5bcc9dca34c4e3eb6f7a796ef9e97c0d273')throw Error('Native fit hash');
    const started=performance.now(),r=__demo.loadPLY(bytes),parse_ms=performance.now()-started;
    if(r.kept!==c.material_count||r.total!==r.kept)throw Error('Native importer did not preserve entire fitted room');
    __demo.research.reset(c.seed,c.params);__t42.camera(camera);
    return {sha256:digest,parse_ms,...r,...__t141.hardware()};
  },{c:cfg,camera:primary}));await save();
  assert.equal(report.load.sh_degree,3);assert.equal(report.load.width,cfg.width);assert.equal(report.load.height,cfg.height);
  assert.equal(report.load.float_color,true);assert.equal(report.load.context_lost,false);
  assert.equal(report.load.load_gl_error,0);assert(report.load.sh_texture_width>0);
  assert.deepEqual(report.load.center,cfg.source_center);
  report.rest=await phase('rest_physical',rootState);
  report.pick_audit=await phase('native_prefix_pixel_audit',()=>auditPickPixels(page,primary,results));await save();
  assert.deepEqual(await rootState(),report.rest,'Pick diagnostic altered rest state');
  await page.evaluate(c=>__t141.registerRest(c),primary);
  report.first=await phase('native_A',()=>page.evaluate(p=>__t86.ignite(p,false),cfg.picks[0]));
  assert.equal(report.first.count,cfg.picks[0].initial_geometric_count);
  report.parent_progress=[];
  for(const frame of [30,60,90,120,150,180]){
    report.parent_progress.push(await phase('ordinary_common_parent_'+frame,()=>page.evaluate(n=>__t141.native(n),frame)));
    await save();
  }
  report.parent=await phase('common_parent_digest',rootState);
  report.shell=await phase('native_eligible_shell',()=>page.evaluate(p=>__t141.shell(p),cfg.picks[2]));
  assert.equal(report.shell.geometric_hash,cfg.geometric_shell_sha256);
  report.matte=await phase('full_scene_rest_native_matte_then_restore',()=>page.evaluate(()=>__t141.matte()));await save();
  assert.deepEqual(await rootState(),report.parent,'Matte diagnostic altered parent');
  if(!report.matte.total){report.status='undefined_primary_matte';}
  else{
    const ref=await actual('ordinary-native',true);
    for(const method of ['ordinary-indexed','transport']){
      await page.evaluate(()=>__t141.cold());
      compare(ref,await actual(method,true));
      assert.deepEqual(await rootState(),report.parent,'Audit failed to restore parent');
    }
    for(const method of ['ordinary-indexed','transport']){
      compare(ref,await actual(method,false));
      assert.deepEqual(await rootState(),report.parent,'Requested action failed to restore parent');
    }
    report.status='correctness_complete';
  }
  assert.equal(report.errors.length,0);
}catch(e){report.status='failed';report.errors.push(String(e.stack||e).replaceAll(root,'<repo>').replaceAll(here,'<task>'));process.exitCode=1;}
finally{
  report.final_phase=report.phase;report.elapsed_ms=performance.now()-start;await save();
  if(browser)await browser.close();if(server)await server.close();
  console.log(report.status,report.phase);
}
