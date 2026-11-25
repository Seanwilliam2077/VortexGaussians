import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {searchGraph,selfCheck} from './geometry.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)),root=path.resolve(here,'../../../..'),tasks=path.dirname(here);
const read=async f=>JSON.parse(await fs.readFile(f));
const sha=s=>createHash('sha256').update(s).digest('hex');
const sets=[
  ['firewoods','t42-firewoods-sequential-workflow',process.env.T86_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply'),[60,180]],
  ['dead-tree','t92-transfer-workload',path.join(tasks,'t92-transfer-workload/local/scene.ply'),[60,180]],
  ['playground','t101-playground-holdout',path.join(tasks,'t101-playground-holdout/local/scene.ply'),[30,60,180]]
];
function plyPositions(bytes) {
  const end=bytes.indexOf('\n',bytes.indexOf('end_header'))+1;
  const header=bytes.subarray(0,end).toString('ascii');
  assert(header.includes('binary_little_endian'));
  const n=Number(header.match(/element vertex (\d+)/)[1]);
  const properties=[...header.matchAll(/^property (\S+) (\S+)/gm)];
  assert(properties.every(p=>p[1]==='float' || p[1]==='float32'));
  assert.deepEqual(properties.slice(0,3).map(p=>p[2]),['x','y','z']);
  const stride=4*properties.length,xyz=new Float64Array(3*n);
  assert.equal(bytes.length,end+n*stride);
  for(let i=0;i<n;i++)for(let k=0;k<3;k++)xyz[i*3+k]=bytes.readFloatLE(end+i*stride+k*4);
  return xyz;
}
const output={schema:'t104-graph-reach-v1',self_check:selfCheck(),assets:{}};
for(const [asset,task,file,horizons] of sets) {
  const t0=performance.now(), budget={tests:0,limit:1e9,deadline:t0+180000};
  const cfg=await read(path.join(tasks,task,'recipe.json')),bytes=await fs.readFile(file);
  const proof=await read(path.join(tasks,'t100-material-repair/evidence',asset,'CAPTURE.json'));
  assert.equal(sha(bytes),proof.sources.asset);assert.equal(cfg.params.spreadR,.11);
  assert.equal(cfg.params.sceneScale,1);assert.equal(cfg.params.sceneYaw,0);assert.equal(cfg.params.scenePitch,0);
  const xyz=plyPositions(bytes),n=xyz.length/3;
  const id=new Int32Array(n),components=[],cc=searchGraph(xyz,.11,budget);
  for(let i=0;i<n;i++)if(cc.seen[i]<0) {
    const {nodes,hops}=cc.expand([i]),c=components.length;
    for(const j of nodes)id[j]=c;
    components.push({representative:i,sites:nodes.length,eccentricity:hops.length-1});
  }
  const arms={};
  for(const arm of ['AB','BA']){
    const p=cfg.picks.find(s=>s.name===arm[1]),seeds=[];
    for(let i=0;i<n;i++) {
      const x=xyz[i*3]-cfg.source_center[0],y=xyz[i*3+1]-cfg.source_center[1]+cfg.params.sceneLift,
        z=xyz[i*3+2]-cfg.source_center[2];
      const d=Math.hypot(x-p.world[0],y-p.world[1],z-p.world[2]);
      if(d>p.radius && d<=p.radius+cfg.params.spreadIgnR)seeds.push(i);
    }
    assert.deepEqual(seeds,proof.arms[arm].shell_ids);
    const touched=[...new Set(seeds.map(i=>id[i]))].sort((a,b)=>a-b);
    const {nodes,hops}=searchGraph(xyz,.11,budget).expand(seeds);
    assert.equal(nodes.length,touched.reduce((s,i)=>s+components[i].sites,0));
    let total=0;const cumulative=hops.map(v=>(total+=v));
    const horizon_reports=horizons.map(H=>{
      const counts=Array.from({length:H},(_,k)=>cumulative[Math.min(k,cumulative.length-1)]);
      return {H,support:counts.at(-1),support_fraction:counts.at(-1)/n,
        mean_sites:counts.reduce((s,v)=>s+v,0)/H,mean_fraction:counts.reduce((s,v)=>s+v,0)/(H*n)};
    });
    arms[arm]={seeds:seeds.length,seed_sha256:sha(JSON.stringify(seeds)),component_ids:touched,
      closure_sites:nodes.length,max_hops:hops.length-1,exact_hop_counts:hops,horizons:horizon_reports};
  }
  output.assets[asset]={sha256:sha(bytes),sites:n,components,arms,distance_checks:budget.tests,elapsed_ms:performance.now()-t0};
  assert(performance.now()<budget.deadline && budget.tests<=budget.limit);
}
const all=Object.values(output.assets).flatMap(a=>Object.values(a.arms));
const requests=all.flatMap(a=>a.horizons);
const most=requests.filter(h=>h.support_fraction>=.75).length;
const promising=all.filter(a=>a.horizons.some(h=>h.support_fraction<.5 && h.mean_fraction<.5)).length;
output.gate={requests:requests.length,at_least_75_percent:most,distinct_arms_below_both_50_percent:promising,
  decision:most>requests.length/2 && promising<2?'stop-geometry-only':'review-qualification'};
const destination=process.argv[2]?path.resolve(process.argv[2]):path.join(here,'GEOMETRY.json');
await fs.writeFile(destination,JSON.stringify(output,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(output.gate));
