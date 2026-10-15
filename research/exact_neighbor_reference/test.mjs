import test from 'node:test';
import assert from 'node:assert/strict';
import {pack,buildGraph,exchange,edgeTriples} from './core.mjs';
import {PARAMS,fixture,definitions,temperature} from './design.mjs';
import {buildThermalGraph,stepThermalGraph} from './p4-thermal-reference.mjs';
import {sameSources} from './run.mjs';
const node=(id,kind,position,T=400)=>({id,kind,position,measure:.01,capacityPerMeasure:kind==='surface'?2:3,capacity:.01*(kind==='surface'?2:3),temperature:T});
const small=()=>({surfaceCount:3,nodes:[node('s0','surface',[-.31,-.02,.01],300),node('s1','surface',[-.30,-.02,.01],350),node('s2','surface',[2,2,2],500),node('g0','gas',[-.21,.03,.02],800),node('g1','gas',[-.4,-.10,.03],700),node('g2','gas',[.2,.3,.4],600)]});
test('negative coordinates, disconnected node, and cache give exact canonical graph',()=>{
 const a=pack(small(),PARAMS),d=buildGraph(a,'allpairs'),h=buildGraph(a,'hash');
 assert.deepEqual(edgeTriples(a,h),edgeTriples(a,d));assert.deepEqual(h.sumG,d.sumG);assert.equal(h.neighborCount[2],0);
 assert.equal(h.work.bucketLookups,h.work.candidateCacheCells*27);assert.equal(h.work.candidateCacheHits,2*a.ns-h.work.candidateCacheCells);assert.equal(h.work.distanceEvaluations,2*h.work.candidatePairsPerPass);
});
test('strict support excludes exactly h and outside while retaining inside',()=>{
 const scene={surfaceCount:1,nodes:[node('s','surface',[0,0,0]),node('in','gas',[.3-Number.EPSILON,0,0]),node('at','gas',[.3,0,0]),node('out','gas',[.3+Number.EPSILON,0,0])]};
 const a=pack(scene,PARAMS);for(const method of ['allpairs','hash']){const g=buildGraph(a,method);assert.equal(g.edgeCount,1);assert.equal(g.gasIndex[0],0);assert.ok(g.work.boundaryPairs>=2);}
});
test('synchronous exchange matches frozen P4 reference and retains extrema/energy',()=>{
 const input=small(),a=pack(input,PARAMS),g=buildGraph(a,'hash'),T=new Float64Array(a.initial),ledger=exchange(a,g,T,PARAMS);
 const scene={surface:[],gas:[]};for(const v of input.nodes)scene[v.kind].push(v.kind==='surface'?{id:v.id,position:v.position,area:v.measure,capacityPerArea:v.capacityPerMeasure,temperature:v.temperature}:{id:v.id,position:v.position,volume:v.measure,capacityPerVolume:v.capacityPerMeasure,temperature:v.temperature});
 const reference=buildThermalGraph(scene,{h:PARAMS.h,beta:PARAMS.beta}),expected=stepThermalGraph(reference.state,reference.graph,PARAMS.dt,{safety:PARAMS.safety,maxSubsteps:PARAMS.maxSubsteps});
 for(let i=0;i<a.n;i++)assert.ok(Math.abs(T[i]-expected.state.temperatures[i])<1e-12);assert.ok(Math.abs(ledger.energyResidual)/ledger.Ebefore.total<1e-12);assert.ok(T.every(x=>x>=300&&x<=800));assert.deepEqual(a.initial,Float64Array.from(input.nodes.map(v=>v.temperature)));
});
test('high beta actually substeps and still preserves maximum principle',()=>{
 const p={...PARAMS,beta:1e6},a=pack(small(),p),g=buildGraph(a,'hash'),T=new Float64Array(a.initial),l=exchange(a,g,T,p);assert.ok(l.substeps>1);assert.ok(l.maxCfl<=.9*(1+1e-14));assert.ok(T.every(x=>x>=300&&x<=800));
});
test('fixture geometry and physical-coordinate temperature definitions are explicit',()=>{
 assert.equal(definitions().length,9);const f=fixture(500,'smooth');assert.equal(f.nodes.length,1100);assert.equal(f.surfaceCount,500);assert.equal(f.nodes[0].position[0],-.2);assert.equal(f.nodes[250].position[0],.2);assert.equal(f.nodes[500].kind,'gas');
 assert.ok(Math.abs(f.nodes.slice(0,500).reduce((s,n)=>s+n.measure,0)-1.28)<1e-12);assert.ok(Math.abs(f.nodes.slice(500).reduce((s,n)=>s+n.measure,0)-.256)<1e-12);
 assert.equal(temperature('gas',[0,.5,0],'hotpatch'),900);assert.equal(temperature('surface',[0,.5,0],'hotpatch'),300);assert.equal(temperature('gas',[.12,.5,0],'hotpatch'),300);assert.ok([300,800].includes(temperature('gas',[-.2,.1,-.4],'checkerboard')));
});
test('malformed/unsafe inputs and unsupported builders fail explicitly',()=>{
 const f=small();f.nodes[0].position=[Number.MAX_VALUE,0,0];assert.throws(()=>pack(f,PARAMS));const a=pack(small(),PARAMS);assert.throws(()=>buildGraph(a,'approx'));assert.throws(()=>exchange(a,buildGraph(a,'hash'),new Float64Array(a.initial),{...PARAMS,safety:2}));assert.throws(()=>pack(small(),{h:0,beta:4}));
});
test('zero edges have one substep and zero exchange',()=>{
 const a=pack({surfaceCount:1,nodes:[node('s','surface',[0,0,0]),node('g','gas',[10,0,0],800)]},PARAMS),g=buildGraph(a,'hash'),T=new Float64Array(a.initial),l=exchange(a,g,T,PARAMS);assert.equal(g.edgeCount,0);assert.equal(l.substeps,1);assert.equal(l.edgeEvaluations,0);assert.deepEqual(T,a.initial);assert.equal(l.energyResidual,0);
});
test('source-freeze equality ignores JSON key ordering but rejects missing/changed hashes',()=>{
 assert.ok(sameSources({a:'1',b:'2'},{b:'2',a:'1'}));assert.ok(!sameSources({a:'1',b:'2'},{a:'1'}));assert.ok(!sameSources({a:'1'},{a:'2'}));
});
