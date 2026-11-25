import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import path from 'node:path';
import {performance} from 'node:perf_hooks';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';

const here=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(here,'../../../..');
const t86=path.join(here,'../t86-ignition-margin');
const sha=b=>createHash('sha256').update(b).digest('hex');
const start=performance.now(), identities={};
const bytes=(file,name)=>{const b=readFileSync(file); identities[name]=sha(b);return b;};
const demo=bytes(path.join(root,'demo/index.html'),'demo').toString();
const plugin=bytes(path.join(here,'estimate.js'),'estimate').toString();
const cfg=JSON.parse(bytes(path.join(here,'../t42-firewoods-sequential-workflow/recipe.json'),'recipe'));
const capture=JSON.parse(readFileSync(path.join(t86,'public/capture-report.json')));
assert.equal(identities.demo,capture.sources.demo.sha256);
assert.equal(identities.recipe,capture.sources.recipe.sha256);
const ply=bytes(process.env.T86_PLY || path.resolve(root,'../real-asset-ingest/foreground.ply'),'ply');
assert.equal(identities.ply,capture.sources.Firewoods_foreground.sha256);
const terminator=Buffer.from('end_header\n'), offset=ply.indexOf(terminator)+terminator.length;
const header=ply.toString('ascii',0,offset).trimEnd().split(/\r?\n/);
const fields=header.filter(x=>x.startsWith('property ')).map(x=>x.split(' '));
assert(fields.every(f=>f[1]==='float')); assert.deepEqual(fields.slice(0,3).map(f=>f[2]),['x','y','z']);
const width=4*fields.length;
const count=Number(header.find(x=>x.startsWith('element vertex ')).split(' ')[2]);
assert.equal(offset+width*count,ply.length);
const scene=Array.from({length:count},(_,i)=>{
  const start=offset+i*width;
  return {p:[0,1,2].map(j=>ply.readFloatLE(start+4*j))};
});
const shell={};
for(const arm of ['AB','BA']){
  const pick=cfg.picks.find(v=>v.name===arm[1]);
  shell[arm]=[];
  for(const [i,q] of scene.entries()){
    const xyz=q.p.map((v,j)=>v-cfg.source_center[j]+(j===1?cfg.params.sceneLift:0));
    const dist=Math.hypot(...xyz.map((v,j)=>v-pick.world[j]));
    if(dist>pick.radius && dist<=pick.radius+cfg.params.spreadIgnR) shell[arm].push(i);
  }
}
const slice=(begin,end)=>{
  const i=demo.indexOf(begin), j=demo.indexOf(end,i+1);
  assert(i>=0&&j>i);return demo.slice(i,j);
};
const factory=new Function('sceneGauss','sceneInfo','P','sceneBurnState','layers',
  slice('const WX =','\n')+'\n'+slice('const VPM_QX0=','\n')+'\n'+
  slice('function worldToSrc(', 'function srcToWorld(')+'\n'+
  slice('function vpmMorton(', '// 节点: ndF stride')+'\n'+plugin+'\nreturn t91Estimate;');
const preparation_ms=performance.now()-start;
const cutRows=[];
for(const arm of ['AB','BA']) for(const cut of [210,240,300]){
  const cutStart=performance.now();
  const file=arm+'-'+cut+'.json.gz';
  const raw=bytes(path.join(t86,'checkpoints',file),file);
  const rec=capture.files.find(x=>x.name===file); assert.equal(sha(raw),rec.sha256);
  const snapshot=JSON.parse(gunzipSync(raw));
  const pred=factory(scene,{center:snapshot.scene_center},snapshot.params,
    {h:snapshot.heat,state:snapshot.state,fuel:snapshot.fuel},
    snapshot.gas.map(g=>({idx:g.idx,ps:g.particles})));
  const row={arm,cut,shell_n:shell[arm].length,decode_setup_ms:performance.now()-cutStart,methods:{}};
  for(const [label,useSampling] of [['allHot',false],['sampled',true]]){
    const t=performance.now(), answer=pred(shell[arm],cfg.dt,useSampling);
    row.methods[label]={answer,wall_ms:performance.now()-t};
  }
  cutRows.push(row);
}
writeFileSync(path.join(here,'PREDICTIONS.json'),JSON.stringify({identities,rows:cutRows.map(r=>({
  arm:r.arm,cut:r.cut,shell_n:r.shell_n,methods:Object.fromEntries(Object.entries(r.methods).map(([k,v])=>[k,v.answer]))}))},null,2)+'\n');
writeFileSync(path.join(here,'COSTS.json'),JSON.stringify({node:process.version,preparation_ms,
  rows:cutRows.map(r=>({arm:r.arm,cut:r.cut,decode_setup_ms:r.decode_setup_ms,
    methods_ms:Object.fromEntries(Object.entries(r.methods).map(([k,v])=>[k,v.wall_ms]))})),
  total_ms:performance.now()-start},null,2)+'\n');
console.log(cutRows.map(r=>[r.arm,r.cut,...Object.values(r.methods).map(m=>m.answer.decision)]));
