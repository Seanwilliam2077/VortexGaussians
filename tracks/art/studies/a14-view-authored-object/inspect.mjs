// A single bounded inspection of the actual A14 sequence. Not an audience test.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser,repoRoot} from '../../../../research/lib/runtime.mjs';
const here=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(here,'inspection-01');
const hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.argv.includes('--execute')){console.log('One 360-step A14 inspection; pass --execute. Existing output is never overwritten.');process.exit(0);}
if(!process.env.PLAYWRIGHT_MODULE||!process.env.BROWSER_EXECUTABLE)throw Error('Use existing runtimes');
await fs.mkdir(out,{recursive:false});
const started=performance.now();const elapsed=()=> (performance.now()-started)/1000;
const result={createdUTC:new Date().toISOString(),status:'started',scope:'One actual work sequence sampled through its normal step/render functions; no human viewing or artistic validation',sources:{},steps:[],pageErrors:[],console:[],external:[],closed:{},budgetSeconds:240};
let server,browser,context,page,timer,hardTimer;
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const snapshot=()=>page.evaluate(()=>window.__a14.snapshot());
const shot=async(name)=>{
 const file=name+'.png';const b=await page.screenshot({path:path.join(out,file),fullPage:true,timeout:10000});
 result.steps.push({name,file,bytes:b.length,sha256:hash(b),wallSeconds:elapsed(),snapshot:await snapshot(),canvases:await page.locator('main canvas').evaluateAll(cs=>cs.map(c=>({width:c.width,height:c.height,rect:{x:c.getBoundingClientRect().x,y:c.getBoundingClientRect().y,width:c.getBoundingClientRect().width,height:c.getBoundingClientRect().height}})))});await save();
};
try{
 for(const file of ['index.html','WORK_SPEC.md','INTENT.md','inspect.mjs']){const b=await fs.readFile(path.join(here,file));result.sources[file]={bytes:b.length,sha256:hash(b)};}
 for(const file of ['demo/index.html','research/lib/runtime.mjs']){const b=await fs.readFile(path.join(repoRoot,file));result.sources[file]={bytes:b.length,sha256:hash(b)};}
 hardTimer=setTimeout(()=>{process.stderr.write('A14 hard worker deadline\n');process.exit(124);},240000);
 timer=setTimeout(()=>{result.deadlineExceeded=true;void save();void browser?.close().catch(()=>{});},225000);
 server=await startServer();const launched=await launchBrowser(process.env.BROWSER_EXECUTABLE);browser=launched.browser;
 result.runtime={node:process.version,browser:browser.version(),launch:launched.launchOptions,module:launched.module};
 context=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});
 await context.route('**/*',async route=>{const u=new URL(route.request().url());if(u.origin===server.url||['data:','blob:'].includes(u.protocol))await route.continue();else{result.external.push(u.href);await route.abort();}});
 page=await context.newPage();page.setDefaultTimeout(15000);
 page.on('pageerror',e=>result.pageErrors.push(e.message));page.on('console',m=>{if(['error','warning'].includes(m.type()))result.console.push({type:m.type(),text:m.text()});});
 await page.goto(server.url+'/tracks/art/studies/a14-view-authored-object/?inspect=1',{waitUntil:'load'});
 await page.waitForFunction(()=>!!window.__a14);await page.evaluate(()=>window.__a14.ready);
 await shot('01-before');
 await page.getByRole('button',{name:'开始观看',exact:true}).click();result.startedSnapshot=await snapshot();
 await page.evaluate(()=>window.__a14.inspectAdvance(90));await shot('02-first-3s');
 await page.getByRole('button',{name:'暂停',exact:true}).click();result.pausedSnapshot=await snapshot();
 await page.getByRole('button',{name:'继续',exact:true}).click();result.resumedSnapshot=await snapshot();
 await page.evaluate(()=>window.__a14.inspectAdvance(90));await shot('03-handoff-6s');
 await page.evaluate(()=>window.__a14.inspectAdvance(90));await shot('04-second-9s');
 await page.evaluate(()=>window.__a14.inspectAdvance(90));await shot('05-end-12s');
 result.final=await snapshot();
 await page.setViewportSize({width:390,height:844});await shot('06-mobile-end');
 result.reinitializeEnabled=await page.getByRole('button',{name:'重新开始（重新初始化）',exact:true}).isEnabled();
 result.sourcesUnchanged=true;
 for(const [f,info] of Object.entries(result.sources)){const p=f.includes('/')?path.join(repoRoot,f):path.join(here,f);if(hash(await fs.readFile(p))!==info.sha256)result.sourcesUnchanged=false;}
 result.sequenceBehavior=result.final.frame===360&&result.final.phase==='ended'&&result.final.ignitionCalls===1&&result.final.resetCalls===1&&result.final.handoffEqualExceptYaw===true&&!result.final.errors.length;
 if(!result.sequenceBehavior||result.pageErrors.length||result.external.length||result.deadlineExceeded||!result.sourcesUnchanged)throw Error('Inspection did not complete its fixed sequence cleanly');
 result.status='completed_sequence_for_visual_review';
}catch(error){result.status='failed';result.failure={message:error.message,stack:error.stack};process.exitCode=1;}
finally{
 clearTimeout(timer);
 if(context)await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);
 if(browser)await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);
 if(server)await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);
 result.wallSeconds=elapsed();await save();clearTimeout(hardTimer);
 console.log(JSON.stringify({status:result.status,wallSeconds:result.wallSeconds,steps:result.steps.length,failure:result.failure,errors:result.pageErrors,console:result.console,closed:result.closed}));
}
