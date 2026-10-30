// Finite normal-UI still inspection of an authored SVG work, not a participant study.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const name=process.argv.find(x=>x.startsWith('--out='))?.slice(6)||'inspection-01';
if(!/^inspection-0[12]$/.test(name))throw Error('Expected a fresh bounded output name');
if(!process.argv.includes('--execute')){console.log('Normal room/threshold/closure/exit plus mobile early exit; <=60s, <=8 images, <=10MiB. Pass --execute.');process.exit(0);}
const out=path.join(here,name);await fs.mkdir(out,{recursive:false});
const started=performance.now(),seconds=()=> (performance.now()-started)/1000,hash=b=>createHash('sha256').update(b).digest('hex');
const result={schema:'a22-ui-stills-1',createdUTC:new Date().toISOString(),status:'started',scope:'Normal UI actions and stills; no simulation, human participant or artistic validation.',sources:{},images:[],checks:{},pageErrors:[],externalRequests:[],imageBytes:0,closed:{}};
const files=['index.html','room.css','room.mjs','inspect.mjs'];
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},60000),hard=setTimeout(()=>process.exit(124),72000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a22.snapshot());
async function shot(label){
 if(result.images.length>=8)throw Error('Image budget exhausted');
 const before=await read(),p=path.join(out,label+'.png');await page.screenshot({path:p,fullPage:true});const b=await fs.readFile(p);
 result.imageBytes+=b.length;result.images.push({file:label+'.png',bytes:b.length,sha256:hash(b),before,after:await read(),inspectionElapsedSeconds:seconds()});
 if(result.imageBytes>10*1024*1024)throw Error('Image budget exceeded');await save();
}
try{
 for(const f of files){const b=await fs.readFile(path.join(here,f));result.sources[f]={bytes:b.length,sha256:hash(b)};}
 server=await startServer();const launched=await launchBrowser();browser=launched.browser;
 result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
 context=await browser.newContext({viewport:{width:1360,height:1100}});
 await context.route('**/*',async route=>{const u=route.request().url();if(u.startsWith(server.url+'/')||u.startsWith('data:'))await route.continue();else{result.externalRequests.push(u);await route.abort();}});
 const url=server.url+'/tracks/art/studies/a22-undelivered-room/';
 async function newPage(viewport){page=await context.newPage();page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));if(viewport)await page.setViewportSize(viewport);await page.goto(url,{waitUntil:'load'});await page.waitForFunction(()=>window.__a22?.snapshot().phase==='room');}
 await newPage();await shot('01-room');await page.locator('#to-threshold').click();await shot('02-threshold');
 result.checks.threshold=(await read()).phase==='threshold';
 await page.locator('#close-door').click();await shot('03-closed-door');result.checks.closed=(await read()).phase==='ended';
 await page.locator('#leave').click();await shot('04-ended');result.checks.normalExit=(await read()).phase==='left';
 await page.close();await newPage({width:390,height:844});await shot('05-mobile-room');
 result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 await page.locator('#leave').click();await shot('06-mobile-early-exit');result.checks.earlyExit=(await read()).phase==='left';
 result.checks.noPageErrors=result.pageErrors.length===0;result.checks.noExternalRequests=result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;for(const f of files)if(hash(await fs.readFile(path.join(here,f)))!==result.sources[f].sha256)result.checks.sourcesUnchanged=false;
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(x=>x===true))throw Error('Recorded behavior did not complete');
 result.status='completed_normal_ui_still_inspection';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=seconds();await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images.length,imageBytes:result.imageBytes,checks:result.checks,error:result.error}));
}
