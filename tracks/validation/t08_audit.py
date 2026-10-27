"""Targeted saved-array T08 audit: NumPy CPU, no Torch/producer/model imports.

All per-array checks run, but the report aggregates successes and lists failures.
No simulation, AD replay, optimizer, BLAS, cache callback or timing rerun.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import time
import traceback
import numpy as np


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rawsha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def identical(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and rawsha(a) == rawsha(b)


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def npz(p):
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def crop(a, roi):
    x0, y0, x1, y1 = roi
    return a[..., y0:y1, x0:x1]


def rms(a, axes=None):
    return np.sqrt(np.mean(a*a, axis=axes))


def force_stats(q, n, steps):
    # Separable independent MAC interpolation, not the producer's 8-corner gather.
    parts = []
    for j, off in enumerate(((0., .5, .5), (.5, 0., .5), (.5, .5, 0.))):
        a = q[:, j]
        for axis in range(3):
            s = (np.arange(n, dtype=np.float64)+off[axis])*8/n-off[axis]
            lo = np.floor(s).astype(np.int64)
            shape = [1]*4
            shape[axis+1] = n
            f = (s-np.floor(s)).reshape(shape)
            a = np.take(a, lo % 8, axis=axis+1)*(1-f)+np.take(a, (lo+1) % 8, axis=axis+1)*f
        parts.append(a)
    expanded = np.stack(parts, axis=1)
    maximum, sq = 0., 0.
    for step in range(steps):
        weights = np.maximum(0., 1-np.abs(3.*step/(steps-1)-np.arange(4)))
        f = np.sum(expanded*weights[:, None, None, None, None], axis=0)
        maximum = max(maximum, float(np.max(np.abs(f))))
        sq += float(np.sum(f*f))
    return maximum, float(np.sqrt(sq/(steps*3*n**3)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task', type=Path, default=Path(__file__).resolve().parents[1]/'tog/tasks/t08-ordinary-evaluation-reuse')
    ap.add_argument('--out', type=Path, default=Path(__file__).with_name('t08-audit.json'))
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    td = args.task.resolve()
    root = td/'runs/run-01/worker'
    report = {'schema': 't08-independent-audit-v1', 'createdUTC': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'auditorSHA256': sha(__file__), 'scope': 'Saved arrays, byte equality, original quality/force/PHR gates, authenticated compact G0 and accounting. CPU only; no Torch, simulation, AD, cache callback or timing replay.',
        'groups': {}, 'failures': [], 'limitations': [
            'Live mutation-version identity checks are source-reviewed and supported by authenticated CPU tests/logs, not independently instrumented during the GPU run.',
            'Intermediate accepted velocity/density are not saved; their finite/min statistics remain producer records. Final fields are saved and checked.',
            'Qualification proof omits full frames; this audit recomposes scalar PHR/FD from authenticated q/constraints and saved gradients, not new AD.',
            'Saved timings are checked arithmetically, not remeasured. One execution does not establish statistical performance. T07 and T08 worker walls have different G0 policies.',
            'Memory counters are Torch allocator/cached payload, not process-wide CUDA peak memory.']}

    def check(group, name, ok, detail=None):
        g = report['groups'].setdefault(group, {'checks': 0, 'failed': 0})
        g['checks'] += 1
        if not bool(ok):
            g['failed'] += 1
            row = {'group': group, 'name': name}
            if detail is not None:
                row['detail'] = detail
            report['failures'].append(row)

    def near(group, name, a, b, atol=1e-10, rtol=1e-10):
        a, b = np.asarray(a), np.asarray(b)
        valid = a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
        err = float(np.max(np.abs(a-b))) if valid and a.size else 0.
        check(group, name, valid and np.all(np.abs(a-b) <= atol+rtol*np.abs(b)), {'maxAbsoluteDifference': err})
        if valid:
            g = report['groups'][group]
            g['maxComparedAbsoluteDifference'] = max(g.get('maxComparedAbsoluteDifference', 0.), err)

    def record_file(group, name, p, row):
        check(group, name, sha(p) == row['sha256'] and Path(p).stat().st_size == row['bytes'])

    def read_raw(p, rec, name):
        record_file('saved raw', name, p, rec)
        a = npz(p)
        check('saved raw', name+' keys', set(a) == set(rec['arrays']))
        for key, value in a.items():
            r = rec['arrays'][key]
            check('saved raw', name+':'+key, list(value.shape) == r['shape'] and value.dtype.str == r['dtype'] and rawsha(value) == r['rawSHA256'] and np.isfinite(value).all())
        return a

    try:
        summary, cfg = load(root/'summary.json'), load(td/'config.json')
        oldtd = td.parent/'t07-ordinary-timing-revision'
        oldroot = oldtd/'runs/run-01/worker'
        old = load(oldroot/'summary.json')
        report['inputHashes'] = {'T08summary': sha(root/'summary.json'), 'T07summary': sha(oldroot/'summary.json'), 'config': sha(td/'config.json')}
        task, base = cfg['task'], cfg['baseline']
        freeze = load(td/'freeze.json')
        for name, row in freeze['files'].items():
            record_file('provenance', 'freeze '+name, td/row['path'], row)
        for phase in ('pinsBefore', 'pinsAfter'):
            for name, row in summary[phase].items():
                record_file('provenance', phase+' '+name, row['path'], row)
        check('provenance', 'pins identical', summary['pinsBefore'] == summary['pinsAfter'])
        check('provenance', 'completed unchanged', summary['status'] == 'completed' and summary['sourcesAndInputsUnchanged'])
        check('provenance', 'embedded config', summary['configuration'] == cfg)
        supervisor = load(root.parent/'supervisor.json')
        check('provenance', 'supervisor completed', supervisor['status'] == 'completed' and supervisor['returnCode'] == 0)
        for name in ('stdout.log', 'stderr.log'):
            check('provenance', name, sha(root.parent/name) == supervisor[name]['sha256'])
        trees = [ast.parse((p/'runner.py').read_text(encoding='utf-8')) for p in (oldtd, td)]
        for name in ('Objective', 'acceptance', 'force_stats'):
            nodes = [[ast.dump(n, include_attributes=False) for n in ast.walk(t) if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name == name] for t in trees]
            check('provenance', name+' AST exact', len(nodes[0]) == 1 and nodes[0] == nodes[1])
        oldcfg = load(oldtd/'config.json')
        for key in ('model', 'task', 'array_manifest', 'expected_gpu_uuid', 'constraint_order'):
            check('provenance', key+' same T07', cfg[key] == oldcfg[key])
        for key, value in oldcfg['baseline'].items():
            if key not in ('start_policy', 'budget_policy'):
                check('provenance', 'baseline '+key, cfg['baseline'][key] == value)
        tiny = load(td/'cache-contract-test.json')
        check('provenance', 'nine cache checks current source', len(tiny['checks']) == 9 and all(tiny['checks'].values()) and tiny['passed'] and not tiny['CUDAInitialized'] and tiny['cacheSourceSHA256'] == sha(td/'evaluation_cache.py'))

        arrays = {name: read_raw(root/name, row, name) for name, row in summary['raw'].items()}
        approved = npz(td/cfg['inputs']['approved'])
        target = np.load(td/cfg['inputs']['target'], allow_pickle=False)
        warm = npz(td/cfg['inputs']['warm_x'])
        for name, value in {'approved': approved['frames'], 'v0': approved['v0'], 'rho0': approved['rho0'], 'target_T06': target, 'warm_x': warm['x']}.items():
            rec = cfg['array_manifest'][name]
            check('provenance', 'input '+name, rawsha(value) == rec['sha256'] and list(value.shape) == rec['shape'] and value.dtype.str == rec['dtype'])
        refs = [crop(approved['frames'], roi) for roi in task['protected_rois']]
        pscale = [rms(a, (-2, -1)) for a in refs]
        escale = rms(target, (-2, -1))
        ptau = [np.minimum(task['protect_relative']*s, task['protect_absolute']) for s in pscale]
        etau = np.minimum(task['edit_relative']*escale, task['edit_absolute'])
        check('quality', 'fixed signal minima', all(np.all(s >= task['signal_min']) for s in pscale+[escale]))

        def terms(q, frames):
            pmse = [np.mean((crop(frames, roi)-ref)**2, axis=(-2, -1)) for roi, ref in zip(task['protected_rois'], refs)]
            emse = np.mean((crop(frames, task['edit_roi'])-target)**2, axis=(-2, -1))
            c = np.concatenate([v/t**2-1 for v, t in zip(pmse, ptau)] + [emse/etau**2-1, [np.mean(q*q)/task['coefficient_rms']**2-1]])
            return c, float(np.mean(emse/etau**2)), float(base['regularizer_weight']*np.mean((q/base['regularizer_scale'])**2)), pmse, emse

        def phr(c, lam, rho):
            branch = lam+rho*c
            return (np.maximum(branch, 0)**2-lam**2)/(2*rho), branch

        def check_phr(name, c, lam, rho, rec):
            p, b = phr(c, lam, rho)
            near('PHR', name+' constraints', c, rec['constraints'])
            near('PHR', name+' multipliers', lam, rec['multipliers'])
            near('PHR', name+' penalty', rho, rec['penalty'])
            for key, value in {
                'protectedPHRRaw': p[:50].sum(), 'protectedPHREffective': p[:50].sum(),
                'editPHRRaw': p[50:75].sum(), 'editPHREffective': p[50:75].sum(), 'RMSPHREffective': p[-1], 'effectivePHR': p.sum(),
                'protectedPositiveConstraintCount': np.count_nonzero(c[:50]>0), 'editPositiveConstraintCount': np.count_nonzero(c[50:75]>0),
                'protectedBranchCountRaw': np.count_nonzero(b[:50]>0), 'protectedBranchCountEffective': np.count_nonzero(b[:50]>0),
                'editBranchCountEffective': np.count_nonzero(b[50:75]>0),
                'protectedPositiveMultiplierCount': np.count_nonzero(lam[:50]>0), 'editPositiveMultiplierCount': np.count_nonzero(lam[50:75]>0),
                'protectedPenaltyWeights': np.maximum(b[:50], 0), 'editPenaltyWeights': np.maximum(b[50:75], 0)}.items():
                near('PHR', name+' '+key, value, rec[key])
            return p

        # Authenticate the compact prior proof, not a second G0.
        proof_meta = load(td/'g0-proof.json')
        proof = npz(td/'g0-proof.npz')
        oldmanifest = load(oldtd/'raw-run-manifest.json')
        check('provenance', 'T07 raw summary authenticated', oldmanifest['workerSummarySHA256'] == sha(oldroot/'summary.json') and oldmanifest['files'] == old['raw'])
        check('G0 reuse', 'proof provenance', proof_meta['sourceManifestSHA256'] == sha(oldtd/'raw-run-manifest.json') and proof_meta['sourceSummarySHA256'] == sha(oldtd/'result-summary.json') and proof_meta['sourceRunnerSHA256'] == sha(oldtd/'runner.py') and proof_meta['proof']['sha256'] == sha(td/'g0-proof.npz'))
        vals, aliases = {}, []
        for name, row in proof_meta['files'].items():
            original = oldmanifest['files'][name]
            check('G0 reuse', name+' descriptors', row['original'] == original and set(row['packedKeys']) == set(original['arrays'])-{'frames'})
            vals[name] = {}
            for key, alias in row['packedKeys'].items():
                a, d = proof[alias], original['arrays'][key]
                check('G0 reuse', name+key, rawsha(a) == d['rawSHA256'] and a.dtype.str == d['dtype'] and list(a.shape) == d['shape'] and np.isfinite(a).all())
                vals[name][key] = a
                aliases.append(alias)
        check('G0 reuse', 'coverage', len(aliases) == len(set(aliases)) == 25 and len(vals) == 11 and set(aliases) == set(proof))
        ana = vals['qualification/analytic.npz']
        lam, penalty = ana['multipliers'], float(ana['penalty'])
        qc = base['qualification']
        check('G0 reuse', 'active mask and lambda', np.all(ana['mask'] == 1) and np.all(lam == qc['multiplier']) and penalty == qc['penalty'] and np.all(lam+penalty*ana['constraints'] > 0))
        def proof_loss(a):
            p, _ = phr(a['constraints'], lam, penalty)
            return float(np.mean(a['constraints'][50:75]+1)+base['regularizer_weight']*np.mean((a['q']/base['regularizer_scale'])**2)+p.sum())
        prior = old['qualification']['arms']['framewise_joint']
        near('G0 reuse', 'analytic scalar', proof_loss(ana), prior['loss'], 1e-10, 1e-12)
        fd_errors = []
        for i in range(2):
            d = vals[f'qualification/direction-{i}.npz']['direction']
            gd = float(np.sum(ana['gradient']*d))
            near('G0 reuse', 'direction RMS', rms(d), 1.)
            near('G0 reuse', 'gradient dot', gd, prior['directions'][i]['gradientDotDirection'])
            for j, h in enumerate(qc['steps']):
                plus = proof_loss(vals[f'qualification/probe-{i}-{j}-plus.npz'])
                minus = proof_loss(vals[f'qualification/probe-{i}-{j}-minus.npz'])
                record = prior['directions'][i]['finiteDifferences'][j]
                near('G0 reuse', f'plus {i} {j}', plus, record['plus'], 1e-10, 1e-12)
                near('G0 reuse', f'minus {i} {j}', minus, record['minus'], 1e-10, 1e-12)
                err = abs((plus-minus)/(2*h)-gd)/max(abs(gd), qc['denominator_floor'])
                fd_errors.append(err)
                check('G0 reuse', f'FD {i} {j}', err <= qc['relative_gate'])
        qual = summary['qualification']
        check('G0 reuse', 'no new forward or backward', qual['status'] == 'reused_authenticated' and qual['passed'] and qual['rolloutCount'] == qual['backwardCalls'] == 0 and qual['priorCost']['rollouts'] == 9 and qual['priorCost']['backwardCalls'] == 1)
        near('G0 reuse', 'raw errors', fd_errors, qual['compactProof']['rawScalarFDErrors'], 1e-8, 1e-8)
        check('G0 reuse', 'same runtime', summary['environment'] == qual['expectedEnvironment'])
        check('provenance', 'actual device UUID', summary['environment']['uuid'].removeprefix('GPU-') == cfg['expected_gpu_uuid'].removeprefix('GPU-'))
        report['qualification'] = {'source': 'T07', 'newForwards': 0, 'newBackwards': 0, 'recomputedErrors': fd_errors}

        check('accounting', 'single arm', len(summary['arms']) == 1)
        arm, oldarm = summary['arms'][0], old['arms'][0]
        accepted, oldaccepted = arm['accepted'], oldarm['accepted']
        check('cross-run bytes', 'accepted count', len(accepted) == len(oldaccepted))
        cross_diffs, sequence = [], []
        cross_exact = 0
        for i, entry in enumerate(accepted):
            a, m = arrays[entry['rawFile']], entry['metrics']
            name = f'accepted {i}'
            near('quality', name+' tanh', a['q'], task['coefficient_max']*np.tanh(a['x']), 1e-14, 1e-14)
            c, edit, reg, pmse, emse = terms(a['q'], a['frames'])
            near('quality', name+' constraints', c, a['constraints'])
            near('quality', name+' recorded constraints', c, m['constraints'])
            near('quality', name+' edit loss', edit, m['editLoss'])
            near('quality', name+' reg', reg, m['regularizer'])
            check('quality', name+' full mask', a['mask'].shape == (76,) and np.all(a['mask'] == 1))
            fpmax, fprms = force_stats(a['q'], cfg['model']['n'], cfg['model']['steps'])
            qmax, qrms = float(np.max(np.abs(a['q']))), float(rms(a['q']))
            for key, value in {'coefficientMax': qmax, 'coefficientRMS': qrms, 'forceMaxComponent': fpmax, 'forceRMS': fprms}.items():
                near('quality', name+' '+key, value, m[key])
            erms = np.sqrt(emse)
            prms = [np.sqrt(v) for v in pmse]
            eok = (erms <= task['edit_absolute']) & (erms/escale <= task['edit_relative'])
            pok = [(r <= task['protect_absolute']) & (r/s <= task['protect_relative']) for r, s in zip(prms, pscale)]
            near('quality', name+' edit abs', erms, m['edit']['absoluteRMS'])
            near('quality', name+' edit rel', erms/escale, m['edit']['relativeRMS'])
            check('quality', name+' edit frame gates', np.array_equal(eok, m['edit']['passedFrames']) and bool(np.all(eok)) == m['edit']['passed'])
            for j, (r, s) in enumerate(zip(prms, pscale)):
                near('quality', name+f' protect{j} abs', r, m['protected'][j]['absoluteRMS'])
                near('quality', name+f' protect{j} rel', r/s, m['protected'][j]['relativeRMS'])
                check('quality', name+f' protect{j} frame gates', np.array_equal(pok[j], m['protected'][j]['passedFrames']) and bool(np.all(pok[j])) == m['protected'][j]['passed'])
            image_force_ok = bool(np.all(eok) and all(np.all(p) for p in pok) and qmax <= task['coefficient_max'] and qrms <= task['coefficient_rms'] and fpmax <= task['applied_force_max'] and np.min(a['frames']) >= 0 and np.max(a['frames']) <= 1)
            expected_pass = image_force_ok and m['finite'] and m['densityMin'] >= 0
            check('quality', name+' pass', bool(m['jointPassed']) == bool(expected_pass) and bool(m['passed']) == bool(expected_pass))
            p = check_phr(name, c, a['multipliers'], float(a['penalty']), entry['penaltyRecord'])
            outer_index = max(0, (i-1)//base['steps_per_outer'])
            expected_lam = np.zeros(76) if outer_index == 0 else np.asarray(arm['outerUpdates'][outer_index-1]['multipliers'])
            expected_penalty = base['initial_penalty'] if outer_index == 0 else arm['outerUpdates'][outer_index-1]['newPenalty']
            near('PHR', name+' current outer lambda', a['multipliers'], expected_lam)
            near('PHR', name+' current outer rho', float(a['penalty']), expected_penalty)
            near('PHR', name+' objective', edit+reg+p.sum(), entry['ALObjective'])
            sequence.append({'index': i, 'returnedStep': entry['returnedStep'], 'realForward': entry['forwardExecuted'], 'cacheResult': entry['cacheResult'], 'editPassedFrames': int(eok.sum()), 'protectPassedFrames': int(sum(p.sum() for p in pok)), 'jointPassed': bool(expected_pass)})
            if i < len(oldaccepted):
                oa = read_raw(oldroot/oldaccepted[i]['rawFile'], old['raw'][oldaccepted[i]['rawFile']], 'T07 '+oldaccepted[i]['rawFile'])
                for key in ('x', 'q', 'frames'):
                    same = identical(a[key], oa[key])
                    check('cross-run bytes', f'{i} {key} shape/dtype', a[key].shape == oa[key].shape and a[key].dtype == oa[key].dtype)
                    cross_exact += int(same)
                    if not same:
                        delta = a[key]-oa[key]
                        denom = float(np.sum(oa[key]*oa[key]))
                        cross_diffs.append({'index': i, 'array': key, 'T07rawSHA256': rawsha(oa[key]), 'T08rawSHA256': rawsha(a[key]),
                            'maxAbsoluteDifference': float(np.max(np.abs(delta))), 'numericallyDifferentElements': int(np.count_nonzero(delta)),
                            'relativeL2': float(np.sqrt(np.sum(delta*delta)/denom)) if denom else None})
        report['acceptedSequence'] = sequence
        report['crossRun'] = {'T07acceptedCount': len(oldaccepted), 'T08acceptedCount': len(accepted), 'comparedArrays': 3*min(len(accepted), len(oldaccepted)),
            'byteExactArrays': cross_exact, 'allComparedArraysByteExact': not cross_diffs, 'differences': cross_diffs,
            'interpretation': 'Cross-run byte equality is an observed equivalence result, not a predeclared correctness gate. Differences prohibit a byte-identical trajectory claim; within-run paid-final equality remains mandatory.'}
        first, last = arrays[accepted[0]['rawFile']], arrays[accepted[-1]['rawFile']]
        for key in ('x', 'q', 'frames'):
            check('warm/final bytes', 'T05 initial '+key, identical(first[key], warm[key]))
        prefix = arm['arm']+'/T06/'
        final, verified = arrays[prefix+'final.npz'], arrays[prefix+'final-verification.npz']
        for key in ('x', 'q', 'frames', 'constraints'):
            check('warm/final bytes', 'final last '+key, identical(final[key], last[key]))
        for key in ('x', 'q', 'frames', 'constraints', 'velocity', 'density'):
            check('warm/final bytes', 'real final '+key, identical(final[key], verified[key]))
        check('warm/final bytes', 'history', identical(final['accepted_q_history'], np.stack([arrays[e['rawFile']]['q'] for e in accepted])))
        check('quality', 'saved final physical/image ranges', np.isfinite(final['velocity']).all() and np.isfinite(final['density']).all() and np.min(final['density']) >= 0 and np.min(final['frames']) >= 0 and np.max(final['frames']) <= 1)
        near('quality', 'final density minimum', np.min(final['density']), arm['finalMetrics']['densityMin'])
        near('quality', 'final density maximum', np.max(final['density']), arm['finalMetrics']['densityMax'])
        near('quality', 'final alpha minimum', np.min(final['frames']), arm['finalMetrics']['alphaMin'])
        near('quality', 'final alpha maximum', np.max(final['frames']), arm['finalMetrics']['alphaMax'])
        check('quality', 'final report original gates', arm['finalMetrics'] == accepted[-1]['metrics'] and arm['taskGatesPassed'] == sequence[-1]['jointPassed'] and summary['allOriginalGatesPassed'] == sequence[-1]['jointPassed'])
        check('quality', 'final independent gates same', arm['finalVerification']['metrics'] == arm['finalMetrics'])

        calls = arm['calls']
        closures = [r for r in calls if r['kind'] == 'closure']
        accalls = [r for r in calls if r['kind'] == 'acceptance']
        finals = [r for r in calls if r['kind'] == 'final_verification']
        returns = [r for r in calls if r['kind'] == 'optimizer_step_return']
        for i, (entry, call) in enumerate(zip(accepted, accalls)):
            check('accounting', f'accepted call match {i}', entry['returnedStep'] == i and all(entry[k] == call[k] for k in ('reason', 'rollout', 'seconds', 'forwardExecuted', 'cacheResult', 'cacheLookupSeconds', 'forwardSeconds', 'acceptanceAndForceSeconds')))
        count, hits, misses = 0, 0, 0
        for i, call in enumerate(calls):
            kind = call['kind']
            if kind == 'closure':
                check('accounting', f'closure reserve {i}', count < arm['budget']-2)
                count += 1
                check('cache evidence', f'finite stored trial {i}', call['stateKind'] == 'trial_not_accepted' and call['cacheStored'] and np.isfinite(call['gradientL2']))
                rec = call['penaltyRecord']
                cc, ll, rr = np.asarray(rec['constraints']), np.asarray(rec['multipliers']), rec['penalty']
                expected_lam = np.zeros(76) if call['outer'] == 0 else np.asarray(arm['outerUpdates'][call['outer']-1]['multipliers'])
                expected_rho = base['initial_penalty'] if call['outer'] == 0 else arm['outerUpdates'][call['outer']-1]['newPenalty']
                near('PHR', f'closure {i} current lambda', ll, expected_lam)
                near('PHR', f'closure {i} current rho', rr, expected_rho)
                pp = check_phr(f'closure {i}', cc, ll, rr, rec)
                near('PHR', f'closure loss {i}', call['editLoss']+call['regularizer']+pp.sum(), call['loss'])
            elif kind == 'acceptance':
                if call['forwardExecuted']:
                    check('accounting', f'acceptance reserve {i}', count < arm['budget']-1)
                    count += 1
                    misses += int(call['reason'] != 'initial_paid_warm')
                else:
                    hits += 1
                    check('cache evidence', f'valid hit record {i}', call['cacheResult'] == 'hit' and call['forwardSeconds'] == 0 and i > 0 and calls[i-1]['kind'] == 'optimizer_step_return')
            elif kind == 'final_verification':
                check('accounting', 'final slot', count < arm['budget'])
                count += 1
            else:
                check('accounting', f'known call kind {i}', kind == 'optimizer_step_return')
            if 'rollout' in call:
                check('accounting', f'forward ledger {i}', call['rollout'] == count)
            check('accounting', f'nonnegative finite time {i}', np.isfinite(call['seconds']) and call['seconds'] >= 0)
        check('accounting', 'all totals', count == arm['rolloutsStarted'] == arm['rolloutsCompleted'] and count <= arm['budget'] and len(closures) == arm['closures'] == arm['backwardCalls'] and len(finals) == arm['finalVerificationRollouts'] == 1 and len(returns) == arm['returnedSteps'] and len(accalls) == arm['acceptanceChecks'] == len(accepted))
        check('accounting', 'cache counters', hits == arm['acceptanceCacheHits'] and misses == arm['acceptanceCacheMisses'] and arm['initialForwardCalls'] == 1 and arm['acceptanceRollouts'] == misses+1 and arm['cacheStoreFailures'] == sum(not c['cacheStored'] for c in closures))
        check('accounting', 'same optimizer steps/backwards T07', arm['returnedSteps'] == oldarm['returnedSteps'] and arm['backwardCalls'] == oldarm['closures'])
        check('cache evidence', 'invalidations', arm['cacheInvalidations'] == len(arm['outerUpdates'])+int('budgetRollback' in arm))
        for j, update in enumerate(arm['outerUpdates']):
            before = arrays[accepted[j*base['steps_per_outer']]['rawFile']]
            after = arrays[accepted[(j+1)*base['steps_per_outer']]['rawFile']]
            new_lam = np.maximum(0., before['multipliers']+float(before['penalty'])*after['constraints'])
            vb = float(np.max(np.maximum(before['constraints'], 0)))
            va = float(np.max(np.maximum(after['constraints'], 0)))
            new_rho = min(base['penalty_max'], float(before['penalty'])*base['penalty_growth']) if va > base['violation_reduction_factor']*vb else float(before['penalty'])
            near('PHR', f'outer{j} lambda update', new_lam, update['multipliers'])
            near('PHR', f'outer{j} violation before', vb, update['violationBefore'])
            near('PHR', f'outer{j} violation after', va, update['violationAfter'])
            near('PHR', f'outer{j} rho update', new_rho, update['newPenalty'])
            check('PHR', f'outer{j} new history', update['historyResetBeforeNextOuter'])
        if 'budgetRollback' in arm:
            b = arm['budgetRollback']
            check('accounting', 'rollback not accepted', b['restoredAcceptedX'] and not b['trialAccepted'] and b['returnedStep'] == arm['returnedSteps'] and arm['lastCacheInvalidation'] == 'budget_rollback')
        check('cache evidence', 'max payload', arm['maxCachePayloadBytes'] == sum(final[k].nbytes for k in ('x', 'frames', 'velocity', 'density')))
        near('accounting', 'cache write sum', sum(c['cacheWriteSeconds'] for c in closures), arm['cacheWriteSeconds'])
        for name, records in [('synchronizedClosureSeconds', closures), ('synchronizedAcceptanceSeconds', accalls), ('synchronizedFinalVerificationSeconds', finals)]:
            near('accounting', name, sum(c['seconds'] for c in records), arm[name])
        near('accounting', 'new cost count', count, summary['costScope']['newSolveRolloutsStarted'])
        near('accounting', 'new backward count', len(closures), summary['costScope']['newSolveBackwardCalls'])
        check('accounting', 'no new G0 cost', summary['costScope']['newQualificationRollouts'] == summary['costScope']['newQualificationBackwardCalls'] == 0)
        check('accounting', 'no method speed claim', summary['measuredMethodSpeedup'] is False)
        fv = arm['finalVerification']
        check('quality', 'verification report true', fv['realForward'] and fv['passed'] and all(fv['exactAcceptedArrays'].values()) and arm['finalVerificationPassed'] and summary['allReuseVerificationsPassed'])
        report['cost'] = {'trueForwards': count, 'backwards': len(closures), 'initialForwards': 1, 'cacheHits': hits, 'cacheMisses': misses, 'realFinalForwards': len(finals), 'returnedSteps': len(returns),
            'T07solveForwards': oldarm['rolloutsStarted'], 'forwardReduction': oldarm['rolloutsStarted']-count,
            'closureSeconds': arm['synchronizedClosureSeconds'], 'cacheWriteSecondsNested': arm['cacheWriteSeconds'],
            'acceptanceSeconds': arm['synchronizedAcceptanceSeconds'], 'finalVerificationSeconds': arm['synchronizedFinalVerificationSeconds'],
            'solveSecondsIncludingIO': arm['wallSecondsIncludingAcceptanceAndEvidenceIO'], 'T07solveSecondsIncludingIO': oldarm['wallSecondsIncludingAcceptanceAndEvidenceIO'],
            'observedSolveRatioNotStatisticalSpeedup': arm['wallSecondsIncludingAcceptanceAndEvidenceIO']/oldarm['wallSecondsIncludingAcceptanceAndEvidenceIO'],
            'workerSecondsDifferentG0Policies': summary['totalWallSecondsIncludingStartupQualificationAndIO'], 'maxCachePayloadBytes': arm['maxCachePayloadBytes'], 'sourceSolutionCostSeparate': summary['costScope']['sourceSolutionRecordedCost']}
        fc, fe, fr, fp, ee = terms(final['q'], final['frames'])
        report['final'] = {'editWorstRelativeRMS': float(np.max(np.sqrt(ee)/escale)), 'protectWorstRelativeRMS': float(max(np.max(np.sqrt(v)/s) for v,s in zip(fp, pscale))), 'coefficientMax': float(np.max(np.abs(final['q']))), 'coefficientRMS': float(rms(final['q'])), 'jointPassed': sequence[-1]['jointPassed'], 'firstJointPassingAcceptedIndex': next((r['index'] for r in sequence if r['jointPassed']), None)}
        report['status'] = 'completed'
    except Exception as exc:
        report.update(status='audit_exception', exception=repr(exc), traceback=traceback.format_exc())
    report['checkCount'] = sum(g['checks'] for g in report['groups'].values())
    report['failedCount'] = sum(g['failed'] for g in report['groups'].values())
    report['passed'] = report['status'] == 'completed' and report['failedCount'] == 0
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'passed': report['passed'], 'checks': report['checkCount'], 'failures': report['failedCount'], 'out': str(args.out)}, ensure_ascii=False))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
