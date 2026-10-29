// Offline input/identity preparation only. Never launches a browser or simulates.
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
const root=process.cwd(),here=path.join(root,'tracks/tog/tasks/t42-firewoods-sequential-workflow');
const outer=path.dirname(path.dirname(root)),stage=path.join(outer,'work/real-asset-static-staging');
const sha=b=>createHash('sha256').update(b).digest('hex');
const input=path.join(outer,'work/real-asset-ingest');
const source=await fs.readFile(path.join(root,'demo/index.html'));
if(sha(source)!=='e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0')throw Error('current demo identity changed');
const text=source.toString('utf8');
const pText=text.slice(text.indexOf('const P = {')+10,text.indexOf('const RESEARCH_DEFAULTS')).trim().replace(/;$/,'');
const defaults=vm.runInNewContext('('+pText+')',{}, {timeout:1000});
const ply=await fs.readFile(path.join(input,'foreground.ply'));
if(sha(ply)!=='906460f162f704b89666b159ae5b4744e53e6dc11baf448a550de581506919b0')throw Error('PLY identity changed');
const headerEnd=ply.indexOf('end_header\n')+11;if(headerEnd<11)throw Error('header missing');
const header=ply.subarray(0,headerEnd).toString('ascii');
if(!header.includes('format binary_little_endian 1.0'))throw Error('unsupported PLY');
const props=[...header.matchAll(/^property (\w+) (\w+)\r?$/gm)].map(m=>({type:m[1],name:m[2]}));
if(props.some(p=>p.type!=='float'))throw Error('non-float field');
const n=Number(header.match(/^element vertex (\d+)/m)?.[1]),stride=props.length*4;
if(n!==34687||stride!==248||headerEnd+n*stride!==ply.length)throw Error('PLY layout mismatch');
const field=name=>{const k=props.findIndex(p=>p.name===name);if(k<0)throw Error('missing '+name);return k*4;};
const offsets=['x','y','z','opacity'].map(field),rows=[],center=[0,0,0],min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
for(let i=0;i<n;i++){
 const row=offsets.map(o=>ply.readFloatLE(headerEnd+i*stride+o));if(!row.every(Number.isFinite))throw Error('nonfinite source');
 const pos=row.slice(0,3);pos.forEach((v,k)=>{center[k]+=v;min[k]=Math.min(min[k],v);max[k]=Math.max(max[k],v);});
 rows.push({index:i,source:pos,opacity:1/(1+Math.exp(-row[3]))});
}
center.forEach((_,k)=>center[k]/=n);
const historical=JSON.parse(await fs.readFile(path.join(stage,'run-01/result.json'),'utf8'));
const oldCenter=historical.captures[0].meta.sceneInfo.center;
if(center.some((v,k)=>Math.abs(v-oldCenter[k])>1e-12))throw Error('center convention differs');
const cameras=JSON.parse(await fs.readFile(path.join(input,'cameras.json'),'utf8'));
const camera=cameras.find(c=>c.id===0&&c.img_name==='00000');if(!camera)throw Error('camera missing');
const placement={sceneScale:1,sceneYaw:0,scenePitch:0,sceneLift:.75,sceneOffX:0,sceneOffZ:0};
const world=p=>p.map((v,k)=>v-center[k]+(k===1?.75:0));
const project=p=>{const d=p.map((v,k)=>v-camera.position[k]);const q=[0,1,2].map(j=>d.reduce((s,v,k)=>s+v*camera.rotation[k][j],0));return {pixel:[camera.fx*q[0]/q[2]+(camera.width-1)/2,camera.fy*q[1]/q[2]+(camera.height-1)/2],depth:q[2]};};
// Targets/rules fixed from the saved full photograph, before any dynamics.
const targets=[{name:'A',pixel:[855,690]},{name:'B',pixel:[962,657]}],radius=.12;
const picks=targets.map(target=>{
 const candidates=rows.filter(p=>p.opacity>=.8).map(p=>({...p,...project(p.source)})).filter(p=>p.depth>0)
  .map(p=>({...p,error2:p.pixel.reduce((s,v,k)=>s+(v-target.pixel[k])**2,0)})).filter(p=>p.error2<=100)
  .sort((a,b)=>a.error2-b.error2||a.depth-b.depth||a.index-b.index);
 if(!candidates.length)throw Error('no opaque center within 10 pixels of '+target.name);
 const p=candidates[0],w=world(p.source);
 if(!(Math.abs(w[0])+radius<1&&w[1]-radius>0&&w[1]+radius<3&&Math.abs(w[2])+radius<.6))throw Error('ignition sphere outside domain '+target.name);
 const neighbors=rows.filter(q=>q.source.reduce((s,v,k)=>s+(v-p.source[k])**2,0)<=radius**2).map(q=>q.index);
 return {name:target.name,requested_photo_pixel:target.pixel,index:p.index,id:'ply:'+p.index,source:p.source,world:w,
  projected_photo_pixel:p.pixel,projected_source_depth:p.depth,pixel_distance:Math.sqrt(p.error2),opacity:p.opacity,
  radius,initial_geometric_neighbors:neighbors};
});
const distance=Math.hypot(...picks[0].world.map((v,k)=>v-picks[1].world[k]));
if(distance<=2*radius)throw Error('ignition spheres overlap');
const params={...defaults,...placement,solver:'vpm',dimMode:'layer',sliceMode:'world',sliceDepth:1.2,
 spreadOn:true,spreadClockMode:'elapsed',spreadMeasureMode:'legacy',emitterOn:false,
 faithful:true,bloom:0,reflect:0,haze:0,embers:false,box:false,orbit:false,paused:true,
 sceneOn:true,sceneSorted:true,sceneBackdrop:false,sceneDepthTest:false,sceneSH:3,sceneLight:1,
 exposure:1,scenePreComp:false};
const recipe={schema:'t42-fixed-ordinary-workflow-v1',parent_commit:'9343f9e957595b6bba1abcccd382a9cc6c8852b1',seed:11,
 width:940,height:528,dt:1/60,steps_per_interval:180,intervals:2,internal_deadline_ms:180000,external_deadline_s:240,
 max_checkpoint_bytes:33554432,camera,params,source_center:center,source_bounds:{min,max},
 world_bounds:{min:world(min),max:world(max)},picks,ignition_center_distance:distance,
 selection:'Fixed photo pixels; nearest projected center among opacity>=.8, positive depth, within10px; ties depth then index. Revised during disclosed pre-freeze input preparation; no dynamics used.',
 mode_scope:'Existing layered world-coordinate VPM plus existing heuristic spread, not 3D physical combustion.',
 reset_scope:'research.reset(seed, same params) clears gas, material and counters; no inverse physics',
 scientific_claim:false};
await fs.writeFile(path.join(here,'recipe.json'),JSON.stringify(recipe,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({n,center,world_bounds:recipe.world_bounds,picks:picks.map(({initial_geometric_neighbors,...p})=>({...p,neighbors:initial_geometric_neighbors.length})),distance}));
