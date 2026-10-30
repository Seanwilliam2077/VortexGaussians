import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
if(!process.argv.includes('--execute')){console.log('One initial image only; 0 ignition/steps; <=60s, 1 PNG <=4MiB; no retry.');process.exit(0);}
const out=path.join(here,'inspection-01');await fs.mkdir(out,{recursive:false});
const started=performance.now(),sha=b=>createHash('sha256').update(b).digest('hex');
const result={schema:'a37-initial-readability-1',createdUTC:new Date().toISOString(),status:'started',sources:{},checks:{},pageErrors:[],console:[],externalRequests:[],images:[],closed:{},scope:'Single initial-state production inspection by informed agents; no viewer study or artistic score.'};
const sources=['BRIEF.md','WORK_SPEC.md','index.html','sample.mjs','inspect.mjs'].map(x=>path.join(here,x)).concat([path.resolve(here,'../a36-handover-material/sample.css'),path.join(repoRoot,'demo/index.html'),path.join(repoRoot,'research/lib/runtime.mjs')]);
let server,browser,context,page,deadline=false;
const timer=setTimeout(()=>{deadline=true;context?.close().catch(()=>{});},60000);
const hard=setTimeout(()=>process.exit(124),75000);
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
try{
 for(const f of sources)result.sources[path.relative(repoRoot,f).replaceAll('\\','/')]={sha256:sha(await fs.readFile(f))};
 const previous=JSON.parse(await fs.readFile(path.resolve(here,'../a36-handover-material/inspection-01/result.json'),'utf8'));
 server=await startServer();const launched=await launchBrowser();browser=launched.browser;
 result.browser={module:launched.module,launchOptions:launched.launchOptions,version:browser.version()};
 context=await browser.newContext({viewport:{width:1360,height:1100}});
 await context.route('**/*',async route=>{const u=route.request().url();if(u.startsWith(server.url+'/')||u.startsWith('data:')||u.startsWith('blob:'))await route.continue();else{result.externalRequests.push(u);await route.abort();}});
 page=await context.newPage();page.setDefaultTimeout(22000);
 page.on('pageerror',e=>result.pageErrors.push(e.stack||String(e)));
 page.on('console',m=>{if(['warning','error'].includes(m.type()))result.console.push({type:m.type(),text:m.text()});});
 await page.goto(server.url+'/tracks/art/studies/a37-handover-readability/',{waitUntil:'load'});
 await page.waitForFunction(()=>['ready','error'].includes(window.__a37?.snapshot().phase));
 const read=()=>page.evaluate(()=>window.__a37.snapshot());
 result.initial=await read();if(result.initial.phase!=='ready')throw Error('Initial qualification failed: '+JSON.stringify(result.initial.errors));
 await page.screenshot({path:path.join(out,'01-ready.png'),fullPage:true});
 const b=await fs.readFile(path.join(out,'01-ready.png'));result.images.push({file:'01-ready.png',bytes:b.length,sha256:sha(b)});
 result.after=await read();
 result.checks.onlyInitialState=result.initial.frame===0&&result.after.frame===0&&result.initial.hash===result.after.hash;
 result.checks.oneResetNoIgnition=result.after.resetCalls===1&&result.after.ignitionCalls===0;
 result.checks.noClockWork=result.after.material.counters.clockProcessed===0;
 const rasterKeys=['id','text','sourceY','pointCount','measuredTextWidth','measuredInkBounds','sampledPixelBounds','rgbaFNV1a32'];
 const rasterGroups=s=>s.geometry.groups.map(g=>Object.fromEntries(rasterKeys.map(k=>[k,g[k]])));
 result.checks.sameRasterAsA36=result.initial.geometry.pointCount===previous.initial.geometry.pointCount&&JSON.stringify(rasterGroups(result.initial))===JSON.stringify(rasterGroups(previous.initial));
 result.checks.imageBudget=b.length<=4*1024*1024;
 result.checks.noErrors=result.pageErrors.length===0&&result.console.length===0&&result.externalRequests.length===0;
 result.checks.sourcesUnchanged=true;
 for(const f of sources)if(sha(await fs.readFile(f))!==result.sources[path.relative(repoRoot,f).replaceAll('\\','/')].sha256)result.checks.sourcesUnchanged=false;
 result.checks.withinDeadline=!deadline;
 if(!Object.values(result.checks).every(x=>x===true))throw Error('Initial-state evidence check failed; no rerun.');
 result.status='completed_single_initial_readability_check';
}catch(e){result.status='failed';result.error={message:e.message,stack:e.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);
 if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=(performance.now()-started)/1000;await save();clearTimeout(hard);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,images:result.images,checks:result.checks,error:result.error}));
}
