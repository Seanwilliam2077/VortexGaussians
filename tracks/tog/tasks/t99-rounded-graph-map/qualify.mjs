import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';
import {bits,value,serial,descriptor,lookup,presummed,width} from './operator.mjs';

const here=path.dirname(fileURLToPath(import.meta.url)), root=path.resolve(here,'../../../..');
const sha=b=>createHash('sha256').update(b).digest('hex');
const loadJson=f=>JSON.parse(f.endsWith('.gz')?gunzipSync(readFileSync(f)):readFileSync(f));
function positions(ply) {
  const token=Buffer.from('end_header\n'), offset=ply.indexOf(token)+token.length;
  const head=ply.toString('ascii',0,offset).split(/\r?\n/), props=head.filter(s=>s.startsWith('property '));
  const n=Number(head.find(s=>s.startsWith('element vertex ')).split(' ')[2]), stride=4*props.length;
  assert.deepEqual(props.slice(0,3),['property float x','property float y','property float z']);
  assert(props.every(s=>s.startsWith('property float ')) && offset+n*stride===ply.length);
  return Array.from({length:n},(_,i)=>[0,1,2].map(k=>ply.readFloatLE(offset+i*stride+k*4)));
}
function cellKey(x,y,z){return x+','+y+','+z;}
function index(xyz,r) {
  const cells=new Map();
  for(const [i,p] of xyz.entries()){
    const key=cellKey(...p.map(x=>Math.floor(x/r)));
    if(!cells.has(key))cells.set(key,[]);
    cells.get(key).push(i);
  }
  return cells;
}
function graph(xyz,cells,src,p,dt) {
  const r=p.spreadR, lists=Array.from({length:xyz.length},()=>[]);
  for(const i of src){
    const a=xyz[i], lo=a.map(v=>Math.floor((v-r)/r)),hi=a.map(v=>Math.floor((v+r)/r));
    for(let x=lo[0];x<=hi[0];x++)for(let y=lo[1];y<=hi[1];y++)for(let z=lo[2];z<=hi[2];z++){
      for(const j of cells.get(cellKey(x,y,z))||[]){
        const b=xyz[j], dx=b[0]-a[0],dy=b[1]-a[1],dz=b[2]-a[2];
        const rr=dx*dx+dy*dy+dz*dz;
        if(rr>r*r)continue;
        const up=Math.max(0,dy/Math.max(1e-4,r)),d=Math.sqrt(rr);
        const inc=dt*p.spreadRate*(1-d/r)*(1+2.2*up);
        if(inc>0)lists[j].push(inc);
      }
    }
  }
  return lists;
}
function preimage(ds,out) {
  // With finite positive increments the starting word cannot exceed out.
  function search(strict){
    let lo=0,hi=out+1;
    while(lo<hi){
      const m=Math.floor((lo+hi)/2), got=bits(serial(value(m),ds));
      if(strict?got<=out:got<out)lo=m+1;else hi=m;
    }
    return lo;
  }
  return [search(false),search(true)-1];
}
function newStats(){
  return {cold:0,zero:0,one:0,multiple:0,native_unique:0,native_ambiguous:0,no_preimage:0,
    all_compatible_fast:0,unique_fast:0,scalar_guaranteed_matching:0,scalar_guaranteed_different:0,
    scalar_unspecified:0,scalar_unique_different:0,graph_threshold_disagreements_possible:0,
    residual_next_scan_disagreements_possible:0,lookup_checked:0,
    representative_queries:0,representative_fast:0,descriptor_builds:0,descriptor_build_adds:0,
    fallback_adds:0,baseline_adds:0,presum_build_adds:0};
}
function trial(asset){
  const transfer=asset==='dead-tree', t=path.join(here,'..',transfer?'t92-transfer-workload':'t86-ignition-margin');
  const t86=path.join(here,'../t86-ignition-margin');
  const ed=transfer?path.join(t,'evidence'):t;
  const refs=loadJson(path.join(ed,transfer?'capture-report.json':'public/capture-report.json'));
  const ply=readFileSync(transfer?path.join(t,'local/scene.ply'):(process.env.T86_PLY||path.resolve(root,'../real-asset-ingest/foreground.ply')));
  assert.equal(sha(ply), (refs.sources.asset || refs.sources.Firewoods_foreground).sha256);
  const xyz=positions(ply);
  const rCfg=loadJson(path.join(transfer?t:path.join(t86,'../t42-firewoods-sequential-workflow'),'recipe.json'));
  const grid=index(xyz,rCfg.params.spreadR);
  const rows=[],totals=newStats(),cache=new Map();
  for(const arm of ['AB','BA']){
    const trace=loadJson(path.join(ed,transfer?'':'public',arm+'-trace.json.gz'));
    for(const frame of [210,240,300]){
      const filename=arm+'-'+frame+'.json.gz', raw=readFileSync(path.join(ed,'checkpoints',filename));
      assert.equal(sha(raw),refs.files.find(f=>path.basename(f.name)===filename).sha256);
      assert.equal(trace[frame-1].retired,0);
      const c=JSON.parse(gunzipSync(raw)),p=c.params;
      assert(p.spreadMeasureMode==='legacy'&&p.spreadClockMode==='elapsed'&&p.sceneScale===1&&p.scenePitch===0&&p.spreadRate>=0);
      assert.equal(c.state.length,xyz.length);
      const donors=c.frontier.slice(0,p.spreadFrontierCap), key=sha(JSON.stringify(donors));
      if(!cache.has(key)){
        const lists=graph(xyz,grid,donors,p,c.dt);
        cache.set(key,{lists,descriptors:new Map(),sums:new Map(),donors:donors.length,
          edges:lists.reduce((n,l)=>n+l.length,0)});
      }
      const {lists,descriptors,sums}=cache.get(key), stats=newStats();
      for(const [j,ds] of lists.entries()){
        if(c.state[j]!==0 || c.fuel[j]<=0)continue;
        stats.cold++;if(ds.length===0){stats.zero++;continue;}
        if(ds.length===1){stats.one++;continue;}
        stats.multiple++;
        const out=bits(c.heat[j]), [lo,hi]=preimage(ds,out);
        if(hi<lo){stats.no_preimage++;continue;}
        if(lo===hi)stats.native_unique++;else stats.native_ambiguous++;
        // Derive all-compatible status without counting ambiguous native inputs as known.
        const block=Math.floor(lo/width);
        let allFast=Math.floor(hi/width)===block;
        if(allFast){
          const rule=descriptor(block,ds);
          for(const par of [0,1]){
            const a=lo+(lo%2!==par?1:0),b=hi-(hi%2!==par?1:0);
            if(a<=b && (lookup(a,rule)===null || lookup(b,rule)===null))allFast=false;
          }
        }
        if(allFast){stats.all_compatible_fast++;if(lo===hi)stats.unique_fast++;}
        if(!sums.has(j)){sums.set(j,presummed(ds));stats.presum_build_adds+=ds.length;}
        const approx=w=>Math.fround(value(w)+sums.get(j));
        const vmin=approx(lo),vmax=approx(hi),target=value(out),D=1-c.dt*.35;
        if(bits(vmin)===out && bits(vmax)===out)stats.scalar_guaranteed_matching++;
        else if(bits(vmin)>out || bits(vmax)<out){stats.scalar_guaranteed_different++;if(lo===hi)stats.scalar_unique_different++;}
        else stats.scalar_unspecified++;
        if([vmin,vmax].some(v=>(v>=p.spreadIgnH)!==(target>=p.spreadIgnH)))stats.graph_threshold_disagreements_possible++;
        if([vmin,vmax].some(v=>(Math.fround(v*D)>=p.spreadIgnH)!==(Math.fround(target*D)>=p.spreadIgnH)))stats.residual_next_scan_disagreements_possible++;
        const mid=Math.floor((hi+lo)/2);
        for(const w of new Set([lo,mid,hi])){
          const result=lookup(w,descriptor(Math.floor(w/width),ds));
          assert.equal(bits(serial(value(w),ds)),out);
          if(result!==null){assert.equal(result,out);stats.lookup_checked++;}
        }
        // The actual starting word is unknown for ambiguous cases. Use its
        // midpoint only for this deliberately labelled representative reuse account.
        stats.representative_queries++;stats.baseline_adds+=ds.length;
        const b=Math.floor(mid/width),ck=j*256+b;
        if(!descriptors.has(ck)){
          descriptors.set(ck,descriptor(b,ds));stats.descriptor_builds++;
          if(b>0 && b<255)stats.descriptor_build_adds+=2*ds.length;
        }
        const seen=lookup(mid,descriptors.get(ck));
        if(seen!==null)stats.representative_fast++;else stats.fallback_adds+=ds.length;
      }
      for(const k of Object.keys(stats))totals[k]+=stats[k];
      rows.push({arm,frame,donor_order_sha256:key,stats});
    }
  }
  return {asset,ply_sha256:sha(ply),multi_recipient_queries:totals.multiple,totals,rows,
    static_frontiers:[...cache].map(([sha,x])=>({sha,donors:x.donors,all_site_positive_edges:x.edges}))};
}
const results=['firewoods','dead-tree'].map(trial);
writeFileSync(path.join(here,'RESULTS.json'),JSON.stringify(results,null,2)+'\n');
for(const r of results)console.log(r.asset, r.totals);
