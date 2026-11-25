import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
import {gunzipSync} from 'node:zlib';
import {parseArgs} from 'node:util';
import {startServer} from '../../../../research/lib/runtime.mjs';

const {values:args}=parseArgs({options:{
  out:{type:'string'},methods:{type:'string',default:'full,trim,regional'},plugin:{type:'string',multiple:true,default:[]},
  recipe:{type:'string'},asset:{type:'string'},reference:{type:'string'},traces:{type:'string'},
  check:{type:'boolean'},repeats:{type:'string',default:'3'}
}});
const here=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(here,'../../../..');
const t86=path.join(here,'../t86-ignition-margin'), t42=path.join(here,'../t42-firewoods-sequential-workflow');
const json=async f=>JSON.parse(await fs.readFile(f));
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const specs=['full','trim','regional','t91','t93','all-carriers','rank-only'];
const methods=args.methods.split(','), repeats=Number(args.repeats);
assert(methods.length>0 && methods.every(m=>specs.includes(m)) && new Set(methods).size===methods.length);
assert(Number.isInteger(repeats) && repeats>0 && repeats<=15);
const started=performance.now(), report={schema:'t90-callable-native-regional-v1',status:'running',
  methods,repeats,started_utc:new Date().toISOString(),sources:{},runtime:{},phases_ms:{},arms:{},queries:[],errors:[]};

async function input(name,file,expected) {
  const data=await fs.readFile(file);
  report.sources[name]=sha(data);
  if(expected) assert.equal(report.sources[name],expected,name);
  return data;
}
function replace(source,needle,replacement) {
  assert.equal(source.split(needle).length,2,'Unique stage marker: '+needle);
  return source.replace(needle,()=>replacement);
}
async function timed(obj,k,fn) {
  const start=performance.now();try {return await fn();}finally {obj[k]=performance.now()-start;}
}
const origin=await json(path.join(t86,'public/capture-report.json'));
const current=JSON.parse(await input('reference',args.reference || path.join(t86,'public/capture-report.json')));
const frozen=await json(path.join(here,'../t81-firewoods-capacity-causality/freeze.json'));
const demo=(await input('demo',path.join(root,'demo/index.html'),origin.sources.demo.sha256)).toString();
const observer=(await input('observer',path.join(t86,'native.js'),origin.sources['native.js'].sha256)).toString();
const camera=(await input('camera',path.join(t42,'adapter.js'),origin.sources.camera_adapter.sha256)).toString();
const query=(await input('query',path.join(here,'query.js'))).toString();
await input('worker',fileURLToPath(import.meta.url));await input('protocol',path.join(here,'PROTOCOL.md'));
await input('joint_protocol',path.join(here,'JOINT_PROTOCOL.md'));
const pluginParts=[];
for(const [i,file] of args.plugin.entries()) pluginParts.push((await input('plugin_'+i,file)).toString());
const plugin=pluginParts.join('\n');
assert(plugin || !methods.some(m=>!['full','trim','regional'].includes(m)),'Plugin required');
const require=createRequire(import.meta.url);
const pw=process.env.PLAYWRIGHT_MODULE || frozen.runtime.playwright_module;
const browserExe=process.env.BROWSER_EXECUTABLE || frozen.runtime.browser_executable;
const playwright=require(pw);
report.runtime={node:process.version,node_sha256:sha(await fs.readFile(process.execPath)),browser_executable_sha256:sha(await fs.readFile(browserExe)),playwright_version:require(path.join(pw,'package.json')).version};
for(const key of Object.keys(report.runtime))assert.equal(report.runtime[key],origin.runtime[key],key);
const cfg=JSON.parse(await input('recipe',args.recipe || path.join(t42,'recipe.json'),args.recipe?undefined:origin.sources.recipe.sha256));
const ply=await input('asset',args.asset || process.env.T86_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply'),args.asset?undefined:origin.sources.Firewoods_foreground.sha256);
const traces={};
for(const arm of ['AB','BA']) {
  traces[arm]=JSON.parse(gunzipSync(await input(arm+'_trace',path.join(args.traces || path.join(t86,'public'),arm+'-trace.json.gz'))));
  assert.equal(traces[arm].length,360);
}
let html=replace(demo,'const full=L.ps.length>=P.ppl; let recycle=-1;',
  'const full=t86Global ? layers.reduce((s,l)=>s+l.ps.length,0)>=P.layers*P.ppl : L.ps.length>=P.ppl; let recycle=-1;');
html=replace(html,'window.__demo = {',camera+'\n'+observer+'\nwindow.__demo = {');
assert.equal(sha(html),origin.sources.staged_html.sha256);
html=replace(html,'window.__demo = {',query+'\n'+plugin+'\nwindow.__demo = {');
const accept='hashQuery(s,rIgn,(j,d)=>{ if(sb.state[j]===0){';
html=replace(html,accept,accept.replace('sb.state[j]===0','sb.state[j]===0 && (!t90Query || !t90Query.regionOnly || t90Query.mask[j])'));
const scan='  const n=sceneGauss.length, hDecay=1-dt*0.35;';
html=replace(html,scan,scan+`
  if(t90Query && t90Query.regionOnly) {
    for(const i of t90Query.ids) {
      if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>0 && Math.fround(sb.h[i]*hDecay)>=P.spreadIgnH) {
        t90Query.witness=i; break;
      }
    }
    return;
  }`);
const ignite='if(sb.state[i]===0 && sb.fuel[i]>0 && sb.h[i]>=P.spreadIgnH){ sb.state[i]=1; sb.burning.push(i); }';
html=replace(html,ignite,ignite.slice(0,-1)+`
      if(t90Query && t90Query.mask[i] && t90Query.witness<0) {
        t90Query.witness=i; if(!t90Query.full) return;
      }
    }`);
const end='  // Source-space world-up = Rx(pitch)^T Ry(yaw)^T [0,1,0].';
html=replace(html,end,'  if(t90Query && !t90Query.full && t90Query.last) return;\n'+end);
for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi))new vm.Script(script[1]);
report.sources.staged_html=sha(html);
report.phases_ms.preflight=performance.now()-started;
if(args.check){console.log('Stage, syntax and environment hashes verified.');process.exit(0);}
const out=path.resolve(args.out || path.join(here,'evidence'));
await fs.mkdir(out,{recursive:true});
await fs.writeFile(path.join(out,'RUN.json'),JSON.stringify({start:report.started_utc,methods,repeats})+'\n',{flag:'wx'});

const referenceFields=['frame','new_ids','retired','active_count','gas_count','random_draws'];
let browser,server;
try {
  server=await startServer(root);
  browser=await timed(report.phases_ms,'browser_launch',()=>playwright.chromium.launch({headless:true,executablePath:browserExe}));
  report.runtime.browser_version=browser.version();
  assert.equal(browser.version(),origin.runtime.browser_version);
  for(const arm of ['AB','BA']) {
    const ref=current.shots[arm], trace=traces[arm], phase={};
    const shot=report.arms[arm]={phases_ms:phase,verified_frames:0,cut_hashes:{}};
    const page=await timed(phase,'new_page',()=>browser.newPage({viewport:{width:cfg.width,height:cfg.height},deviceScaleFactor:1}));
    page.on('pageerror',e=>report.errors.push(String(e)));
    await page.addInitScript(()=>{window.requestAnimationFrame=()=>0;window.cancelAnimationFrame=()=>{};});
    await page.route('**/*',route=>{
      const u=new URL(route.request().url());
      if(u.origin!==server.url) {report.errors.push('Unexpected origin '+u.origin);return route.abort();}
      if(u.pathname==='/query/')return route.fulfill({status:200,body:html,contentType:'text/html; charset=utf-8'});
      if(u.pathname==='/scene.ply')return route.fulfill({status:200,body:ply,contentType:'application/octet-stream'});
      return route.continue();
    });
    await timed(phase,'load',async()=>{
      await page.goto(server.url+'/query/?embed=1&orbit=0',{waitUntil:'load'});
      await page.waitForFunction(()=>window.__t90 && window.__demo);
    });
    const picks=[...arm].map(s=>cfg.picks.find(p=>p.name===s));
    const initial=await timed(phase,'load_reset_and_first_brush',()=>page.evaluate(async ({c,pick})=>{
      __demo.P.paused=true; __demo.forceSize(c.width,c.height);
      const res=await fetch('/scene.ply');
      if(!res.ok)throw Error('Missing scene');
      const load=__demo.loadPLY(await res.arrayBuffer());
      __demo.research.reset(c.seed,c.params); __t42.camera(c.camera);
      return {count:load.kept,stroke:__t86.ignite(pick,false)};
    },{c:cfg,pick:picks[0]}));
    assert.deepEqual(initial.stroke,ref.initial);
    shot.sites=initial.count;
    const ids=await timed(phase,'build_region_and_export_ids',()=>page.evaluate(p=>__t90.configure(p),picks[1]));
    const idSet=new Set(ids);shot.shell_ids=ids;
    assert.equal(idSet.size,ids.length);
    if(!args.reference){
      const historical=JSON.parse(gunzipSync(await fs.readFile(path.join(here,'../t87-stroke-halo/PREDICTIONS.json.gz'))));
      assert.deepEqual(ids,historical.shell_ids[arm],'static T87 shell');
    }
    for(const stop of [180,210,240,300,360]) {
      const batch=await timed(phase,'advance_to_'+stop,()=>page.evaluate(([end,dt])=>__t86.frames(end,dt),[stop,cfg.dt]));
      for(const r of batch){
        const expected=trace[r.frame-1];
        for(const k of referenceFields)assert.deepEqual(r[k],expected[k],arm+' '+r.frame+' '+k);
      }
      shot.verified_frames+=batch.length;
      if(stop===180){
        const compare=await page.evaluate(p=>({pre_edit:__t86.marker(),edit:__t86.ignite(p,true),post_edit:__t86.marker()}),picks[1]);
        for(const k of Object.keys(compare))assert.deepEqual(compare[k],ref[k],arm+' '+k);
      } else if(stop===360) {
        shot.endpoint=await page.evaluate(()=>__t86.marker()); assert.deepEqual(shot.endpoint,ref.end);
      } else {
        const marker=await page.evaluate(()=>__t86.marker());
        const cut=ref.cuts.find(r=>r.frame===stop);assert.equal(marker.hash,cut.native_hash);
        shot.cut_hashes[stop]=marker.hash;
        for(const horizon of [1,4,8]) {
          const rows=trace.slice(stop,stop+horizon);
          const first=rows.find(r=>r.new_ids.some(i=>idSet.has(i)));
          const expected_ids=first?first.new_ids.filter(i=>idSet.has(i)):[];
          const query={arm,cut:stop,horizon,first_frame:first?.frame ?? null,expected_ids,trials:[]};
          report.queries.push(query);
          for(let rep=0;rep<=repeats;rep++) {
            for(let j=0;j<methods.length;j++) {
              const method=methods[(rep+j+report.queries.length-1)%methods.length];
              const t=performance.now();
              const res=await page.evaluate(([m,h,d])=>__t90.query(m,h,d),[method,horizon,cfg.dt]);
              const delivered_ms=performance.now()-t;
              query.trials.push({...res,rep,method,delivered_ms});
              assert.equal(res.yes,!!first,arm+' '+stop+' '+horizon+' '+method+' yes');
              assert.equal(res.first_frame,query.first_frame,arm+' '+stop+' '+method+' frame');
              assert(first ? expected_ids.includes(res.witness) : res.witness===null,'Wrong witness');
            }
          }
        }
        const restored=await page.evaluate(()=>__t86.marker()); assert.deepEqual(restored,marker,'Live cut changed');
      }
    }
    assert.equal(shot.verified_frames,360);
    await page.close();assert.equal(report.errors.length,0);
  }
  report.status='validated';
} catch(error) {report.status='failed';report.errors.push(String(error.stack||error));process.exitCode=1;}
finally {
  await timed(report.phases_ms,'cleanup',async()=>{await browser?.close();await server?.close();});
  report.phases_ms.wall_before_receipt=performance.now()-started;
  await fs.writeFile(path.join(out,'CAPTURE.json'),JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({status:report.status,queries:report.queries.length,ms:report.phases_ms.wall_before_receipt,errors:report.errors}));
}
