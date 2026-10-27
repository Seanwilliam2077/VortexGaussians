"""Independent saved-array T05 audit. CPU NumPy only; no producer/core imports.

Recomputes image/force/PHR/FD metrics, not trajectories or reverse derivatives.
No np.linalg or other BLAS operations. Existing audit outputs are never replaced.
"""
from pathlib import Path
import argparse
import ast
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
    ap.add_argument('--task', type=Path, default=Path(__file__).resolve().parents[1]/'tog/tasks/t05-framewise-cold-start')
    ap.add_argument('--out', type=Path, default=Path(__file__).with_name('t05-audit.json'))
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
    result = {'schema': 't05-independent-audit-v1', 'createdUTC': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'scope': 'Saved-array, input/source, metric, force interpolation, FD and accounting audit; no Torch/producer import, no simulation, no optimization, no reverse-AD replay.',
              'sourceSHA256': sha(__file__), 'summarySHA256': sha(summary_path), 'checks': checks}
    result['auditHistory'] = []

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

    # Reuse authentication uses only retained qualification arrays and metadata.
    # This does not re-read omitted G0 images or re-execute differentiation.
    pins = summary['pinsBefore']
    previous_path = Path(pins['T04-result-summary.json']['path'])
    previous = json.loads(previous_path.read_text(encoding='utf-8'))
    oldconfig = json.loads(Path(pins['T04-config.json']['path']).read_text(encoding='utf-8'))
    oldraw = json.loads(Path(pins['T04-raw-run-manifest.json']['path']).read_text(encoding='utf-8'))
    proofmeta = json.loads((taskdir/'g0-proof.json').read_text(encoding='utf-8'))
    qrec = summary['qualification']; priorqual = previous['qualification']
    check('reuse completed prerequisite', previous['status']=='completed' and previous['sourcesAndInputsUnchanged']
          and priorqual['status']=='completed' and priorqual['passed'] and priorqual['rolloutCount']==9 and priorqual['backwardCalls']==1)
    check('new G0 work zero', qrec['status']=='reused_authenticated' and qrec['passed'] and qrec['rolloutCount']==0 and qrec['backwardCalls']==0)
    check('reuse source report', qrec['sourceReportSHA256']==sha(previous_path)==proofmeta['sourceSummarySHA256'])
    check('proof manifests', proofmeta['sourceManifestSHA256']==sha(pins['T04-raw-run-manifest.json']['path'])
          and proofmeta['sourceRunnerSHA256']==sha(pins['T04-runner.py']['path'])
          and proofmeta['producerSHA256']==sha(pins['prepare_qualification_proof.py']['path']))
    for oldname,newname in [('runner.py','T04-runner.py'),('config.json','T04-config.json'),('freeze.json','T04-freeze.json'),
                            ('core.py','core.py'),('approved.npz','approved.npz'),('target-edit.npy','target-edit.npy'),('brief.json','brief.json')]:
        check('reuse source '+oldname, previous['pins'][oldname]['sha256']==pins[newname]['sha256'])
    for key in ('model','task','constraint_order','expected_gpu_uuid'):
        check('reuse config '+key, oldconfig[key]==config[key])
    check('reuse raw input contract', {k:v for k,v in oldconfig['array_manifest'].items() if k!='warm_x'}==config['array_manifest'])
    check('reuse numerical baseline', {k:v for k,v in oldconfig['baseline'].items() if k!='start_policy'}==
          {k:v for k,v in baseline.items() if k!='start_policy'})
    check('cold input allowlist',set(config['inputs'])=={'approved','target','brief','core'})
    for name in ('Objective','acceptance','force_stats','penalty_record','closure'):
        nodes=[]
        for path in (Path(pins['T04-runner.py']['path']),taskdir/'runner.py'):
            tree=ast.parse(path.read_text(encoding='utf-8'))
            found=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name]
            check('unique AST '+name+' '+path.parent.name,len(found)==1)
            nodes.append(ast.dump(found[0],include_attributes=False))
        check('reuse AST exact '+name,nodes[0]==nodes[1])
    for key in ('torch','numpy','torchBuildCUDA','dtype','threads','device','uuid','gpuName'):
        check('runtime reuse '+key,summary['environment'][key]==previous['environment'][key]==qrec['expectedEnvironment'][key])
    check('actual GPU UUID',summary['environment']['uuid'].removeprefix('GPU-')==config['expected_gpu_uuid'].removeprefix('GPU-')
          and summary['runtimePolicy']['CUDA_VISIBLE_DEVICES']==config['expected_gpu_uuid'])
    expectednames={'qualification/analytic.npz'}|{f'qualification/direction-{i}.npz' for i in range(2)}|{
        f'qualification/probe-{i}-{j}-{sign}.npz' for i in range(2) for j in range(2) for sign in ('plus','minus')}
    check('only fixed G0 files',set(proofmeta['files'])==expectednames=={k for k in oldraw['files'] if k.startswith('qualification/')})
    proofpath=taskdir/'g0-proof.npz'
    check('proof file',sha(proofpath)==proofmeta['proof']['sha256']==qrec['compactProof']['sha256']
          and proofpath.stat().st_size==proofmeta['proof']['bytes']==qrec['compactProof']['bytes'])
    ga={}; keys=[]
    with np.load(proofpath,allow_pickle=False) as z:
        for name, record in proofmeta['files'].items():
            check('proof original descriptor '+name,record['original']==oldraw['files'][name])
            check('proof retained allowlist '+name,set(record['packedKeys'])==set(record['original']['arrays'])-{'frames'})
            ga[name]={}
            for key,packedkey in record['packedKeys'].items():
                keys.append(packedkey); value=z[packedkey]; rec=record['original']['arrays'][key]
                ga[name][key]=value
                check('proof raw '+name+' '+key,rawsha(value)==rec['rawSHA256'] and list(value.shape)==rec['shape']
                      and value.dtype.str==rec['dtype'] and np.isfinite(value).all())
        check('proof exact packed keys',len(keys)==len(set(keys)) and set(keys)==set(z.files))
    check('proof retained count',len(keys)==qrec['compactProof']['verifiedRawArrayCount'])
    check('proof retained bytes',sum(a.nbytes for row in ga.values() for a in row.values())==proofmeta['retainedArrayBytes'])
    ana=ga['qualification/analytic.npz']; qc=baseline['qualification']; mask=np.ones(76)
    near('G0 q parameterization',ana['q'],task['coefficient_max']*np.tanh(ana['x']))
    near('G0 initial x amplitude',np.abs(ana['x']),np.full_like(ana['x'],qc['x_amplitude']))
    near('G0 all mask',ana['mask'],mask); near('G0 lambda',ana['multipliers'],np.full(76,qc['multiplier']))
    near('G0 rho',ana['penalty'],qc['penalty'])
    check('G0 constraint shape',ana['constraints'].shape==(76,))
    raw,eff,branch=phr(ana['constraints'],ana['multipliers'],float(ana['penalty']),mask)
    check('G0 all branches active',np.all(branch>0))
    oldarm=priorqual['arms']['framewise_joint']
    near('G0 recorded branch margin',branch.min(),oldarm['minimumActivePHRBranchMargin'])
    def proofloss(a):
        return float(np.mean(a['constraints'][50:75]+1)+baseline['regularizer_weight']*np.mean((a['q']/baseline['regularizer_scale'])**2)
                     +phr(a['constraints'],ana['multipliers'],float(ana['penalty']),mask)[1].sum())
    near('G0 analytic scalar',proofloss(ana),oldarm['loss'],atol=1e-10,rtol=1e-12)
    fd_errors=[]; scalar_errors=[]
    for i in range(qc['directions']):
        d=ga[f'qualification/direction-{i}.npz']['direction']; near('G0 direction RMS '+str(i),rms(d),1.)
        gd=float(np.sum(ana['gradient']*d)); olddir=oldarm['directions'][i]
        near('G0 independent gradient dot '+str(i),gd,olddir['gradientDotDirection'],atol=1e-10,rtol=1e-12)
        for j,h in enumerate(qc['steps']):
            vals=[]
            for sign in ('plus','minus'):
                a=ga[f'qualification/probe-{i}-{j}-{sign}.npz']
                near(f'G0 q {i} {j} {sign}',a['q'],task['coefficient_max']*np.tanh(ana['x']+(h if sign=='plus' else -h)*d))
                val=proofloss(a); vals.append(val)
                near(f'G0 scalar {i} {j} {sign}',val,olddir['finiteDifferences'][j][sign],atol=1e-10,rtol=1e-12)
                scalar_errors.append(abs(val-olddir['finiteDifferences'][j][sign]))
            fd=(vals[0]-vals[1])/(2*h); error=abs(fd-gd)/max(abs(gd),qc['denominator_floor']); fd_errors.append(error)
            check(f'G0 reused raw FD gate {i} {h}',error<=qc['relative_gate'],{'relativeError':error})
    near('G0 reported raw FD',fd_errors,qrec['compactProof']['rawScalarFDErrors'],atol=1e-12,rtol=1e-8)
    result['qualification']={'mode':'reused_authenticated','retainedRawArrays':len(keys),'maximumRecomputedRelativeFD':max(fd_errors),
        'maximumScalarRecordDifference':max(scalar_errors),'newForwardCalls':0,'newBackwardCalls':0,
        'limitations':'Saved constraints/gradients authenticated and scalar PHR/FD recomputed; no new image-to-constraint calculation, differentiation or model replay.'}

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
        first=arrays[row['accepted'][0]['rawFile']]
        check(arm+' zero x and q', np.count_nonzero(first['x'])==0 and np.count_nonzero(first['q'])==0 and row['warmStart']=='zero_cold_start')
        check(arm+' zero initial image byte exact approved', rawsha(first['frames'])==rawsha(approved))
        check(arm+' zero initial metadata', row['accepted'][0]['reason']=='initial_zero' and row['accepted'][0]['rollout']==1 and row['accepted'][0]['returnedStep']==0)
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
    # Charge this cold solve only. Reused G0 is a prerequisite, not new rollout work.
    newsolve=sum(a['rollouts'] for a in arms.values())
    near('cost solve calls',newsolve,summary['costScope']['newSolveRolloutsStarted'])
    near('cost G0 calls',0,summary['costScope']['newQualificationRollouts'])
    near('cost worker seconds',summary['totalWallSecondsIncludingStartupQualificationAndIO'],summary['costScope']['currentWorkerSeconds'])
    priorcost=summary['costScope']['priorQualification']
    near('cost prerequisite calls',priorqual['rolloutCount'],priorcost['rollouts'])
    near('cost prerequisite backward',priorqual['backwardCalls'],priorcost['backwardCalls'])
    near('cost prerequisite seconds',priorqual['wallSecondsIncludingEvidenceIO'],priorcost['wallSecondsIncludingEvidenceIO'])
    result['costRecomputed']={'newSolveRollouts':newsolve,'newQualificationRollouts':0,
        'coldSolveSeconds':sum(a['wallSecondsIncludingAcceptanceAndEvidenceIO'] for a in summary['arms']),
        'workerSecondsIncludingStartupAuthenticationIO':summary['totalWallSecondsIncludingStartupQualificationAndIO'],
        'supervisorSeconds':supervisor['wallSeconds'],
        'priorQualificationSeparate':priorcost,
        'priorOptimizationCostsIncluded':False}
    for row in summary['arms']:
        closuresec=sum(c['seconds'] for c in row['calls'] if c['kind']=='closure')
        acceptsec=sum(c['seconds'] for c in row['calls'] if c['kind']=='acceptance')
        near('timing closure subtotal',closuresec,row['synchronizedClosureSeconds'])
        near('timing acceptance subtotal',acceptsec,row['synchronizedAcceptanceSeconds'])
        check('timing nonnegative and nested',all(c['seconds']>=0 for c in row['calls']) and
              closuresec+acceptsec<=row['wallSecondsIncludingAcceptanceAndEvidenceIO']<=summary['totalWallSecondsIncludingStartupQualificationAndIO']<=supervisor['wallSeconds']<=supervisor['wallLimitSeconds'])
        check('quality termination',row['termination']=='quality_pass' and row['passed']==arms[row['arm']]['final']['jointPassed'])
        check('stopped at first accepted joint pass',not arms[row['arm']]['anyEarlierJointPass'])
        check('completed no budget rollback',('budgetRollback' not in row) and arms[row['arm']]['lastAcceptedRollout']==row['rolloutsStarted'])
    check('all original final gates',summary['allOriginalGatesPassed']==all(a['final']['jointPassed'] for a in arms.values()))
    check('configuration saved exact',summary['configuration']==config)
    check('supervisor pins consistent',supervisor['sourceAndInputPinsAfter']==summary['pinsAfter'])
    # Published copy must remain the same result, not a differently selected solution.
    published=json.loads((taskdir/'result-summary.json').read_text(encoding='utf-8'))
    near('published current worker seconds',published['totalWorkerWallSeconds'],summary['totalWallSecondsIncludingStartupQualificationAndIO'])
    check('published qualification unchanged',published['qualification']==summary['qualification'])
    check('published costs unchanged',published['costScope']==summary['costScope'])
    for name,row in published['publishedFinalArrays'].items():
        check('published final hash '+name,sha(taskdir/name)==row['sha256']==sha(root/'framewise_joint/T02/final.npz'))
    result['publicationSummarySHA256']=sha(taskdir/'result-summary.json')
    result['arms']=arms
    result['rawFilesVerified']=len(arrays)
    result['acceptedStatesRecomputed']=sum(len(a['accepted']) for a in arms.values())
    result['interpretation']='One fixed ordinary 76-constraint cold-start solve on the same development target. No previous optimized control/state is used. This audits numerical feasibility and observed cost; it does not establish a new method, statistical speedup, holdout generalization or comparative optimizer causality.'
    result['limitations']=['Intermediate accepted velocity/density were not retained; their finite/density gates remain producer evidence; final fields are independently checked.',
        'Closure constraint/multiplier arithmetic and accounting are rechecked, not closure image trajectories or reverse gradients.',
        'Reused G0 compact proof omits images. It authenticates prior raw constraints/gradient and recomputes scalar finite differences without a new derivative experiment.',
        'Force interpolation is independently evaluated on CPU from all accepted q; no model rollout or CUDA work.',
        'Quality thresholds are evaluated without relaxed margins. Small tolerances only compare independently recomputed reductions to saved records.',
        'Timing sums and scope are audited; wall-clock values are saved measurements, not independently repeated timing.',
        'Torch allocator records are not complete process/device memory peaks.']
    result['passed']=all(c['passed'] for c in checks)
    result['checkCount']=len(checks)
    result['failedChecks']=[c for c in checks if not c['passed']]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failed':result['failedChecks'],'out':str(args.out)},ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
