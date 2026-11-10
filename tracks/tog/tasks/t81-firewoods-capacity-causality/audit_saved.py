"""Read saved T81 output only. No browser, solver, retry or threshold adjustment."""
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT=Path.cwd();HERE=ROOT/'tracks/tog/tasks/t81-firewoods-capacity-causality';OUT=HERE/'local/run-01';OUTER=ROOT.parent.parent
ARM_SPEC=[('per-layer-AB','per-layer',True),('per-layer-A','per-layer',False),('global-AB','global',True),('global-A','global',False)]
HISTORY_KEYS=['sceneFeedAttempts','sceneFeedCapacityBlocked','sceneSeedsEmitted']


def require_equal(observed,expected,label,checks):
    passed=observed==expected;checks.append({'label':label,'observed':observed,'expected':expected,'passed':passed})
    if not passed:raise RuntimeError(label+' mismatch; observed='+repr(observed)+' expected='+repr(expected))


def historical(state,label,checks,endpoint=False):
    n=state['native']
    observed={'frame':n['frame'],'hash':n['hash'],'count':n['particles']['count'],'counters':[n['counters'][k]for k in HISTORY_KEYS]}
    expected={'frame':360,'hash':'cb784052','count':2433,'counters':[17280,12379,2437]} if endpoint else {'frame':180,'hash':'24ba7dc9','count':2394,'counters':[8640,3826,2394]}
    require_equal(observed,expected,label,checks)


def state_checks(state,label,checks,frame,policy):
    n=state['native']
    require_equal({'glError':n['glError'],'contextLost':n['contextLost']},{'glError':0,'contextLost':False},label+' GL',checks)
    require_equal({'frame':n['frame'],'policy':state['policy'],'layers':n['params']['layers'],'ppl':n['params']['ppl']},
                  {'frame':frame,'policy':policy,'layers':9,'ppl':600},label+' controls',checks)
    require_equal(len(n['points']),34687,label+' material count',checks)
    gas_count=sum(len(layer['particles'])for layer in state['gas'])
    require_equal({'gas':gas_count,'layers':len(state['gas'])},{'gas':n['particles']['count'],'layers':9},label+' gas count',checks)
    if gas_count>5400 or (policy=='per-layer'and any(len(layer['particles'])>600 for layer in state['gas'])):raise RuntimeError(label+' capacity exceeded')
    ids=[p['observation']['id']for layer in state['gas']for p in layer['particles']]
    if len(set(ids))!=len(ids):raise RuntimeError(label+' duplicate particle IDs')


def load(name):
    path=OUT/name
    raw=gzip.decompress(path.read_bytes()) if name.endswith('.gz') else path.read_bytes()
    return json.loads(raw)


def pixels(name):return gzip.decompress((OUT/name).read_bytes())


def pixel_difference(a,b):
    if len(a)!=len(b) or len(a)%4: raise RuntimeError('Pixel dimensions differ')
    count=0;absolute=0;squared=0;maximum=0;changed=0
    for i in range(0,len(a),4):
        difference=[abs(a[i+j]-b[i+j]) for j in range(3)]
        changed+=any(difference)
        for d in difference:count+=1;absolute+=d;squared+=d*d;maximum=max(maximum,d)
    return {'rgb_samples':count,'pixels':len(a)//4,'absolute_rgb_mae_u8':absolute/count,
            'absolute_rgb_rmse_u8':math.sqrt(squared/count),'max_absolute_channel_u8':maximum,
            'changed_pixel_fraction':changed/(len(a)//4),'normalization':'raw RGB8 channel differences; no exposure rescale, threshold or perceptual pass gate'}


def main():
    checks=[];frozen_raw=(HERE/'freeze.json').read_bytes();frozen=json.loads(frozen_raw)
    invocation=json.loads((HERE/'invocation.json').read_bytes())
    require_equal(invocation['freeze_sha256'],hashlib.sha256(frozen_raw).hexdigest(),'invocation frozen identity',checks)
    require_equal(invocation['status'],'attempt_consumed','one-shot invocation state',checks)
    for f in frozen['files']:
        path=Path(f['path'])
        if not path.is_absolute():
            path=(OUTER/path).resolve()
            if not path.is_relative_to(OUTER.resolve()):raise RuntimeError('Frozen relative path escapes outer workspace')
        raw=path.read_bytes()
        require_equal({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
                      {'bytes':f['bytes'],'sha256':f['sha256']},'frozen '+f['path'],checks)
    actual_output_bytes=sum(p.stat().st_size for p in OUT.rglob('*')if p.is_file())
    if actual_output_bytes>64*1024*1024 or actual_output_bytes>frozen['budget']['max_output_bytes']:raise RuntimeError('Actual saved output including supervisor exceeds cap')
    report=load('result.json');supervisor=load('supervisor.json')
    if report['status']!='completed_capture_pending_saved_audit' or report['completed_native_steps']!=1440:
        raise RuntimeError('Capture incomplete: retain failure; no causal pass')
    if supervisor['exit_code']!=0 or supervisor['worker_still_live'] or not supervisor['within_external_deadline'] or not supervisor['within_output_budget']:
        raise RuntimeError('Supervisor qualification failed')
    if report['deadline_expired'] or report['page_errors'] or report['console_errors'] or report['blocked_requests'] or report['failures']:
        raise RuntimeError('Capture/runtime qualification failed')
    if report['worker_total_ms']>600000 or supervisor['elapsed_before_receipt_seconds']>660:raise RuntimeError('Actual recorded deadline exceeded')
    require_equal([(a['id'],a['policy'],a['B'])for a in report['arms']],ARM_SPEC,'exact four arms',checks)
    require_equal([(a['id'],a['policy'],a['B'])for a in frozen['arms']],ARM_SPEC,'frozen exact four arms',checks)
    require_equal([a['steps']for a in report['arms']],[360]*4,'four 360-step counts',checks)
    if not report['checks']or any(not c['passed']for c in report['checks']):raise RuntimeError('Capture recorded failed qualification')
    for f in report['files']:
        raw=(OUT/f['name']).read_bytes()
        if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise RuntimeError('Saved identity changed: '+f['name'])
        if 'decoded_bytes'in f:
            decoded=gzip.decompress(raw)
            if len(decoded)!=f['decoded_bytes']or hashlib.sha256(decoded).hexdigest()!=f['decoded_sha256']:raise RuntimeError('Decoded identity changed')
    arms={};prefixes=[];traces=[]
    for a in report['arms']:
        name=a['id'];rows=[json.loads(line)for line in gzip.decompress((OUT/(name+'-steps.jsonl.gz')).read_bytes()).splitlines()]
        if [r['frame']for r in rows]!=list(range(1,361)):raise RuntimeError('Step order')
        if any(r['glError']!=0 or r['contextLost']for r in rows):raise RuntimeError(name+' per-step GL failure')
        if any(r['policy']!=('per-layer'if r['frame']<=180 else a['policy'])for r in rows):raise RuntimeError(name+' policy sequence')
        prefix=load(name+'-prefix.json.gz');end=load(name+'-endpoint.json.gz');prefixes.append(prefix)
        after_intervention=load(name+'-after-intervention.json.gz')
        state_checks(prefix,name+' prefix',checks,180,'per-layer');historical(prefix,name+' historical prefix',checks)
        state_checks(end,name+' endpoint',checks,360,a['policy'])
        state_checks(after_intervention,name+' intervention',checks,180,a['policy'])
        require_equal(after_intervention['native']['hash'],'36e624bc'if a['B']else'24ba7dc9',name+' zero-time intervention hash',checks)
        require_equal(after_intervention['native']['particles']['count'],2394,name+' zero-time gas count',checks)
        require_equal([after_intervention['native']['counters'][k]for k in HISTORY_KEYS],[8640,3826,2394],name+' zero-time counters',checks)
        if name=='per-layer-AB':historical(end,name+' historical endpoint',checks,endpoint=True)
        traces.append([{k:v for k,v in r.items()if k not in ('timing','node_bridge_ms')}for r in rows[:180]])
        before=prefix['native']['counters'];after=end['native']['counters']
        offer_rows=[o for r in rows[180:]for o in r['offers']]
        counts={k:sum(o[6]==k for o in offer_rows)for k in ['blocked','randomRejected','emitted']}
        if sum(counts.values())!=len(offer_rows):raise RuntimeError('Offer partition')
        for k,n in [('blocked','sceneFeedCapacityBlocked'),('randomRejected','sceneFeedRandomRejected'),('emitted','sceneSeedsEmitted')]:
            if counts[k]!=after[n]-before[n]:raise RuntimeError('Counter/offer mismatch')
        groups={}
        for label,predicate in [('fixed_B_region',lambda o:bool(o[8])),('newly_B_ignited',lambda o:bool(o[9])),('other_sources',lambda o:not o[8])]:
            selected=[o for o in offer_rows if predicate(o)]
            groups[label]={'offers':len(selected),**{k:sum(o[6]==k for o in selected)for k in counts}}
        counts['blocked_with_global_free']=sum(o[6]=='blocked'and o[3]<5400 for o in offer_rows)
        counts['native_attrition']=sum(len(r['nativeRemovedIds'])for r in rows[180:])
        second_interval_timing={}
        for key in rows[180]['timing']:
            values=[r['timing'][key]for r in rows[180:]]
            second_interval_timing[key]={'sum':sum(values),'mean':sum(values)/len(values),'max':max(values)}
        arms[name]={'second_interval':counts,'source_groups':groups,'prefix':a['prefix'],'endpoint':a['endpoint'],
                    'timing':a['timing'],'second_interval_timing':second_interval_timing,
                    'second_interval_timing_frames':180,
                    'whole_arm_ms':a['whole_arm_ms'],'newly_B_count':len(end['newlyBIndices'])}
    if any(p!=prefixes[0]for p in prefixes[1:])or any(t!=traces[0]for t in traces[1:]):raise RuntimeError('Prefix inequality')
    comparisons={}
    for policy in ['per-layer','global']:
        comparisons[policy]=pixel_difference(pixels(policy+'-AB-endpoint.rgba.gz'),pixels(policy+'-A-endpoint.rgba.gz'))
    # Numeric allocation outcome, deliberately no visual success threshold.
    gains={condition:arms['global-'+condition]['second_interval']['emitted']-arms['per-layer-'+condition]['second_interval']['emitted']for condition in ['A','AB']}
    result={'schema':'t81-saved-causal-readback-v1','qualification':'passed_original_identity_prefix_accounting_and_runtime_checks',
            'saved_verification':{'checks':checks,'all_recorded_checks_passed':all(c['passed']for c in checks),
                'actual_output_bytes_including_supervisor':actual_output_bytes,'frozen_files_rehashed':len(frozen['files']),
                'native_hash_scope':'Compared saved native selected-field hash values to original T42 receipts; no independent full FNV recomputation or restart certificate.'},
            'arms':arms,'paired_endpoint_B_minus_noB':comparisons,'global_minus_per_layer_emitted':gains,
            'worker_total_ms':report['worker_total_ms'],'supervisor':supervisor,
            'new_scientific_executions':0,'new_method_claim':False,'perceptual_identifiability_established':False,
            'historical_T42_visual_verdict':'unqualified','interpretation':'Emission gains diagnose admission under a total deterministic policy intervention; changed conditional RNG, native attrition, source distributions and complete cost remain part of the result.'}
    target=HERE/'SUMMARY.json'
    encoded=json.dumps(result,indent=2)+'\n'
    if target.exists() and target.read_text()!=encoded:raise RuntimeError('Existing saved audit differs; do not overwrite')
    if not target.exists():target.write_text(encoded,encoding='utf-8')
    print(json.dumps({'qualification':result['qualification'],'global_minus_per_layer_emitted':gains,'paired_endpoint_B_minus_noB':comparisons,'worker_total_ms':report['worker_total_ms']}))


if __name__=='__main__':main()
