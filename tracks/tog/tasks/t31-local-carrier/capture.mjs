// One fixed state acquisition. Importing this file does not launch the demo.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import { gzipSync } from 'node:zlib';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../..');
const out = path.join(here, 'run-01');
const browserExecutable = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const playwrightPath = 'C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const need = (ok, message) => { if (!ok) throw new Error(message); };
const finite = value => typeof value === 'number' && Number.isFinite(value);
const close = (a, b) => Math.abs(a-b) <= 1e-10 * Math.max(1, Math.abs(a), Math.abs(b));
const clamp = x => Math.max(0, Math.min(1, x));
const smooth = (a, b, x) => { const u = clamp((x-a)/(b-a)); return u*u*(3-2*u); };
const mix = (a, b, w) => a.map((x, i) => x*(1-w)+b[i]*w);

export function color(p, params) {
  if (params.mode === 'smoke') return mix([.02,.02,.026], [.17,.17,.19], clamp(p.d));
  need(params.mode === 'fire', 'Unexpected color mode');
  const t = clamp(p.T);
  let c = mix([.05,.012,0], [.6,.05,.012], smooth(0,.28,t));
  c = mix(c, [1,.32,.04], smooth(.22,.5,t));
  c = mix(c, [1,.72,.22], smooth(.46,.74,t));
  c = mix(c, [1,.96,.86], smooth(.7,1,t));
  return c.map(x => x*params.emis*(.25+.85*t));
}

export function lift(snapshot, expectedFrame, spec) {
  const {params:p, config:c, physicsParticles:physics, renderParticles:render} = snapshot;
  need(snapshot.frame === expectedFrame && close(snapshot.time, expectedFrame*spec.dt), 'Wrong frame/time');
  need(c.mode === 'shared3d' && c.nSim === 600 && c.nRender === 600 && c.renderSeed === 101, 'Wrong mode/budget/seed');
  need(c.optics.radius === .045 && c.optics.tau === .2 && p.layers === 3 && p.rate === 180, 'Wrong fixed recipe');
  need(p.orbit === false && p.sceneOn === false && p.box === false && p.embers === false && p.flicker === false, 'Unexpected scene extras');
  need(p.camDist > 0 && finite(p.camDist) && finite(p.camElev) && Math.abs(p.camElev) < Math.PI/2 && p.fov > 0 && p.fov < Math.PI && finite(p.emis), 'Invalid camera/color params');
  need(!snapshot.render.overridden && snapshot.render.opticalWeight === 1, 'Unexpected rendering override');
  need(Array.isArray(physics) && Array.isArray(render) && physics.length > 0 && physics.length <= 600 && physics.length === render.length, 'Missing/incomplete particles');
  need(physics.length === snapshot.physics.count && render.length === snapshot.render.count, 'Declared count mismatch');
  let density=0, temperature=0, optical=0;
  const h = c.optics.radius/Math.sqrt(6);
  const primitives = render.map((particle, i) => {
    const {id, ...copy} = particle;
    need(JSON.stringify(copy) === JSON.stringify(physics[i]), 'Shared render/physics mismatch');
    need(['x','y','z','T','d'].every(k => finite(particle[k])) && particle.d >= 0, 'Invalid particle');
    const w = particle.weight === undefined ? 1 : particle.weight;
    need(finite(w) && w >= 0, 'Invalid optical weight');
    const k = Math.max(0, w*c.optics.tau*particle.d);
    const rgb = color(particle, p);
    need(finite(k) && k >= 0 && rgb.every(x => finite(x) && x >= 0), 'Invalid lifted Gaussian');
    density += particle.d; temperature += particle.T; optical += w*particle.d;
    return {source_index:i, mu:[particle.x,particle.y,particle.z], h, k, color:rgb};
  });
  need(close(density,snapshot.physics.densitySum) && close(density,snapshot.render.densitySum), 'Density aggregate mismatch');
  need(close(temperature,snapshot.physics.temperatureSum) && close(temperature,snapshot.render.temperatureSum), 'Temperature aggregate mismatch');
  need(close(optical,snapshot.render.opticalDensitySum) && optical > 0, 'Optical aggregate mismatch');
  return {frame:expectedFrame, time:snapshot.time, physical_hash:snapshot.physicalHash,
    camera_params:{camDist:p.camDist,camElev:p.camElev,fov:p.fov}, mode:p.mode, emis:p.emis,
    primitives, checks:{complete_state:true, shared_arrays:true, aggregate_agreement:true, finite_lift:true},
    statistics:{count:primitives.length, sum_k:primitives.reduce((s,g)=>s+g.k,0),
      integrated_3d_strength:primitives.reduce((s,g)=>s+2*Math.PI*g.k*h*h,0),
      max_color:Math.max(...primitives.flatMap(g=>g.color)),
      min_color:Math.min(...primitives.flatMap(g=>g.color))}};
}

async function saveGzip(name, value) {
  const raw = Buffer.from(JSON.stringify(value)+'\n');
  need(raw.length <= 20*1024*1024, 'Artifact exceeds fixed raw byte cap');
  const compressed = gzipSync(raw);
  await fs.writeFile(path.join(out,name), compressed, {flag:'wx'});
  return {path:name, bytes:compressed.length, sha256:sha(compressed), raw_bytes:raw.length, raw_sha256:sha(raw)};
}

async function main() {
  // The supervisor consumes the sole attempt before spawning this worker.
  await fs.readFile(path.join(out,'attempt.json'));
  await fs.writeFile(path.join(out,'worker-start.json'),JSON.stringify({started_utc:new Date().toISOString()})+'\n',{flag:'wx'});
  const started = new Date().toISOString(), tic = performance.now();
  let browser, server, expired=false, frames, spec, definition, freeze;
  const errors=[], blockedRequests=[], stepReceipts=[], snapshots=[];
  const receipt = {schema:'t31-capture-v1', started_utc:started, invocation:1, status:'incomplete',
    browser_launches:0, resets:0, simulation_steps:0, snapshot_frames:[], partial_snapshots:[], integrations:0, image_outputs:0,
    installations:0, external_source_acquisitions:0, retries:0};
  const check = () => need(!expired,'90-second acquisition deadline');
  const deadline=setTimeout(() => {
    expired=true;
    // Awaited work is not abandoned: closing the browser interrupts pending page calls.
    // A launch that resolves later is caught by check() and closed in finally.
    if(browser) void browser.close().catch(error=>{receipt.deadline_close_error=String(error);});
  },90000);
  const verify = async () => {
    for (const item of freeze.artifacts) {
      const bytes = await fs.readFile(path.join(root,item.path));
      need(bytes.length === item.bytes && sha(bytes) === item.sha256, `Frozen source changed: ${item.path}`);
    }
  };
  try {
    const frozenBytes=await fs.readFile(path.join(here,'freeze.json'));
    receipt.freeze_sha256=sha(frozenBytes); freeze=JSON.parse(frozenBytes);
    await verify(); check();
    const require = createRequire(import.meta.url);
    const playwright = require(playwrightPath);
    const runtime = await import(pathToFileURL(path.join(root,'research/lib/runtime.mjs')).href);
    const {P3, p3Config} = await import(pathToFileURL(path.join(root,'research/p3-design.mjs')).href);
    need(P3.frames === 180 && P3.dt === 1/60 && JSON.stringify(P3.captures) === '[90,180]' && P3.width === 256 && P3.height === 192, 'Recipe changed');
    spec=P3;
    definition = {id:'shared-s11',family:'shared',mode:'shared3d',seed:11,repeat:null,renderSeed:101,nRender:600};
      server = await runtime.startServer(root); check();
      receipt.browser_launches++;
      browser = await playwright.chromium.launch({headless:true, executablePath:browserExecutable, timeout:25000});
      check();
      receipt.runtime = {node:process.version, playwright:require(path.join(playwrightPath,'package.json')).version,
        browser:browser.version(), browser_executable:browserExecutable, playwright_module:playwrightPath};
      const page = await browser.newPage({viewport:{width:P3.width,height:P3.height}});
      check();
      page.setDefaultTimeout(25000);
      page.on('pageerror', error => errors.push(error.stack || error.message));
      await page.route('**/*', route => {
        if (new URL(route.request().url()).origin === server.url) return route.continue();
        blockedRequests.push(route.request().url()); return route.abort();
      });
      await page.addInitScript(() => { window.requestAnimationFrame = () => 0; window.cancelAnimationFrame = () => {}; });
      check();
      await page.goto(`${server.url}/demo/?embed=1&orbit=0`, {waitUntil:'load',timeout:25000});
      check();
      await page.waitForFunction(() => window.__demo?.researchP3?.snapshot,null,{polling:100});
      check();
      receipt.graphics = await page.evaluate(() => {
        const gl=window.__demo.gl, ext=gl.getExtension('WEBGL_debug_renderer_info');
        return {user_agent:navigator.userAgent, version:gl.getParameter(gl.VERSION),
          renderer:gl.getParameter(ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER)};
      });
      check();
      receipt.resets++;
      receipt.reset = await page.evaluate(({seed,config,width,height}) => {
        window.__demo.P.paused=true; window.__demo.forceSize(width,height);
        return window.__demo.researchP3.reset(seed,config);
      }, {seed:definition.seed,config:p3Config(definition),width:P3.width,height:P3.height});
      check();
      for (const frame of P3.captures) {
        const count=frame-receipt.simulation_steps;
        const state=await page.evaluate(({n,dt}) => {
          const api=window.__demo.researchP3;
          const step=api.step(n,dt);
          return {step,snapshot:api.snapshot({detail:true})};
        }, {n:count,dt:P3.dt});
        receipt.simulation_steps += count;
        stepReceipts.push(state.step); snapshots.push(state.snapshot); receipt.snapshot_frames.push(frame);
        receipt.partial_snapshots.push(await saveGzip(`frame-${String(frame).padStart(3,'0')}.json.gz`,state));
        check();
      }
      need(errors.length === 0 && blockedRequests.length === 0, 'Browser errors or blocked external requests');
      frames=snapshots.map((s,i)=>lift(s,P3.captures[i],P3));
      check();
  } catch (error) {
    receipt.error = error.stack || error.message;
    process.exitCode=2;
  } finally {
    try { if(browser) await browser.close(); } catch(error) { receipt.browser_cleanup_error=String(error); process.exitCode=2; }
    try { if(server) await server.close(); } catch(error) { receipt.server_cleanup_error=String(error); process.exitCode=2; }
    try {
      // Preserve every returned snapshot, even if a later step or gate failed.
      receipt.raw=await saveGzip('states.json.gz',{schema:'t31-p3-states-v1',definition,dt:spec?.dt,step_receipts:stepReceipts,snapshots});
      check();
      need(!receipt.error && !receipt.browser_cleanup_error && !receipt.server_cleanup_error && errors.length === 0 && blockedRequests.length === 0, 'Final acquisition/cleanup/browser gate failed');
      need(receipt.simulation_steps === 180 && JSON.stringify(receipt.snapshot_frames) === '[90,180]' && frames?.length === 2, 'Incomplete acquisition');
      await verify();
      need(sha(await fs.readFile(path.join(here,'freeze.json'))) === receipt.freeze_sha256, 'Freeze file changed during execution');
      check();
      receipt.post_source_check_pass=true;
      receipt.carrier=await saveGzip('carrier.json.gz',{schema:'t31-authored-isotropic-carrier-v1',
        model_contract:'MODEL.md',width:spec.width,height:spec.height,views:spec.views,background:[0,0,0],
        clip_planes:[.05,50],pixel_convention:'top-down pixel centers',frames});
      check();
      receipt.frames=frames.map(({primitives,...summary})=>summary);
      receipt.status='qualified_authored_input_only';
    } catch(error) {
      receipt.finalization_error=error.stack || error.message; receipt.status='failed'; process.exitCode=2;
    }
    clearTimeout(deadline);
    receipt.browser_errors=errors; receipt.blocked_requests=blockedRequests;
    receipt.finished_utc=new Date().toISOString(); receipt.worker_elapsed_ms=performance.now()-tic;
    receipt.not_a_render_benchmark=true; receipt.independent_replay_verified=false;
    await fs.writeFile(path.join(out,'result.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
    console.log(JSON.stringify({status:receipt.status,frames:receipt.frames?.map(f=>({frame:f.frame,...f.statistics})),worker_elapsed_ms:receipt.worker_elapsed_ms,error:receipt.error}));
  }
}
if (process.argv[2] === '--execute') await main();
