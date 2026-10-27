// A04: one uncut, isolated public-UI recording; no demo API calls or notes.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { startServer, launchBrowser, repoRoot } from '../../../../research/lib/runtime.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const outIndex = args.indexOf('--out');
const out = path.resolve(outIndex < 0 ? path.join(here, 'run-01') : args[outIndex+1]);
const plan = { scope: 'Agent-authored automated demonstration draft, not author rehearsal/audience evidence/art-effect validation',
  viewport: { width: 1280, height: 800 }, attempts: 1, ignitionActions: 1, simulatedSeconds: 1,
  resetActions: 1, receiptHide: 1, receiptShow: 1, notesWritten: 0, wallLimitMs: 58000,
  source: 'synthetic test_scene.ply; not a captured memory', out };
if (!args.includes('--execute')) { console.log(JSON.stringify(plan, null, 2)); process.exit(0); }
if (!process.env.PLAYWRIGHT_MODULE || !process.env.BROWSER_EXECUTABLE) throw new Error('Explicit existing PLAYWRIGHT_MODULE and BROWSER_EXECUTABLE required; no installation or launch fallback.');
const relativeOut = path.relative(here, out);
if (relativeOut.startsWith('..') || path.isAbsolute(relativeOut) || relativeOut === '') throw new Error('Output must be a fresh child of this study directory.');
await fs.mkdir(out, { recursive: false });
const began = performance.now();
const wall = () => (performance.now()-began)/1000;
const names = ['tracks/art/index.html', 'tracks/art/art.js', 'tracks/art/art.css', 'demo/index.html', 'static/test_scene.ply', 'research/lib/runtime.mjs',
  'tracks/art/studies/a04-automated-score/record.mjs', 'tracks/art/studies/a04-automated-score/PROTOCOL.md'];
const hash = b => createHash('sha256').update(b).digest('hex');
const hashes = async () => Object.fromEntries(await Promise.all(names.map(async n=>[n,hash(await fs.readFile(path.join(repoRoot,n)))])));
const r = { schema: 'a04-automated-score-v1', createdUTC: new Date().toISOString(), plan, actions: [], snapshots: [], errors: [], console: [],
  resourcesClosed: {}, sourceBefore: await hashes(), runtime: { node:process.version, module:process.env.PLAYWRIGHT_MODULE, executable:process.env.BROWSER_EXECUTABLE },
  dependencyMetadataProbe: { scope: 'Read-only before recording', error: 'Old playwright-core/lib/server/registry/index.js layout unavailable in installed1.62.1; no browser or recording was started by this metadata query.', installationPerformed:false } };
let server, browser, context, page, video, watchdog;
const publish = async () => fs.writeFile(path.join(out,'result.json'), JSON.stringify(r,null,2)+'\n');
const action = async (name, fn) => { const e={name,startedWallSeconds:wall()};r.actions.push(e);await publish();try{await fn();e.completed=true;}finally{e.endedWallSeconds=wall();await publish();} };
const visible = async () => ({status:await page.locator('#status').innerText(),time:await page.locator('#time-label').innerText(),
  burning:await page.locator('#burning-count').innerText(),charred:await page.locator('#char-count').innerText(),
  scene:await page.locator('#scene-count').innerText(),notes:await page.locator('#note-count').innerText()});
const shot = async (name) => { const p=path.join(out,name+'.png');await page.screenshot({path:p});r.snapshots.push({name,wallSeconds:wall(),visible:await visible(),file:name+'.png'});await publish(); };
const waitText = async (selector,text,ms) => {const end=performance.now()+ms;while(performance.now()<end){if((await page.locator(selector).innerText()).includes(text))return;await page.waitForTimeout(100);}throw new Error(`Visible UI timeout ${selector}: ${text}`);};
try {
  server=await startServer();r.server={url:server.url,scope:'fresh ephemeral loopback; no user8137 server'};
  const launch=await launchBrowser(process.env.BROWSER_EXECUTABLE);browser=launch.browser;r.browser=browser.version();r.launch=launch.launchOptions;
  watchdog=setTimeout(()=>{r.watchdogFired=true;void browser.close();},plan.wallLimitMs);
  context=await browser.newContext({viewport:plan.viewport, recordVideo:{dir:path.join(out,'video'),size:plan.viewport}});
  r.context={persistent:false,storageStateProvided:false,recordVideo:true};
  page=await context.newPage();video=page.video();page.setDefaultTimeout(12000);
  page.on('pageerror',e=>r.errors.push({wallSeconds:wall(),message:e.message,stack:e.stack}));
  page.on('console',m=>{if(['warning','error'].includes(m.type()))r.console.push({wallSeconds:wall(),type:m.type(),text:m.text()});});
  r.recordingStartedWallSeconds=wall();await publish();
  await action('open unchanged art page',()=>page.goto(server.url+'/tracks/art/',{waitUntil:'load',timeout:12000}));
  await shot('01-opening');await page.waitForTimeout(1800);
  await action('load synthetic example once',()=>page.locator('#start-example').click());
  await waitText('#status','45,808 / 45,808',16000);await page.locator('#viewer').scrollIntoViewIfNeeded();
  await shot('02-loaded');await page.waitForTimeout(1800);
  await action('switch intervene',()=>page.locator('[data-stage=intervene]').click());
  await action('ignite once at existing defaults',()=>page.locator('#ignite').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();await shot('03-ignited');await page.waitForTimeout(1600);
  await action('request exactly one simulated second',()=>page.locator('#advance').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();await waitText('#status','本段推进完成',18000);
  await shot('04-after-one-second');r.completedSimulation=await visible();
  if(r.completedSimulation.time!=='模拟时间 1.00 s')throw new Error('Visible simulated time did not equal1.00s');
  await page.waitForTimeout(3000);
  await action('switch revisit',()=>page.locator('[data-stage=revisit]').click());
  await action('reset once',()=>page.locator('#reset').click());
  await page.locator('#viewer').scrollIntoViewIfNeeded();await shot('05-reset-scene');
  r.afterReset=await visible();if(r.afterReset.time!=='模拟时间 0.00 s'||r.afterReset.burning!=='0'||r.afterReset.charred!=='0')throw new Error('Visible reset counters mismatch');
  await page.waitForTimeout(2000);
  await page.locator('.reset-receipt').scrollIntoViewIfNeeded();await shot('06-receipt-expanded');await page.waitForTimeout(3000);
  r.receipt={time:await page.locator('#receipt-time').innerText(),burning:await page.locator('#receipt-burning').innerText(),charred:await page.locator('#receipt-charred').innerText()};
  await action('hide receipt once',()=>page.locator('#receipt-toggle').click());await shot('07-receipt-hidden');await page.waitForTimeout(1500);
  await action('reopen receipt once',()=>page.locator('#receipt-toggle').click());await shot('08-receipt-reopened');await page.waitForTimeout(3000);
  r.notesUntouched=(await page.locator('#note-count').innerText())==='0 条记录' &&
    (await page.locator('#context').inputValue())==='' && (await page.locator('#choice').inputValue())==='' && (await page.locator('#observation').inputValue())==='';
  if(!r.notesUntouched)throw new Error('Unexpected nonempty notes; no form writes were authorized');
  if(r.errors.length)throw new Error('Page errors observed; see full record');
  r.status='completed';
} catch(e) {
  r.status='failed';r.failure={wallSeconds:wall(),message:e.message,stack:e.stack};process.exitCode=1;
  if(page&&!page.isClosed()){try{await page.screenshot({path:path.join(out,'failure-visible.png'),timeout:3000});}catch(se){r.failureScreenshotError=se.message;}}
} finally {
  clearTimeout(watchdog);
  if(context){try{await context.close();r.resourcesClosed.context=true;}catch(e){r.resourcesClosed.contextError=e.message;}}
  if(browser){try{await browser.close();r.resourcesClosed.browser=true;}catch(e){r.resourcesClosed.browserError=e.message;}}
  if(server){try{await server.close();r.resourcesClosed.server=true;}catch(e){r.resourcesClosed.serverError=e.message;}}
  if(video){try{const p=await video.path();const b=await fs.readFile(p);r.video={file:path.relative(out,p).replaceAll('\\','/'),bytes:b.length,sha256:hash(b),commitEligible:b.length<=20*1024*1024,durationSeconds:null,durationScope:'Not yet parsed; wall time is not container duration'};}catch(e){r.videoError=e.message;}}
  r.sourceAfter=await hashes();r.sourcesUnchanged=JSON.stringify(r.sourceBefore)===JSON.stringify(r.sourceAfter);
  if(!r.sourcesUnchanged){r.status='failed';process.exitCode=1;}
  r.totalWallSeconds=wall();r.noRetry=true;await publish();
  console.log(JSON.stringify({status:r.status,wallSeconds:r.totalWallSeconds,video:r.video||null,failure:r.failure||null,sourcesUnchanged:r.sourcesUnchanged,out}));
}
