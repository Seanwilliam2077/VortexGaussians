"""CPU saved-evidence review. Default plan imports no NumPy/Torch or producer."""
import argparse
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent/'tog/tasks/t13-ordinary-feasibility-recovery'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(run):
    import numpy as np
    c = json.loads((TASK/'config.json').read_text())
    s = json.loads((run/'summary.json').read_text())
    f = json.loads((TASK/'freeze.json').read_text())
    manifest = json.loads((TASK/'inputs-manifest.json').read_text())
    r = {'scope': 'CPU saved arrays and scalar ledger only; no simulation, renderer, AD or Torch',
         'scriptSHA256': sha(__file__), 'summarySHA256': sha(run/'summary.json'), 'failures': [], 'arrays': {}, 'metrics': {}}
    def need(label, ok):
        if not ok:
            r['failures'].append(label)
    def raw(a):
        return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
    def mx(a):
        return float(np.max(np.abs(a)))
    def near(a, b):
        return bool(np.allclose(a, b, atol=1e-11, rtol=1e-12))
    def unpack(path):
        with np.load(path, allow_pickle=False) as z:
            return {k:z[k].copy() for k in z.files}
    for name, p in f['sources'].items():
        need('source '+name, sha(TASK/p['path']) == p['sha256'] and s['sourcesBefore'][name] == p and s['sourcesAfter'][name] == p)
    need('freeze', sha(TASK/'freeze.json') == s['freezeSHA256'])
    need('terminal result', s['status'] in ['completed', 'failed'])
    inputs = unpack(TASK/'inputs.npz')
    need('input pack file', sha(TASK/'inputs.npz') == c['input_pack']['sha256'] == manifest['pack']['sha256'])
    need('input manifest file', sha(TASK/'inputs-manifest.json') == c['input_pack']['manifest_sha256'])
    need('pack keys', set(inputs) == set(manifest['arrays']))
    for k, a in inputs.items():
        p = manifest['arrays'][k]
        need('input '+k, raw(a) == p['rawSHA256'] and list(a.shape) == p['shape'] and a.dtype.str == p['dtype'])
    saved = {}
    for name, pin in s['raw'].items():
        path = run/name
        need('file '+name, sha(path) == pin['sha256'] and path.stat().st_size == pin['bytes'])
        a = saved[name] = unpack(path)
        need('keys '+name, set(a) == set(pin['arrays']))
        for k, x in a.items():
            p = pin['arrays'][k]
            need(name+'/'+k, raw(x) == p['rawSHA256'] and list(x.shape) == p['shape']
                 and x.dtype.str == p['dtype'] and bool(np.isfinite(x).all()))
        r['arrays'][name] = {'sha256': sha(path), 'arrays': len(a)}
    lower, upper, seed_v = inputs['lower'], inputs['upper'], inputs['seed_velocity']
    codes = inputs['observed_uint8'].astype(np.float64)
    need('quantized intervals', near(lower, np.maximum(0,(codes-.5)/255)) and near(upper,np.minimum(1,(codes+.5)/255)))
    gate = c['gates']
    def div(v):
        return sum((np.roll(v[j], -1, axis=j)-v[j])*c['model']['n'] for j in range(3))
    def evaluate(a, name):
        alpha, v, st = a['observation_alpha'], a['initial_velocity'], a['state_metrics']
        need(name+' observation shape', alpha.shape == (20, 64, 64))
        constraints = np.concatenate((255*(lower-alpha).ravel(), 255*(alpha-upper).ravel(),
            [mx(v)/c['velocity']['initial_max_component']-1,
             float(np.mean(v*v))/c['velocity']['initial_component_rms']**2-1]))
        need(name+' constraints', near(constraints, a['constraints']))
        violation = np.maximum(np.maximum(lower-alpha, alpha-upper), 0)
        numerical = (bool(np.isfinite(st).all()) and bool(np.all(st[:,5] == 1))
            and float(st[:,0].max()) <= gate['divergence_inf'] and mx(div(v)) <= gate['divergence_inf']
            and float(st[:,1].min()) >= gate['density_min'] and float(st[:,3].min()) >= gate['alpha_min']
            and float(st[:,4].max()) <= gate['alpha_max'])
        qualified = (numerical and float(violation.max()) <= gate['interval_alpha_tolerance']
            and mx(v) <= c['velocity']['initial_max_component']
            and float(np.sqrt(np.mean(v*v))) <= c['velocity']['initial_component_rms'])
        delta = v-seed_v
        code_delta = np.abs(np.clip(np.floor(255*alpha+.5),0,255).astype(np.int16)-inputs['observed_uint8'].astype(np.int16))
        nonseed = mx(delta) > c['nonseed_velocity_max_absolute_threshold']
        for velocity in [a['observation_velocity20'], *a.get('final_velocity', [])]:
            need(name+' stored velocity divergence', mx(div(velocity)) <= gate['divergence_inf'])
        m = {'intervalMaxAlphaViolation': float(violation.max()), 'intervalViolatingPixels': int((violation>gate['interval_alpha_tolerance']).sum()),
             'intervalViolatingPixelsPerFrame': (violation>gate['interval_alpha_tolerance']).sum(axis=(1,2)).tolist(),
             'intervalMaxAlphaViolationPerFrame': violation.max(axis=(1,2)).tolist(),
             'quantizedDifferentPixels':int((code_delta!=0).sum()), 'quantizedByteExact':bool((code_delta==0).all()),
             'maxPositiveConstraint':float(np.maximum(constraints,0).max()),
             'positiveConstraintSquareSum':float(np.sum(np.maximum(constraints,0)**2)),
             'seedVelocityDifferenceMax': mx(delta), 'seedVelocityDifferenceRelativeL2': float(np.sqrt(np.sum(delta*delta)/np.sum(seed_v*seed_v))),
             'initialVelocityMaxComponent': mx(v), 'initialVelocityComponentRMS': float(np.sqrt(np.mean(v*v))),
             'numericalPassed': numerical, 'qualified': qualified, 'nonseed': nonseed, 'eligible': qualified and nonseed}
        r['metrics'][name] = m
        return constraints, m
    for name,a in saved.items():
        if 'observation_alpha' in a:
            evaluate(a,name)
    qc = c['qualification']; analytic = saved['qualification/analytic.npz']
    # The only old trajectory read is the frozen T12 G0/reference input source.
    oldrun = TASK.parent/'t12-ordinary-wind-response-extrema/runs/run-01/worker'
    need('T12 summary source',sha(oldrun/'summary.json')==manifest['sourceSummarySHA256'])
    oldarrays = {}
    for name,p in manifest['originalFiles'].items():
        need('T12 source '+name,sha(oldrun/name)==p['sha256'] and (oldrun/name).stat().st_size==p['bytes'])
        oldarrays[name]=unpack(oldrun/name)
    for key,p in manifest['arrays'].items():
        need('input original bytes '+key,raw(inputs[key])==raw(oldarrays[p['sourceFile']][p['sourceKey']]))
    prefix={}
    olda=oldarrays['qualification/analytic.npz']
    for key in ['theta','observation_alpha','initial_velocity','observation_velocity20','observation_density20','state_metrics','constraints']:
        before=olda[key][:20] if key=='state_metrics' else olda[key]
        after=analytic[key]
        prefix[key]={'bytesExact':raw(before)==raw(after),'maxAbsoluteDifference':mx(before-after),
                     'shape':list(after.shape),'dtype':after.dtype.str}
        need('T12 observation prefix '+key,near(before,after))
    r['T12AnalyticPrefix']=prefix
    need('G0 starting theta', raw(analytic['theta']) == raw(inputs['start_theta']))
    lam = analytic['multipliers']
    need('G0 fixed lambda', bool(np.all(lam == qc['multiplier'])))
    def loss(a, name):
        constraints, _ = evaluate(a,name)
        mu = qc['penalty']
        value = float(np.sum(np.maximum(lam+mu*constraints,0)**2-lam**2)/(2*mu))
        need(name+' PHR sum', near(value,a['loss']))
        return value
    loss(analytic,'qualification/analytic.npz')
    fdrows=[]
    for i in range(qc['directions']):
        direction = saved[f'qualification/direction-{i}.npz']['direction']
        need('direction input '+str(i), raw(direction) == raw(inputs[f'direction{i}']))
        norm=float(np.sqrt(np.sum(direction**2))); need('L2 '+str(i), abs(norm-1)<=1e-12)
        dot=float(np.sum(analytic['gradient_loss']*direction))
        for hi,h in enumerate(qc['h']):
            pair=[]
            for sign,label in [(1,'plus'),(-1,'minus')]:
                name=f'qualification/probe-{i}-{hi}-{label}.npz'; a=saved[name]
                need(name+' perturbation',near(a['theta'],inputs['start_theta']+sign*h*direction))
                pair.append(loss(a,name))
            fd=(pair[0]-pair[1])/(2*h); err=abs(fd-dot)/max(abs(dot),qc['denominator_floor'])
            fdrows.append({'direction':i,'L2Norm':norm,'h':h,'dot':dot,'fd':fd,'relativeError':err})
            need('G0 FD '+str((i,h)), bool(np.isfinite(err)) and err<=qc['relative_gate'])
    qm=s['qualification']['memory']
    memory_ok=(qm['peakAllocatedBytes']<=qc['peak_allocated_limit_bytes'] and qm['peakReservedBytes']<=qc['peak_reserved_limit_bytes'])
    numerical_ok=all(v['numericalPassed'] for k,v in r['metrics'].items() if k.startswith('qualification/'))
    need('G0 numerical and memory',numerical_ok and memory_ok)
    branch=lam+qc['penalty']*analytic['constraints']
    need('G0 active branch',int((branch>0).sum())==s['qualification']['activePHRBranches'])
    # The minimum absolute margin is independent of the constraint's sign.
    need('G0 branch margin',near(float(np.min(np.abs(branch))),s['qualification']['minimumAbsolutePHRBranch']))
    r['G0']={'differences':fdrows,'maxRelativeError':max(x['relativeError'] for x in fdrows),
             'numericalPassed':numerical_ok,'memoryPassed':memory_ok,'reported':s['qualification']}
    need('G0 count',s['qualification']['observationEvaluations']==9 and s['qualification']['backwardCalls']==1)
    search=s.get('search',{}); calls=search.get('calls',[])
    if calls:
        need('sequential calls',[x['evaluation'] for x in calls]==list(range(1,len(calls)+1)))
        def compare_metrics(label, actual, reported):
            for key,value in actual.items():
                need(label+' '+key, near(value,reported[key]))
        compare_metrics('initial from G0 arrays',r['metrics']['qualification/analytic.npz'],calls[0]['metrics'])
        need('initial lambda0 merit',near(.5*r['metrics']['qualification/analytic.npz']['positiveConstraintSquareSum'],calls[0]['loss']))
        classified=[]
        for call in calls:
            m=call['metrics']
            qualified=(m['numericalPassed'] and m['intervalMaxAlphaViolation']<=gate['interval_alpha_tolerance']
                and m['initialVelocityMaxComponent']<=c['velocity']['initial_max_component']
                and m['initialVelocityComponentRMS']<=c['velocity']['initial_component_rms'])
            eligible=qualified and m['seedVelocityDifferenceMax']>c['nonseed_velocity_max_absolute_threshold']
            need('call gate '+str(call['evaluation']),qualified==m['qualified'] and eligible==m['eligible'])
            classified.append({'evaluation':call['evaluation'],'kind':call['kind'],'origin':call['origin'],
                               'eligible':eligible,'intervalMaxAlphaViolation':m['intervalMaxAlphaViolation']})
        r['callClassificationFromLedger']=classified
        best_score=None; updates=[]
        for call in calls:
            m=call['metrics']
            if m['finite'] and m['numericalPassed']:
                score=(m['maxPositiveConstraint'],m['positiveConstraintSquareSum'])
                if best_score is None or score<best_score:
                    best_score=score; updates.append({'evaluation':call['evaluation'],'score':list(score)})
        need('earliest lexicographic least ledger',updates==search['leastViolatingUpdates'])
        least_id=updates[-1]['evaluation']; least_call=calls[least_id-1]
        need('least selected identity',least_id==search['leastViolating']['evaluation'])
        compare_metrics('least raw vs call',r['metrics']['search/least-violating.npz'],least_call['metrics'])
        # Reconstruct the two saved AL transitions, using saved constraints, not new trajectories.
        previous_lam=np.zeros_like(analytic['constraints']); previous_mu=1.; stages=[]
        for i,update in enumerate(search['outerUpdates']):
            a=saved[f'search/outer-update-{i}.npz']
            expect_lam=np.maximum(previous_lam+previous_mu*a['constraints'],0)
            expect_mu=min(c['optimizer']['penalty_max'],previous_mu*c['optimizer']['penalty_growth']) if update['violationAfter']>c['optimizer']['violation_reduction_factor']*update['violationBefore'] else previous_mu
            need('AL update '+str(i),near(a['multipliers'],expect_lam) and near(a['penalty'],expect_mu)
                 and near(update['maxMultiplier'],float(expect_lam.max())))
            accepted=search['accepted'][(i+1)*c['optimizer']['returned_steps_per_outer']]
            need('AL boundary '+str(i),near(np.maximum(a['constraints'],0).max(),accepted['metrics']['maxPositiveConstraint'])
                 and near(update['violationAfter'],accepted['metrics']['maxPositiveConstraint']))
            stages.append({'afterEvaluation':accepted['evaluation'],'multipliers':expect_lam,'penalty':expect_mu})
            previous_lam,previous_mu=expect_lam,expect_mu
        least_lam=np.zeros_like(analytic['constraints']); least_mu=1.
        for stage in stages:
            if stage['afterEvaluation']<least_id:least_lam,least_mu=stage['multipliers'],stage['penalty']
        lc=saved['search/least-violating.npz']['constraints']
        least_loss=float(np.sum(np.maximum(least_lam+least_mu*lc,0)**2-least_lam**2)/(2*least_mu))
        need('least PHR under current AL',near(least_loss,least_call['loss']))
        r['least']={'evaluation':least_id,'metrics':r['metrics']['search/least-violating.npz'],
                    'PHRLoss':least_loss,'updateEvaluations':[x['evaluation'] for x in updates],
                    'selectionScope':'Earliest strict lexicographic minimum among recorded finite/numerically valid evaluations; only final least arrays retained.'}
        for accepted in search['accepted']:
            recorded=calls[accepted['evaluation']-1]
            need('accepted ledger '+str(accepted['returnedStep']),accepted['metrics']==recorded['metrics'] and near(accepted['ALObjective'],recorded['loss']))
        need('returned and cache ledger',len(search['accepted'])==search['returnedSteps']+1
             and sum(x['cacheHit'] for x in search['accepted'])==search['cacheHits']
             and search['cacheHits']+search['cacheMisses']==search['returnedSteps'])
        observation_calls=[x for x in calls if x['kind']=='observation']; full_calls=[x for x in calls if x['kind']=='full']
        need('search budget',len(calls)==search['evaluationsStarted']<=80 and len(full_calls)<=1)
        need('forward/backward counts',sum(bool(x.get('forwardCompleted')) for x in calls)==search['evaluationsCompleted']
             and sum(bool(x['backwardCalled']) for x in calls)==search['backwardCalls'])
        eligible=[x for x in classified if x['kind']=='observation' and x['eligible']]
        if eligible:
            need('first selected',search['selectedEvaluation']==eligible[0]['evaluation'] and len(eligible)==1 and len(full_calls)==1)
            first=saved['search/first-feasible.npz']; final=saved['search/final-verification.npz']
            comparisons={k:raw(first[k])==raw(final[k][:20] if k=='state_metrics' else final[k]) for k in first}
            r['prefixFirstVsFinalBytes']=comparisons
            need('selected theta bytes',comparisons['theta'])
            _,m=evaluate(final,'search/final-verification.npz')
            need('final decision',search['nonseedWitnessFound']==m['eligible'])
            x0,y0,x1,y1=c['response']['roi']
            gs=final['future_alpha'][:,-1,y0:y1,x0:x1].sum(axis=(1,2))/inputs['denominator'].item()
            d=float(gs[1]-gs[0]); need('final response',near(gs,final['gs']) and near(d,final['d']))
            r['response']={'g':gs.tolist(),'d':d,'selectionByResponse':False}
        else:
            need('no invented witness/future',not search['nonseedWitnessFound'] and not search['finalPerformed'] and not full_calls)
            need('no future arrays',not any('future_alpha' in a or 'd' in a for a in saved.values()))
            need('decision',s['decision']=='NO_NONSEED_FEASIBLE_POINT_FOUND_WITHIN_FIXED_SEARCH')
        r['ledgerGateCounts']={'calls':len(calls),'qualified':sum(x['metrics']['qualified'] for x in calls),
            'nonseed':sum(x['metrics']['nonseed'] for x in calls),'numericallyValid':sum(x['metrics']['numericalPassed'] for x in calls),
            'velocityPriorPassed':sum(x['metrics']['initialVelocityMaxComponent']<=c['velocity']['initial_max_component'] and x['metrics']['initialVelocityComponentRMS']<=c['velocity']['initial_component_rms'] for x in calls)}
        work=s['actualWork']; expected_observations=9+len(observation_calls)
        need('aggregate work',work['observationEvaluationsCompleted']==expected_observations
             and work['fullEvaluationsCompleted']==len(full_calls)
             and work['stepsCompleted']==20*expected_observations+60*len(full_calls)
             and work['reverseCalls']==1+search['backwardCalls'])
        r['costsReported']={'actualWork':work,'qualificationSeconds':s['qualification']['secondsIncludingIO'],
                            'searchSeconds':search['secondsIncludingFinalAndIO'],'workerSeconds':s['workerWallSeconds'],
                            'sumCallSeconds':sum(x['seconds'] for x in calls),'returnedSteps':search['returnedSteps'],
                            'cacheHits':search['cacheHits'],'cacheMisses':search['cacheMisses'],'termination':search['termination']}
    need('input identity unchanged',s.get('runtimeInputsBefore')==s.get('runtimeInputsAfter'))
    r['limitations']=['No independent renderer, AD or full dynamics rerun. Intermediate state_metrics remain producer measurements.',
        'Unsaved trial arrays are not reconstructed: trial eligibility is independently classified from the complete scalar ledger.',
        'Timing/allocator statistics are original measurements. Nonseed >1e-10 excludes identity, not a practical ambiguity threshold.']
    r['passed']=not r['failures']
    return r


def main():
    p=argparse.ArgumentParser(); p.add_argument('--execute',action='store_true')
    p.add_argument('--run',type=Path,default=TASK/'runs/run-01/worker'); p.add_argument('--out',type=Path)
    a=p.parse_args()
    if not a.execute:
        print(json.dumps({'mode':'plan','CPUOnly':True,'run':str(a.run)})); return 0
    result=audit(a.run)
    if a.out:
        with a.out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps({'passed':result['passed'],'failures':result['failures'],'files':len(result['arrays']),
                      'FD':result['G0']['differences'],'response':result.get('response'),'costs':result.get('costsReported')}))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
