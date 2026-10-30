// One bounded, visible-UI inspection of the A11 form study, not an audience test.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {startServer,launchBrowser} from '../../../../research/lib/runtime.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const out=path.join(here,process.argv[2]||'inspection-01');
if(path.dirname(out)!==here)throw new Error('Output must be a direct child of this study');
if(!process.env.PLAYWRIGHT_MODULE||!process.env.BROWSER_EXECUTABLE)throw new Error('Existing runtime paths required');
await fs.mkdir(out,{recursive:false});
const start=performance.now();
const seconds=()=> (performance.now()-start)/1000;
const hash=b=>createHash('sha256').update(b).digest('hex');
const source=await fs.readFile(path.join(here,'index.html'));
const result={createdUTC:new Date().toISOString(),scope:'Agent UI behavior and frame inspection only',
  source:{bytes:source.length,sha256:hash(source)},viewport:{width:1440,height:1000},
  steps:[],pageErrors:[],consoleWarnings:[],externalRequests:[],status:'started',closed:{}};
let server,browser,context,page,timer;
const save=()=>fs.writeFile(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');
const shot=async(name)=>{
  const file=name+'.png';
  const bytes=await page.screenshot({path:path.join(out,file),fullPage:name.startsWith('05-'),timeout:10000});
  const uses=[];
  for(const element of await page.locator('svg use').all()){
    uses.push({id:await element.getAttribute('id'),href:await element.getAttribute('href'),
      visible:await element.isVisible(),box:await element.boundingBox()});
  }
  const buttons=[];
  for(const button of await page.getByRole('button').all())buttons.push({text:await button.innerText(),enabled:await button.isEnabled()});
  result.steps.push({name,file,wallSeconds:seconds(),bytes:bytes.length,sha256:hash(bytes),uses,buttons});
  await save();
};
try{
  server=await startServer();
  const launched=await launchBrowser(process.env.BROWSER_EXECUTABLE);browser=launched.browser;
  if(launched.module!==process.env.PLAYWRIGHT_MODULE)throw new Error('Unexpected runtime fallback');
  result.runtime={node:process.version,browser:browser.version(),launch:launched.launchOptions};
  timer=setTimeout(()=>{result.deadlineExceeded=true;void browser.close().catch(()=>{});},60000);
  context=await browser.newContext({viewport:result.viewport,serviceWorkers:'block'});
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.origin===server.url||url.protocol==='data:')await route.continue();
    else{result.externalRequests.push(url.href);await route.abort();}
  });
  page=await context.newPage();page.setDefaultTimeout(8000);
  page.on('pageerror',e=>result.pageErrors.push(e.message));
  page.on('console',m=>{if(['error','warning'].includes(m.type()))result.consoleWarnings.push({type:m.type(),text:m.text()});});
  await page.goto(server.url+'/tracks/art/studies/a11-content-first/',{waitUntil:'load'});
  await shot('01-doorway');
  await page.getByRole('button',{name:'按约定移走',exact:true}).click();
  await shot('02-reserved');
  await page.getByRole('button',{name:'留下数字副本',exact:true}).click();
  await shot('03-copy');
  await page.getByRole('button',{name:'重新开始小样',exact:true}).click();
  await shot('04-restart');
  await page.setViewportSize({width:375,height:900});
  await shot('05-mobile');
  const expected=[[true,false],[false,true],[true,true],[true,false],[true,false]];
  result.visibleGeometrySequence=result.steps.every((step,index)=>
    ['bench-shop','bench-reserved'].every((id,column)=>{
      const element=step.uses.find(item=>item.id===id);
      return element?.href==='#bench-definition'&&element.visible===expected[index][column];
    }));
  result.sourceUnchanged=hash(await fs.readFile(path.join(here,'index.html')))===result.source.sha256;
  if(!result.visibleGeometrySequence||!result.sourceUnchanged||result.pageErrors.length||result.externalRequests.length||result.deadlineExceeded)throw new Error('Inspection condition failed');
  result.status='completed_ui_sequence';
}catch(error){result.status='failed';result.failure={message:error.message,stack:error.stack};process.exitCode=1;}
finally{
  clearTimeout(timer);
  if(context){await context.close().then(()=>result.closed.context=true,e=>result.closed.context=e.message);}
  if(browser){await browser.close().then(()=>result.closed.browser=true,e=>result.closed.browser=e.message);}
  if(server){await server.close().then(()=>result.closed.server=true,e=>result.closed.server=e.message);}
  result.wallSeconds=seconds();await save();
  console.log(JSON.stringify({status:result.status,seconds:result.wallSeconds,steps:result.steps.length,errors:result.pageErrors,console:result.consoleWarnings,closed:result.closed}));
}
