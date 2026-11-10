"""Read-only public T81 evidence verification; Python standard library only.

Works from a fresh checkout without the external asset, browser, original local
run directory or runtime executables. This checks archived bytes and saved-record
consistency; it does not rerun science, recompute native FNV hashes, reconstruct
omitted geometry or validate perceptual significance.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PUBLIC=HERE/'public'
ARMS=['per-layer-AB','per-layer-A','global-AB','global-A']
TAGS=['prefix','after-intervention','endpoint']
COLUMNS=['id','fuelInitial','fuel','heat','char','glow','state']
OUTCOME_KEYS={'blocked':'sceneFeedCapacityBlocked','randomRejected':'sceneFeedRandomRejected','emitted':'sceneSeedsEmitted'}
PROJECTION_KEYS=set('schema frame time seed original_native_hash original_particle_state_hash random_draws material_columns material_rows frontier emit_cursor scene_aggregates gas_aggregates counters counters_by_group gas policy fixed_B_indices newly_B_indices observation_counters scope'.split())


def require(condition,message):
    if not condition:raise ValueError(message)


def identity(raw):return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def finite(value,label):
    if isinstance(value,float):require(math.isfinite(value),label+': non-finite number')
    elif isinstance(value,dict):
        for k,v in value.items():finite(v,label+'.'+k)
    elif isinstance(value,list):
        for v in value:finite(v,label)


def projection(value,entry,arm,tag,summary):
    name=entry['file'];require(set(value)==PROJECTION_KEYS,name+': projection schema fields')
    require(value['schema']=='t81-public-dynamic-projection-v1',name+': schema')
    require(value['material_columns']==COLUMNS,name+': material columns')
    rows=value['material_rows']
    require(len(rows)==entry['material_rows']==34687,name+': material count')
    require(all(isinstance(r,list)and len(r)==7 for r in rows),name+': material row width')
    require({r[0]for r in rows}=={'ply:'+str(i)for i in range(34687)},name+': unique material IDs')
    finite(value,name)
    policy='per-layer'if tag=='prefix'or arm.startswith('per-layer')else'global'
    frame=360 if tag=='endpoint' else 180
    require((value['frame'],value['seed'],value['policy'])==(frame,11,policy),name+': fixed controls')
    layers=value['gas'];require([v['idx']for v in layers]==list(range(9)),name+': layer inventory')
    particles=[p for layer in layers for p in layer['particles']]
    count=len(particles)
    require(count==entry['gas_particles']==value['gas_aggregates']['count'],name+': gas count')
    require([len(v['particles'])for v in layers]==value['gas_aggregates']['layerCounts'],name+': layer counts')
    require(count<=5400 and (policy!='per-layer'or all(len(v['particles'])<=600 for v in layers)),name+': capacity')
    ids=[p['observation']['id']for p in particles];require(len(set(ids))==count,name+': unique gas IDs')
    require(all(set(p)=={'observation','native'}for p in particles),name+': gas record fields')
    if tag in ['prefix','endpoint']:
        reference=summary['arms'][arm][tag]
        for key,reference_key in [('frame','frame'),('time','time'),('original_native_hash','hash'),
            ('original_particle_state_hash','particleStateHash'),('random_draws','randomDraws'),
            ('scene_aggregates','scene'),('gas_aggregates','particles'),('counters','counters'),
            ('observation_counters','observationCounters')]:
            require(value[key]==reference[reference_key],name+': SUMMARY '+key)
    else:
        require(value['original_native_hash']==('36e624bc'if arm.endswith('-AB')else'24ba7dc9'),name+': zero-time hash value')
        require(count==2394,name+': zero-time gas count')
    return count


def check_log(rows,arm,states,summary):
    require([r['frame']for r in rows]==list(range(1,361)),arm+': 360 sequential frames')
    fixed=set(states['prefix']['fixed_B_indices']);new=set(states['after-intervention']['newly_B_indices'])
    previous_native={k:0 for k in OUTCOME_KEYS.values()};previous_attempts=0;previous_count=0
    total={key:0 for key in OUTCOME_KEYS};blocked_free=0;attrition=0;second=[]
    for row in rows:
        finite(row,arm+' step')
        policy='per-layer'if row['frame']<=180 or arm.startswith('per-layer')else'global'
        require(row['policy']==policy and row['glError']==0 and row['contextLost']is False,arm+': step controls/GL')
        require(len(row['layerCounts'])==9 and sum(row['layerCounts'])<=5400,arm+': step capacity')
        if policy=='per-layer':require(max(row['layerCounts'])<=600,arm+': per-layer cap')
        offers=row['offers'];native=row['counters'];counts={k:0 for k in OUTCOME_KEYS}
        for o in offers:
            require(len(o)==10 and 0<=o[0]<34687 and 0<=o[1]<9 and o[6]in counts,arm+': offer record')
            require(bool(o[4])==(o[2]>=600),arm+': local fullness')
            require(bool(o[5])==(o[3]>=5400 if policy=='global'else o[2]>=600),arm+': policy fullness')
            require((o[6]=='blocked')==bool(o[5]),arm+': admission outcome')
            require((o[7]is not None)==(o[6]=='emitted'),arm+': emitted identity')
            require(bool(o[8])==(o[0]in fixed)and bool(o[9])==(row['frame']>180 and o[0]in new),arm+': source labels')
            counts[o[6]]+=1
            blocked_free+=int(o[6]=='blocked'and o[3]<5400)
        require(native['sceneFeedAttempts']-previous_attempts==len(offers),arm+': per-step attempts')
        for outcome,key in OUTCOME_KEYS.items():
            require(native[key]-previous_native[key]==counts[outcome],arm+': per-step outcome count')
            total[outcome]+=counts[outcome]
        removed=row['nativeRemovedIds'];require(len(set(removed))==len(removed),arm+': duplicate attrition IDs')
        attrition+=len(removed);count=sum(row['layerCounts'])
        require(previous_count+counts['emitted']-len(removed)==count,arm+': particle count balance')
        expected={'offers':native['sceneFeedAttempts'],**total,'blockedWithGlobalFree':blocked_free,'nativeAttrition':attrition}
        require(row['observationCounters']==expected,arm+': cumulative observation accounting')
        previous_native={k:native[k]for k in previous_native};previous_attempts=native['sceneFeedAttempts'];previous_count=count
        if row['frame']>180:second.extend(offers)
    for tag,index in [('prefix',179),('endpoint',359)]:
        value=states[tag];row=rows[index]
        for left,right in [('time','time'),('random_draws','randomDraws'),('counters','counters'),('observation_counters','observationCounters')]:
            require(value[left]==row[right],arm+': log/projection '+tag+' '+left)
        require(value['gas_aggregates']['layerCounts']==row['layerCounts'],arm+': log/projection layer counts')
    second_counts={k:sum(o[6]==k for o in second)for k in OUTCOME_KEYS}
    second_counts['blocked_with_global_free']=sum(o[6]=='blocked'and o[3]<5400 for o in second)
    second_counts['native_attrition']=sum(len(r['nativeRemovedIds'])for r in rows[180:])
    require(second_counts==summary['arms'][arm]['second_interval'],arm+': SUMMARY second-interval accounting')
    groups={}
    for label,predicate in [('fixed_B_region',lambda o:bool(o[8])),('newly_B_ignited',lambda o:bool(o[9])),('other_sources',lambda o:not o[8])]:
        selected=[o for o in second if predicate(o)]
        groups[label]={'offers':len(selected),**{k:sum(o[6]==k for o in selected)for k in OUTCOME_KEYS}}
    require(groups==summary['arms'][arm]['source_groups'],arm+': SUMMARY source-group accounting')
    return [{k:v for k,v in r.items()if k not in ('timing','node_bridge_ms')}for r in rows[:180]]


def main():
    manifest=json.loads((PUBLIC/'MANIFEST.json').read_bytes())
    require(manifest['schema']=='t81-public-evidence-archive-v1','Manifest schema')
    summary_raw=(HERE/'SUMMARY.json').read_bytes();summary=json.loads(summary_raw)
    require(identity(summary_raw)==manifest['audited_summary_identity'],'SUMMARY byte identity')
    result_ids=[{k:f[k]for k in ['bytes','sha256']}for f in summary['supervisor']['files']if f['name']=='result.json']
    require(result_ids==[manifest['audited_result_identity']],'Original result identity binding through SUMMARY')
    require(summary['qualification']=='passed_original_identity_prefix_accounting_and_runtime_checks','Saved qualification')
    expected={arm+'-steps.jsonl.gz'for arm in ARMS}|{arm+'-'+tag+'.dynamic.json.gz'for arm in ARMS for tag in TAGS}
    entries=manifest['files'];require(len(entries)==manifest['files_total']==16,'Sixteen archives')
    require({e['file']for e in entries}==expected,'Exact public archive inventory')
    require({p.name for p in PUBLIC.glob('*.gz')}==expected,'No missing/extra gzip files')
    records={};compressed=0;decoded_total=0;gas_total=0
    for entry in entries:
        name=entry['file'];raw=(PUBLIC/name).read_bytes()
        require(identity(raw)=={k:entry[k]for k in ['bytes','sha256']},name+': compressed identity')
        require(0<entry['decoded_bytes']<=64*1024*1024,name+': bounded decoded size')
        decoded=gzip.decompress(raw)
        require(identity(decoded)=={'bytes':entry['decoded_bytes'],'sha256':entry['decoded_sha256']},name+': decoded identity')
        compressed+=len(raw);decoded_total+=len(decoded)
        if entry['kind']=='lossless_original_step_log':
            require(entry['original']=={'name':name,**identity(raw)},name+': lossless original identity')
            records[name]=[json.loads(line)for line in decoded.splitlines()]
        else:
            require(entry['kind']=='documented_dynamic_projection',name+': archive kind')
            records[name]=json.loads(decoded)
    require(compressed==manifest['bytes_total'],'Total compressed bytes')
    prefix_states=[];prefix_traces=[]
    for arm in ARMS:
        states={tag:records[arm+'-'+tag+'.dynamic.json.gz']for tag in TAGS}
        for tag in TAGS:
            entry=next(e for e in entries if e['file']==arm+'-'+tag+'.dynamic.json.gz')
            gas_total+=projection(states[tag],entry,arm,tag,summary)
        prefix_states.append(states['prefix'])
        prefix_traces.append(check_log(records[arm+'-steps.jsonl.gz'],arm,states,summary))
    require(all(p==prefix_states[0]for p in prefix_states),'All four projected prefixes equal')
    require(all(p==prefix_traces[0]for p in prefix_traces),'All four timing-free prefix traces equal')
    print(json.dumps({'status':'verified_public_saved_evidence','archive_files':16,'step_logs':4,'step_records':1440,
        'dynamic_projections':12,'material_rows_per_projection':34687,'material_rows_total':12*34687,
        'gas_particle_records_total':gas_total,'compressed_bytes':compressed,'decoded_bytes':decoded_total,
        'summary_identity_bound':True,'original_result_identity_bound_via_summary':True,
        'all_controls_counts_and_summary_accounting_checked':True,'scientific_executions':0,
        'external_asset_browser_or_local_run_required':False,
        'limitations':'Saved bytes/record consistency only; no replay, independent native-hash recomputation, omitted-image validation or contribution judgment.'},indent=2))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'status':'verification_failed','error':str(exc)}),file=sys.stderr)
        raise SystemExit(1)
