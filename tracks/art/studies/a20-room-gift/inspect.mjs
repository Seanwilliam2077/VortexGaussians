// Normal-UI inspection, not an audience session or aesthetic validation.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const outputName=process.argv.find(x=>x.startsWith('--out='))?.slice(6)||'inspection-01';
if(!/^inspection-0[123]$/.test(outputName))throw Error('Expected a bounded fresh inspection directory');
if(!process.argv.includes('--execute')){console.log('One normal UI path and one mobile early exit, <=120 seconds, <=12 screenshots, <=20 MiB; --execute to run.');process.exit(0);}
const out=path.join(here,outputName);await fs.mkdir(out,{recursive:false});
const started=performance.now(),seconds=()=> (performance.now()-started)/1000;
const hash=b=>createHash('sha256').update(b).digest('hex');
const result={schema:'a20-ui-inspection-1',createdUTC:new Date().toISOString(),status:'started',scope:'Automated normal UI actions and still images; no human participant, continuous-video judgment, or simulated paper destruction.',sources:{},images:[],checks:{},pageErrors:[],externalRequests:[],closed:{},imageBytes:0};
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},120000);
const hard=setTimeout(()=>process.exit(124),132000);
const files=['tracks/art/studies/a20-room-gift/index.html','tracks/art/studies/a20-room-gift/room.css','tracks/art/studies/a20-room-gift/room.mjs','tracks/art/studies/a20-room-gift/inspect.mjs','demo/index.html','research/lib/runtime.mjs'];
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const read=()=>page.evaluate(()=>window.__a20.snapshot());
async function shot(name){
 if(result.images.length>=12)throw Error('Image budget exhausted');
 const before=await read(),p=path.join(out,name+'.png');
 await page.screenshot({path:p,fullPage:true});
 const bytes=await fs.readFile(p);result.imageBytes+=bytes.length;
 result.images.push({file:name+'.png',bytes:bytes.length,sha256:hash(bytes),before,after:await read(),inspectionElapsedSeconds:seconds()});
 if(result.imageBytes>20*1024*1024)throw Error('Image byte budget exceeded');
 await save();
}
try{
 for(const f of files){const b=await fs.readFile(path.join(repoRoot,f));result.sources[f]={bytes:b.length,sha256:hash(b)};}
 server=await startServer();const launched=await launchBrowser();browser=launched.browser;
 result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
 context=await browser.newContext({viewport:{width:1360,height:1100}});
 await context.route('**/*',async route=>{const u=route.request().url();if(u.startsWith(server.url+'/')||u.startsWith('data:')||u.startsWith('blob:'))await route.continue();else{result.externalRequests.push(u);await route.abort();}});
 page=await context.newPage();page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));
 const url=server.url+'/tracks/art/studies/a20-room-gift/';
 await page.goto(url,{waitUntil:'load'});await page.waitForFunction(()=>window.__a20?.snapshot().phase==='room',{},{timeout:30000});
 await shot('01-room');await page.waitForTimeout(700);
 result.checks.roomDoesNotAdvance=(await read()).fireFrame===0;
 await page.locator('#start-fire').click();
 await page.waitForFunction(()=>window.__a20.snapshot().fireFrame>=1);await shot('02-fire-start');
 await page.waitForFunction(()=>window.__a20.snapshot().fireFrame>=75);await shot('03-fire-middle');
 await page.waitForFunction(()=>window.__a20.snapshot().fireFrame===150);await shot('04-fire-held');
 await page.waitForTimeout(500);const held=await read();
 result.checks.materialLimit=held.fireFrame===150&&held.fireStoppedBecause==='fixed_material_limit';
 await page.locator('#to-threshold').click();await shot('05-threshold');
 await page.locator('#close-door').click();await shot('06-closed-door');const closed=await read();
 result.checks.authoredClosure=closed.phase==='ended'&&closed.door==='authored_closed_from_inside'&&closed.viewpoint==='outside_threshold';
 result.checks.oneEmissionStart=closed.resetCalls===1&&closed.ignitionCalls===0&&closed.emissionStartCalls===1;
 result.checks.noReturnControl=await page.locator('#start-fire').isHidden()&&await page.locator('#to-threshold').isHidden()&&await page.locator('#close-door').isHidden();
 await page.locator('#leave').click();await shot('07-ended');result.checks.normalExit=(await read()).phase==='left';
 await page.close();page=await context.newPage();page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));await page.setViewportSize({width:390,height:844});
 await page.goto(url,{waitUntil:'load'});await page.waitForFunction(()=>window.__a20?.snapshot().phase==='room');await shot('08-mobile-room');
 result.checks.mobileNoHorizontalOverflow=await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
 await page.locator('#leave').click();await shot('09-mobile-early-exit');const early=await read();
 result.checks.earlyExitWithoutFire=early.phase==='left'&&early.fireFrame===0&&early.resetCalls===0&&early.emissionStartCalls===0;
 result.final=early;result.checks.noPageErrors=result.pageErrors.length===0;result.checks.noExternalRequests=result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;for(const f of files){if(hash(await fs.readFile(path.join(repoRoot,f)))!==result.sources[f].sha256)result.checks.sourcesUnchanged=false;}
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(v=>v===true))throw Error('At least one recorded behavioral check failed');
 result.status='completed_normal_ui_still_inspection';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=seconds();await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,checks:result.checks,images:result.images.length,imageBytes:result.imageBytes,error:result.error}));
}
