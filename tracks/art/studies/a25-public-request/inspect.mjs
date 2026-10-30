// Normal authored viewing sequence; one fire, plus a no-fire mobile early exit.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
if(!process.argv.includes('--execute')){console.log('Normal read/request processing, pause/return request/resume, finish; mobile no-fire exit. <=120s/10PNG/16MiB. No retry.');process.exit(0);}
const out=path.join(here,'inspection-01');await fs.mkdir(out,{recursive:false});
const started=performance.now(),elapsed=()=> (performance.now()-started)/1000;
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['index.html','work.css','work.mjs','WORK_SPEC.md','BRIEF.md','inspect.mjs'].map(f=>path.join(here,f)).concat([path.join(repoRoot,'demo/index.html'),path.join(repoRoot,'research/lib/runtime.mjs'),path.join(here,'../a24-signature-material/inspection-01/result.json')]);
const result={schema:'a25-normal-viewing-1',createdUTC:new Date().toISOString(),status:'started',scope:'A25 viewing behavior using frozen A24 material. One desktop fire sequence, one initial-only mobile page; no participant, social withdrawal, new material search or artistic validation.',sources:{},images:[],checks:{},pageErrors:[],console:[],externalRequests:[],imageBytes:0,closed:{}};
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},120000),hard=setTimeout(()=>process.exit(124),140000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a25.snapshot());
async function shot(label){
 if(result.images.length>=10)throw Error('Image count budget exhausted');
 const before=await read(),file=label+'.png';await page.screenshot({path:path.join(out,file),fullPage:true});
 const b=await fs.readFile(path.join(out,file));result.imageBytes+=b.length;
 result.images.push({file,bytes:b.length,sha256:sha(b),before,after:await read(),inspectionElapsedSeconds:elapsed()});
 await save();if(result.imageBytes>16*1024*1024)throw Error('Image byte budget exhausted');
}
try{
 for(const file of sources){const b=await fs.readFile(file);result.sources[path.relative(repoRoot,file).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};}
 const previous=JSON.parse(await fs.readFile(path.join(here,'../a24-signature-material/inspection-01/result.json'),'utf8'));
 server=await startServer();const launched=await launchBrowser();browser=launched.browser;
 result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
 context=await browser.newContext({viewport:{width:1360,height:1100}});
 await context.route('**/*',async route=>{const u=route.request().url();if(u.startsWith(server.url+'/')||u.startsWith('data:')||u.startsWith('blob:'))await route.continue();else{result.externalRequests.push(u);await route.abort();}});
 async function newPage(viewport){
   page=await context.newPage();page.setDefaultTimeout(25000);if(viewport)await page.setViewportSize(viewport);
   page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));
   page.on('console',m=>{if(['error','warning'].includes(m.type())&&result.console.length<100)result.console.push({type:m.type(),text:m.text()});});
   await page.goto(server.url+'/tracks/art/studies/a25-public-request/',{waitUntil:'load'});
   await page.waitForFunction(()=>window.__a25?.snapshot().phase==='ready');
 }
 await newPage();await shot('01-statement');result.initial=await read();
 await page.locator('#read-request').click();await shot('02-request');result.requestRead=await read();
 result.checks.requestBeforeProcessing=result.requestRead.phase==='request'&&result.requestRead.requestVisible===true&&result.requestRead.frame===0;
 await page.locator('#begin').click();
 await page.waitForFunction(()=>window.__a25.snapshot().frame>=120);
 await page.locator('#pause').click();await shot('03-paused-processing');result.paused=await read();
 result.checks.processingBeforePause=result.paused.phase==='paused'&&result.paused.frame>=120&&result.paused.frame<360&&result.paused.requestVisible===false;
 await page.locator('#request').click();await shot('04-request-returned');result.returnedRequest=await read();
 result.checks.requestReturnDoesNotAdvance=result.returnedRequest.requestVisible===true&&result.returnedRequest.frame===result.paused.frame&&result.returnedRequest.material.hash===result.paused.material.hash;
 await page.locator('#pause').click();await page.waitForFunction(()=>window.__a25.snapshot().phase==='held',{},{timeout:30000});
 await shot('05-window-end');result.final=await read();
 result.checks.fixedWindow=result.final.frame===360&&result.final.phase==='held';
 result.checks.singleDesktopIgnition=result.final.ignitionCalls===1;
 result.checks.singleDesktopReset=result.final.resetCalls===1;
 result.checks.materialMatchesFrozenA24=result.final.material.hash===previous.final.material.hash&&JSON.stringify(result.final.material.groups)===JSON.stringify(previous.final.material.groups);
 await page.locator('#finish').click();await shot('06-finished');result.finished=await read();
 result.checks.finishPreservesState=result.finished.phase==='ended'&&result.finished.frame===360&&result.finished.material.hash===result.final.material.hash;
 await page.close();await newPage({width:390,height:844});await shot('07-mobile-opening');
 result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 await page.locator('#finish').click();await shot('08-mobile-early-end');result.mobileEnded=await read();
 result.checks.mobileExitWithoutFire=result.mobileEnded.phase==='ended'&&result.mobileEnded.frame===0&&result.mobileEnded.ignitionCalls===0;
 result.checks.allStillsPaused=result.images.every(im=>im.before.frame===im.after.frame);
 result.checks.noPageErrors=result.pageErrors.length===0;result.checks.noExternalRequests=result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;
 for(const file of sources){const key=path.relative(repoRoot,file).replaceAll('\\','/');if(sha(await fs.readFile(file))!==result.sources[key].sha256)result.checks.sourcesUnchanged=false;}
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(x=>x===true))throw Error('Recorded behavior check failed');
 result.status='completed_normal_viewing_sequence';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);
 if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=elapsed();await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images.length,imageBytes:result.imageBytes,checks:result.checks,error:result.error}));
}
