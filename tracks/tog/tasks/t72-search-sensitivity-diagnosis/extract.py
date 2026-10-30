"""Saved-scalar diagnostic only: no scientific imports or calls to model code."""
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

START = time.perf_counter()
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = HERE.parent/'t71-causal-full-window/result.json'

def identity(path):
    assert path.suffix.lower() not in ('.npy','.npz')
    raw = path.read_bytes()
    return dict(path=path.relative_to(REPO).as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

before = identity(SOURCE)
assert before['sha256'] == 'cf97d25c2fe6d9759a338f2e2890f93569ce8e0f4c4f4aa463fe574c2e6b7e4b'
r = json.loads(SOURCE.read_bytes())
assert r['numerical_qualified'] and r['verdict'] == 'time_or_reference_sensitive_inconclusive'
assert [p['completed_steps'] for p in r['paths']] == [16,32] and len(r['searches']) == 48
records = []
for item in r['searches']:
    s,h,index = item['search'],item['path_h'],item['step']
    old,new = s['current_state'],s['selected_state']
    scales = [s['search_scales']['R'],s['search_scales']['Z'],s['search_scales']['Z']]
    matches = []
    for perm in itertools.permutations((0,1)):
        delta = [[new['geometry'][perm[i]][k]-old['geometry'][i][k] for k in range(3)] for i in range(2)]
        cost = math.fsum((delta[i][k]/scales[k])**2 for i in range(2) for k in range(3))
        matches.append((cost,perm,delta))
    match = min(matches,key=lambda x:(x[0],x[1]))
    boundary = []
    for slot,g in enumerate(new['geometry']):
        for coord in range(3):
            for side in range(2):
                if g[coord] == s['search_bounds'][coord][side]:
                    boundary.append(dict(slot=slot,coordinate=coord,side=side))
    ends = {}
    for poll in s['polls']:
        ends[poll['start'],poll['level']] = poll
    capped = [dict(start=k[0],level=k[1]) for k,p in ends.items() if p['poll']==7 and p['improved']]
    path = next(p for p in r['paths'] if p['h']==h)
    state = path['steps'][index]
    primary = state['confirmation']['routes'][0]
    assert primary['order'] == 128
    direct_gain = primary['N_unchanged']-primary['N']
    stored_gain = s['selected_record']['J']-s['control']['J']
    assert abs(direct_gain-stored_gain) <= 1e-10+1e-9*max(abs(direct_gain),abs(stored_gain))
    initial = path['steps'][0]['moments']
    records.append(dict(h=h,step=index,time=index*h,
        current=old,selected=new,scales=s['search_scales'],
        unchanged_geometry=new['geometry']==old['geometry'],
        inherited_selected_slots=sum(g in old['geometry'] for g in new['geometry']),
        matched_permutation=list(match[1]),matched_delta=match[2],
        matched_normalized_geometry_distance=math.sqrt(match[0]),
        finest_poll=[.025*scales[0],.025*scales[1],.05*scales[2]],
        finest_poll_over_h=[.025*scales[0]/h,.025*scales[1]/h,.05*scales[2]/h],
        selected_boundary_hits=boundary,poll_caps=capped,
        selected_from_initial_bank=s['selected_record']['evaluation_index']<s['summary']['bank_proposals'],
        selected_classification_unresolved=s['summary']['selected_classification_unresolved'],
        pair_classification_unresolved_count=s['summary']['floating_point_unresolved_pairs'],
        target_error=primary['relative_target_error'],unchanged_target_error=primary['unchanged_relative_target_error'],
        direct_gain=direct_gain,saved_J_gain=stored_gain,gain_over_h_squared=direct_gain/(h*h),
        residual_fraction=primary['N']/primary['N_unchanged'],
        gamma_relative_drift=state['moments']['Gamma']/initial['Gamma']-1,
        impulse_relative_drift=state['moments']['I_z']/initial['I_z']-1,
        counters=s['counters']))

common = []
for k,sensitivity in enumerate(r['scoring']['time_sensitivity']['records']):
    assert sensitivity['time'] == k/16
    pair = [p['steps'][k*(i+1)] for i,p in enumerate(r['paths'])]
    packet = dict(time=k/16,time_sensitivity=sensitivity,states=[p['state'] for p in pair],
        moments=[p['moments'] for p in pair])
    if k:
        packet['ending_updates'] = [next(x for x in records if (x['h'],x['step']) == (h,index))
                                   for h,index in ((1/16,k),(1/32,2*k))]
    common.append(packet)
summary = []
for h in (1/16,1/32):
    rows = [x for x in records if x['h']==h]
    summary.append(dict(h=h,updates=len(rows),unchanged_geometry_steps=[x['step'] for x in rows if x['unchanged_geometry']],
        selected_boundary_steps=[x['step'] for x in rows if x['selected_boundary_hits']],
        selected_unresolved_steps=[x['step'] for x in rows if x['selected_classification_unresolved']],
        exhausted_poll_steps=[x['step'] for x in rows if x['poll_caps']],
        final_gamma_relative_drift=rows[-1]['gamma_relative_drift'],
        final_impulse_relative_drift=rows[-1]['impulse_relative_drift']))
assert identity(SOURCE) == before
output = dict(schema='t72-saved-scalar-diagnosis-v1',source=before,
    source_after=identity(SOURCE),extractor=identity(Path(__file__)),
    scientific_invocations=0,raw_array_accesses=0,new_trajectories=0,
    common_times=common,updates=records,summary=summary,
    bookkeeping_seconds_before_write=time.perf_counter()-START)
with (HERE/'diagnostic.json').open('x',encoding='utf-8',newline='\n') as f:
    json.dump(output,f,indent=2,allow_nan=False);f.write('\n')
lines = ['# T72 saved-state comparison','','Parameter values are diagnostic, not independent numerical validation. Full precision, all 48 updates and source identities are in [diagnostic.json](diagnostic.json).','',
    '| t | coarse eta | fine eta | coarse geometry | fine geometry | field difference | covariance difference |',
    '|---:|---:|---:|---|---|---:|---:|']
for p in common:
    a,b = p['states'];s = p['time_sensitivity']
    fmt = lambda geom:' / '.join('('+','.join(f'{v:.5f}' for v in g)+')' for g in geom)
    lines.append(f"| {p['time']:.4f} | {a['eta']:.6f} | {b['eta']:.6f} | {fmt(a['geometry'])} | {fmt(b['geometry'])} | {s['primary']['relative_error']:.7f} | {s['normalized_covariance_difference']:.7f} |")
lines += ['', '## Per-update diagnostics','',
    '| h | step | inherited slots | same geometry | target error | gain / h² | residual fraction | boundary hits | capped polls |',
    '|---:|---:|---:|---|---:|---:|---:|---:|---:|']
for x in records:
    lines.append(f"| {x['h']:.5f} | {x['step']} | {x['inherited_selected_slots']} | {x['unchanged_geometry']} | {x['target_error']:.7f} | {x['gain_over_h_squared']:.7f} | {x['residual_fraction']:.7f} | {len(x['selected_boundary_hits'])} | {len(x['poll_caps'])} |")
with (HERE/'TABLES.md').open('x',encoding='utf-8',newline='\n') as f:
    f.write('\n'.join(lines)+'\n')
print(json.dumps(dict(summary=summary,common_times=len(common),updates=len(records),
    output=identity(HERE/'diagnostic.json'),bookkeeping_seconds=time.perf_counter()-START),indent=2))
