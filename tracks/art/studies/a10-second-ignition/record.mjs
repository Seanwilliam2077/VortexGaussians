// A10: one public-UI record, inherited A06 screenshot/concat approach.
import fs from 'node:fs/promises';
import { openSync, closeSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { spawnSync } from 'node:child_process';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const began=performance.now(),wall=()=>(performance.now()-began)/1000;
const here=path.dirname(fileURLToPath(import.meta.url)),out=path.join(here,'run-01');
const encoder='C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe';
const probe=path.join(path.dirname(encoder),'ffprobe.exe');
const plan={scope:'Synthetic Agent-operated creative rehearsal; no contribution or audience claim',
  method:'all timestamped viewport screenshots, not native video or performance measurement',
  viewport:{width:1280,height:800},targetSamplingFPS:4,browserLimitSeconds:360,
  workerLimitSeconds:400,supervisorLimitSeconds:420,maximumEncodeSeconds:120,
  recordingAttempts:1,loads:1,ignitions:2,advanceSeconds:[10,10,10,1],
  targetSimulatedTimes:[10,20,30,31],resets:0,notesWritten:0,
  defaults:{x:0,y:0.65,z:0,radius:0.30,cameraYaw:0},out};
if(!process.argv.includes('--execute')){console.log(JSON.stringify(plan,null,2));process.exit(0);}
if(!process.env.PLAYWRIGHT_MODULE||!process.env.BROWSER_EXECUTABLE)throw new Error('Explicit existing runtime paths required');
await fs.mkdir(out,{recursive:false});await fs.mkdir(path.join(out,'frames'));
const hash=b=>createHash('sha256').update(b).digest('hex');
const sourceNames=['tracks/art/index.html','tracks/art/art.js','tracks/art/art.css','demo/index.html',
  'static/test_scene.ply','research/lib/runtime.mjs',
  ...['INTENT.md','PROTOCOL.md','record.mjs','execute.py','.gitignore'].map(n=>'tracks/art/studies/a10-second-ignition/'+n)];
const pins=[...sourceNames.map(n=>[n,path.join(repoRoot,n)]),
  ['node_executable',process.execPath],['browser_executable',process.env.BROWSER_EXECUTABLE],
  ['playwright_package',path.join(process.env.PLAYWRIGHT_MODULE,'package.json')],['ffmpeg',encoder],['ffprobe',probe]];
const hashes=async()=>Object.fromEntries(await Promise.all(pins.map(async([key,p])=>{
  const data=await fs.readFile(p);return [key,{path:p,bytes:data.length,sha256:hash(data)}];
})));
const r={schema:'a10-second-ignition-record-v1',createdUTC:new Date().toISOString(),plan,
  actions:[],snapshots:[],frames:[],segments:[],errors:[],console:[],blockedExternal:[],resourcesClosed:{},
  workflowCompleted:false,runtime:{node:process.version,module:process.env.PLAYWRIGHT_MODULE,executable:process.env.BROWSER_EXECUTABLE}};
const publish=async()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(r,null,2)+'\n');
await fs.writeFile(path.join(out,'attempt.json'),JSON.stringify({createdUTC:r.createdUTC,plan},null,2)+'\n',{flag:'wx'});
let server,browser,context,page,watchdog,capturing=false,captureLoop,captureError;
let captureChain=Promise.resolve();
const healthy=()=>{
  if(captureError)throw captureError;
  if(r.watchdogFired||wall()>=plan.browserLimitSeconds)throw new Error('Browser phase deadline reached');
  if(r.errors.length||r.blockedExternal.length)throw new Error('Page error or blocked external request');
};
const capture=()=>{
  const task=captureChain.then(async()=>{
    healthy();const index=r.frames.length,file=`frames/frame-${String(index).padStart(5,'0')}.png`,start=wall();
    const bytes=await page.screenshot({path:path.join(out,file),type:'png',timeout:7000});
    const end=wall(),item={index,file,startedWallSeconds:start,endedWallSeconds:end,
      timestampSeconds:(start+end)/2,bytes:bytes.length,sha256:hash(bytes)};
    r.frames.push(item);return item;
  });captureChain=task.catch(()=>{});return task;
};
const action=async(name,fn)=>{
  healthy();const a={name,startedWallSeconds:wall()};r.actions.push(a);await publish();
  try{await fn();healthy();a.completed=true;}finally{a.endedWallSeconds=wall();await publish();}
};
const visible=async()=>{
  const start=wall();const s={status:await page.locator('#status').innerText(),
    time:await page.locator('#time-label').innerText(),burning:await page.locator('#burning-count').innerText(),
    charred:await page.locator('#char-count').innerText(),scene:await page.locator('#scene-count').innerText(),
    notes:await page.locator('#note-count').innerText(),cameraYaw:await page.locator('#camera-yaw').inputValue()};
  return {...s,readStartedWallSeconds:start,readEndedWallSeconds:wall(),atomicSnapshot:false};
};
const defaults=async()=>{
  const value={};for(const [key,id] of Object.entries({x:'ignite-x',y:'ignite-y',z:'ignite-z',radius:'ignite-radius',cameraYaw:'camera-yaw'})){
    const text=await page.locator('#'+id).inputValue();value[key]={text,value:Number(text)};
    if(text.trim()===''||Number(text)!==plan.defaults[key])throw new Error(`Default changed: ${id}=${text}`);
  }return value;
};
const shot=async(name)=>{
  const f=await capture();await fs.copyFile(path.join(out,f.file),path.join(out,name+'.png'));
  r.snapshots.push({name,file:name+'.png',frameIndex:f.index,sha256:f.sha256,wallSeconds:f.timestampSeconds,visible:await visible()});await publish();
};
const waitLoaded=async()=>{
  const end=Math.min(performance.now()+20000,began+360000);
  while(performance.now()<end){healthy();if((await page.locator('#status').innerText()).includes('45,808 / 45,808'))return;await page.waitForTimeout(100);}
  throw new Error('Visible synthetic scene did not load within budget');
};
const advance=async(seconds,target,name)=>{
  const segment={requestedSeconds:seconds,targetSeconds:target,observations:[],startedWallSeconds:wall()};r.segments.push(segment);
  await action(`request public ${seconds}-second segment to ${target}s`,()=>page.locator(seconds===1?'#advance':'#play').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();
  while(true){
    healthy();const state=await visible();segment.observations.push(state);
    if(state.status.includes('异常')||state.status.includes('已停止推进'))throw new Error(state.status);
    if(state.status.includes('本段推进完成')){
      if(state.time!==`模拟时间 ${target.toFixed(2)} s`)throw new Error('Completed segment at unexpected visible time');
      break;
    }
    await page.waitForTimeout(500);
  }
  segment.endedWallSeconds=wall();segment.completed=true;await shot(name);
};
const boundedClose=async(key,fn)=>{
  let timer;const start=wall();
  try{await Promise.race([fn(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(new Error('cleanup timeout')),6000);})]);r.resourcesClosed[key]=true;}
  catch(e){r.resourcesClosed[key]=false;r.resourcesClosed[key+'Error']=e.message;r.status='failed';}
  finally{clearTimeout(timer);r.resourcesClosed[key+'Seconds']=wall()-start;}
};
try{
  r.sourceBefore=await hashes();await publish();
  server=await startServer();r.server={url:server.url,scope:'fresh ephemeral loopback; user8137 untouched'};
  const launch=await launchBrowser(process.env.BROWSER_EXECUTABLE);browser=launch.browser;
  r.browser=browser.version();r.launch=launch.launchOptions;
  if(launch.module!==process.env.PLAYWRIGHT_MODULE)throw new Error('Unexpected module fallback');
  watchdog=setTimeout(()=>{r.watchdogFired=true;void browser.close().catch(()=>{});},Math.max(1,(360-wall())*1000));
  context=await browser.newContext({viewport:plan.viewport,serviceWorkers:'block'});
  r.context={persistent:false,storageStateProvided:false,recordVideo:false,serviceWorkers:'block'};
  await context.route('**/*',async route=>{
    const url=route.request().url(),u=new URL(url);
    if(u.origin===server.url||['data:','blob:','about:'].includes(u.protocol))await route.continue();
    else{r.blockedExternal.push({wallSeconds:wall(),url});await route.abort('blockedbyclient');}
  });
  page=await context.newPage();page.setDefaultTimeout(12000);
  page.on('pageerror',e=>r.errors.push({wallSeconds:wall(),message:e.message,stack:e.stack}));
  page.on('console',m=>{
    if(['warning','error'].includes(m.type())){
      const item={wallSeconds:wall(),type:m.type(),text:m.text()};r.console.push(item);
      if(/CONTEXT_LOST|WebGL.*(error|lost)|uncaught/i.test(item.text))r.errors.push({...item,source:'console'});
    }
  });
  await capture();r.recordingStartedWallSeconds=r.frames[0].timestampSeconds;capturing=true;
  captureLoop=(async()=>{while(capturing){const tick=performance.now();await capture();
    if(capturing)await new Promise(resolve=>setTimeout(resolve,Math.max(0,250-(performance.now()-tick))));
  }})().catch(e=>{captureError=e;r.captureFailure={wallSeconds:wall(),message:e.message};capturing=false;void browser.close().catch(()=>{});});
  await action('open unchanged art page',()=>page.goto(server.url+'/tracks/art/',{waitUntil:'load',timeout:12000}));
  await shot('01-opening');
  await action('load synthetic example once',()=>page.locator('#start-example').click());
  await waitLoaded();await page.locator('#viewer').scrollIntoViewIfNeeded();
  r.initialDefaults=await defaults();await shot('02-loaded');await page.waitForTimeout(1000);
  await action('switch intervene once',()=>page.locator('[data-stage=intervene]').click());
  await action('first ignition at unchanged defaults',()=>page.locator('#ignite').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();r.firstIgnition=await visible();
  await shot('03-first-ignited');await page.waitForTimeout(1000);
  await advance(10,10,'04-ten-seconds');
  await advance(10,20,'05-twenty-seconds');
  await advance(10,30,'06-thirty-seconds');
  r.beforeSecondIgnition=await visible();r.secondDefaults=await defaults();
  await action('second ignition at same unchanged defaults',()=>page.locator('#ignite').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();r.secondIgnition=await visible();
  if(r.secondIgnition.time!=='模拟时间 30.00 s')throw new Error('Second ignition changed simulated time');
  await shot('07-second-ignited');await page.waitForTimeout(1000);
  await advance(1,31,'08-thirty-one-seconds');r.finalDefaults=await defaults();
  await page.waitForTimeout(3000);await shot('09-final-hold');r.finalVisible=await visible();
  if(r.finalVisible.time!=='模拟时间 31.00 s')throw new Error('Final visible time changed');
  r.notesUntouched=(await page.locator('#note-count').innerText())==='0 条记录'&&
    (await page.locator('#context').inputValue())===''&&(await page.locator('#choice').inputValue())===''&&(await page.locator('#observation').inputValue())==='';
  if(!r.notesUntouched)throw new Error('Unexpected nonempty notes');healthy();
  r.workflowCompleted=true;r.status='completed_recording';
}catch(e){r.status='failed';r.failure={wallSeconds:wall(),message:e.message,stack:e.stack};}
finally{
  capturing=false;if(captureLoop)await captureLoop;await captureChain;
  r.recordingEndedWallSeconds=wall();clearTimeout(watchdog);
  if(context)await boundedClose('context',()=>context.close());
  if(browser)await boundedClose('browser',()=>browser.close());
  if(server)await boundedClose('server',()=>server.close());
  r.browserPhaseWallSeconds=wall();
  if(r.errors.length||r.blockedExternal.length||r.browserPhaseWallSeconds>360)r.status='failed';
  await publish();
}
const command=async(label,args,cap)=>{
  const timeout=Math.floor(Math.min(cap,400-wall()-3)*1000);
  if(timeout<=0)throw new Error(`No remaining work budget for ${label}`);
  const row={label,command:args,timeoutMilliseconds:timeout,startedWallSeconds:wall()};r.mediaCommands.push(row);
  const stdout=openSync(path.join(out,label+'.stdout.log'),'wx'),stderr=openSync(path.join(out,label+'.stderr.log'),'wx');
  try{const child=spawnSync(args[0],args.slice(1),{cwd:out,timeout,windowsHide:true,stdio:['ignore',stdout,stderr]});
    row.exitCode=child.status;row.signal=child.signal;row.error=child.error?.message||null;
    if(child.error||child.status!==0)throw new Error(row.error||`${label} exit ${child.status}`);
  }finally{closeSync(stdout);closeSync(stderr);row.endedWallSeconds=wall();}
};
r.mediaCommands=[];
if(r.frames.length){
  try{
    const lines=['ffconcat version 1.0'];
    for(let j=0;j<r.frames.length;j++){
      const f=r.frames[j],next=j+1<r.frames.length?r.frames[j+1].timestampSeconds:r.recordingEndedWallSeconds;
      if(next<=f.timestampSeconds)throw new Error('Nonmonotonic capture time');
      lines.push(`file '${f.file}'`,'option framerate 1000',`duration ${(next-f.timestampSeconds).toFixed(6)}`);
    }
    lines.push(`file '${r.frames.at(-1).file}'`,'option framerate 1000');
    await fs.writeFile(path.join(out,'timeline.ffconcat'),lines.join('\n')+'\n');
    await command('encode',[encoder,'-hide_banner','-nostdin','-n','-f','concat','-safe','0','-i','timeline.ffconcat',
      '-fps_mode','vfr','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p',
      '-threads','2','-video_track_timescale','1000000','-movflags','+faststart','study.mp4'],120);
    const data=await fs.readFile(path.join(out,'study.mp4'));
    r.video={file:'study.mp4',bytes:data.length,sha256:hash(data),commitEligible:data.length<=20*1024*1024,
      completeWorkflow:r.workflowCompleted,frameCountCaptured:r.frames.length,
      untrimmedSamplingSpanSeconds:r.recordingEndedWallSeconds-r.frames[0].timestampSeconds};
    await command('probe',[probe,'-v','error','-show_entries','format=duration,size:stream=codec_type,codec_name,width,height,nb_frames,duration','-of','flat','study.mp4'],15);
    const text=await fs.readFile(path.join(out,'probe.stdout.log'),'utf8'),fields={};
    for(const line of text.trim().split(/\r?\n/)){const eq=line.indexOf('=');if(eq<1)throw new Error('Bad flat probe line');
      const key=line.slice(0,eq),value=line.slice(eq+1);fields[key]=value.startsWith('"')?JSON.parse(value):value;}
    if(fields['streams.stream.0.codec_name']!=='h264'||fields['streams.stream.0.width']!=='1280'||fields['streams.stream.0.height']!=='800'||
      Object.entries(fields).some(([k,v])=>k.endsWith('.codec_type')&&v==='audio'))throw new Error('Unexpected media format');
    r.video.probeFlat=fields;
    await command('decode',[encoder,'-hide_banner','-loglevel','error','-nostdin','-xerror','-i','study.mp4','-an','-f','null','-'],30);
    r.video.fullDecodePassed=true;r.decodedSnapshots=[];
    for(const s of r.snapshots){
      const time=Math.max(0,s.wallSeconds-r.recordingStartedWallSeconds),file='decoded-'+s.file;
      await command('extract-'+s.name,[encoder,'-hide_banner','-loglevel','error','-nostdin','-n','-ss',time.toFixed(6),'-i','study.mp4','-frames:v','1','-update','1',file],15);
      const image=await fs.readFile(path.join(out,file));r.decodedSnapshots.push({file,seconds:time,sourceSnapshot:s.name,bytes:image.length,sha256:hash(image)});
    }
    if(r.status==='completed_recording')r.status='completed_workflow_and_media';
  }catch(e){r.encodingFailure={wallSeconds:wall(),message:e.message,stack:e.stack};r.status='failed';}
}
try{r.sourceAfter=await hashes();r.sourcesUnchanged=JSON.stringify(r.sourceBefore)===JSON.stringify(r.sourceAfter);
  if(!r.sourcesUnchanged)r.status='failed';}catch(e){r.sourceCheckFailure=e.message;r.sourcesUnchanged=false;r.status='failed';}
if(wall()>400)r.status='failed';
r.totalWallSecondsBeforeFinalReceipt=wall();r.noFurtherRecording=true;r.visualInspection='not yet performed';
await publish();console.log(JSON.stringify({status:r.status,workflowCompleted:r.workflowCompleted,
  seconds:r.totalWallSecondsBeforeFinalReceipt,video:r.video||null,failure:r.failure||r.encodingFailure||null,out}));
process.exitCode=r.status==='completed_workflow_and_media'?0:1;
