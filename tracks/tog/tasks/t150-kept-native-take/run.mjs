import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import http from 'node:http';
import {createRequire} from 'node:module';
import path from 'node:path';
import {Script} from 'node:vm';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../../..');
const tasks=path.dirname(here), sha=b=>createHash('sha256').update(b).digest('hex');
const read=s=>fs.readFile(path.resolve(here,s)),json=async s=>JSON.parse(await read(s));
const assetFile=process.env.FIREWOODS_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply');
const [id,outPath,privatePath]=process.argv.slice(2);
const block=Number(id),out=outPath && path.resolve(outPath),check=id==='--check';
const start=performance.now(),result={schema:'t150-kept-take-v1',process:block,pid:process.pid,
  started_utc:new Date().toISOString(),sources:{},setup_ms:{},trials:[],status:'starting'};
async function persist(){if(!check)await fs.writeFile(path.join(out,'RUN.json'),JSON.stringify(result,null,2)+'\n');}
async function phase(k,task){const at=performance.now();const v=await task();result.setup_ms[k]=performance.now()-at;return v;}
async function source(name){
  const raw=await read(name);result.sources[path.relative(root,path.resolve(here,name)).split(path.sep).join('/')]=sha(raw);
  return raw.toString('utf8').replaceAll('\r\n','\n');
}
function between(s,first,next){
  const a=s.indexOf(first),b=s.indexOf(next,a+first.length);
  assert(a>=0 && b>a,first);return s.slice(a,b);
}
function replace(s,key,replacement){assert.equal(s.split(key).length,2,key);return s.replace(key,()=>replacement);}
let server,browser,payload=null,expecting=false;
try{
  if(!check){assert([1,2].includes(block));await fs.mkdir(out);await persist();}
  const cfg=await json('../t109-common-parent-choice/recipe.json'),ref=await json('../t109-common-parent-choice/REFERENCE.json');
  const prior=await json('../t109-common-parent-choice/evidence/native/capture-report.json');
  const weights=JSON.parse(gunzipSync(await read('../t107-visible-burn-progression/evidence/weights-0.json.gz')));
  const shell=JSON.parse(gunzipSync(await read('../t109-common-parent-choice/shell.json.gz')));
  const demoFile='../../../../demo/index.html', demoBytes=await read(demoFile);
  assert.equal(sha(demoBytes),prior.sources.demo.sha256);
  const cameraRaw=await read('../t42-firewoods-sequential-workflow/adapter.js'),observerRaw=await read('../t86-ignition-margin/native.js');
  assert.equal(sha(cameraRaw),prior.sources.camera.sha256);assert.equal(sha(observerRaw),prior.sources.observer.sha256);
  let html=replace(demoBytes.toString(),'const full=L.ps.length>=P.ppl; let recycle=-1;',
    'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
  const marker='window.__demo = {';
  html=replace(html,marker,cameraRaw+'\n'+observerRaw+'\n'+marker);
  assert.equal(sha(html),prior.staged_sha256);
  const k=await source('../t129-native-image-choice/native-kernels.js');
  const native=replace(k,'sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i);','sb.state[i]=1; t116Remove(grid,i); sb.burning.push(i); if(p && p.mask[i])t111Add(p,i);');
  const slices=await source('../t95-multistep-material-slice/slice.js'),rep=await source('../t100-material-repair/repair.js');
  const feed=between(native,'  for(let m=0;m<M;m++){','\n}\n');
  const helpers=between(slices,'function t95Open(','function t95Advance(')+
    between(rep,'function t100Plan(','function t100FullStep(')+
    'function t95Feed(dt){const sb=sceneBurnState,N=layers.length,areaMode=false,M=P.spreadFeedCap,feedSources=null;\n'+feed+'\n}\n';
  const added=[native,helpers,await source('regional.js'),await source('action.js')].join('\n');
  new Script(added);html=replace(html,marker,added+'\n'+marker);
  const asset=await fs.readFile(assetFile);assert.equal(sha(asset),cfg.asset_sha256);
  result.sources.asset=sha(asset);result.sources.staged_html=sha(html);result.sources.material_weights=sha(await read('../t107-visible-burn-progression/evidence/weights-0.json.gz'));
  if(check){console.log('Stage verified',sha(html));}else{
    const frameBytes=cfg.width*cfg.height*4,totalBytes=30*frameBytes;
    server=http.createServer(async(req,res)=>{
      try{
        const url=new URL(req.url,'http://localhost');
        if(url.pathname==='/take' && req.method==='POST' && expecting && req.headers['content-length']===String(totalBytes)){
          expecting=false;const chunks=[];let n=0;
          for await(const chunk of req){n+=chunk.length;assert(n<=totalBytes);chunks.push(chunk);}
          assert.equal(n,totalBytes);payload=Buffer.concat(chunks,n);res.writeHead(204);res.end();return;
        }
        if(req.method==='GET' && url.pathname==='/scene'){res.writeHead(200,{'content-type':'application/octet-stream'});res.end(asset);return;}
        if(req.method==='GET' && url.pathname==='/'){res.writeHead(200,{'content-type':'text/html; charset=utf-8'});res.end(html);return;}
        res.writeHead(404);res.end();
      }catch(e){result.network_error=String(e);res.writeHead(500);res.end();}
    });
    await new Promise((ok,fail)=>{server.once('error',fail);server.listen(0,'127.0.0.1',ok);});
    const rt=(await json('../t81-firewoods-capacity-causality/freeze.json')).runtime;
    const pw=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||rt.playwright_module);
    browser=await phase('browser_launch',()=>pw.chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE||rt.browser_executable}));
    const page=await browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1});
    page.on('pageerror',e=>{(result.page_errors??=[]).push(String(e));});
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await phase('navigate',()=>page.goto('http://127.0.0.1:'+server.address().port+'/?embed=1&orbit=0'));
    const first=await phase('load_and_first_stroke',()=>page.evaluate(async c=>{
      __demo.P.paused=true;__demo.forceSize(c.width,c.height);
      const fit=__demo.loadPLY(await (await fetch('/scene')).arrayBuffer());
      if(fit.kept!==c.material_count || fit.total!==c.material_count)throw Error('Incomplete room');
      __demo.research.reset(c.seed,c.params);__t42.camera(c.camera);return __t86.ignite(c.picks[0],false);
    },cfg));
    assert.deepEqual(first,prior.shots.AL.initial);
    result.parent=await phase('native_parent',()=>page.evaluate(dt=>{__t86.frames(180,dt);return __t86.marker();},cfg.dt));
    assert.deepEqual(result.parent,prior.shots.AL.pre_edit);
    const picks=cfg.picks.slice(1);
    const target=await phase('target_install',()=>page.evaluate(([p,pairs])=>__t150.install(p,pairs),[picks[1],weights.eligible_weights]));
    assert.deepEqual(target.shell,shell);
    result.target={total:target.total,eligible:target.eligible,weights:weights.eligible_weights.length};
    result.runtime={node:process.version,browser:browser.version(),backend:await page.evaluate(()=>__t150.backend())};
    result.status='running';await persist();
    let original,oracle;
    async function perform(method,audit,wave,position){
      result.phase={method,audit,wave,position};await persist();
      if(audit && method!=='native')await page.evaluate(()=>__t150.cold());
      payload=null;expecting=true;const t=performance.now();
      const row=await page.evaluate(a=>__t150.take(...a),[method,picks,audit]);
      row.host_ms=performance.now()-t;
      assert(!expecting && payload && payload.length===totalBytes,'Host pixel stream');
      assert.equal(row.chosen,'F');assert.deepEqual(row.answers.map(x=>x.arm),['L','F']);
      for(const a of row.answers){
        const r=ref.queries.find(q=>q.arm==='A'+a.arm && q.camera===0);
        for(const [key,old] of [['first','first_frame'],['count','count'],['mass','mass'],['total','total'],['target','target']])assert.equal(a[key],r[old]);
      }
      const state=await page.evaluate(h=>__t150.consume(h),row.handle);
      assert.equal(state.end.frame,254);assert.equal(state.next.frame,255);
      const digests=Array.from({length:30},(_,i)=>sha(payload.subarray(i*frameBytes,(i+1)*frameBytes)));
      if(method==='native'){
        original=payload;oracle={answers:row.answers,crossing:row.crossing,...state,frames:digests};
        if(block===1 && privatePath){
          await fs.mkdir(privatePath,{recursive:true});
          await fs.writeFile(path.join(privatePath,'225-254-bottom-up.rgba'),payload,{flag:'wx'});
        }
      }else{
        assert(original.equals(payload),'Actual delivered pixels differ');
        assert.deepEqual(digests,oracle.frames);
        assert.deepEqual(state.end,oracle.end);assert.deepEqual(state.next,oracle.next);assert.deepEqual(row.answers,oracle.answers);
        if(audit)assert.deepEqual(row.crossing,oracle.crossing);
      }
      assert.deepEqual(await page.evaluate(()=>__t86.marker()),result.parent);
      Object.assign(row,{wave,position,audit,frame_digests:digests,delivered_bytes:payload.length,endpoint:state.end,successor:state.next});
      result.trials.push(row);await persist();
    }
    const methods=['ordinary','repair','hybrid','sibling'];
    if(block===2)methods.reverse();
    await perform('native',true,0,0);
    for(let i=0;i<4;i++)await perform(methods[i],true,0,i+1);
    for(let wave=1;wave<=4;wave++)for(let i=0;i<4;i++)await perform(methods[(i+wave-1)%4],false,wave,i+1);
    assert(!result.page_errors && !result.network_error);
    result.status='complete';
  }
}catch(e){result.status='failed';result.error=String(e);console.error(String(e));process.exitCode=1;}
finally{
  if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));
  result.elapsed_ms=performance.now()-start;await persist();
}
