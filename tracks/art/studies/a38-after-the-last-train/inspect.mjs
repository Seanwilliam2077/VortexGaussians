// One predeclared pointer sequence; not a participant study or artistic score.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
if(!process.argv.includes('--execute')){console.log('One full-work sequence, 3 holds, 360 steps, final reset only; <=120s, <=7 PNG/12MiB. No retry.');process.exit(0);}
const out=path.join(here,'inspection-01');await fs.mkdir(out,{recursive:false});
const started=performance.now(),elapsed=()=> (performance.now()-started)/1000;
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['index.html','work.css','work.mjs','WORK_SPEC.md','BRIEF.md','INSPECTION_PROTOCOL.md','inspect.mjs'].map(f=>path.join(here,f)).concat([path.join(repoRoot,'demo/index.html'),path.join(repoRoot,'research/lib/runtime.mjs')]);
const result={schema:'a38-full-work-single-sequence-1',createdUTC:new Date().toISOString(),status:'started',scope:'One authored UI sequence and stills; no participant, continuous viewing, physical validation or artistic score.',sources:{},images:[],inputs:[],checks:{},pageErrors:[],console:[],externalRequests:[],imageBytes:0,closed:{}};
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},120000);
const hard=setTimeout(()=>process.exit(124),140000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a38.snapshot());
async function shot(label){
 if(result.images.length>=7)throw Error('Image count budget exhausted');
 const before=await read(),file=label+'.png';await page.screenshot({path:path.join(out,file),fullPage:true});
 const b=await fs.readFile(path.join(out,file));result.imageBytes+=b.length;
 result.images.push({file,bytes:b.length,sha256:sha(b),before,after:await read(),inspectionElapsedSeconds:elapsed()});
 await save();if(result.imageBytes>12*1024*1024)throw Error('Image byte budget exhausted');
}
async function move(sx,sy,steps=1){
 const b=await page.locator('#view').boundingBox();if(!b)throw Error('Canvas not visible');
 result.inputs.push({action:'move',source:[sx,sy],steps,beforeFrame:(await read()).frame});
 await page.mouse.move(b.x+sx*b.width/1200,b.y+sy*b.height/600,{steps});
}
async function press(){result.inputs.push({action:'down',beforeFrame:(await read()).frame});await page.mouse.down({button:'left'});}
async function release(){await page.mouse.up({button:'left'});result.inputs.push({action:'up',afterFrame:(await read()).frame});}
async function atLeast(frame){
 await page.waitForFunction(n=>{const s=window.__a38.snapshot();return s.phase==='error'||s.frame>=n;},frame,{timeout:40000});
 const s=await read();if(s.phase==='error')throw Error('Work failed: '+JSON.stringify(s.errors));
}
try{
 for(const file of sources){const b=await fs.readFile(file);result.sources[path.relative(repoRoot,file).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};}
 server=await startServer();const launched=await launchBrowser();browser=launched.browser;
 result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
 context=await browser.newContext({viewport:{width:1360,height:1100}});
 await context.route('**/*',async route=>{const u=route.request().url();if(u.startsWith(server.url+'/')||u.startsWith('data:')||u.startsWith('blob:'))await route.continue();else{result.externalRequests.push(u);await route.abort();}});
 page=await context.newPage();page.setDefaultTimeout(25000);
 page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));
 page.on('console',m=>{if(['error','warning'].includes(m.type())&&result.console.length<100)result.console.push({type:m.type(),text:m.text()});});
 await page.goto(server.url+'/tracks/art/studies/a38-after-the-last-train/',{waitUntil:'load'});
 await page.waitForFunction(()=>['ready','error'].includes(window.__a38?.snapshot().phase));
 result.initial=await read();if(result.initial.phase!=='ready')throw Error('Initial qualification failed: '+JSON.stringify(result.initial.errors));
 await shot('01-ready');
 await move(424,300);await press();await move(568,300,12);await atLeast(120);await release();
 result.firstRelease=await read();
 if(result.firstRelease.phase!=='held'||result.firstRelease.frame<120||result.firstRelease.frame>149)throw Error('First release outside predeclared frame interval');
 await shot('02-first-release');
 await move(664,348);await press();await move(856,348,12);await atLeast(240);await release();
 result.secondRelease=await read();
 if(result.secondRelease.phase!=='held'||result.secondRelease.frame<240||result.secondRelease.frame>269)throw Error('Second release outside predeclared frame interval');
 await shot('03-second-release');
 await move(488,444);await press();await atLeast(360);await release();result.final=await read();
 await shot('04-six-seconds');
 await page.locator('#leave').click();result.left=await read();await shot('05-left');
 await page.locator('#restart').click();result.restarted=await read();await shot('06-restarted');
 await page.setViewportSize({width:390,height:844});await shot('07-mobile-ready');result.mobile=await read();
 result.checks.complete360=result.final.phase==='ended'&&result.final.frame===360;
 result.checks.fullSixLines=Object.keys(result.initial.groups).length===6;
 result.checks.snapshotReadsValid=result.images.every(x=>!x.before.snapshotError&&!x.after.snapshotError&&typeof x.before.hash==='string');
 result.checks.noScreenshotAdvance=result.images.every(x=>x.before.frame===x.after.frame&&x.before.hash===x.after.hash);
 result.checks.releasePermitsReading=result.firstRelease.phase==='held'&&result.secondRelease.phase==='held';
 result.checks.endRetainsMaterial=result.left.phase==='left'&&result.left.hash===result.final.hash&&result.left.frame===360;
 result.checks.restartRestoresInitial=result.restarted.phase==='ready'&&result.restarted.frame===0&&result.restarted.hash===result.initial.hash;
 result.checks.twoResetsOnly=result.initial.resetCalls===1&&result.restarted.resetCalls===2&&result.mobile.resetCalls===2;
 result.checks.noPostRestartIgnition=result.restarted.ignitionCalls===result.final.ignitionCalls&&result.mobile.ignitionCalls===result.final.ignitionCalls;
 result.checks.noPostRestartSteps=result.restarted.totalStepCalls===360&&result.mobile.totalStepCalls===360&&result.mobile.frame===0;
 result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 result.checks.noErrors=result.pageErrors.length===0&&result.console.length===0&&result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;
 for(const file of sources){const key=path.relative(repoRoot,file).replaceAll('\\','/');if(sha(await fs.readFile(file))!==result.sources[key].sha256)result.checks.sourcesUnchanged=false;}
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(x=>x===true))throw Error('A predeclared behavior/evidence check failed');
 result.status='completed_single_full_handover_sequence';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};if(page)try{result.atFailure=await read();}catch{}process.exitCode=1;}
finally{
 clearTimeout(timer);
 if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=elapsed();await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images.length,imageBytes:result.imageBytes,checks:result.checks,error:result.error}));
}
