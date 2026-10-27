"""Independent saved-array T04 audit. CPU NumPy only; no producer/core imports.

Recomputes image/force/PHR/FD metrics, not trajectories or reverse derivatives.
No np.linalg or other BLAS operations. Existing audit outputs are never replaced.
"""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rawsha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def rms(a, axis=None):
    return np.sqrt(np.mean(np.square(a), axis=axis))


def crop(a, roi):
    x0, y0, x1, y1 = roi
    return a[..., y0:y1, x0:x1]


def force_stats(q, n, steps):
    # Independent separable interpolation on the matching coarse/fine MAC faces.
    offsets = ((0., .5, .5), (.5, 0., .5), (.5, .5, 0.))
    components = []
    for j, offset in enumerate(offsets):
        a = q[:, j]
        for axis in range(3):
            s = (np.arange(n, dtype=np.float64) + offset[axis]) * 8 / n - offset[axis]
            lo = np.floor(s).astype(np.int64)
            frac = s - np.floor(s)
            shape = [1] * 4
            shape[axis + 1] = n
            t = frac.reshape(shape)
            a = np.take(a, lo % 8, axis=axis + 1) * (1-t) + np.take(a, (lo+1) % 8, axis=axis + 1) * t
        components.append(a)
    expanded = np.stack(components, axis=1)
    mx, sq = 0., 0.
    for s in range(steps):
        weights = np.maximum(0., 1 - np.abs(3. * s / (steps-1) - np.arange(4)))
        f = np.sum(expanded * weights[:, None, None, None, None], axis=0)
        mx = max(mx, float(np.max(np.abs(f))))
        sq += float(np.sum(f*f))
    return mx, float(np.sqrt(sq/(steps*3*n**3)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task', type=Path, default=Path(__file__).resolve().parents[1]/'tog/tasks/t04-framewise-feasibility')
    ap.add_argument('--out', type=Path, default=Path(__file__).with_name('t04-audit.json'))
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    taskdir = args.task.resolve()
    root = taskdir/'runs/run-01/worker'
    summary_path = root/'summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    config = json.loads((taskdir/'config.json').read_text(encoding='utf-8'))
    task, baseline = config['task'], config['baseline']
    checks, arrays = [], {}
    result = {'schema': 't04-independent-audit-v1', 'createdUTC': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'scope': 'Saved-array, input/source, metric, force interpolation, FD and accounting audit; no Torch/producer import, no simulation, no optimization, no reverse-AD replay.',
              'sourceSHA256': sha(__file__), 'summarySHA256': sha(summary_path), 'checks': checks}
    result['auditHistory'] = [{'attempt': 1, 'status': 'auditor_schema_error_no_output_file',
        'auditorSHA256': '3c1291224c9b2f47c52b0b29731b999b9dc317fc3471b11729e2dd6c4c314e84',
        'error': "KeyError: totalWallSecondsIncludingStartupQualificationAndIO at prior full T03 worker time",
        'correction': 'The published T03 result-summary uses totalWorkerWallSeconds; source data, thresholds and producer are unchanged.'}]

    def check(name, passed, detail=None):
        row = {'name': name, 'passed': bool(passed)}
        if detail is not None:
            row['detail'] = detail
        checks.append(row)

    def near(name, value, expected, atol=1e-10, rtol=1e-10):
        a, b = np.asarray(value), np.asarray(expected)
        ok = a.shape == b.shape and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
        error = float(np.max(np.abs(a-b))) if ok and a.size else 0.
        check(name, ok and np.all(np.abs(a-b) <= atol + rtol*np.abs(b)), {'maxAbsoluteDifference': error})

    frozen = json.loads((taskdir/'freeze.json').read_text(encoding='utf-8'))
    for name, row in frozen['files'].items():
        p = (taskdir/row['path']).resolve()
        check('frozen '+name, sha(p) == row['sha256'] and p.stat().st_size == row['bytes'])
    for phase in ('pinsBefore', 'pinsAfter'):
        for name, row in summary[phase].items():
            check(phase+' '+name, sha(row['path']) == row['sha256'] and Path(row['path']).stat().st_size == row['bytes'])
    check('before after records identical', summary['pinsBefore'] == summary['pinsAfter'])
    check('completed source unchanged', summary['status'] == 'completed' and summary['sourcesAndInputsUnchanged'])
    supervisor = json.loads((root.parent/'supervisor.json').read_text(encoding='utf-8'))
    check('supervisor exit zero', supervisor['status'] == 'completed' and supervisor['returnCode'] == 0)
    for name in ('stdout.log', 'stderr.log'):
        check('supervisor '+name, sha(root.parent/name) == supervisor[name]['sha256'])

    for name, row in summary['raw'].items():
        path = root/name
        check('file '+name, sha(path) == row['sha256'] and path.stat().st_size == row['bytes'])
        with np.load(path, allow_pickle=False) as z:
            a = {key: z[key] for key in z.files}
        arrays[name] = a
        check('array keys '+name, set(a) == set(row['arrays']))
        for key, value in a.items():
            rec = row['arrays'][key]
            check('raw '+name+' '+key, list(value.shape) == rec['shape'] and value.dtype.str == rec['dtype']
                  and rawsha(value) == rec['rawSHA256'] and bool(np.isfinite(value).all()))
    with np.load(taskdir/config['inputs']['approved'], allow_pickle=False) as z:
        approved = z['frames']
        check('approved only allowed arrays', set(z.files) == {'v0', 'rho0', 'frames'})
        for key in ('v0', 'rho0'):
            check('input raw '+key, rawsha(z[key]) == config['array_manifest'][key]['sha256'])
    target = np.load(taskdir/config['inputs']['target'], allow_pickle=False)
    check('input raw approved', rawsha(approved) == config['array_manifest']['approved']['sha256'])
    check('input raw target', rawsha(target) == config['array_manifest']['target_T02']['sha256'])
    refs = [crop(approved, r) for r in task['protected_rois']]
    scales = [rms(a, (-2, -1)) for a in refs]
    escale = rms(target, (-2, -1))
    ptau = [np.minimum(task['protect_relative']*s, task['protect_absolute']) for s in scales]
    etau = np.minimum(task['edit_relative']*escale, task['edit_absolute'])
    check('all fixed ROI signals', all(np.all(s >= task['signal_min']) for s in scales+[escale]))

    def terms(q, frames):
        pmse = [np.mean((crop(frames, roi)-ref)**2, axis=(-2, -1)) for roi, ref in zip(task['protected_rois'], refs)]
        emse = np.mean((crop(frames, task['edit_roi'])-target)**2, axis=(-2, -1))
        c = np.concatenate([a/t**2-1 for a, t in zip(pmse, ptau)] + [emse/etau**2-1] + [np.array([np.mean(q*q)/task['coefficient_rms']**2-1])])
        edit = float(np.mean(emse/etau**2))
        reg = float(baseline['regularizer_weight']*np.mean((q/baseline['regularizer_scale'])**2))
        return c, edit, reg, pmse, emse

    def phr(c, lam, rho, mask):
        branch = lam + rho*c
        raw = (np.maximum(branch, 0)**2-lam**2)/(2*rho)
        return raw, raw*mask, branch

    def audit_phr(name, c, lam, rho, mask, rec):
        raw, eff, branch = phr(c, lam, rho, mask)
        near(name+' constraints', c, rec['constraints'])
        near(name+' lambda', lam, rec['multipliers'])
        near(name+' rho', rho, rec['penalty'])
        for key, value in [('protectedPHRRaw', raw[:50].sum()), ('protectedPHREffective', eff[:50].sum()),
                           ('RMSPHREffective', eff[-1]), ('effectivePHR', eff.sum()),
                           ('protectedPositiveConstraintCount', np.count_nonzero(c[:50]>0)),
                           ('protectedBranchCountRaw', np.count_nonzero(branch[:50]>0)),
                           ('protectedBranchCountEffective', np.count_nonzero((branch[:50]>0)&(mask[:50]>0))),
                           ('protectedPositiveMultiplierCount', np.count_nonzero(lam[:50]>0)),
                           ('protectedPenaltyWeights', np.maximum(branch[:50], 0)*mask[:50]),
                           ('editPHRRaw', raw[50:75].sum()), ('editPHREffective', eff[50:75].sum()),
                           ('editPositiveConstraintCount', np.count_nonzero(c[50:75]>0)),
                           ('editBranchCountEffective', np.count_nonzero(branch[50:75]>0)),
                           ('editPositiveMultiplierCount', np.count_nonzero(lam[50:75]>0)),
                           ('editPenaltyWeights', np.maximum(branch[50:75],0))]:
            near(name+' '+key, value, rec[key])
        return eff

    # FD objectives are rebuilt from saved q/frames, not reported scalar losses.
    qcfg = baseline['qualification']
    ana = arrays['qualification/analytic.npz']
    c, edit, reg, _, _ = terms(ana['q'], ana['frames'])
    near('G0 tanh', ana['q'], task['coefficient_max']*np.tanh(ana['x']))
    near('G0 constraints', c, ana['constraints'])
    g0 = {}
    for arm in ('framewise_joint',):
        mask = np.ones(76)
        near('G0 mask '+arm, ana['mask'], mask)
        raw, eff, branch = phr(c, ana['multipliers'], float(ana['penalty']), mask)
        recorded = summary['qualification']['arms'][arm]
        near('G0 loss '+arm, edit+reg+eff.sum(), recorded['loss'])
        check('G0 active '+arm, np.all(branch[mask>0] > 0))
        errors = []
        for i in range(2):
            d = arrays[f'qualification/direction-{i}.npz']['direction']
            near('G0 direction RMS '+str(i), rms(d), 1.)
            gd = float(np.sum(ana['gradient']*d))
            near('G0 grad dot '+arm+str(i), gd, recorded['directions'][i]['gradientDotDirection'])
            for k, h in enumerate(qcfg['steps']):
                values = []
                for sign in ('plus', 'minus'):
                    a = arrays[f'qualification/probe-{i}-{k}-{sign}.npz']
                    near(f'G0 probe tanh {i} {k} {sign}', a['q'], task['coefficient_max']*np.tanh(ana['x']+(h if sign=='plus' else -h)*d))
                    cp, ep, rp, _, _ = terms(a['q'], a['frames'])
                    near(f'G0 probe constraints {i} {k} {sign}', cp, a['constraints'])
                    values.append(ep+rp+phr(cp, ana['multipliers'], float(ana['penalty']), mask)[1].sum())
                fd = float((values[0]-values[1])/(2*h))
                err = abs(fd-gd)/max(abs(gd), qcfg['denominator_floor'])
                check(f'G0 FD gate {arm} {i} {h}', err <= qcfg['relative_gate'], {'relativeError': err})
                errors.append(err)
        g0[arm] = {'maximumRecomputedRelativeFD': max(errors), 'effectiveBranches': int(mask.sum())}
    check('G0 cost accounting', summary['qualification']['rolloutCount'] == 9 and summary['qualification']['backwardCalls'] == 1)
    result['qualification'] = g0

    arms = {}
    for row in summary['arms']:
        arm = row['arm']; mask = np.ones(76)
        accepted = []
        for i, record in enumerate(row['accepted']):
            a = arrays[record['rawFile']]; q, frames = a['q'], a['frames']
            c, edit, reg, pmse, emse = terms(q, frames)
            near(f'{arm} {i} tanh', q, task['coefficient_max']*np.tanh(a['x']))
            near(f'{arm} {i} mask', a['mask'], mask)
            near(f'{arm} {i} constraints', c, a['constraints'])
            near(f'{arm} {i} reported constraints', c, record['metrics']['constraints'])
            qmax, qrms = float(np.max(np.abs(q))), float(rms(q))
            fmax, frms = force_stats(q, config['model']['n'], config['model']['steps'])
            ea, er = np.sqrt(emse), np.sqrt(emse)/escale
            epass = (ea <= task['edit_absolute']) & (er <= task['edit_relative']) & (escale >= task['signal_min'])
            pa = [np.sqrt(v) for v in pmse]; pr = [v/s for v, s in zip(pa, scales)]
            pp = [(a <= task['protect_absolute']) & (r <= task['protect_relative']) & (s >= task['signal_min']) for a,r,s in zip(pa,pr,scales)]
            m = record['metrics']
            for key, val in [('coefficientMax',qmax),('coefficientRMS',qrms),('forceMaxComponent',fmax),('forceRMS',frms),
                             ('editLoss',edit),('regularizer',reg),('alphaMin',frames.min()),('alphaMax',frames.max()),
                             ('maxPositiveViolation', np.maximum(c,0).max()),('maxActivePositiveViolation',(np.maximum(c,0)*mask).max())]:
                near(f'{arm} {i} '+key, val, m[key])
            near(f'{arm} {i} edit abs',ea,m['edit']['absoluteRMS']);near(f'{arm} {i} edit rel',er,m['edit']['relativeRMS'])
            check(f'{arm} {i} edit flags',epass.tolist()==m['edit']['passedFrames'])
            for j in range(2):
                near(f'{arm} {i} protect abs {j}',pa[j],m['protected'][j]['absoluteRMS'])
                near(f'{arm} {i} protect rel {j}',pr[j],m['protected'][j]['relativeRMS'])
                check(f'{arm} {i} protect flags {j}',pp[j].tolist()==m['protected'][j]['passedFrames'])
            # Intermediate final fields were not saved; do not independently certify their finite/density check.
            numerical = bool(m['finite'] and m['densityMin']>=0 and frames.min()>=0 and frames.max()<=1)
            budget = qmax<=task['coefficient_max'] and qrms<=task['coefficient_rms'] and fmax<=task['applied_force_max']
            edit_ok = bool(np.all(epass) and budget and numerical)
            joint_ok = bool(edit_ok and all(np.all(p) for p in pp))
            check(f'{arm} {i} own/joint flags', m['editAndBudgetPassed']==edit_ok and m['jointPassed']==joint_ok and m['passed']==(joint_ok if arm=='framewise_joint' else edit_ok))
            eff = audit_phr(f'{arm} {i} PHR',c,a['multipliers'],float(a['penalty']),mask,record['penaltyRecord'])
            near(f'{arm} {i} merit',edit+reg+eff.sum(),record['ALObjective'])
            accepted.append({'index':i,'returnedStep':record['returnedStep'],'rollout':record['rollout'],
                'editPassedCount':int(epass.sum()),'protectionPassedCount':int(sum(p.sum() for p in pp)),
                'editFailedFrames':(np.flatnonzero(~epass)+16).tolist(),
                'protectionFailedFramesByROI':[(np.flatnonzero(~p)+16).tolist() for p in pp],
                'editWorstRelative':float(er.max()),'protectionWorstRelative':float(max(r.max() for r in pr)),
                'editRelative':er.tolist(),'protectionRelative':[r.tolist() for r in pr],
                'coefficientMax':qmax,'coefficientRMS':qrms,'forceMaxComponent':fmax,'forceRMS':frms,
                'coefficientNearMaxCount99Percent':int(np.count_nonzero(np.abs(q)>=.99*task['coefficient_max'])),
                'editLoss':edit,'maxProtectionConstraint':float(c[:50].max()),'RMSConstraint':float(c[-1]),
                'jointPassed':joint_ok,'ownPassed':joint_ok if arm=='framewise_joint' else edit_ok,
                'protectionPHREffective':float(eff[:50].sum()),'editPHREffective':float(eff[50:75].sum()),'maxEditConstraint':float(c[50:75].max()),'rho':float(a['penalty'])})
        final = arrays[arm+'/T02/final.npz']; last = arrays[row['accepted'][-1]['rawFile']]
        for key in ('x','q','frames','constraints'):
            check(arm+' final lastaccepted exact '+key,np.array_equal(final[key],last[key]))
        check(arm+' qhistory exact',np.array_equal(final['accepted_q_history'],np.stack([arrays[r['rawFile']]['q'] for r in row['accepted']])))
        with np.load(taskdir/config['inputs']['warm_x'], allow_pickle=False) as wz:
            check(arm+' paid warm x exact',np.array_equal(arrays[row['accepted'][0]['rawFile']]['x'],wz['x']))
            check(arm+' warm x raw pin',rawsha(wz['x'])==config['array_manifest']['warm_x']['sha256'])
            near(arm+' warm image replay',arrays[row['accepted'][0]['rawFile']]['frames'],wz['frames'])
            check(arm+' warm image replay byte exact',rawsha(arrays[row['accepted'][0]['rawFile']]['frames'])==rawsha(wz['frames']))
        first=arrays[row['accepted'][0]['rawFile']]
        check(arm+' reset AL',np.count_nonzero(first['multipliers'])==0 and float(first['penalty'])==1.)
        check(arm+' final fields finite positive',np.isfinite(final['velocity']).all() and np.isfinite(final['density']).all() and final['density'].min()>=0)
        near(arm+' final density min',final['density'].min(),row['finalMetrics']['densityMin'])
        near(arm+' final density max',final['density'].max(),row['finalMetrics']['densityMax'])
        check(arm+' final metrics exact accepted',row['finalMetrics']==row['accepted'][-1]['metrics'])
        calls=[c for c in row['calls'] if c['kind'] in ('closure','acceptance')]
        nc=sum(c['kind']=='closure' for c in calls); na=len(calls)-nc
        check(arm+' rollout sequence', [c['rollout'] for c in calls]==list(range(1,len(calls)+1)))
        check(arm+' counts', len(calls)==row['rolloutsStarted']==row['rolloutsCompleted'] and nc==row['closures'] and na==row['acceptanceRollouts']==len(accepted) and len(accepted)==row['returnedSteps']+1 and len(calls)<=baseline['max_rollouts_per_task'])
        check(arm+' return count',sum(c['kind']=='optimizer_step_return' for c in row['calls'])==row['returnedSteps'])
        for i, call in enumerate(row['calls']):
            if call['kind']!='closure':continue
            prc=call['penaltyRecord']; cc=np.array(prc['constraints']); ll=np.array(prc['multipliers']); rr=prc['penalty']
            eff=audit_phr(f'{arm} closure{i}',cc,ll,rr,mask,prc)
            near(f'{arm} closure{i} loss',call['editLoss']+call['regularizer']+eff.sum(),call['loss'])
            check(f'{arm} closure{i} trial',call['stateKind']=='trial_not_accepted')
        for j, update in enumerate(row['outerUpdates']):
            idx=(update['outer']+1)*baseline['steps_per_outer']
            beforeidx=update['outer']*baseline['steps_per_outer']
            a=arrays[row['accepted'][idx]['rawFile']]; b=arrays[row['accepted'][beforeidx]['rawFile']]
            before=float((np.maximum(b['constraints'],0)*mask).max()); after=float((np.maximum(a['constraints'],0)*mask).max())
            near(arm+' AL before'+str(j),before,update['violationBefore']);near(arm+' AL after'+str(j),after,update['violationAfter'])
            near(arm+' AL lambda'+str(j),np.maximum(a['multipliers']+float(a['penalty'])*a['constraints'],0)*mask,update['multipliers'])
            newrho=min(baseline['penalty_max'],float(a['penalty'])*baseline['penalty_growth']) if after>baseline['violation_reduction_factor']*before else float(a['penalty'])
            near(arm+' AL rho'+str(j),newrho,update['newPenalty'])
        if 'budgetRollback' in row:
            rb=row['budgetRollback']
            check(arm+' reserved budget rollback',rb['rolloutsStarted']==row['rolloutsStarted']==row['budget']-1 and rb['returnedStep']==row['returnedSteps'] and not rb['trialAccepted'] and rb['restoredAcceptedX'] and calls[-1]['kind']=='closure')
        arms[arm]={'accepted':accepted,'final':accepted[-1], 'anyEarlierJointPass':any(a['jointPassed'] for a in accepted[:-1]),
            'termination':row['termination'],'rollouts':len(calls),'closures':nc,'acceptances':na,'returnedSteps':row['returnedSteps'],
            'lastAcceptedRollout':row['accepted'][-1]['rollout'],'budgetRollback':row.get('budgetRollback'),
            'outerUpdates':row['outerUpdates'],'maximumAcceptedCoefficient':max(a['coefficientMax'] for a in accepted),
            'maximumAcceptedRMS':max(a['coefficientRMS'] for a in accepted),
            'closureProtectionEffectiveBranchMaximum':max((c['penaltyRecord']['protectedBranchCountEffective'] for c in calls if c['kind']=='closure'),default=0),
            'closureProtectionEffectivePHRMaximum':max((c['penaltyRecord']['protectedPHREffective'] for c in calls if c['kind']=='closure'),default=0)}
    prior=config['prior_cost']
    cost=summary['costLineage']
    previous=json.loads(Path(summary['pinsBefore']['T03-result-summary.json']['path']).read_text(encoding='utf-8'))
    oldjoint=next(a for a in previous['arms'] if a['arm']=='joint')
    near('prior joint rollouts',prior['joint_rollouts'],oldjoint['rolloutsStarted'])
    near('prior joint seconds',prior['joint_seconds'],oldjoint['wallSecondsIncludingAcceptanceAndEvidenceIO'])
    near('prior full T03 rollouts',prior['full_T03_rollouts'],previous['qualification']['rolloutCount']+sum(a['rolloutsStarted'] for a in previous['arms']))
    near('prior full T03 worker time',prior['full_T03_worker_seconds'],previous['totalWorkerWallSeconds'])
    newg0=summary['qualification']['rolloutCount']; newsolve=sum(a['rolloutsStarted'] for a in summary['arms'])
    expected_cost={
      'newQualificationRollouts':newg0,'newSolveRolloutsStarted':newsolve,
      'paidWarmDependencyRolloutsPlusAllT04':prior['joint_rollouts']+newg0+newsolve,
      'paidWarmDependencySecondsPlusT04Worker':prior['joint_seconds']+summary['totalWallSecondsIncludingStartupQualificationAndIO'],
      'fullChronologicalRolloutsIncludingT03':prior['full_T03_rollouts']+newg0+newsolve,
      'fullChronologicalWorkerSecondsIncludingT03':prior['full_T03_worker_seconds']+summary['totalWallSecondsIncludingStartupQualificationAndIO']}
    for key,value in expected_cost.items(): near('cost '+key,value,cost[key])
    result['costLineageRecomputed']=expected_cost
    result['arms']=arms
    result['rawFilesVerified']=len(arrays)
    result['acceptedStatesRecomputed']=sum(len(a['accepted']) for a in arms.values())
    result['interpretation']='One post-hoc ordinary framewise feasibility revision from paid T03 accepted x. Actual final/accepted gates are reported above. This does not isolate explicit constraints from warm start or extra budget, prove infeasibility on failure, or establish a new method/speedup.'
    result['limitations']=['Intermediate accepted final velocity/density were not retained; their finite/density gates remain producer evidence.',
        'Closure c/lambda/rho arithmetic and accounting are rechecked; closure image trajectories and gradients are not saved and cannot be independently replayed here.',
        'G0 checks saved finite differences against saved analytic gradients, not a second differentiation implementation.',
        'Force interpolation is independently re-evaluated on CPU; no model rollout or CUDA work.',
        'Small numerical comparison tolerances authenticate reported reductions; original quality thresholds are evaluated without relaxed margins.']
    result['passed']=all(c['passed'] for c in checks)
    result['checkCount']=len(checks)
    result['failedChecks']=[c for c in checks if not c['passed']]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':result['failedChecks'],'out':str(args.out)},ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
