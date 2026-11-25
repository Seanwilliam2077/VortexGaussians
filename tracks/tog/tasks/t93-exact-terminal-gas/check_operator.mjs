// Deterministic unit stress for the terminal selection/threshold operator.
// The supplied field is synthetic. Native field accuracy is checked on the actual scene benchmarks.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
const template = await readFile(new URL('terminal.js', import.meta.url),'utf8');
const code = template.replace('/* NATIVE_FIELD */',
  'const p=layer.ps[pl.ord[i]]; pl.UX[i]=p.vx; pl.UY[i]=p.vy;');
let state = 0x2387139;
function random() {
  state = (Math.imul(1664525,state) + 1013904223) >>> 0;
  return state/4294967296;
}
const dt=1/60, radius=.14, width=2, height=3;
const sum={cases:0, yes:0, no:0, empty:0, ambiguous:0, spatial_skips:0, expected_field_calls:0, selective_field_calls:0};
function context(seed) {
  const scene = seed.xyz.map(p=>({p}));
  const sb={state:Uint8Array.from(seed.states), fuel:Float32Array.from(seed.fuel),
    h:Float32Array.from(seed.heat)};
  const layers=seed.layers.map((ps,idx)=>({ps,idx,t:0}));
  const pools=layers.map(l=>({n:l.ps.length,ord:seed.order[l.idx], UX:new Float32Array(l.ps.length), UY:new Float32Array(l.ps.length)}));
  const P={dimMode:'layer',solver:'vpm',sliceMode:'world',simLayers:3,sceneScale:1,sceneYaw:0,scenePitch:0,
    sceneOffX:0,sceneOffZ:0,sceneLift:0,spreadOn:true,spreadFlameHeat:true,embers:false,filament:false,cool:1.2,
    spreadIgnR:radius,spreadHeat:2.2,spreadIgnH:1,spreadSampleCap:seed.cap,sliceDepth:.48};
  function hashQuery(pos,r,visit) {
    scene.forEach(({p},i)=>{
      const dx=p[0]-pos[0],dy=p[1]-pos[1],dz=p[2]-pos[2];
      const d2=dx*dx+dy*dy+dz*dz;
      if(d2<=r*r) visit(i,Math.sqrt(d2));
    });
  }
  return {layers,sceneGauss:scene,sceneBurnState:sb,vpmPools:pools,P,WX:width,WY:height,sceneInfo:{center:[0,0,0]},
    cv:{width:10,height:10},simTime:0,updateCam(){},vpmPrepare(){},evenMask:()=>[true,true,true],worldToSrc:(x,y,z)=>[x,y,z],hashQuery};
}

function oracle(c, ids) {
  const {sceneBurnState:sb,P}=c;
  let sampled=0;
  for(const layer of c.layers) {
    const survivors=[];
    for(const i of c.vpmPools[layer.idx].ord) {
      const p=layer.ps[i], T=p.T-dt*P.cool*p.T*p.T, d=p.d*(1-dt*.3);
      const x=p.x+dt*Math.fround(p.vx), y=p.y+dt*Math.fround(p.vy);
      if(T>.04 && y<height && Math.abs(x)<width*.7 && d>.03) survivors.push({x,y,T});
    }
    for(let i=0;i<survivors.length;i+=7) {
      const p=survivors[i];
      if(p.T<.55 || sampled>=P.spreadSampleCap) continue;
      sampled++;
      c.hashQuery([p.x,p.y,(layer.idx/2-.5)*P.sliceDepth],radius,(j,d)=>{
        if(sb.state[j]===0) sb.h[j]+=dt*P.spreadHeat*p.T*(1-d/radius);
      });
    }
  }
  return ids.find(id=>sb.state[id]===0 && sb.fuel[id]>0 && sb.h[id]>0 && Math.fround(sb.h[id]*(1-dt*.35))>=1) ?? null;
}
for(let k=0;k<120;k++) {
  const lengths=[52,63,49], cap=[0,1,3,11,160][k%5];
  const seed={layers:[],order:[],xyz:[],states:[],fuel:[],heat:[],cap};
  for(const n of lengths) {
    const ps=[];
    for(let i=0;i<n;i++) {
      const speed=4*random(), angle=random()*2*Math.PI;
      ps.push({x:i%6===0 ? 1.4+(random()-.5)*.14 : (random()-.5)*2.9,
        y:i%4===0 ? 3+(random()-.5)*.14 : random()<.5 ? .4+(random()-.5)*.12 : 2.9,
        vx:speed*Math.cos(angle), vy:speed*Math.sin(angle),
        T:[.035,.56,.561,.75,.99][Math.floor(random()*5)],d:random()<.07?.03:.9});
    }
    const order=Array.from({length:n},(_,i)=>i);
    for(let i=n-1;i>0;i--) { const j=Math.floor(random()*(i+1)); [order[i],order[j]]=[order[j],order[i]]; }
    seed.layers.push(ps);seed.order.push(order);
  }
  for(let j=0;j<90;j++) {
    seed.xyz.push([(random()-.5)*.5,.4+(random()-.5)*.15,(Math.floor(random()*3)-1)*.24]);
    seed.states.push(j%17===3?1:0);seed.fuel.push(j%13===5?0:1);
    seed.heat.push(.985+(random()-.5)*.04);
  }
  const ids=seed.heat.map((_,i)=>i).filter(i=>i%2===0 && k%13!==0);
  const ref=context(seed), truth=oracle(ref,ids);
  if(!ids.length) sum.empty++;
  if(truth===null) sum.no++; else sum.yes++;
  for(const mode of ['spatial','rank','all']) {
    const ctx=context(seed); vm.runInNewContext(code,ctx);
    const answer=ctx.t93TerminalQuery(ids,dt,mode);
    assert.equal(answer.witness,truth);
    assert.equal(answer.decision,truth===null?'no':'yes');
    for(const i of ids) if(seed.states[i]===0 && seed.fuel[i]>0)
      assert.equal(ctx.sceneBurnState.h[i],ref.sceneBurnState.h[i], 'per-site binary32 heat mismatch');
    if(mode==='spatial'){
      sum.ambiguous+=answer.counts.uncertain_boundary;sum.spatial_skips+=answer.counts.spatially_excluded;
      sum.selective_field_calls+=answer.counts.field_calls;
    } else if(mode==='all') sum.expected_field_calls+=answer.counts.field_calls;
  }
  sum.cases++;
}
assert(sum.yes>0 && sum.no>0 && sum.empty>0 && sum.ambiguous>0 && sum.spatial_skips>0);
console.log(JSON.stringify(sum));
