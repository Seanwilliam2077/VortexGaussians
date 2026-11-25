// Stress possible rank changes and clipping at the shared hot-sample cap.
// The reference actually moves each particle, compacts survivors, samples and heats.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const native=fs.readFileSync(path.resolve(here,'../../../../demo/index.html'),'utf8');
const piece=(a,b)=>native.slice(native.indexOf(a),native.indexOf(b,native.indexOf(a)+1));
const code=piece('const VPM_QX0=','\n')+'\n'+piece('function vpmMorton(', '// 节点: ndF stride');
const wx=2, wy=3, dt=1/60, prog=fs.readFileSync(path.join(here,'estimate.js'),'utf8');
const make=new Function('sceneGauss','P','sceneBurnState','layers',
  code+'\nconst WX=2,WY=3;const worldToSrc=(x,y,z)=>[x,y,z];\n'+prog+'\nreturn t91Estimate;');
const morton=new Function(code+'\nreturn vpmMorton;')();
let seed=0x534947, possibleCulls=0, observedCulls=0, capReached=0;
const random=()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};
const summary={yes:0,no:0,abstain:0,gasSupportedYes:0};
for(let trial=0;trial<160;trial++){
  const P={solver:'vpm',dimMode:'layer',simLayers:3,layers:3,sliceMode:'world',emitterOn:false,
    spreadOn:true,spreadFlameHeat:true,sceneScale:1,sceneYaw:0,scenePitch:0,cool:1.2,
    spreadHeat:2.2,spreadIgnR:.14,spreadIgnH:1,spreadSampleCap:1+trial%13,sliceDepth:.12};
  const center=trial%2===0 ? 1.375 : 0.3, baseY=trial%3===0 ? 2.974 : 1.4;
  const layers=Array.from({length:3},(_,idx)=>({idx,ps:Array.from({length:20+trial%37},(_,i)=>({
    x:center+(i%3===0?0:(random()-.5)*.18), y:baseY+(i%3===0?0:(random()-.5)*.14),
    T:i%8===0?.04:random()<.34?.43:.8+random()*.19, d:i%16===0?.029:.9}))}));
  const sites=Array.from({length:4},()=>({p:[center+(random()-.5)*.05,baseY+(random()-.5)*.04,0]}));
  const sb={state:[0,0,0,0],fuel:[1,1,1,1],h:Float32Array.from(sites,()=>
    trial%4===0?.72+random()*.13 : trial%4===1?.98+random()*.02 : 1.006+(random()-.5)*.08)};
  const guessed=make(sites,P,sb,layers)([0,1,2,3],dt);
  summary[guessed.decision]++;
  if(guessed.decision==='yes' && Math.fround(sb.h[guessed.witness]*(1-dt*.35))<1) summary.gasSupportedYes++;
  for(let alternative=0;alternative<24;alternative++){
    const heat=sb.h.slice();
    let selected=0;
    for(const l of layers){
      const ord=l.ps.map((p,i)=>({p,i,key:morton(p.x,p.y)})).sort((a,b)=>a.key-b.key||a.i-b.i);
      const survivors=[];
      for(const {p} of ord){
        const angle=random()*Math.PI*2, speed=4*random();
        const x=p.x+dt*Math.fround(speed*Math.cos(angle)), y=p.y+dt*Math.fround(speed*Math.sin(angle));
        const T=p.T-dt*P.cool*p.T*p.T, d=p.d*(1-dt*.3);
        if(T>.04 && d>.03 && (Math.abs(Math.abs(p.x)-wx*.7)<dt*4 || Math.abs(p.y-wy)<dt*4))possibleCulls++;
        if(!(T>.04 && d>.03 && Math.abs(x)<wx*.7 && y<wy)){observedCulls++;continue;}
        survivors.push({x,y,T});
      }
      for(let i=0;i<survivors.length;i+=7){
        const p=survivors[i];
        if(p.T<.55 || selected>=P.spreadSampleCap)continue;
        selected++;
        for(let j=0;j<sites.length;j++){
          const q=sites[j].p, dx=q[0]-p.x,dy=q[1]-p.y,dz=q[2]-(l.idx/2-.5)*P.sliceDepth;
          const d2=dx*dx+dy*dy+dz*dz;
          if(d2<=P.spreadIgnR*P.spreadIgnR)heat[j]+=dt*P.spreadHeat*p.T*(1-Math.sqrt(d2)/P.spreadIgnR);
        }
      }
    }
    if(selected===P.spreadSampleCap)capReached++;
    const lit=Array.from(heat,h=>Math.fround(h*(1-dt*.35))>=1);
    if(guessed.decision==='yes')assert(lit[guessed.witness]);
    if(guessed.decision==='no')assert(!lit.some(Boolean));
  }
}
assert(summary.gasSupportedYes>0 && summary.no>0 && summary.abstain>0 && capReached>0 && possibleCulls>0);
console.log({trials:160,displacements_per_trial:24,possibleCulls,observedCulls,capReached,summary});
