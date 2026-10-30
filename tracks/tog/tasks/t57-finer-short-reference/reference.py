"""T57: unchanged T56 numerics, four new cases, two immutable saved cases."""
import datetime
import importlib.util
import json
from pathlib import Path
import platform
import sys
import time

START=time.perf_counter()
ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'t56-coupled-reference'
spec=importlib.util.spec_from_file_location('t56_unchanged',OLD/'reference.py')
ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
np=ref.np
assert ref.ROOT.resolve()==OLD.resolve() and ROOT.resolve()!=OLD.resolve()
ref.ROOT=ROOT  # Only output destination changes; do not call the T56 main function.
CASES=[('S256',8.,256,.0025,32),('T128',8.,128,.00125,32),
       ('D192',12.,192,.0025,32),('Q128',8.,128,.0025,64)]

def saved(name,nr):
    record=json.loads((OLD/'local'/(name+'.json')).read_bytes())
    assert record['name']==name and record['radial_cells']==nr and record['R']==8.
    assert record['dt']==.0025 and record['angular_order']==32 and record['steps']==100
    assert [s['time'] for s in record['snapshots']]==[0.,.125,.25]
    for key in ('raw','log'):
        item=record[key]
        assert ref.identity(OLD/'local'/item['path'])=={k:item[k] for k in ('bytes','sha256')}
    g=ref.geometry(8.,nr)
    with np.load(OLD/'local'/(name+'.npz'),allow_pickle=False) as arrays:
        for key in ('r','rc','z'):assert np.array_equal(arrays[key],g[key])
        snapshots=[{key:arrays[key][i].copy() for key in ('q','qr','qz','u','ur','uz','phi','boundary')}
                   for i in range(3)]
        assert arrays['q'].shape==(3,nr,2*nr)
    return record,dict(g=g,snapshots=snapshots)

def main():
    assert platform.python_version()=='3.12.14' and np.__version__=='2.3.5'
    gauss=(np.polynomial.legendre.leggauss(3),np.polynomial.legendre.leggauss(2))
    records=[];fields={};origins={}
    for name,nr in [('S64',64),('S128',128)]:
        record,field=saved(name,nr);records.append(record);fields[name]=field;origins[name]='reused_T56'
    for config in CASES:
        record,field=ref.solve_case(config,gauss)
        records.append(record);fields[record['name']]=field;origins[record['name']]='new_T57'
    byname={c['name']:c for c in records};comparisons=[];tick=time.perf_counter()
    for a,b,kind in [('S64','S128','space'),('S128','S256','space'),('S128','T128','time'),
                     ('S128','D192','domain'),('S128','Q128','angular')]:
        for index,t in enumerate((0.,.125,.25)):
            metrics=ref.compare(fields[a],fields[b],index,gauss)
            sa=byname[a]['snapshots'][index];sb=byname[b]['snapshots'][index]
            metrics.update(axial_centroid_absolute=abs(sa['centroid'][1]-sb['centroid'][1]),
                covariance_relative=float(np.linalg.norm(np.array(sa['covariance'])-np.array(sb['covariance']))/ref.SHAPE_NORM))
            comparisons.append(dict(a=a,b=b,kind=kind,time=t,
                evidence_origin='reused_T56_pair' if a=='S64' else 'new_T57_pair',**metrics))
    ratios=[]
    for index in (1,2):
        coarse=comparisons[index]['vorticity_relative'];fine=comparisons[3+index]['vorticity_relative']
        ratios.append(dict(time=(.125,.25)[index-1],coarse=coarse,fine=fine,
            ratio=coarse/fine if fine>0. else None,small_error_waiver=max(coarse,fine)<=1e-8,
            passed=max(coarse,fine)<=1e-8 or coarse>=1.5*fine))
    initial_checks={c['name']:max(c['initial_analytic_errors'].values())<=
                    (.01 if c['name']=='S64' else .005) for c in records}
    checks=dict(initial_analytic=all(initial_checks.values()),
        all_stage_invariants=all(c['max_CFL']<=.5 and c['max_volume_divergence']<=1e-10 and
            c['minimum_Euler_stage_q']>=0. and c['max_solver_true_residual']<=1e-10 for c in records),
        vorticity_disagreements=all(c['vorticity_relative']<=.01 for c in comparisons),
        velocity_disagreements=all(c['velocity_relative']<=(.02 if c['kind']=='space' else .01) for c in comparisons),
        centroid_disagreements=all(c['axial_centroid_absolute']<=.01 for c in comparisons),
        covariance_disagreements=all(c['covariance_relative']<=.01 for c in comparisons),
        spatial_reduction=all(c['passed'] for c in ratios),
        circulation_ledger=all(c['max_circulation_ledger_relative']<=1e-10 for c in records),
        q_squared_drift=all(max(c['q_squared_relative_drift'])<=.02 for c in records),
        axial_impulse_drift=all(max(c['impulse_relative_drift'])<=.01 for c in records))
    result=dict(schema='t57-finer-short-reference-v1',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        status='qualified_short_reference_only' if all(checks.values()) else 'failed_checks',
        python=platform.python_version(),numpy=np.__version__,executable=sys.executable,
        code=ref.identity(Path(__file__)),numerical_code=ref.identity(OLD/'reference.py'),
        spatial_code=ref.identity(ref.PREVIOUS),cases=records,case_origins=origins,comparisons=comparisons,
        spatial_reductions=ratios,initial_checks=initial_checks,checks=checks,
        comparison_seconds=time.perf_counter()-tick,new_completed_trajectories=4,reused_trajectories=2,time_end=.25,
        prior_T56_status='failed_checks',prior_T56_supervised_seconds=116.53663460002281,
        candidate_trajectories=0,full_t1_task_pass=None,formal_error_certificate=False,
        child_elapsed_before_result_write_seconds=time.perf_counter()-START)
    ref.write_json(ROOT/'result.json',result)
    print(json.dumps(dict(status=result['status'],checks=checks)),flush=True)
    return 0 if all(checks.values()) else 2

if __name__=='__main__':raise SystemExit(main())
