import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
const here=path.dirname(fileURLToPath(import.meta.url));
const src=await fs.readFile(path.join(here,'grid.js'),'utf8');
const r=.14,centers=[[-r,0,0],[0,0,0],[r,0,0],[r,0,0],[r+Number.EPSILON,0,0],[-3*r,-2*r,r]];
for(let i=0;i<181;i++)centers.push([Math.sin(.281*i)*.52,Math.cos(.417*i)*.67,Math.sin(.197*i)*.22]);
const queries=[...centers.slice(0,22),[0,0,0],[100,100,100],[-100,0,0]];
const context=vm.createContext({sceneGauss:centers.map(p=>({p})),P:{spreadIgnR:r},performance,Uint8Array,Int32Array,Math});
vm.runInContext(src+'\nfunction t116VisitTracked(...x){return t116VisitRaw(...x);}',context);
const begin=vm.runInContext('t116Begin',context),index=vm.runInContext('t116Grid',context),remove=vm.runInContext('t116Remove',context);
begin(false);
let checks=0;
for(const subset of [null,Array.from({length:centers.length},(_,i)=>i).filter(i=>i%3===0)]){
  const sb={state:new Uint8Array(centers.length)};sb.state[6]=2;
  const g=index(sb,subset),allowed=new Set(subset??centers.map((_,i)=>i));
  const inspect=()=>{
    for(const p of queries){
      const expected=[];
      centers.forEach((c,i)=>{
        const x=c[0]-p[0],y=c[1]-p[1],z=c[2]-p[2],dd=x*x+y*y+z*z;
        if(allowed.has(i) && !sb.state[i] && dd<=r*r)expected.push([i,Math.sqrt(dd)]);
      });
      const got=[];g.walk(g,p,r,(i,d)=>got.push([i,d]));got.sort((a,b)=>a[0]-b[0]);
      assert.deepEqual(got,expected);checks++;
    }
  };
  inspect();
  // The sitewise operator can remove its current bucket item while evaluating it.
  g.walk(g,[0,0,0],r,i=>{sb.state[i]=1;remove(g,i);});
  inspect();
  for(let i=1;i<centers.length;i+=5){sb.state[i]=1;remove(g,i);}
  inspect();
}
console.log(JSON.stringify({queries:checks,sites:centers.length,duplicate_centers:true,inclusive_radius:true}));
