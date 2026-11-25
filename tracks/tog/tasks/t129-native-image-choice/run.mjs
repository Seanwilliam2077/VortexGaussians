import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {startServer} from '../../../../research/lib/runtime.mjs';
const self=fileURLToPath(import.meta.url), here=path.dirname(self),root=path.resolve(here,'../../../..');
const source=path.resolve(process.env.FIREWOODS_SOURCE||path.join(root,'../real-asset-ingest'));
const read=(name)=>fs.readFile(path.resolve(here,name)),json=async n=>JSON.parse(await read(n));
const sha=x=>createHash('sha256').update(x).digest('hex');
async function timed(phases,key,f){const t=performance.now();try{return await f();}finally{phases[key]=performance.now()-t;}}
function launch(command,args,ms){
  return new Promise((resolve,reject)=>{
    const child=spawn(command,args,{stdio:'inherit',windowsHide:true,timeout:ms});
    child.once('error',reject);child.once('exit',(code,signal)=>code===0?resolve():reject(Error('Worker exit '+code+' '+signal)));
  });
}
function unique(text,from,to){assert.equal(text.split(from).length,2,from);return text.replace(from,()=>to);}
const args=process.argv.slice(2);
if(args[0]!=='--block'){
  assert.equal(args.length,1,'Supply a fresh output results directory.');
  const out=path.resolve(args[0]),tmp=await fs.mkdtemp(path.join(os.tmpdir(),'vortex-t129-'));
  await fs.mkdir(out);
  const maps=path.join(tmp,'maps'),setup={};
  await timed(setup,'projection_host_ms',()=>launch(process.env.T129_PYTHON||'python',[path.join(here,'weights.py'),'--source',source,'--out',maps],60000));
  setup.weights=JSON.parse(await fs.readFile(path.join(maps,'weights.json')));
  await fs.writeFile(path.join(out,'common_setup.json'),JSON.stringify(setup,null,2)+'\n',{flag:'wx'});
  for(const block of [1,2])await launch(process.execPath,[self,'--block',String(block),out,maps],220000);
}else{
  const [_,index,output,maps]=args,block=Number(index);
  assert([1,2].includes(block));
  const file=path.join(output,'process-'+block+'.json'),begin=performance.now();
  const result={schema:'t129-native-final-image-choice-v1',process:block,pid:process.pid,started_utc:new Date().toISOString(),
    status:'running',setup_ms:{},sources:{},runtime:{},common_parent:null,calibration:{},audits:[],trials:[],errors:[]};
  const persist=()=>fs.writeFile(file,JSON.stringify(result,null,2)+'\n');
  await fs.writeFile(file,JSON.stringify(result),{flag:'wx'});
  let browser,server,watchdog;
  try{
    const t109='../t109-common-parent-choice',t127='../t127-woodpile-native-camera';
    const capture=await json(t127+'/evidence/CAPTURE.json'),score=await json(t127+'/evidence/SCORE.json');
    const prior=await json(t109+'/evidence/native/capture-report.json'),cfg=await json(t109+'/recipe.json');
    assert.equal(sha(await read(t109+'/recipe.json')),prior.sources.recipe.sha256);
    const shell=JSON.parse(gunzipSync(await read(t109+'/shell.json.gz')));
    const imageData=Object.values(capture.arms).flatMap(a=>a.images);
    async function pinned(f,h){const b=await read(f);assert.equal(sha(b),h,f);result.sources[path.basename(f)]=h;return b;}
    const demo=(await pinned(path.join(root,'demo/index.html'),prior.sources.demo.sha256)).toString();
    const observer=(await pinned('../t86-ignition-margin/native.js',prior.sources.observer.sha256)).toString();
    const camera=(await pinned('../t42-firewoods-sequential-workflow/adapter.js',prior.sources.camera.sha256)).toString();
    const asset=await pinned(path.join(source,'foreground.ply'),cfg.asset_sha256);
    const nativeCameras=JSON.parse(await pinned(path.join(source,'cameras.json'),capture.sources['cameras.json']));
    const kernels=(await read('native-kernels.js')).toString(),action=(await read('action.js')).toString();
    const marker='window.__demo = {';
    let html=unique(demo,'const full=L.ps.length>=P.ppl; let recycle=-1;',
      'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
    html=unique(html,marker,camera+'\n'+observer+'\n'+marker);
    assert.equal(sha(html),prior.staged_sha256);
    html=unique(html,marker,[kernels,action,marker].join('\n'));
    html=unique(html,'function drawPartRange(start,count){ if(count<=0) return;',
      'function drawPartRange(start,count){ if(count<=0 || t129Wood) return;');
    Object.assign(result.sources,{T127_capture:sha(await read(t127+'/evidence/CAPTURE.json')),T127_score:sha(await read(t127+'/evidence/SCORE.json')),
      native_kernels:sha(kernels),action:sha(action),worker:sha(await read('run.mjs')),staged_html:sha(html)});
    const manifest=JSON.parse(await fs.readFile(path.join(maps,'weights.json'))),tables={};
    await timed(result.setup_ms,'read_matte_tables_ms',async()=>{
      for(const id of [0,124]){
        tables[id]=await fs.readFile(path.join(maps,'camera-'+id+'.f64'));
        assert.equal(sha(tables[id]),manifest.views[id].sha256);result.sources['view_'+id]=manifest.views[id].sha256;
      }
    });
    const req=createRequire(import.meta.url),rt=(await json('../t81-firewoods-capacity-causality/freeze.json')).runtime;
    const modulePath=process.env.PLAYWRIGHT_MODULE||rt.playwright_module,pw=req(modulePath);
    watchdog=setTimeout(()=>{result.expired=true;browser?.close().catch(()=>{});},210000-(performance.now()-begin));
    server=await startServer(root);
    browser=await timed(result.setup_ms,'browser_launch_ms',()=>pw.chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE||rt.browser_executable}));
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>result.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());if(u.origin!==server.url)return route.abort();
      if(u.pathname==='/t129/')return route.fulfill({contentType:'text/html',body:html});
      if(u.pathname==='/woodpile.ply')return route.fulfill({contentType:'application/octet-stream',body:asset});
      for(const id of [0,124])if(u.pathname==='/map-'+id)return route.fulfill({body:tables[id],contentType:'application/octet-stream'});
      return route.continue();
    });
    await timed(result.setup_ms,'load_scene_and_first_brush_ms',async()=>{
      await page.goto(server.url+'/t129/?embed=1&orbit=0',{waitUntil:'load'});
      const first=await page.evaluate(async c=>{
        __demo.P.paused=true;__demo.forceSize(c.width,c.height);
        const bytes=await (await fetch('/woodpile.ply')).arrayBuffer(),loaded=__demo.loadPLY(bytes);
        if(loaded.kept!==c.material_count || loaded.total!==c.material_count)throw Error('Geometry mismatch');
        __demo.research.reset(c.seed,c.params);__t42.camera(c.camera);return __t86.ignite(c.picks[0],false);
      },cfg);
      assert.deepEqual(first,prior.shots.AL.initial);
    });
    result.runtime={node:process.version,browser:browser.version(),graphics:await page.evaluate(()=>__t129.backend())};
    for(const id of [0,124]){
      result.calibration[id]=await timed(result.setup_ms,'upload_view_'+id+'_ms',()=>page.evaluate(async camera=>{
        const r=await fetch('/map-'+camera.id);if(!r.ok)throw Error('Missing calibrated view');
        return __t129.install(camera,await r.arrayBuffer());
      },nativeCameras.find(c=>c.id===id)));
    }
    await timed(result.setup_ms,'native_parent_180_ms',()=>page.evaluate(dt=>{__t86.frames(180,dt);},cfg.dt));
    result.common_parent=await page.evaluate(()=>__t86.marker());assert.deepEqual(result.common_parent,prior.shots.AL.pre_edit);
    const picks=['L','F'].map(key=>cfg.picks.find(p=>p.name===key));
    const ids=await timed(result.setup_ms,'verify_shell_selection_ms',()=>page.evaluate(p=>__t129.configure(p),picks[1]));
    assert.deepEqual(ids,shell);
    for(const test of score.comparisons)assert(Math.abs(result.calibration[test.camera].total-test.shell_mass)<1e-8);
    async function perform(method,cameras,audit,rep){
      const t=performance.now();
      const row=await page.evaluate(a=>__t129.action(...a),[method,picks,cameras,cfg.dt,audit]);
      row.delivered_ms=performance.now()-t;row.rep=rep;
      assert.deepEqual(row.choices,Object.fromEntries(cameras.map(c=>[c,c===0?'L':'none'])));
      const expectedSequence=audit || cameras.includes(124)?['L','F']:['L'];
      assert.deepEqual(row.strokes.map(s=>s.pick),expectedSequence);
      for(const stroke of row.strokes){
        const brush=stroke.pick==='L'?'light':'full';
        if(audit)assert.deepEqual(stroke.state,capture.arms['A'+stroke.pick].frames['270']);
        assert.deepEqual(stroke.views.map(v=>v.camera),stroke.pick==='F'&&!audit?[124]:cameras);
        for(const v of stroke.views){
          const ref=score.comparisons.find(x=>x.brush===brush&&x.horizon===90&&x.camera===v.camera);
          assert(Math.abs(v.changed_shell_mass-ref.changed_shell_mass)<1e-8);
          assert(Math.abs(v.shell_mass-ref.shell_mass)<1e-8);
          assert.equal(v.passes_quarter,ref.passes_quarter);
          if(audit){
            v.png_sha256={};
            for(const tag of ['full','wood']){
              const digest=sha(Buffer.from(v.images[tag],'base64'));
              const f=brush+'-c'+v.camera+'-h90-'+tag+'.png';
              assert.equal(digest,imageData.find(r=>r.name===f).sha256,f);
              v.png_sha256[tag]=digest;
            }
            delete v.images;
          }
        }
      }
      assert.deepEqual(await page.evaluate(()=>__t86.marker()),result.common_parent,'action must restore the pre-click physical parent');
      return row;
    }
    for(const method of ['ordinary','sibling']){
      const audit=await perform(method,[0,124],true,-1);result.audits.push(audit);
    }
    const scopes=block===1?[[0],[0,124]]:[[0,124],[0]];
    for(const [scopeIndex,cameras] of scopes.entries()){
      for(let rep=0;rep<=6;rep++){
        const methods=(rep+block-1+scopeIndex)%2===0?['ordinary','sibling']:['sibling','ordinary'];
        for(const method of methods){
          if(rep===0)await page.evaluate(()=>__t129.cold());
          const trial=await perform(method,cameras,false,rep);
          result.trials.push(trial);
        }
        await persist();
      }
    }
    assert.equal(result.trials.length,28);assert.equal(result.errors.length,0);
    result.status='validated';
  }catch(e){result.status='failed';result.errors.push(e.stack||String(e));process.exitCode=1;}
  finally{
    await browser?.close();await server?.close();clearTimeout(watchdog);
    result.wall_ms=performance.now()-begin;
    if(result.expired||result.wall_ms>210000){result.status='failed';result.errors.push('210 s process limit reached');process.exitCode=1;}
    result.finished_utc=new Date().toISOString();await persist();
    console.log(JSON.stringify({block,status:result.status,wall_ms:result.wall_ms,trials:result.trials.length,errors:result.errors}));
  }
}

