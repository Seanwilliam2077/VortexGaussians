// Regression for the P5b thermal traversal repair. No browser, mutable state files,
// renderer, or prior-result ZIP is required. Mechanical fingerprint comes from
// frozen original demo 56ed450cf18c81ceda59a0f0373c55f73bad7c9e3545d5a7242d462e1e018abf.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import test from 'node:test';
const json=x=>JSON.parse(JSON.stringify(x));
const source=fs.readFileSync(new URL('../../demo/index.html',import.meta.url),'utf8').replaceAll('\r\n','\n');
function make(source){
 const between=(a,b)=>{const i=source.indexOf(a),j=source.indexOf(b,i);assert(i>=0&&j>i);return source.slice(i,j);};
 const kernel=between('const VPM_KGAIN=','const vpmPools='),field=between('function vpmErf(','function stepSimVPM3(');
 const c=vm.createContext({});
 vm.runInContext(`const P={eps:.07,gam:1,layers:3,sliceDepth:1.2};const HX=2/32,HY=3/48;
 ${kernel}\n${field}
 globalThis.query=(input,target,angle,allLeaves,collectStats=true)=>{
  const p=vpm3Ensure(input.length),n=input.length;vpmInvTheta=allLeaves?1e9:1/Math.max(.15,angle);
  for(let i=0;i<n;i++)p.code[i]=vpm3Morton(...input[i].position);vpm3Sort(n);const packed=[];
  for(let i=0;i<n;i++){const q=input[p.ord[i]];
   p.X[i]=q.position[0];p.Y[i]=q.position[1];p.Z[i]=q.position[2];p.AX[i]=q.G[0];p.AY[i]=q.G[1];p.AZ[i]=q.G[2];p.T[i]=q.Tb;p.SG[i]=q.sg;p.scode[i]=p.code[p.ord[i]];
   packed.push({id:q.id,position:[p.X[i],p.Y[i],p.Z[i]],G:[p.AX[i],p.AY[i],p.AZ[i]],Tb:p.T[i],sg:p.SG[i]});
  }
  p.nNodes=0;p.root=n?vpm3Node(0,n,0,VPM_QSIDE,21):-1;
  const self=target.id===null?-1:packed.findIndex(q=>q.id===target.id);if(target.id!==null&&self<0)throw new Error('self missing');
  const query=self<0?target:packed[self],stats=collectStats?{}:null;
  const C3=P.gam*VPM_KGAIN*HX*HY*(P.sliceDepth/P.layers)/(4*Math.PI);
  vpm3FieldAt(...query.position,...query.G,query.Tb,query.sg*query.sg,C3,self,stats);
  return {packed,target:query,selfIndex:self,raw:{...vpm3Out},stats,treeNodes:p.nNodes};
 };
 globalThis.heat=()=>({values:Array.from(vpmF3),scale:VPM_LSC});`,c);
 return c;
}

const candidate=make(source),lut=json(candidate.heat());
const thermalKeys=['S','sT','gx','gxx','gz','gzz'],mechanicalKeys=['ux','uy','uz','sx','sy','sz'];
function reference(r){
 const p=r.target;let S=1,sT=p.Tb,gx=0,gxx=0,gz=0,gzz=0;const terms=[];
 for(let j=0;j<r.packed.length;j++){
  if(j===r.selfIndex)continue;const q=r.packed[j];
  const dx=p.position[0]-q.position[0],dy=p.position[1]-q.position[1],dz=p.position[2]-q.position[2],qq=dx*dx+dy*dy+dz*dz;
  const s2=.5*(p.sg*p.sg+q.sg*q.sg),a=qq*(1/(s2+s2)),index=a<9?(a*lut.scale)|0:null,w=index===null?0:lut.values[index];
  if(w>0){S+=w;sT+=w*q.Tb;gx+=(q.Tb-p.Tb)*(-dx)*w;gxx+=dx*dx*w;gz+=(q.Tb-p.Tb)*(-dz)*w;gzz+=dz*dz*w;}
  terms.push({id:q.id,sourceIndex:j,a,index,weight:w});
 }
 return {raw:{S,sT,gx,gxx,gz,gzz},terms,positiveContributions:terms.filter(t=>t.weight>0).length};
}
function near(a,b,name){assert(Math.abs(a-b)<=1e-12+1e-12*Math.abs(b),`${name}: ${a}, ${b}`);}

const fixtures=[];
const point=(id,position,sg,Tb,G=[.2,-.1,.3])=>({id,position,sg,Tb,G});
for(const uniform of [false,true]){
 const input=[];for(let z=0;z<4;z++)for(let y=0;y<4;y++)for(let x=0;x<4;x++)input.push(point(`h-${x}-${y}-${z}`,[.30+x*.01,.60+y*.01,.30+z*.01],.07,.75));
 const target=point('query',[.50,.615,.315],.07,uniform?.75:.25,[0,0,0]);input.push(target);
 fixtures.push({id:uniform?'missed-uniform':'missed-heterogeneous',family:'missed-support',input,target});
}
const widths=Array.from({length:8},(_,i)=>point('v-'+i,[i*.002,.5+(i%2)*.001,0],i===0?.3:.01,i===0?1:.2,[.1+i*.02,-.1,.2]));
fixtures.push({id:'variable-width-far',family:'variable-width',input:widths,target:point(null,[.5,.5,0],.01,.25,[0,0,0])},
 {id:'variable-width-self',family:'variable-width',input:widths,target:widths[3]});
const single=point('self',[0,.8,0],.07,.75,[.2,.3,.4]);
fixtures.push({id:'empty',family:'self-and-empty',input:[],target:point(null,[0,.8,0],.07,.4,[.1,.2,.3])},
 {id:'singleton-self',family:'self-and-empty',input:[single],target:single},
 {id:'coincident-external',family:'self-and-empty',input:[single],target:point(null,[0,.8,0],.07,.25,[.3,.1,-.2])},
 {id:'coincident-self-pair',family:'self-and-empty',input:[single,point('other',[0,.8,0],.03,.25,[.1,-.2,.4])],target:single});
const radius=15/32,boundary=point('boundary',[0,.8,0],3/32,.75);
for(const [id,offset]of [['inside',-1e-12],['almost-inside',-2*Number.EPSILON],['equal',0],['almost-outside',2*Number.EPSILON],['outside',1e-12]]){
 fixtures.push({id:'boundary-'+id,family:'support-boundary',input:[boundary],target:point(null,[radius*(1+offset),.8,0],4/32,.25,[.1,.2,.3])});
}
function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return x/4294967296;};}
for(const [seed,n]of [[7,31],[19,64],[53,129]]){
 const rand=rng(seed),input=Array.from({length:n},(_,i)=>point('r-'+i,[(rand()-.5)*1.2,.25+rand()*1.1,(rand()-.5)*1.2],.01+rand()*.24,rand()*1.6,[rand()-.5,rand()-.5,rand()-.5]));
 for(const [id,target]of [['self-first',input[0]],['self-last',input[n-1]],['central',point(null,[0,.6,0],.06,.45,[.12,-.2,.1])],['far',point(null,[1.2,2.5,1.2],.015,.45,[.12,-.2,.1])]])
  fixtures.push({id:`random-${seed}-${id}`,family:'random',input,target});
}
assert.equal(fixtures.length,25);

let rows=null;
function matrix(){
 if(rows)return rows;rows=[];
 for(const fixture of fixtures)for(const angle of [.15,.6,2,'all-leaves']){
  const allLeaves=angle==='all-leaves',theta=allLeaves?.6:angle;
  const actual=json(candidate.query(fixture.input,fixture.target,theta,allLeaves));
  rows.push({id:fixture.id+'-theta-'+angle,fixture,theta,allLeaves,...actual,reference:reference(actual)});
 }
 return rows;
}
test('native velocity and stretch retain the frozen 100-query fingerprint',()=>{
 const values=matrix().map(c=>({id:c.id,field:mechanicalKeys.map(k=>c.raw[k])}));
 assert.equal(crypto.createHash('sha256').update(JSON.stringify(values)).digest('hex'),'22f35a20363734e0520d53fc061e594466595f7887f6e6a3d81c0403fc40c211');
});
test('all thermal raw sums match independent same-LUT all-pairs and do not depend on theta',()=>{
 const first=new Map();
 for(const c of matrix()){
  for(const k of thermalKeys)near(c.raw[k],c.reference.raw[k],c.id+' '+k);
  const thermal=Object.fromEntries(thermalKeys.map(k=>[k,c.raw[k]]));
  if(first.has(c.fixture.id))assert.deepEqual(thermal,first.get(c.fixture.id));else first.set(c.fixture.id,thermal);
  assert.equal(c.stats.positiveContributions,c.reference.positiveContributions);
 }
 assert.equal(first.size,25);assert.equal(matrix().length,100);
});
test('heterogeneous temperature and uniform support both retain clustered heat',()=>{
 const h=matrix().find(c=>c.id==='missed-heterogeneous-theta-0.6'),u=matrix().find(c=>c.id==='missed-uniform-theta-0.6');
 near(h.raw.S,12.19688194990158,'cluster S');near(h.raw.sT/h.raw.S,.7090059162617348,'cluster T');
 assert.equal(h.stats.positiveContributions,64);assert.equal(u.stats.positiveContributions,64);
 near(u.raw.S,h.raw.S,'uniform S');assert.equal(u.raw.sT/u.raw.S,.75);
});
test('variable widths need max source sigma; incorrect pruning is rejected',()=>{
 const f=fixtures.find(f=>f.id==='variable-width-far'),good=matrix().find(c=>c.id==='variable-width-far-theta-0.6');
 assert(source.includes('limit=9*(tS2+b[o+6])'),'update mutation anchor deliberately if implementation changes');
 const wrong=make(source.replace('limit=9*(tS2+b[o+6])','limit=9*(tS2+0)'));
 const bad=json(wrong.query(f.input,f.target,.6,false));assert(bad.raw.S<good.raw.S);
 assert(good.stats.positiveContributions>0);
});
test('support equality, near-boundary values, self, empty tree and spatial pruning',()=>{
 const byId=new Map(matrix().map(c=>[c.id,c]));
 const at=id=>byId.get(id+'-theta-0.6');
 assert.equal(at('boundary-equal').reference.positiveContributions,0);assert.equal(at('boundary-equal').stats.sourceTests,1);
 assert.equal(at('boundary-inside').reference.positiveContributions,1);assert.equal(at('boundary-outside').reference.positiveContributions,0);
 assert.equal(at('singleton-self').raw.S,1);assert.equal(at('singleton-self').raw.sT,.75);
 assert.equal(at('empty').raw.S,1);assert.equal(at('empty').raw.sT,.4);assert.equal(at('empty').stats.sourceTests,0);
 assert(matrix().some(c=>c.stats.nodesPruned>0&&c.stats.sourceTests<c.reference.terms.length));
 for(const c of matrix())assert(c.stats.sourceTests<=c.reference.terms.length);
});
test('optional thermal work statistics do not change any raw output',()=>{
 for(const c of matrix()){
  const plain=json(candidate.query(c.fixture.input,c.fixture.target,c.theta,c.allLeaves,false));
  assert.deepEqual(plain.raw,c.raw,c.id);
 }
});
