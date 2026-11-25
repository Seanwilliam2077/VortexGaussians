import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {gunzipSync} from 'node:zlib';

const here=path.dirname(fileURLToPath(import.meta.url)),tasks=path.dirname(here);
const sources={};
async function load(name,file) {
  const b=await fs.readFile(file);sources[name]=createHash('sha256').update(b).digest('hex');
  return JSON.parse(file.endsWith('.gz')?gunzipSync(b):b);
}
const t86=path.join(tasks,'t86-ignition-margin'),publicDir=path.join(t86,'public');
const crop=await load('recipe',path.join(tasks,'t42-firewoods-sequential-workflow/recipe.json'));
const capture=await load('native',path.join(publicDir,'capture-report.json'));
const milestone=await load('target',path.join(tasks,'t108-visible-progression/REFERENCE.json'));
const timed=await load('historical_cost',path.join(tasks,'t108-visible-progression/evidence/CAPTURE.json'));
assert.equal(sources.recipe,capture.sources.recipe.sha256);
assert.equal(timed.status,'validated');
assert.equal(sources.native,timed.sources.reference);assert.equal(sources.recipe,timed.sources.recipe);
const p=crop.params,b=p.spreadFeedCap,start=180,cap=p.layers*p.ppl;
for(const [key,value] of Object.entries({solver:'vpm',dimMode:'layer',spreadParticlePolicy:'block',spreadMeasureMode:'legacy',
  spreadClockMode:'elapsed',emitterOn:false,embers:false,simLayers:9,layers:9,spreadFrontierCap:1400,spreadFeedCap:48}))
  assert.equal(p[key],value);
const fuelAt=frames=>{let f=1;for(let i=0;i<frames;i++)f=Math.fround(f-crop.dt/p.spreadBurnT);return f;};
const sha=x=>createHash('sha256').update(JSON.stringify(x)).digest('hex');

// A production implementation replaces readMaterialBatch by one native-order
// material-only step over a saved gas-deposition log. This screen counts such steps.
function conservativeDemand(old,initialCursor,readMaterialBatch) {
  const known=old.slice(),work=[];let last=start,cursor=initialCursor;
  return {
    service(frame) {
      const from=last,oldLength=known.length;
      while(known.length<=cursor+b && last<frame) {
        const ids=readMaterialBatch(++last,frame);known.push(...ids);
      }
      if(known.length<=cursor+b)assert.equal(last,frame,'wrap requires current exact length');
      const ids=[],begin=cursor;
      for(let j=0;j<b;j++){cursor=(cursor+1)%known.length;ids.push(known[cursor]);}
      if(last!==from)work.push({at:frame,oldest_read:from+1,latest_read:last,batches:last-from,
        additional_ids:known.length-oldLength,known_length:known.length,begin_cursor:begin,end_cursor:cursor});
      return {ids,cursor,last};
    },
    report(){return {material_steps:last-start,latest_reconstructed:last,total_new_ids:known.length-old.length,work};}
  };
}

function randomNumber(seed,draw) {
  const a=(seed+Math.imul(draw,0x6D2B79F5))|0;
  let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;
}
function decodeSuccess(before,after,previousGas,gas) {
  let draws=before;
  const slots=[];
  for(let j=0;j<b;j++){
    if(draws===after)break;
    const coin=randomNumber(crop.seed,++draws);
    if(coin<.5){draws+=5;slots.push(j);}
    assert(draws<=after);
  }
  assert.equal(draws,after);
  const beforeFeed=gas-slots.length;
  assert(beforeFeed>=0 && beforeFeed<=previousGas && gas<=cap);
  let occupancy=beforeFeed,pos=before;
  for(let j=0;j<b;j++){
    if(occupancy>=cap)continue;
    const accept=randomNumber(crop.seed,++pos)<.5;
    assert.equal(accept,slots.includes(j));if(accept){occupancy++;pos+=5;}
  }
  assert.equal(pos,after);assert.equal(occupancy,gas);
  return slots;
}
const answer={schema:'t112-demand-screen-v1',sources,arms:{}};
for(const arm of ['BA','AB']) {
  const trace=await load(arm+'_trace',path.join(publicDir,arm+'-trace.json.gz'));
  assert.equal(sources[arm+'_trace'],timed.sources[arm+'_trace']);
  const ref=capture.shots[arm],target=milestone.queries.find(x=>x.arm===arm).first_frame;
  const inputFrontier=[...ref.initial.ids,...trace.slice(0,start).flatMap(row=>row.new_ids),...ref.edit.ids];
  assert.equal(ref.post_edit.burning,inputFrontier.length);
  assert.equal(new Set(inputFrontier).size,inputFrontier.length);assert(inputFrontier.length>=p.spreadFrontierCap);
  assert(trace.slice(0,start).every(row=>row.retired===0));assert(fuelAt(target)>0);
  const truth=inputFrontier.slice(),appendFrame=new Map(),offered=[],accepted=[],wraps=[],checkpoints=[];
  let cursor=ref.post_edit.cursor,draws=ref.post_edit.random_draws,gas=ref.post_edit.gas_count;
  let acceptedLower=start,bottleneck=null,transmitted=0,peakPending=0,primary=null;
  const readBatch=(at,now)=>{assert(at>start && at<=now);return trace[at-1].new_ids;};
  const lazy=conservativeDemand(inputFrontier,cursor,readBatch);
  let prevRetro=start;
  for(let at=start+1;at<=target;at++) {
    const row=trace[at-1];assert.equal(row.frame,at);assert.equal(row.retired,0);
    assert(row.new_ids.every((id,j,ids)=>j===0||id>ids[j-1]));
    for(const id of row.new_ids){assert(!appendFrame.has(id));appendFrame.set(id,at);}
    truth.push(...row.new_ids);assert.equal(truth.length,row.active_count);
    const successes=decodeSuccess(draws,row.random_draws,gas,row.gas_count);
    draws=row.random_draws;gas=row.gas_count;
    const certified=lazy.service(at),oracle=[];
    for(let j=0;j<b;j++){
      const next=(cursor+1)%truth.length;
      if(next<=cursor)wraps.push({frame:at,slot:j,count:truth.length});
      cursor=next;const id=truth[cursor];oracle.push(id);
      if(successes.includes(j)){
        accepted.push(id);
        if(appendFrame.has(id)){
          const born=appendFrame.get(id);
          if(born>acceptedLower){acceptedLower=born;bottleneck={feed_frame:at,slot:j,rank:cursor,id,born};}
          transmitted++;
        }
      }
    }
    assert.deepEqual(certified.ids,oracle);assert.equal(certified.cursor,cursor);offered.push(...oracle);
    peakPending=Math.max(peakPending,at-prevRetro);prevRetro=certified.last;
    if([210,240].includes(at)) {
      const snap=await load(arm+'_'+at,path.join(t86,'checkpoints',arm+'-'+at+'.json.gz'));
      assert.equal(snap.emit_cursor,cursor);assert.deepEqual(snap.frontier,truth);
      assert.equal(snap.random_draws,draws);checkpoints.push(at);
    }
    if(at===target-1)primary={...lazy.report(),work:[...lazy.report().work],
      accepted_prefix_material_lower_bound:acceptedLower-start,accepted_bottleneck:bottleneck,
      accepted_appended_services:transmitted,offers:offered.length,accepted:accepted.length,
      actual_wraps:[...wraps],peak_pending_frames:peakPending,peak_buffer_bytes_if_capacity_allocated:peakPending*32*p.spreadSampleCap,
      offered_sha256:sha(offered),accepted_sha256:sha(accepted),final_cursor:cursor};
  }
  assert(primary);
  const trials=timed.queries.find(q=>q.arm===arm).trials;
  const ordinary=trials.filter(r=>r.method==='ordinary' && r.rep>0),repair=trials.filter(r=>r.method==='repair' && r.rep>0);
  const oldEager=repair[0].work.repair_steps;
  assert(repair.every(r=>r.first_frame===target && r.work.repair_steps===oldEager) && repair.length===3 && ordinary.length===3);
  const median3=values=>values.slice().sort((a,b)=>a-b)[1];
  answer.arms[arm]={cut:start,target,base_length:inputFrontier.length,
    min_fuel_lower_bound_at_cut:fuelAt(start),min_fuel_lower_bound_at_target:fuelAt(target),
    old_eager_material_steps:oldEager,declared_gate_ratio:primary.material_steps/oldEager,primary,
    measured_t108_ms:{eager_repair_phase:median3(repair.map(r=>r.phases.repair_ms)),
      eager_delivered:median3(repair.map(r=>r.delivered_ms)),ordinary_delivered:median3(ordinary.map(r=>r.delivered_ms))},
    terminal_feed_sensitivity:{material_steps:lazy.report().material_steps,accepted_only_lower:acceptedLower-start},
    verified_native_checkpoints:checkpoints};
}
const r=answer.arms.BA.declared_gate_ratio;
answer.decision=r>=.8?'reject-lagging-full-material-replay':r<=.5?'qualify-native-replay':'inconclusive';
const out=process.argv[2]||path.join(here,'RANKS.json');
await fs.writeFile(out,JSON.stringify(answer,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(Object.fromEntries(Object.entries(answer.arms).map(([k,a])=>[k,[a.primary.material_steps,a.primary.accepted_prefix_material_lower_bound,a.old_eager_material_steps]]))));
console.log(answer.decision);
