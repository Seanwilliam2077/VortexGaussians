import fs from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { startServer, launchBrowser, repoRoot, researchRoot } from './lib/runtime.mjs';

// Same physical seven-point arrangement encoded in four source frames. The
// expected kernel is evaluated from observed WORLD points, independently of
// stepSpread's source-space directional expression. No rendering/physics claim.
const cases = [
  { id: 'identity', pitch: 0, yaw: 0, scale: 1 },
  { id: 'source-z-up', pitch: -Math.PI / 2, yaw: .41, scale: 1 },
  { id: 'source-minus-z-up', pitch: Math.PI / 2, yaw: -.23, scale: 1 },
  { id: 'oblique-scaled', pitch: .62, yaw: .37, scale: 1.3 },
];
const offsets = [[0,0,0],[0,.05,0],[0,-.05,0],[.05,0,0],[-.05,0,0],[0,0,.05],[0,0,-.05]];
function fixture(c) {
  const cy=Math.cos(c.yaw),sy=Math.sin(c.yaw),cp=Math.cos(c.pitch),sp=Math.sin(c.pitch);
  const Q=[[cy,sy*sp,sy*cp],[0,cp,-sp],[-sy,cy*sp,cy*cp]];
  const fields=['x','y','z','f_dc_0','f_dc_1','f_dc_2','opacity','scale_0','scale_1','scale_2','rot_0','rot_1','rot_2','rot_3'];
  const header=Buffer.from('ply\nformat binary_little_endian 1.0\nelement vertex 7\n'+fields.map(k=>'property float '+k+'\n').join('')+'end_header\n');
  const data=Buffer.alloc(7*14*4);
  offsets.forEach((p,i)=>{
    const source=Array.from({length:3},(_,j)=>Q.reduce((a,row,k)=>a+row[j]*p[k],0)/c.scale);
    [...source,0,0,0,2,-5,-5,-5,1,0,0,0].forEach((v,j)=>data.writeFloatLE(v,(i*14+j)*4));
  });
  return Array.from(Buffer.concat([header,data]));
}
const args=process.argv.slice(2);
if(args.length && (args.length!==2 || args[0]!=='--out')) throw Error('Usage: node research/scene-up-regression.mjs [--out NEW_DIRECTORY]');
const out=args.length ? path.resolve(args[1]) : path.join(researchRoot,'runs','scene-up-'+Date.now());
await fs.mkdir(path.dirname(out),{recursive:true});await fs.mkdir(out);
const demoPath=path.join(repoRoot,'demo/index.html');
const fingerprint=async()=>createHash('sha256').update(await fs.readFile(demoPath)).digest('hex');
const report={startedAtUTC:new Date().toISOString(),sourceSHA256:await fingerprint(),node:process.version,
  runs:[],failures:[],scope:'One-step world-up graph coordinate regression; not combustion validation.'};
const server=await startServer();let browser;
try {
  const launched=await launchBrowser();browser=launched.browser;report.browser=browser.version();
  for(const c of cases) {
    const page=await browser.newPage({viewport:{width:480,height:360}}),errors=[];
    page.setDefaultTimeout(30000);page.on('pageerror',e=>errors.push(e.message));
    await page.goto(server.url+'/demo/?embed=1&orbit=0',{waitUntil:'load'});
    const result=await page.evaluate(({c,bytes})=>{
      const d=window.__demo,loaded=d.loadPLY(Uint8Array.from(bytes).buffer);
      d.research.reset(11,{...d.P,sceneScale:c.scale,scenePitch:c.pitch,sceneYaw:c.yaw,
        sceneLift:.5,sceneOffX:0,sceneOffZ:0,paused:true,orbit:false,box:false,spreadOn:true,
        emitterOn:false,spreadFlameHeat:false,spreadSceneFeed:false,rate:0,embers:false,
        spreadR:.2,spreadRate:3,spreadIgnH:100,spreadBurnT:6,spreadClockMode:'legacy'});
      const ignited=d.ignite(0,.5,0,.005),before=d.research.snapshot({detail:true});
      d.research.step(1,.1);
      return {loaded,ignited,before,after:d.research.snapshot({detail:true}),glError:d.gl.getError()};
    },{c,bytes:fixture(c)});
    const bad=[];
    if(errors.length||result.glError||result.ignited!==1||result.after.particles.count!==0||
      result.loaded.kept!==7||result.after.scene.burning!==1)bad.push('execution contract');
    for(let i=0;i<7;i++) {
      const p=result.before.points[i].position,target=offsets[i].map((v,k)=>v+(k===1?.5:0));
      if(p.some((v,k)=>Math.abs(v-target[k])>1e-8))bad.push('world position '+i);
      if(i) {
        const delta=p.map((v,k)=>v-result.before.points[0].position[k]);
        const expected=Math.fround(.1*3*(1-Math.hypot(...delta)/.2)*(1+2.2*Math.max(0,delta[1]/.2)));
        if(Math.abs(result.after.points[i].heat-expected)>2e-7)bad.push('world-up kernel '+i);
      }
    }
    report.runs.push({case:c,errors,...result,failures:bad});
    report.failures.push(...bad.map(s=>c.id+': '+s));await page.close();
  }
  report.sourceAfterSHA256=await fingerprint();
  if(report.sourceAfterSHA256!==report.sourceSHA256)report.failures.push('Source changed during test');
} catch(e) { report.failures.push(e.stack||e.message); }
finally { if(browser)await browser.close();await server.close(); }
report.finishedAtUTC=new Date().toISOString();report.passed=report.failures.length===0;
await fs.writeFile(path.join(out,'result.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,cases:report.runs.length,failures:report.failures,out}));
if(!report.passed)process.exitCode=1;
