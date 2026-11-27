import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {startServer} from '../../../../research/lib/runtime.mjs';
import {instrumentNativeMatte} from './native-matte.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(here,'../../../..');
const [source, labelsFile, local, receipt] = process.argv.slice(2).map(v=>path.resolve(v));
assert(receipt && !local.startsWith(root+path.sep),'Supply source, labels, fresh private directory, fresh public receipt');
const priorDir=path.resolve(here,'../t109-common-parent-choice');
const readjson=async p=>JSON.parse(await fs.readFile(p));
const sha=b=>createHash('sha256').update(b).digest('hex');
const start=performance.now(), report={schema:'t140-native-woodpile-matte-v1',status:'running',draws:[],errors:[]};
const require=createRequire(import.meta.url);
let browser,server,watchdog;
await fs.mkdir(local);
await fs.mkdir(path.dirname(receipt),{recursive:true});
await fs.writeFile(receipt,JSON.stringify(report),{flag:'wx'});
try{
  const baseline=await readjson(path.join(priorDir,'evidence/native/capture-report.json'));
  const cfg=await readjson(path.join(priorDir,'recipe.json'));
  const {runtime}=await readjson(path.join(here,'../t81-firewoods-capacity-causality/freeze.json'));
  const demo=await fs.readFile(path.join(root,'demo/index.html'));
  const adapter=await fs.readFile(path.join(here,'../t42-firewoods-sequential-workflow/adapter.js'));
  const asset=await fs.readFile(path.join(source,'foreground.ply'));
  const cameraBytes=await fs.readFile(path.join(source,'cameras.json'));
  const labelBytes=await fs.readFile(labelsFile), labels=JSON.parse(labelBytes);
  assert.equal(sha(demo),baseline.sources.demo.sha256);assert.equal(sha(adapter),baseline.sources.camera.sha256);
  assert.equal(sha(asset),cfg.asset_sha256);
  assert.equal(sha(cameraBytes),'5cdd4605b0bf11970357c26e66ce3affb6c25ab2823171488fa41288ceb4a5c5');
  const cameras=[0,124].map(id=>JSON.parse(cameraBytes).find(c=>c.id===id));
  assert.deepEqual(cameras[0],cfg.camera);assert.equal(cameras[1].img_name,'00124');
  assert.equal(labels.eligible.length,2371);
  const marker='window.__demo = {';
  assert.equal(demo.toString().split(marker).length,2);
  const html=instrumentNativeMatte(demo.toString().replace(marker,()=>adapter.toString()+'\n'+marker));
  report.source={demo:sha(demo),adapter:sha(adapter),asset:sha(asset),cameras:sha(cameraBytes),
                 tag_ids:sha(labelBytes),helper:sha(await fs.readFile(path.join(here,'native-matte.mjs'))),
                 staged_html:sha(html)};
  watchdog=setTimeout(()=>{report.expired=true;browser?.close().catch(()=>{});},180000-(performance.now()-start));
  const modulePath=process.env.PLAYWRIGHT_MODULE||runtime.playwright_module;
  const executablePath=process.env.BROWSER_EXECUTABLE||runtime.browser_executable;
  server=await startServer(root);
  browser=await require(modulePath).chromium.launch({executablePath,headless:true});
  report.browser=browser.version();
  const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
  page.on('pageerror',e=>report.errors.push(String(e)));
  await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
  await page.route('**/*',route=>{
    const url=new URL(route.request().url());
    if(url.origin!==server.url)return route.abort();
    if(url.pathname==='/t140/')return route.fulfill({contentType:'text/html',body:html});
    if(url.pathname==='/woodpile.ply')return route.fulfill({contentType:'application/octet-stream',body:asset});
    return route.continue();
  });
  await page.goto(server.url+'/t140/?embed=1&orbit=0',{waitUntil:'load'});
  report.initial=await page.evaluate(async c=>{
    const d=window.__demo;d.P.paused=true;d.forceSize(c.width,c.height);
    const result=await fetch('/woodpile.ply');
    const loaded=d.loadPLY(await result.arrayBuffer());
    if(!result.ok || loaded.total!==c.material_count || loaded.kept!==loaded.total)throw Error('Incorrect PLY count');
    d.research.reset(c.seed,c.params);d.P.paused=true;
    return {loaded:loaded.kept,width:c.width,height:c.height};
  },cfg);
  let primary;
  for(const [cam,kind,repeat] of [...cameras.flatMap(c=>['eligible','light','full'].map(k=>[c,k,false])),[cameras[0],'eligible',true]]){
    const data=await page.evaluate(([camera,ids])=>{__t42.camera(camera);return __nativeMatte.capture(ids);},[cam,labels[kind]]);
    assert.deepEqual([data.width,data.height,data.block],[470,264,2]);
    assert.equal(data.stats.tagCount,labels[kind].length);assert.equal(data.stats.dynamic,0);
    assert.equal(data.stats.sites,cfg.material_count);
    const hashes={},mapped={};
    for(const field of ['eligible','all']){
      const bytes=Buffer.from(data[field],'base64');assert.equal(bytes.length,470*264*4);
      hashes[field]=sha(bytes);mapped[field]=bytes;
      if(!repeat)await fs.writeFile(path.join(local,`c${cam.id}-${kind}-${field}.f32`),bytes,{flag:'wx'});
    }
    if(cam.id===0 && kind==='eligible'&&!repeat)primary=hashes;
    if(repeat)assert.deepEqual(hashes,primary);
    report.draws.push({camera:cam.id,kind,repeat,stats:data.stats,hashes});
    await fs.writeFile(receipt,JSON.stringify(report,null,2)+'\n');
  }
  assert.deepEqual(report.errors,[]);
  report.status='complete';
}catch(e){
  report.errors.push(String(e));report.status='failed';process.exitCode=1;
}finally{
  clearTimeout(watchdog);await browser?.close();await server?.close();
  report.wall_ms=performance.now()-start;
  if(report.wall_ms>180000 || report.expired){report.status='timeout';process.exitCode=1;}
  await fs.writeFile(receipt,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,draws:report.draws.length,wall_ms:report.wall_ms,errors:report.errors}));
}
