// One normal presentation pass and a separate mobile early exit; no simulation.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';

if(!process.argv.includes('--execute')){
  console.log('A32: one 14-second desktop presentation, two pauses, finish; mobile initial/early exit. <=90s, <=7 PNG, <=12MiB. No simulation, video or automatic retry.');
  process.exit(0);
}
const here=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(here,'inspection-01');
await fs.mkdir(out,{recursive:false});
const start=performance.now(), elapsed=()=>(performance.now()-start)/1000;
const sha=b=>createHash('sha256').update(b).digest('hex');
const sourceFiles=['index.html','work.css','work.mjs','WORK_SPEC.md','BRIEF.md','inspect.mjs'].map(x=>path.join(here,x)).concat([
  path.join(here,'../a25-public-request/inspection-01/04-request-returned.png'),
  path.join(here,'../a25-public-request/inspection-01/result.json'),
  path.join(repoRoot,'research/lib/runtime.mjs')
]);
const requestText='叶青：下次张贴时，请不要再列我的名字。正文由另两人保留。';
const statementText='我们同意将小院的周六晚间开放给放映，并在闭场后共同收拾。';
const result={schema:'a32-form-inspection-1',createdUTC:new Date().toISOString(),status:'started',scope:'One authored presentation of an unchanged source still. UI behavior and discrete frames only; no new physics, continuous aesthetic viewing or human response.',sources:{},images:[],imageBytes:0,checks:{},pageErrors:[],console:[],externalRequests:[],closed:{}};
let server,browser,context,page,timedOut=false;
const timer=setTimeout(()=>{timedOut=true;context?.close().catch(()=>{});},90000);
const hard=setTimeout(()=>process.exit(124),110000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a32.snapshot());
async function shot(name){
  if(result.images.length>=7)throw Error('Screenshot count exceeded');
  const before=await read(),file=name+'.png';
  await page.screenshot({path:path.join(out,file),fullPage:true});
  const bytes=await fs.readFile(path.join(out,file));
  result.imageBytes+=bytes.length;
  result.images.push({file,bytes:bytes.length,sha256:sha(bytes),before,after:await read(),requestActuallyVisible:await page.getByText(requestText,{exact:true}).isVisible(),elapsedSeconds:elapsed()});
  await save();
  if(result.imageBytes>12*1024*1024)throw Error('Screenshot byte budget exceeded');
}
try{
  for(const f of sourceFiles){const b=await fs.readFile(f);result.sources[path.relative(repoRoot,f).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};}
  const previous=JSON.parse(await fs.readFile(path.join(here,'../a25-public-request/inspection-01/result.json'),'utf8'));
  const original=previous.images.find(x=>x.file==='04-request-returned.png');
  const imageBytes=await fs.readFile(path.join(here,'../a25-public-request/inspection-01/04-request-returned.png'));
  result.checks.sourceMatchesA25=original?.sha256===sha(imageBytes);
  server=await startServer();
  const launched=await launchBrowser();browser=launched.browser;
  result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
  context=await browser.newContext({viewport:{width:1360,height:1100}});
  await context.route('**/*',async route=>{
    const url=route.request().url();
    if(url.startsWith(server.url+'/')||url.startsWith('data:')||url.startsWith('blob:'))await route.continue();
    else{result.externalRequests.push(url);await route.abort();}
  });
  async function open(viewport){
    page=await context.newPage();page.setDefaultTimeout(20000);
    if(viewport)await page.setViewportSize(viewport);
    page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));
    page.on('console',m=>{if(['warning','error'].includes(m.type())&&result.console.length<100)result.console.push({type:m.type(),text:m.text()});});
    await page.goto(server.url+'/tracks/art/studies/a32-image-reuse-study/',{waitUntil:'load'});
    await page.waitForFunction(()=>window.__a32?.snapshot().ready===true);
  }
  await open();result.initial=await read();await shot('01-source-ready');
  await page.locator('#begin').click();
  await page.waitForFunction(()=>window.__a32.snapshot().elapsedMs>=5000);
  await page.locator('#pause').click();result.cropPause=await read();await shot('02-cropping-paused');
  await page.waitForTimeout(150);result.cropAfterWait=await read();
  result.checks.pauseFreezesTime=result.cropPause.elapsedMs===result.cropAfterWait.elapsedMs&&!result.cropPause.running&&result.cropPause.phase==='cropping';
  await page.locator('#pause').click();
  await page.waitForFunction(()=>window.__a32.snapshot().elapsedMs>=9000);
  await page.locator('#pause').click();result.placingPause=await read();await shot('03-placing-paused');
  result.checks.placingReached=result.placingPause.phase==='placing'&&!result.placingPause.running;
  await page.locator('#pause').click();
  await page.waitForFunction(()=>{const s=window.__a32.snapshot();return s.phase==='posted'&&!s.running&&s.elapsedMs>=14000;});
  result.posted=await read();await shot('04-posted');
  result.checks.postedAtFixedEnd=result.posted.elapsedMs===14000&&!result.posted.ended;
  result.checks.continuingNamesActuallyVisible=await page.getByText('宁岚',{exact:true}).isVisible()&&await page.getByText('沈舟',{exact:true}).isVisible();
  result.checks.statementActuallyVisible=await page.getByText(statementText,{exact:true}).isVisible();
  result.finalDOM=await page.evaluate(()=>{
    const notice=document.getElementById('notice'),request=document.getElementById('request');
    const signatures=Array.from(document.querySelectorAll('#notice-signatures [data-signature]'),el=>({name:el.textContent,fontSize:getComputedStyle(el).fontSize,color:getComputedStyle(el).color}));
    return {requestInsidePaper:notice.contains(request),signatures,sourceNodes:document.querySelectorAll('#source-image').length,sourceHref:document.getElementById('source-image').getAttribute('href')};
  });
  result.checks.requestOutsidePaper=result.finalDOM.requestInsidePaper===false;
  result.checks.retypesExactlyContinuingNames=JSON.stringify(result.finalDOM.signatures.map(x=>x.name))===JSON.stringify(['宁岚','沈舟']);
  result.checks.equalNewSignatures=result.finalDOM.signatures.length===2&&result.finalDOM.signatures[0].fontSize===result.finalDOM.signatures[1].fontSize&&result.finalDOM.signatures[0].color===result.finalDOM.signatures[1].color;
  result.checks.sameSourceNodeAndPath=result.finalDOM.sourceNodes===1&&result.finalDOM.sourceHref==='../a25-public-request/inspection-01/04-request-returned.png';
  result.checks.finalCropAndPlacement=result.posted.clip.height===214&&result.posted.clip.bottom===510&&result.posted.notice.imageAlignedWithSlot;
  await page.locator('#finish').click();result.ended=await read();await shot('05-ended');
  result.checks.finishStops=result.ended.phase==='ended'&&result.ended.ended===true&&!result.ended.running&&result.ended.elapsedMs===14000;
  await page.close();await open({width:390,height:844});await shot('06-mobile-ready');
  result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
  await page.locator('#finish').click();result.mobileEnded=await read();await shot('07-mobile-early-end');
  result.checks.mobileEarlyExit=result.mobileEnded.phase==='ended'&&result.mobileEnded.elapsedMs===0&&!result.mobileEnded.running;
  result.checks.stillsHaveStableTime=result.images.every(im=>im.before.elapsedMs===im.after.elapsedMs);
  result.checks.requestRemainsVisible=result.images.every(im=>im.requestActuallyVisible);
  result.checks.noPageErrors=result.pageErrors.length===0;
  result.checks.noExternalRequests=result.externalRequests.length===0;
  result.checks.withinBudget=!timedOut;
  result.checks.sourcesUnchanged=true;
  for(const f of sourceFiles){const key=path.relative(repoRoot,f).replaceAll('\\','/');if(sha(await fs.readFile(f))!==result.sources[key].sha256)result.checks.sourcesUnchanged=false;}
  if(!Object.values(result.checks).every(x=>x===true))throw Error('One or more recorded behavior checks failed');
  result.status='completed_single_presentation_check';
}catch(error){result.status='failed';result.error={message:error.message,stack:error.stack};process.exitCode=1;}
finally{
  clearTimeout(timer);
  if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
  if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
  if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
  result.wallSeconds=elapsed();await save();clearTimeout(hard);
  console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images.length,imageBytes:result.imageBytes,checks:result.checks,error:result.error}));
}
