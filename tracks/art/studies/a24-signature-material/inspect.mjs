// One normal UI sequence, not a participant session or artistic success test.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
if(!process.argv.includes('--execute')){console.log('One ignition + three normal 2-second advances; <=120s, <=8 PNG, <=12MiB. No retry or tuning.');process.exit(0);}
const out=path.join(here,'inspection-01');await fs.mkdir(out,{recursive:false});
const started=performance.now(),elapsed=()=> (performance.now()-started)/1000;
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['index.html','sample.css','sample.mjs','WORK_SPEC.md','BRIEF.md','inspect.mjs'].map(f=>path.join(here,f)).concat([path.join(repoRoot,'demo/index.html'),path.join(repoRoot,'research/lib/runtime.mjs')]);
const result={schema:'a24-normal-ui-material-1',createdUTC:new Date().toISOString(),status:'started',scope:'Single original-model signature material sample. No participant, artistic validation, consent withdrawal, recording or parameter search.',sources:{},images:[],checks:{},pageErrors:[],console:[],externalRequests:[],imageBytes:0,closed:{}};
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},120000);
const hard=setTimeout(()=>process.exit(124),140000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a24.snapshot());
async function shot(label){
 if(result.images.length>=8)throw Error('Image count budget exhausted');
 const before=await read(),file=label+'.png';await page.screenshot({path:path.join(out,file),fullPage:true});
 const b=await fs.readFile(path.join(out,file));result.imageBytes+=b.length;
 result.images.push({file,bytes:b.length,sha256:sha(b),before,after:await read(),inspectionElapsedSeconds:elapsed()});
 await save();if(result.imageBytes>12*1024*1024)throw Error('Image byte budget exhausted');
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
 await page.goto(server.url+'/tracks/art/studies/a24-signature-material/',{waitUntil:'load'});
 await page.waitForFunction(()=>window.__a24?.snapshot().phase==='ready');
 await shot('01-ready');result.initial=await read();
 await page.locator('#ignite').click();await shot('02-ignited');result.afterIgnition=await read();
 if(result.afterIgnition.phase!=='ignited')throw Error('Fixed ignition did not qualify');
 for(const [i,label] of ['03-two-seconds','04-four-seconds','05-six-seconds'].entries()){
   await page.locator('#advance').click();
   await page.waitForFunction(target=>{const s=window.__a24.snapshot();return s.frame===target&&['held','ended'].includes(s.phase);},(i+1)*120,{timeout:30000});
   await shot(label);
 }
 result.final=await read();
 result.checks.completeFixedSequence=result.final.frame===360&&result.final.phase==='ended';
 result.checks.singleIgnition=result.final.ignitionCalls===1;
 result.checks.singleReset=result.final.resetCalls===1;
 result.checks.exactSampleFrames=result.images.map(x=>x.before.frame).join(',')==='0,0,120,240,360';
 result.checks.noScreenshotAdvance=result.images.every(x=>x.before.frame===x.after.frame);
 await page.setViewportSize({width:390,height:844});await shot('06-mobile-ended');
 result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 result.checks.mobileDidNotAdvance=(await read()).frame===360;
 await page.locator('#leave').click();await shot('07-left');result.checks.leave=(await read()).phase==='left';
 result.checks.noPageErrors=result.pageErrors.length===0;result.checks.noExternalRequests=result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;
 for(const file of sources){const key=path.relative(repoRoot,file).replaceAll('\\','/');if(sha(await fs.readFile(file))!==result.sources[key].sha256)result.checks.sourcesUnchanged=false;}
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(x=>x===true))throw Error('A recorded behavior check failed');
 result.status='completed_fixed_signature_material_sample';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);
 if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=elapsed();await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images.length,imageBytes:result.imageBytes,checks:result.checks,error:result.error}));
}
