import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {gzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../..');
const out = path.resolve(process.argv[2] || path.join(here, 'evidence'));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const read = filename => fs.readFile(path.join(here, filename));
const cfg = JSON.parse(await read('recipe.json'));
const base = JSON.parse(await read('../t86-ignition-margin/public/capture-report.json'));
const freeze = JSON.parse(await read('../t81-firewoods-capacity-causality/freeze.json'));
const report = {schema:'t92-transfer-native-v1', status:'running', sources:{}, shots:{}, errors:[], files:[]};
async function source(name, file, sha) {
  const bytes = await fs.readFile(file);
  const hash = digest(bytes); if(sha) assert.equal(hash,sha,name);
  report.sources[name] = {sha256:hash, bytes:bytes.length};
  return bytes;
}
async function packed(filename,value){
  const bytes = Buffer.from(JSON.stringify(value)+'\n');
  const gz = gzipSync(bytes,{level:6});
  await fs.writeFile(path.join(out,filename),gz,{flag:'wx'});
  report.files.push({name:filename,sha256:digest(gz),decoded_sha256:digest(bytes),bytes:gz.length});
}
function sameSet(left,right,label) {
  assert.deepEqual([...left].sort((a,b)=>a-b),[...right].sort((a,b)=>a-b),label);
}
const started = performance.now();
await fs.mkdir(path.dirname(out),{recursive:true});
await fs.mkdir(out); // fresh output only, no concurrent writer
await fs.mkdir(path.join(out,'checkpoints'));
let browser,server;
try {
  const demo = (await source('demo',path.join(root,'demo/index.html'),base.sources.demo.sha256)).toString();
  const camera = (await source('camera',path.join(here,'../t42-firewoods-sequential-workflow/adapter.js'),base.sources.camera_adapter.sha256)).toString();
  const adapter = (await source('observer',path.join(here,'../t86-ignition-margin/native.js'),base.sources['native.js'].sha256)).toString();
  await source('protocol',path.join(here,'PROTOCOL.md'));
  await source('recipe',path.join(here,'recipe.json'));
  await source('worker',fileURLToPath(import.meta.url));
  const ply = await source('asset',path.join(here,'local/scene.ply'),cfg.asset_sha256);
  const predicate='const full=L.ps.length>=P.ppl; let recycle=-1;', marker='window.__demo = {';
  assert.equal(demo.split(predicate).length,2); assert.equal(demo.split(marker).length,2);
  const html = demo.replace(predicate, 'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;')
    .replace(marker,()=>camera+'\n'+adapter+'\n'+marker);
  assert.equal(digest(html), base.sources.staged_html.sha256);
  for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script[1]);
  report.staged_sha256=digest(html);
  server=await startServer(root);
  const require=createRequire(import.meta.url), pw=process.env.PLAYWRIGHT_MODULE||freeze.runtime.playwright_module;
  const executablePath=process.env.BROWSER_EXECUTABLE||freeze.runtime.browser_executable;
  browser=await require(pw).chromium.launch({executablePath,headless:true});
  report.runtime={node:process.version,browser:browser.version(),playwright:require(path.join(pw,'package.json')).version};
  for(const arm of ['AB','BA']){
    const shot={cuts:[]}; report.shots[arm]=shot;
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.origin!==server.url)return route.abort();
      if(u.pathname==='/t92/')return route.fulfill({contentType:'text/html',body:html});
      if(u.pathname==='/trunk.ply')return route.fulfill({contentType:'application/octet-stream',body:ply});
      return route.continue();
    });
    await page.goto(server.url+'/t92/?embed=1&orbit=0',{waitUntil:'load'});
    const [first,second]=[...arm].map(name=>cfg.picks.find(p=>p.name===name));
    shot.initial=await page.evaluate(async({c,pick})=>{
      const d=window.__demo;d.P.paused=true;d.forceSize(c.width,c.height);
      const r=await fetch('/trunk.ply');if(!r.ok)throw Error('missing trunk');
      const loaded=d.loadPLY(await r.arrayBuffer());
      if(loaded.kept!==c.material_count||loaded.total!==c.material_count)throw Error('subsampled native sites');
      d.research.reset(c.seed,c.params);window.__t42.camera(c.camera);
      return window.__t86.ignite(pick,false);
    },{c:cfg,pick:first});
    sameSet(shot.initial.ids,first.initial_geometric_neighbors,'Initial brush');
    const seen=new Set(shot.initial.ids),rows=[];
    let retired=0;
    for (const frame of [180,210,240,300,360]){
      const batch=await page.evaluate(([f,dt])=>window.__t86.frames(f,dt),[frame,cfg.dt]);
      for (const row of batch){
        assert.equal(row.frame,rows.length+1);
        for(const id of row.new_ids){assert(!seen.has(id));seen.add(id);}
        retired+=row.retired;assert.equal(row.active_count,seen.size-retired);
        rows.push(row);
      }
      if(frame===180){
        const fork=await page.evaluate(pick=>{
          const pre_edit=__t86.marker(),edit=__t86.ignite(pick,true),post_edit=__t86.marker();
          return {pre_edit,edit,post_edit};
        },second);
        Object.assign(shot,fork);
        sameSet(shot.edit.ids,second.initial_geometric_neighbors.filter(id=>!seen.has(id)),'Edited brush');
        shot.edit.ids.forEach(id=>seen.add(id));
        assert.equal(shot.pre_edit.particle_hash,shot.post_edit.particle_hash);
        assert.equal(shot.post_edit.burning,seen.size-retired);
      }else if(frame===360){
        shot.end=await page.evaluate(()=>window.__t86.marker());
        assert.equal(shot.end.burning,seen.size-retired);assert.equal(shot.end.charred,retired);
        assert.equal(shot.end.gas_count,rows.at(-1).gas_count);
      }else{
        const cut=await page.evaluate(([a,dt])=>window.__t86.cut(a,dt),[arm,cfg.dt]);
        assert.deepEqual(cut.scene_center,cfg.source_center);
        sameSet(cut.state.flatMap((st,i)=>st!==0?[i]:[]),seen,'Native cut labels');
        sameSet(cut.state.flatMap((st,i)=>st===1?[i]:[]),cut.frontier,'Native active frontier');
        assert.equal(cut.state.length,cfg.material_count);
        const file=arm+'-'+frame+'.json.gz';
        await packed('checkpoints/'+file,cut);
        shot.cuts.push({frame,file:'checkpoints/'+file,native_hash:cut.native_hash,active:cut.frontier.length});
      }
    }
    assert.equal(rows.length,360);
    await packed(arm+'-trace.json.gz',rows);
    shot.native_step_total_ms=rows.reduce((a,row)=>a+row.step_ms,0);
    await page.close();
  }
  assert.equal(report.errors.length,0);
  report.status='validated';
}catch(e){report.status='failed';report.errors.push(String(e));process.exitCode=1;}
finally{
  await browser?.close();await server?.close();
  report.capture_wall_ms=performance.now()-started;
  await fs.writeFile(path.join(out,'capture-report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,errors:report.errors,wall_ms:report.capture_wall_ms}));
}
