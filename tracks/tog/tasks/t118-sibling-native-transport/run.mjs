import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)), tasks=path.dirname(here);
const root=path.resolve(here,'../../../..'), require=createRequire(import.meta.url);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const pinned=await read(path.join(tasks,'t86-ignition-margin/public/capture-report.json'));
const freeze=await read(path.join(tasks,'t81-firewoods-capacity-causality/freeze.json'));
const sources={};
async function source(name, file, expected) {
  const bytes=await fs.readFile(file), hash=sha(bytes);
  if(expected) assert.equal(hash,expected,name);
  sources[name]=hash;
  return bytes.toString();
}
function section(source, first, next) {
  const a=source.indexOf(first), b=source.indexOf(next,a);
  assert(a>=0 && b>a);
  return source.slice(a,b);
}
const scratch=path.resolve(process.argv[2]||path.join(here,'evidence'));
await fs.mkdir(scratch); // refuse to overwrite an existing receipt
let browser,server;
const report={schema:'sibling-native-transport-v1',status:'running',sources,scenes:{},errors:[]};
try {
  const native=await source('native',path.join(root,'demo/index.html'),pinned.sources.demo.sha256);
  const camera=await source('camera',path.join(tasks,'t42-firewoods-sequential-workflow/adapter.js'),pinned.sources.camera_adapter.sha256);
  const observer=await source('observer',path.join(tasks,'t86-ignition-margin/native.js'),pinned.sources['native.js'].sha256);
  const fork=await source('fork',path.join(tasks,'t90-callable-regional-query/query.js'));
  const physical=await source('physical',path.join(tasks,'t100-material-repair/repair.js'));
  const operator=await source('operator',path.join(here,'transport.js'));
  const predicate='const full=L.ps.length>=P.ppl; let recycle=-1;', marker='window.__demo = {';
  assert.equal(native.split(predicate).length,2); assert.equal(native.split(marker).length,2);
  const original=native.replace(predicate,'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;')
    .replace(marker,()=>camera+'\n'+observer+'\n'+marker);
  assert.equal(sha(original),pinned.sources.staged_html.sha256);
  const helpers=['let t90Query=null;',section(fork,'function t90Fork()','function t90Run('),
    section(physical,'function t100Physical()','function t100Audit('),operator];
  const html=original.replace(marker,()=>helpers.join('\n')+'\n'+marker);
  sources.staged_html=sha(html);
  server=await startServer(root);
  const pw=process.env.PLAYWRIGHT_MODULE||freeze.runtime.playwright_module;
  const executablePath=process.env.BROWSER_EXECUTABLE||freeze.runtime.browser_executable;
  browser=await require(pw).chromium.launch({executablePath,headless:true});
  report.runtime={node:process.version,browser:browser.version(),playwright:require(path.join(pw,'package.json')).version};
  for (const [label,folder,asset,valid] of [
    ['woodpile','t109-common-parent-choice',process.env.T86_PLY||path.resolve(root,'../real-asset-ingest/foreground.ply'),24],
    ['playground','t111-playground-shot-choice',path.join(tasks,'t101-playground-holdout/local/scene.ply'),16]]) {
    const study=path.join(tasks,folder), cfg=await read(path.join(study,'recipe.json'));
    const bytes=await fs.readFile(asset); assert.equal(sha(bytes),cfg.asset_sha256);
    const parent=(await read(path.join(study,'evidence/native/capture-report.json'))).shots.AF.pre_edit;
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.origin!==server.url)return route.abort();
      if(u.pathname==='/t118/')return route.fulfill({contentType:'text/html',body:html});
      if(u.pathname==='/scene.ply')return route.fulfill({contentType:'application/octet-stream',body:bytes});
      return route.continue();
    });
    await page.goto(server.url+'/t118/?embed=1&orbit=0',{waitUntil:'load'});
    const receipt=await page.evaluate(async ({cfg,valid})=>{
      const d=window.__demo;d.P.paused=true;d.forceSize(cfg.width,cfg.height);
      const loaded=d.loadPLY(await (await fetch('/scene.ply')).arrayBuffer());
      if(loaded.kept!==cfg.material_count||loaded.total!==cfg.material_count)throw Error('Missing sites');
      d.research.reset(cfg.seed,cfg.params); __t42.camera(cfg.camera);
      __t86.ignite(cfg.picks.find(p=>p.name==='A'),false); __t86.frames(180,cfg.dt);
      return __transport(cfg,valid);
    },{cfg,valid});
    assert.deepEqual(receipt.parent,parent);
    const trace=JSON.parse(gunzipSync(await fs.readFile(path.join(study,'evidence/native/AF-trace.json.gz'))));
    assert.deepEqual(receipt.onsets,trace.slice(180,270).map(r=>r.new_ids));
    receipt.onsets_sha256=sha(JSON.stringify(receipt.onsets));receipt.verified_onset_frames=receipt.onsets.length;
    delete receipt.onsets;
    report.scenes[label]=receipt;
    await page.close();
  }
  assert.deepEqual(report.errors,[]);report.status='validated';
} catch(error) {
  report.status='failed';report.errors.push(String(error));process.exitCode=1;
} finally {
  await browser?.close();await server?.close();
  await fs.writeFile(path.join(scratch,'CAPTURE.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,scenes:Object.keys(report.scenes),errors:report.errors}));
}
