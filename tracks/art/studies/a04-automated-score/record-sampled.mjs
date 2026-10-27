// One authorized follow-up: timestamped public-UI screenshots, existing H.264 encoder.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { execFileSync, spawnSync } from 'node:child_process';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2), i=args.indexOf('--out');
const out=path.resolve(i<0?path.join(here,'run-02'):args[i+1]);
const encoder='C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe';
const probe=path.join(path.dirname(encoder),'ffprobe.exe');
const plan={scope:'Agent-authored synthetic demonstration draft; no artist/audience evidence',
  method:'timestamped page screenshots, not native recordVideo or performance measurement',
  viewport:{width:1280,height:800},targetSamplingFPS:6,wallLimitMs:58000,
  supplementalRecordingAttempts:1,ignitions:1,simulatedSeconds:1,resets:1,receiptHide:1,receiptShow:1,notesWritten:0,out};
if(!args.includes('--execute')){console.log(JSON.stringify(plan,null,2));process.exit(0);}
if(!process.env.PLAYWRIGHT_MODULE||!process.env.BROWSER_EXECUTABLE)throw new Error('Explicit existing browser/module paths required');
const rel=path.relative(here,out);if(!rel||rel.startsWith('..')||path.isAbsolute(rel))throw new Error('Fresh child output required');
await fs.mkdir(out,{recursive:false});await fs.mkdir(path.join(out,'frames'));
const began=performance.now(),wall=()=>(performance.now()-began)/1000;
const hash=b=>createHash('sha256').update(b).digest('hex');
const names=['tracks/art/index.html','tracks/art/art.js','tracks/art/art.css','demo/index.html','static/test_scene.ply','research/lib/runtime.mjs',
  ...['record.mjs','PROTOCOL.md','FOLLOWUP.md','record-sampled.mjs','run-01/result.json'].map(n=>'tracks/art/studies/a04-automated-score/'+n)];
const hashes=async()=>Object.fromEntries(await Promise.all(names.map(async n=>[n,hash(await fs.readFile(path.join(repoRoot,n)))])));
const r={schema:'a04-sampled-v1',createdUTC:new Date().toISOString(),plan,sourceBefore:await hashes(),actions:[],snapshots:[],frames:[],errors:[],console:[],resourcesClosed:{},
  runtime:{node:process.version,module:process.env.PLAYWRIGHT_MODULE,executable:process.env.BROWSER_EXECUTABLE}};
const publish=async()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(r,null,2)+'\n');
let server,browser,context,page,watchdog,capturing=false,captureLoop,captureError;
let captureChain=Promise.resolve();
const healthy=()=>{if(captureError)throw captureError;};
const capture=()=>{
  const task=captureChain.then(async()=>{
    healthy();const index=r.frames.length,file=`frames/frame-${String(index).padStart(5,'0')}.png`,start=wall();
    const bytes=await page.screenshot({path:path.join(out,file),type:'png',timeout:7000});const end=wall();
    const item={index,file,startedWallSeconds:start,endedWallSeconds:end,timestampSeconds:(start+end)/2,bytes:bytes.length,sha256:hash(bytes)};
    r.frames.push(item);return item;
  });captureChain=task.catch(()=>{});return task;
};
const action=async(name,fn)=>{healthy();const a={name,startedWallSeconds:wall()};r.actions.push(a);await publish();try{await fn();healthy();a.completed=true;}finally{a.endedWallSeconds=wall();await publish();}};
const visible=async()=>({status:await page.locator('#status').innerText(),time:await page.locator('#time-label').innerText(),burning:await page.locator('#burning-count').innerText(),
  charred:await page.locator('#char-count').innerText(),scene:await page.locator('#scene-count').innerText(),notes:await page.locator('#note-count').innerText()});
const shot=async(name)=>{const f=await capture();await fs.copyFile(path.join(out,f.file),path.join(out,name+'.png'));r.snapshots.push({name,file:name+'.png',frameIndex:f.index,sha256:f.sha256,wallSeconds:f.timestampSeconds,visible:await visible()});await publish();};
const waitText=async(selector,text,ms)=>{const end=performance.now()+ms;while(performance.now()<end){healthy();if((await page.locator(selector).innerText()).includes(text))return;await page.waitForTimeout(100);}throw new Error(`Visible UI timeout ${selector}: ${text}`);};
try{
  r.encoder={path:encoder,sha256:hash(await fs.readFile(encoder)),version:execFileSync(encoder,['-version'],{encoding:'utf8',timeout:10000,windowsHide:true}).split('\n')[0]};
  server=await startServer();r.server={url:server.url,scope:'fresh ephemeral loopback; user8137 untouched'};
  const launch=await launchBrowser(process.env.BROWSER_EXECUTABLE);browser=launch.browser;r.browser=browser.version();r.launch=launch.launchOptions;
  watchdog=setTimeout(()=>{r.watchdogFired=true;void browser.close();},plan.wallLimitMs);
  context=await browser.newContext({viewport:plan.viewport});r.context={persistent:false,storageStateProvided:false,recordVideo:false};
  page=await context.newPage();page.setDefaultTimeout(12000);
  page.on('pageerror',e=>r.errors.push({wallSeconds:wall(),message:e.message,stack:e.stack}));
  page.on('console',m=>{if(['warning','error'].includes(m.type()))r.console.push({wallSeconds:wall(),type:m.type(),text:m.text()});});
  await capture();r.recordingStartedWallSeconds=r.frames[0].timestampSeconds;capturing=true;
  captureLoop=(async()=>{while(capturing){const tick=performance.now();await capture();if(capturing)await new Promise(resolve=>setTimeout(resolve,Math.max(0,1000/6-(performance.now()-tick))));}})().catch(e=>{captureError=e;r.captureFailure={wallSeconds:wall(),message:e.message};capturing=false;void browser.close();});
  await action('open unchanged art page',()=>page.goto(server.url+'/tracks/art/',{waitUntil:'load',timeout:12000}));
  await shot('01-opening');await page.waitForTimeout(1800);
  await action('load synthetic example once',()=>page.locator('#start-example').click());
  await waitText('#status','45,808 / 45,808',16000);await page.locator('#viewer').scrollIntoViewIfNeeded();await shot('02-loaded');await page.waitForTimeout(1800);
  await action('switch intervene',()=>page.locator('[data-stage=intervene]').click());
  await action('ignite once at existing defaults',()=>page.locator('#ignite').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();await shot('03-ignited');await page.waitForTimeout(1600);
  await action('request exactly one simulated second',()=>page.locator('#advance').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();await waitText('#status','本段推进完成',18000);
  await shot('04-after-one-second');r.completedSimulation=await visible();
  if(r.completedSimulation.time!=='模拟时间 1.00 s')throw new Error('Visible simulated time did not equal1.00s');
  await page.waitForTimeout(3000);
  await action('switch revisit',()=>page.locator('[data-stage=revisit]').click());
  await action('reset once',()=>page.locator('#reset').click());await page.locator('#viewer').scrollIntoViewIfNeeded();await shot('05-reset-scene');
  r.afterReset=await visible();if(r.afterReset.time!=='模拟时间 0.00 s'||r.afterReset.burning!=='0'||r.afterReset.charred!=='0')throw new Error('Visible reset counters mismatch');
  await page.waitForTimeout(2000);await page.locator('.reset-receipt').scrollIntoViewIfNeeded();await shot('06-receipt-expanded');await page.waitForTimeout(3000);
  r.receipt={time:await page.locator('#receipt-time').innerText(),burning:await page.locator('#receipt-burning').innerText(),charred:await page.locator('#receipt-charred').innerText()};
  await action('hide receipt once',()=>page.locator('#receipt-toggle').click());await shot('07-receipt-hidden');await page.waitForTimeout(1500);
  await action('reopen receipt once',()=>page.locator('#receipt-toggle').click());await shot('08-receipt-reopened');await page.waitForTimeout(3000);
  r.notesUntouched=(await page.locator('#note-count').innerText())==='0 条记录'&&
    (await page.locator('#context').inputValue())===''&&(await page.locator('#choice').inputValue())===''&&(await page.locator('#observation').inputValue())==='';
  if(!r.notesUntouched)throw new Error('Unexpected nonempty notes');if(r.errors.length)throw new Error('Page errors observed');healthy();r.status='completed';
}catch(e){r.status='failed';r.failure={wallSeconds:wall(),message:e.message,stack:e.stack};process.exitCode=1;}
finally{
  capturing=false;if(captureLoop)await captureLoop;await captureChain;r.recordingEndedWallSeconds=wall();clearTimeout(watchdog);
  if(context){try{await context.close();r.resourcesClosed.context=true;}catch(e){r.resourcesClosed.contextError=e.message;}}
  if(browser){try{await browser.close();r.resourcesClosed.browser=true;}catch(e){r.resourcesClosed.browserError=e.message;}}
  if(server){try{await server.close();r.resourcesClosed.server=true;}catch(e){r.resourcesClosed.serverError=e.message;}}
  r.browserPhaseWallSeconds=wall();await publish();
}
if(r.frames.length){
  try{
    const lines=['ffconcat version 1.0'];for(let j=0;j<r.frames.length;j++){
      const f=r.frames[j],next=j+1<r.frames.length?r.frames[j+1].timestampSeconds:r.recordingEndedWallSeconds;
      lines.push(`file '${f.file}'`,'option framerate 1000',`duration ${Math.max(.001,next-f.timestampSeconds).toFixed(6)}`);
    }
    lines.push(`file '${r.frames.at(-1).file}'`,'option framerate 1000');await fs.writeFile(path.join(out,'timeline.ffconcat'),lines.join('\n')+'\n');
    r.encoding={startedWallSeconds:wall(),command:[encoder,'-hide_banner','-nostdin','-f','concat','-safe','0','-i','timeline.ffconcat','-fps_mode','vfr','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-video_track_timescale','1000000','-movflags','+faststart','study.mp4']};
    const encoded=spawnSync(encoder,r.encoding.command.slice(1),{cwd:out,encoding:'utf8',timeout:60000,windowsHide:true,stdio:['ignore','pipe','pipe']});
    await fs.writeFile(path.join(out,'encode.stdout.log'),encoded.stdout||'');await fs.writeFile(path.join(out,'encode.stderr.log'),encoded.stderr||'');
    r.encoding.exitCode=encoded.status;if(encoded.error||encoded.status!==0)throw new Error(encoded.error?.message||`Encoder exit ${encoded.status}`);
    const bytes=await fs.readFile(path.join(out,'study.mp4'));r.video={file:'study.mp4',bytes:bytes.length,sha256:hash(bytes),commitEligible:bytes.length<=20*1024*1024,
      frameCountCaptured:r.frames.length,untrimmedSamplingSpanSeconds:r.recordingEndedWallSeconds-r.frames[0].timestampSeconds};
    const probeText=execFileSync(probe,['-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,nb_frames,duration','-of','json','study.mp4'],{cwd:out,encoding:'utf8',timeout:10000,windowsHide:true});
    await fs.writeFile(path.join(out,'video-probe.json'),probeText);r.video.probe=JSON.parse(probeText);r.encoding.endedWallSeconds=wall();
    if(!r.video.commitEligible)await fs.appendFile(path.join(here,'.gitignore'),'\n/run-02/study.mp4\n');
  }catch(e){r.encodingFailure={message:e.message,stdout:e.stdout?.toString(),stderr:e.stderr?.toString()};r.status='failed';process.exitCode=1;}
}
r.sourceAfter=await hashes();r.sourcesUnchanged=JSON.stringify(r.sourceBefore)===JSON.stringify(r.sourceAfter);
if(!r.sourcesUnchanged){r.status='failed';process.exitCode=1;}
r.totalWallSeconds=wall();r.noFurtherRecording=true;await publish();
console.log(JSON.stringify({status:r.status,wallSeconds:r.totalWallSeconds,browserPhaseWallSeconds:r.browserPhaseWallSeconds,video:r.video||null,failure:r.failure||r.encodingFailure||null,sourcesUnchanged:r.sourcesUnchanged,out}));
