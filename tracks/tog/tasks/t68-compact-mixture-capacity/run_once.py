"""One T68 scientific child with fixed OS memory/time observation; no NumPy."""
import datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[3]
MEMORY_SOURCE=ROOT.parent/'t57-finer-short-reference/memory.py'
PRIOR=1980.2512354997452
CAP=512*1024*1024
REQUIRED=1024*1024*1024
LIMIT=120.
INTERVAL=.25

def identity(path):
    h=hashlib.sha256();size=0
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024):h.update(block);size+=len(block)
    return dict(bytes=size,sha256=h.hexdigest())

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

QUALIFIED_STATUSES = {
    'ordinary_two_gaussian_endpoint_witness': 'ordinary_two_gaussian_endpoint_witness',
    'bounded_search_inconclusive': 'bounded_search_inconclusive',
    'reference_sensitive_inconclusive': 'reference_sensitive_inconclusive',
}
RAW_INPUTS = {
    'tracks/tog/tasks/t60-full-window-gaussian-screen/local/S128-snapshot-4.npz',
    'tracks/tog/tasks/t60-full-window-gaussian-screen/local/S256-snapshot-4.npz',
}


CHECK_KEYS = {
    'frozen_inputs_and_prior_reference_qualification', 'rules_and_original_reference_statistics',
    'unchanged_T63_control_and_primary_contractions', 'prescribed_search_completed',
    'selected_direct_confirmation_or_explicit_no_candidate', 'complete_work_counts', 'frozen_inputs_after',
}
COUNTER_KEYS = {'control_primary_contractions', 'neighbor_geometry_proposals', 'search_component_axis_exponentials', 'direct_component_point_evaluations', 'root_max_rational_bits', 'geometry_evaluations', 'fixed_model_reference_route_gate_comparisons', 'direct_selected_integrals', 'fixed_control_selected_moment_routes', 'component_basis_cache_hits', 'direct_control_integrals', 'control_additional_diagonal_gram_axis_products', 'root_max_sturm_chain_length', 'initial_geometry_proposals', 'direct_integrals_completed', 'reference_polynomial_node_cells', 'direct_reference_model_node_cells', 'rule_count', 'input_arrays', 'rule_nodes', 'root_max_depth', 'distinct_S256_components', 'weight_attempts', 'search_three_term_reference_cell_visits', 'direct_integrals_started', 'geometry_cache_hits', 'rejected_geometry_proposals', 'search_original_moment_checks', 'input_npz_files', 'root_isolation_nodes', 'rule_eigh_calls', 'polynomial_integrals', 'search_diagonal_gram_axis_products', 'rational_operations', 'input_bytes_hashed_after', 'reference_corner_cells', 'search_cross_gram_axis_products', 'exact_polynomial_long_divisions', 'geometry_proposals', 'control_additional_three_term_cell_visits', 'control_additional_axis_exponentials', 'input_bytes_hashed_before', 'direct_diagnostic_reductions'}


def validate_result(result, manifest, receipt, exe, manifest_path):
    # Saved scalar/metadata readback only. No worker import, quadrature, roots or array decode.
    def finite(value):
        if type(value) is float: assert math.isfinite(value)
        elif isinstance(value, dict):
            for item in value.values(): finite(item)
        elif isinstance(value, list):
            for item in value: finite(item)
    def number(value):
        assert type(value) in (int, float) and math.isfinite(value)
        return value
    def close(a, b):
        assert math.isclose(number(a), number(b), rel_tol=3e-11, abs_tol=3e-14), (a, b)
    def same(a, b):
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            assert isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a)==len(b)
            for x,y in zip(a,b): same(x,y)
        else: close(a,b)
    def compare_stats(a,b):
        for key in ('circulation','centroid','covariance','q_squared_integral','axial_impulse','vorticity_squared_integral'):
            same(a[key],b[key])
    def pair_key(pair): return tuple((g[2],g[0],g[1]) for g in pair)
    def canonical(pair): return sorted(pair,key=lambda g:(g[2],g[0],g[1]))
    def rank(record):
        candidate=record['best_candidate']
        return -candidate['J'],pair_key(record['geometry']),candidate['parameters']['eta']
    finite(result)
    assert result['numerical_qualified'] is True and result['status'] in QUALIFIED_STATUSES
    assert result['candidate_verdict']==result['status']
    assert set(result['checks'])==CHECK_KEYS and all(v is True for v in result['checks'].values())
    for key in ('formal_exclusion','formal_error_certificate','continuous_inner_optimality_certified',
                'global_geometry_optimality_certified','causal_dynamics_claim'):
        assert result[key] is False
    assert type(result['new_flow_trajectories']) is int and result['new_flow_trajectories']==0
    assert result['python']==manifest['expected_python']=='3.12.14' and result['numpy']==manifest['expected_numpy']=='2.3.5'
    assert result['prior_scientific_child_seconds']==PRIOR
    assert result['scientific_series_scope']==manifest['prior_scientific_series_scope']
    admitted={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs']}
    admitted[exe.resolve()]={k:manifest['executable'][k] for k in ('bytes','sha256')}
    admitted[manifest_path.resolve()]=receipt['input_manifest_identity']
    saved=result['input_identities']
    assert len(saved)==len({str(Path(x['path'])) for x in saved})==len(admitted)
    actual={(REPO/x['path']).resolve():{k:x[k] for k in ('bytes','sha256')} for x in saved}
    assert actual==admitted
    def frozen_json(relative):
        path=(REPO/relative).resolve()
        assert path in admitted and path.suffix=='.json'
        return json.loads(path.read_bytes())
    contract=frozen_json('tracks/tog/tasks/t67-compact-mixture-contract/evidence.json')['future_measurement']
    assert manifest['count_caps']==contract['count_caps'] and manifest['root_contract']==contract['root_contract']
    previous=frozen_json('tracks/tog/tasks/t63-endpoint-capacity/result.json')
    assert previous['status']=='search_inconclusive' and previous['capacity_witness'] is False
    prior=frozen_json('tracks/tog/tasks/t61-saved-output-qualification/result.json')
    assert prior['accepted_saved_evidence'] is True and prior['reference_qualified_full_window'] is True
    old_path=(ROOT.parent/'t60-full-window-gaussian-screen/result.json').resolve()
    assert {k:prior['original_numerical_result'][k] for k in ('bytes','sha256')}==admitted[old_path]
    old=frozen_json('tracks/tog/tasks/t60-full-window-gaussian-screen/result.json')
    D0=manifest['initial_S256_covariance_norm']
    assert D0==old['ordinary_model_screen']['actual_initial_S256_covariance_frobenius_norm']==1.0882203729522952
    initial=frozen_json('tracks/tog/tasks/t60-full-window-gaussian-screen/local/S256.json')['snapshots'][0]['covariance']
    close(math.sqrt(math.fsum(x*x for row in initial for x in row)),D0)
    refs=result['references'];assert set(refs)=={'S256','S128'}
    metadata={name:frozen_json('tracks/tog/tasks/t60-full-window-gaussian-screen/local/'+name+'-snapshot-4.json')
              for name in ('S256','S128')}
    for name,reference in refs.items():
        compare_stats(reference,metadata[name]['statistics']);compare_stats(reference,previous['reference_checks'][name])
        assert reference['circulation']>0. and reference['vorticity_squared_integral']>0. and reference['minimum_corner']>=0.
    c=result['counters']
    assert set(c)==COUNTER_KEYS and all(type(v) is int and v>=0 for v in c.values())
    assert c['input_bytes_hashed_before']==c['input_bytes_hashed_after']==sum(x['bytes'] for x in admitted.values())
    has_selected=result['selected'] is not None
    fixed=dict(input_npz_files=2,input_arrays=12,rule_count=6,rule_nodes=47,rule_eigh_calls=6,
        polynomial_integrals=2,reference_polynomial_node_cells=983040,reference_corner_cells=655360,
        control_primary_contractions=2,initial_geometry_proposals=1081,direct_control_integrals=4,
        direct_selected_integrals=4 if has_selected else 0,
        fixed_control_selected_moment_routes=4 if has_selected else 2,
        fixed_model_reference_route_gate_comparisons=8 if has_selected else 4,
        direct_integrals_started=8 if has_selected else 4,direct_integrals_completed=8 if has_selected else 4,
        direct_reference_model_node_cells=78643200 if has_selected else 39321600)
    assert all(c[k]==v for k,v in fixed.items())
    for key,limit in manifest['count_caps'].items():
        name=key[:-4] if key.endswith('_max') else key
        assert name in c and c[name]<=limit
    assert c['root_max_depth']<=64 and c['root_max_rational_bits']<=8192 and c['root_max_sturm_chain_length']<=5
    assert c['geometry_proposals']==c['initial_geometry_proposals']+c['neighbor_geometry_proposals']
    assert c['geometry_proposals']==c['geometry_evaluations']+c['geometry_cache_hits']+c['rejected_geometry_proposals']
    assert 0<=result['child_elapsed_before_result_write_seconds']<=receipt['scientific_child_supervised_seconds']
    phases=result['phases_seconds'];assert phases and all(number(v)>=0. for v in phases.values())

    def moment_gates(moments,name):
        reference=metadata[name]['statistics']
        axial=abs(moments['centroid'][1]-reference['centroid'][1])
        error=math.sqrt(math.fsum((moments['covariance'][i][j]-reference['covariance'][i][j])**2
                                 for i in range(2) for j in range(2)))/D0
        return dict(axial_centroid_error=axial,normalized_covariance_error=error,
                    axial_centroid_pass=axial<=.1,covariance_pass=error<=.1,joint_moment_pass=axial<=.1 and error<=.1)
    def check_gates(saved_gates,computed):
        assert set(saved_gates)==set(computed)
        for key,value in computed.items():
            if type(value) is bool: assert saved_gates[key] is value
            else: close(saved_gates[key],value)
    def moments_for(params,route):
        pair=params['geometry'];eta=params['eta']
        assert len(pair)==2 and all(len(g)==3 for g in pair)
        assert all(.5<=g[0]<=1.5 and .5<=g[1]<=1.5 and -.5<=g[2]<=1.5 for g in pair)
        assert 0.<=number(eta)<=1. and number(params['Gamma'])>0.
        means=[[math.sqrt(math.pi/2.)*g[0],g[2]] for g in pair]
        covs=[[[((4.-math.pi)/2.)*g[0]*g[0],0.],[0.,g[1]*g[1]]] for g in pair]
        raw=[[[2.*g[0]*g[0],means[k][0]*g[2]],[means[k][0]*g[2],g[1]*g[1]+g[2]*g[2]]]
             for k,g in enumerate(pair)]
        d=[means[1][i]-means[0][i] for i in range(2)]
        mean=[means[0][i]+eta*d[i] for i in range(2)]
        if route=='between':
            cov=[[math.fsum(((1.-eta)*covs[0][i][j],eta*covs[1][i][j],eta*(1.-eta)*d[i]*d[j]))
                  for j in range(2)] for i in range(2)]
        else:
            cov=[[math.fsum(((1.-eta)*raw[0][i][j],eta*raw[1][i][j],-mean[i]*mean[j]))
                  for j in range(2)] for i in range(2)]
        return dict(centroid=mean,covariance=cov)
    def check_moments(packet,params):
        assert set(packet['routes'])=={'between','raw'} and set(packet['gates'])=={'S256','S128'}
        for route in ('between','raw'):
            expected=moments_for(params,route)
            for key in ('centroid','covariance'): same(packet['routes'][route][key],expected[key])
            for name in refs: check_gates(packet['gates'][name][route],moment_gates(packet['routes'][route],name))
        for key in ('centroid','covariance'): same(packet['routes']['between'][key],packet['routes']['raw'][key])
        close(packet['fullspace_circulation'],params['Gamma'])
        impulse=2.*math.pi*params['Gamma']*math.fsum(((1.-params['eta'])*params['geometry'][0][0]**2,
                                                        params['eta']*params['geometry'][1][0]**2))
        close(packet['fullspace_axial_impulse'],impulse)
        for name in refs:
            close(packet['diagnostics'][name]['circulation_difference'],params['Gamma']-metadata[name]['statistics']['circulation'])
            close(packet['diagnostics'][name]['axial_impulse_difference'],impulse-metadata[name]['statistics']['axial_impulse'])
    direct_records=[]
    def check_scores(packet,name,label):
        for key,orders in (('primary_8x6',[8,6]),('confirmation_16x12',[16,12])):
            score=packet[key];direct_records.append(score)
            assert score['reference']==name and score['label']==label and score['orders']==orders
            assert number(score['numerator'])>=0. and number(score['denominator'])>0.
            close(score['denominator'],refs[name]['vorticity_squared_integral'])
            close(score['relative_error'],math.sqrt(score['numerator']/score['denominator']))
            assert score['node_cell_points']==metadata[name]['nr']*metadata[name]['nz']*math.prod(orders)
            assert number(score['seconds'])>=0.
            for diagnostic in ('D8_circulation','D8_axial_impulse'):
                assert number(score[diagnostic])>=0.
        difference=abs(packet['primary_8x6']['relative_error']-packet['confirmation_16x12']['relative_error'])
        close(packet['rule_difference'],difference);assert difference<=1e-9
        for diagnostic in ('D8_circulation','D8_axial_impulse'):
            close(packet['primary_8x6'][diagnostic],packet['confirmation_16x12'][diagnostic])
    control=previous['selected']['parameters']
    assert result['original_T63_control_parameters']==control
    g=[control[k] for k in ('sr','sz','z0')]
    params=result['control_parameters']
    assert params['geometry']==[g,g] and params['eta']==0.
    close(params['Gamma'],control['A']*g[0]**2*math.sqrt(2.*math.pi)*g[1])
    check_moments(result['control_moments'],params)
    assert set(result['control_scores'])==set(refs)
    for name,packet in result['control_scores'].items():
        check_scores(packet,name,'control')
        for key in ('primary_8x6','confirmation_16x12'):
            assert abs(packet[key]['relative_error']-previous['selected_scores'][name][key]['relative_error'])<=1e-9
        for route in ('between','raw'):
            for key in ('centroid','covariance'):
                same(result['control_moments']['routes'][route][key],previous['selected_scores'][name]['moments'][key])
        contraction=packet['contraction']
        assert contraction['amplitude_refitted'] is False and contraction['B']>0. and contraction['M']>0.
        close(contraction['Gamma'],params['Gamma']);close(contraction['C'],refs[name]['vorticity_squared_integral'])
        value=math.fsum((contraction['C'],-2.*params['Gamma']*contraction['B'],params['Gamma']**2*contraction['M']))
        close(contraction['numerator'],value);assert value>=0.
        close(contraction['relative_error'],math.sqrt(value/contraction['C']))
        difference=abs(contraction['relative_error']-packet['primary_8x6']['relative_error'])
        close(packet['contraction_direct_difference'],difference);assert difference<=1e-9
    selected=result['selected']
    if has_selected:
        assert selected['geometry']==selected['parameters']['geometry']==canonical(selected['geometry'])
        assert selected['parameters']['Gamma']>0. and 0.<=selected['parameters']['eta']<=1.
        assert selected['identical_components'] is (selected['geometry'][0]==selected['geometry'][1])
        assert selected['zero_weight'] is (selected['parameters']['eta'] in (0.,1.))
        check_moments(result['selected_moments'],selected['parameters'])
        assert set(result['selected_scores'])==set(refs)
        for name,packet in result['selected_scores'].items():
            check_scores(packet,name,'selected')
            gates=result['selected_moments']['gates'][name]
            expected=dict(field_both_rules=all(packet[k]['relative_error']<=.1 for k in ('primary_8x6','confirmation_16x12')),
                axial_both_routes=all(gates[k]['axial_centroid_pass'] for k in ('between','raw')),
                covariance_both_routes=all(gates[k]['covariance_pass'] for k in ('between','raw')))
            assert packet['physical_gates']==expected and all(type(x) is bool for x in packet['physical_gates'].values())
            assert packet['joint_pass'] is all(expected.values())
        difference=abs(selected['relative_error']-result['selected_scores']['S256']['primary_8x6']['relative_error'])
        close(result['selected_contraction_direct_difference'],difference);assert difference<=1e-9
        sensitivity=result['sensitivity']
        delta=abs(result['selected_scores']['S256']['primary_8x6']['relative_error']-result['selected_scores']['S128']['primary_8x6']['relative_error'])
        close(sensitivity['absolute_difference'],delta)
        assert sensitivity['tolerance']==.001 and sensitivity['passed'] is (delta<=.001)
        assert sensitivity['selected_parameters_identical'] is True and sensitivity['selection_reference']=='S256'
        expected_status=('ordinary_two_gaussian_endpoint_witness' if sensitivity['passed'] and all(x['joint_pass'] for x in result['selected_scores'].values())
                         else 'reference_sensitive_inconclusive' if not sensitivity['passed'] else 'bounded_search_inconclusive')
    else:
        assert result['selected_scores']=={} and result['selected_moments'] is None
        assert result['selected_contraction_direct_difference'] is None and result['sensitivity'] is None
        expected_status='bounded_search_inconclusive'
    assert result['status']==expected_status and result['capacity_witness'] is (expected_status=='ordinary_two_gaussian_endpoint_witness')
    assert sum(x['node_cell_points'] for x in direct_records)==c['direct_reference_model_node_cells']
    assert 2*sum(math.prod(x['orders']) for x in direct_records)==c['direct_diagnostic_reductions']
    selected_components=(1 if selected['zero_weight'] or selected['identical_components'] else 2) if has_selected else 0
    assert c['direct_component_point_evaluations']==39321600*(1+selected_components)

    # Journal proves the prescribed proposal schedule and charges partial inner work;
    # it does not independently solve the rounded-coefficient polynomial.
    events=[json.loads(line) for line in (ROOT/'local/work.jsonl').read_text(encoding='utf-8').splitlines()]
    finite(events)
    assert events and not any(x['kind'] in {'worker_failure','geometry_deadline_partial'} for x in events)
    assert all(0<=number(x['elapsed_seconds'])<=result['child_elapsed_before_result_write_seconds'] for x in events)
    assert all(a['elapsed_seconds']<=b['elapsed_seconds'] for a,b in zip(events,events[1:]))
    def kinds(kind): return [x for x in events if x['kind']==kind]
    starts=kinds('phase_started');ends=kinds('phase_finished')
    assert len(starts)==len(ends)==len(phases)==6
    assert [x['name'] for x in starts]==[x['name'] for x in ends]==list(phases)
    assert len({x['name'] for x in starts})==6
    for event in ends: assert event['seconds']==phases[event['name']]
    assert events[-1]['kind']=='phase_finished' and events[-1]['name']=='counts_verdict_and_final_hashes'
    outcomes=kinds('outcome');assert len(outcomes)==1
    assert outcomes[0]['status']==result['status'] and outcomes[0]['selected']==selected
    assert outcomes[0]['sensitivity']==result['sensitivity'] and outcomes[0]['counters']==c
    arrays=kinds('array_decoded');assert len(arrays)==12
    expected_arrays={}
    for name,n in (('S256',256),('S128',128)):
        for key in ('q','qr','qz','r','rc','z'):
            shape=[n,2*n] if key in ('q','qr','qz') else [2*n] if key=='z' else [n]
            expected_arrays[(name,key)]=(shape,8*math.prod(shape))
    assert len({(x['reference'],x['key']) for x in arrays})==12
    for event in arrays: assert (event['shape'],event['bytes'])==expected_arrays[(event['reference'],event['key'])]
    rules=kinds('rule_constructed');orders=[3,2,8,6,16,12]
    assert [x['order'] for x in rules]==[x['order'] for x in kinds('rule_eigh_started')]==orders
    for event in rules:
        n=event['order'];nodes=event['nodes'];weights=event['weights']
        assert len(nodes)==len(weights)==n and event['symmetric_matrix_order']==n and event['eigensolver']=='numpy.linalg.eigh'
        assert all(-1.<x<1. for x in nodes) and all(a<b for a,b in zip(nodes,nodes[1:])) and all(w>0. for w in weights)
        assert abs(math.fsum(weights)-2.)<=1e-13
        assert all(abs(nodes[i]+nodes[-i-1])<=1e-13 and abs(weights[i]-weights[-i-1])<=1e-13 for i in range(n))
    reference_events=kinds('reference_qualified');assert len(reference_events)==2
    assert {x['reference'] for x in reference_events}==set(refs)
    for event in reference_events: assert event['statistics']==refs[event['reference']]
    direct_events=kinds('direct_score');assert len(direct_events)==len(direct_records)
    for event,record in zip(direct_events,direct_records):
        assert {key:event[key] for key in record}==record
    basis_events=kinds('component_basis')
    assert c['distinct_S256_components']==sum(x['reference']=='S256' for x in basis_events)
    assert c['component_basis_cache_hits']==2+2*c['geometry_evaluations']-len(basis_events)
    for scope,prefix in (('control','control_additional'),('search','search')):
        matching=[x for x in basis_events if x['origin']==scope]
        axis=sum(x['axis_points'] for x in matching);cells=sum(x['three_term_cell_visits'] for x in matching)
        if scope=='control':
            assert len(matching)==2 and {x['reference'] for x in matching}==set(refs)
            assert c[prefix+'_axis_exponentials']==axis and c[prefix+'_diagonal_gram_axis_products']==axis
            assert c[prefix+'_three_term_cell_visits']==cells
        else:
            assert all(x['reference']=='S256' for x in matching)
            assert c['search_component_axis_exponentials']==axis and c['search_diagonal_gram_axis_products']==axis
            assert c['search_three_term_reference_cell_visits']==cells
    assert c['search_cross_gram_axis_products']==5120*c['geometry_evaluations']
    evaluated_events=kinds('geometry_evaluated');records=[x['record'] for x in evaluated_events]
    assert len(records)==c['geometry_evaluations'] and [x['index'] for x in records]==list(range(len(records)))
    assert all(x['kind']=='geometry_evaluated' for x in [e for e in events if e['kind'] in {'geometry_evaluated','geometry_cache_hit','geometry_rejected'}][:1081])
    by_index={x['index']:x for x in records}
    assert len(kinds('geometry_started'))==len(records)
    proposals=[x for x in events if x['kind'] in {'geometry_evaluated','geometry_cache_hit','geometry_rejected'}]
    assert [x['proposal_index'] for x in proposals]==list(range(c['geometry_proposals']))
    assert len(kinds('geometry_cache_hit'))==c['geometry_cache_hits'] and len(kinds('geometry_rejected'))==c['rejected_geometry_proposals']
    bank=[[sr,sz,z] for sr in (.75,1.,1.25) for sz in (.75,1.,1.25) for z in (-.5,0.,.5,1.,1.5)]+[g]
    expected_pairs=[(i,j) for i in range(46) for j in range(i,46)]
    for event,(i,j) in zip(proposals[:1081],expected_pairs):
        assert event['origin']==dict(stage='bank',i=i,j=j) and event['proposed_geometry']==[bank[i],bank[j]]
    assert all(x['origin']['stage']=='neighbor' for x in proposals[1081:])
    for event in proposals:
        pair=canonical(event['proposed_geometry']);assert event['canonical_geometry']==pair
        assert event['component_order_swapped'] is (event['proposed_geometry']!=pair)
        outside=any(not(.5<=sr<=1.5 and .5<=sz<=1.5 and -.5<=z<=1.5) for sr,sz,z in pair)
        if event['kind']=='geometry_rejected': assert outside and event['reason']=='outside_frozen_box'
        else:
            assert not outside
            record=event['record'] if event['kind']=='geometry_evaluated' else by_index[event['evaluation_index']]
            assert record['geometry']==pair
    solver_sums=dict(polynomial_long_divisions=0,isolation_nodes=0,rational_operations=0,weight_attempts=0)
    maxima=dict(max_depth=0,max_rational_bits=0,max_sturm_chain_length=0)
    for record in records:
        inner=record['inner'];counts=inner['counters'];candidates=record['original_candidates'];primary=record['primary']
        for key in ('root_isolation_complete_for_rounded_polynomial','representable_candidate_construction_complete'):
            assert type(inner[key]) is bool and type(record[key]) is bool
        assert inner['rounded_feasible_set_empty'] is None or type(inner['rounded_feasible_set_empty']) is bool
        assert inner['status'] in {'inner_feasibility_unresolved','rounded_infeasible','candidate_construction_complete'}
        assert all(type(value) is int and value>=0 for value in counts.values())
        assert len(inner['roots'])==counts['distinct_roots']<=4
        assert len(inner['attempts'])<=counts['weight_attempts']<=26
        assert [x['ordinal'] for x in inner['attempts']]==list(range(1,len(inner['attempts'])+1))
        if inner['rounded_feasible_set_empty'] is None:
            assert inner['root_isolation_complete_for_rounded_polynomial'] is False
            assert inner['status']=='inner_feasibility_unresolved' and inner['unresolved_reasons']
            assert all(isinstance(reason,str) and reason for reason in inner['unresolved_reasons'])
        assert all(number(primary[k])>0. for k in ('b1','b2','M11','M12','M22'))
        assert primary['M12']**2<=(1.+1e-12)*primary['M11']*primary['M22']
        for key in solver_sums:
            assert type(counts[key]) is int and counts[key]>=0;solver_sums[key]+=counts[key]
        for key in maxima:
            assert type(counts[key]) is int and counts[key]>=0;maxima[key]=max(maxima[key],counts[key])
        assert counts['polynomial_long_divisions']<=24 and counts['isolation_nodes']<=512 and counts['weight_attempts']<=26
        assert len(candidates)<=counts['weight_attempts'] and len(candidates)==len(inner['candidates'])
        accepted=[];discrepancies=[]
        for point,original in zip(inner['candidates'],candidates):
            eta=original['eta'];assert type(eta) is float and 0.<=eta<=1. and eta==point['eta']
            assert type(point['rounded_feasible']) is bool
            assert original['rounded_feasible'] is point['rounded_feasible'] and original['sources']==point['sources']
            gates=moment_gates(original['moments'],'S256');check_gates(original['gates'],gates)
            if gates['joint_moment_pass']!=point['rounded_feasible']:
                discrepancies.append(dict(eta=eta,rounded_feasible=point['rounded_feasible'],original_feasible=gates['joint_moment_pass']))
            objective=original['objective']
            if objective is not None:
                assert gates['joint_moment_pass']
                B=math.fsum(((1.-eta)*primary['b1'],eta*primary['b2']))
                w0,w1=1.-eta,eta
                M=math.fsum((w0*w0*primary['M11'],2.*w0*w1*primary['M12'],w1*w1*primary['M22']))
                J=B*B/M;C=refs['S256']['vorticity_squared_integral']
                for key,value in dict(B=B,M=M,J=J,C=C,numerator=C-J,relative_error=math.sqrt((C-J)/C)).items(): close(objective[key],value)
                accepted.append((objective,original))
        assert record['rounded_original_discrepancies']==discrepancies
        assert record['numerical_unresolved_reasons']==[x['unresolved_reason'] for x in candidates if 'unresolved_reason' in x]
        accepted_etas={x[1]['eta'] for x in accepted}
        uncovered=[x['id'] for x in inner['coverage_groups'] if not any(eta in accepted_etas for eta in x['candidate_etas'])]
        assert record['uncovered_feasible_groups']==uncovered
        complete=inner['representable_candidate_construction_complete'] and not discrepancies and not record['numerical_unresolved_reasons'] and not uncovered
        assert record['root_isolation_complete_for_rounded_polynomial'] is inner['root_isolation_complete_for_rounded_polynomial']
        assert record['representable_candidate_construction_complete'] is bool(complete)
        best=record['best_candidate']
        if not accepted: assert best is None
        else:
            obj,point=min(accepted,key=lambda x:(-x[0]['J'],x[1]['eta']))
            assert best is not None and best['parameters']['geometry']==record['geometry'] and best['parameters']['eta']==point['eta']
            for key,value in obj.items(): close(best[key],value)
            close(best['parameters']['Gamma'],best['B']/best['M'])
            assert best['moments']==point['moments'] and best['gates']==point['gates']
    for target,source in (('exact_polynomial_long_divisions','polynomial_long_divisions'),('root_isolation_nodes','isolation_nodes'),
                          ('rational_operations','rational_operations'),('weight_attempts','weight_attempts')):
        assert c[target]==solver_sums[source]
    assert c['search_original_moment_checks']==sum(len(x['original_candidates']) for x in records)
    for key,value in maxima.items(): assert c['root_'+key]==value
    summary=result['search_summary'];procedural=result['geometry_procedural_summary']
    assert summary['initial_components']==bank and summary['initial_pairs']==1081 and summary['proposals']==len(proposals)
    assert summary['early_success_shortcut'] is False and summary['global_geometry_optimality_certified'] is False
    assert summary['continuous_inner_optimality_certified'] is False
    eligible=[x for x in records if x['best_candidate'] is not None]
    bank_records=[x['record'] for x in proposals[:1081] if x['kind']=='geometry_evaluated' and x['record']['best_candidate'] is not None]
    starts=sorted(bank_records,key=rank)[:4]
    assert summary['local_start_indices']==[x['index'] for x in starts]
    local_starts=kinds('local_starts');assert len(local_starts)==1 and local_starts[0]['evaluation_indices']==summary['local_start_indices']
    polls=kinds('poll_completed');assert summary['polls']==[{k:v for k,v in x.items() if k not in {'kind','elapsed_seconds'}} for x in polls]
    assert c['neighbor_geometry_proposals']==12*len(polls)
    cursor=1081;poll_cursor=0
    for start_index,start_record in enumerate(starts):
        current=start_record
        for level,(width,zstep) in enumerate(((.10,.20),(.05,.10),(.025,.05))):
            for poll in range(8):
                assert poll_cursor<len(polls)
                log=polls[poll_cursor];poll_cursor+=1;neighbors=[]
                assert (log['start'],log['level'],log['poll'],log['width_step'],log['axial_step'],log['center_before'])==(start_index,level,poll,width,zstep,current['index'])
                for axis in range(6):
                    for sign in (-1,1):
                        event=proposals[cursor];cursor+=1
                        assert event['origin']==dict(stage='neighbor',start=start_index,level=level,poll=poll,axis=axis,sign=sign,center_index=current['index'])
                        expected=[list(g) for g in current['geometry']];expected[axis//3][axis%3]+=sign*(zstep if axis%3==2 else width)
                        assert event['proposed_geometry']==expected
                        if event['kind']!='geometry_rejected':
                            record=event['record'] if event['kind']=='geometry_evaluated' else by_index[event['evaluation_index']]
                            if record['best_candidate'] is not None: neighbors.append(record)
                neighbor=min(neighbors,key=rank) if neighbors else None
                improved=neighbor is not None and neighbor['best_candidate']['J']>current['best_candidate']['J']
                assert log['improved'] is improved
                if improved: current=neighbor
                assert log['center_after']==current['index']
                if not improved: break
    assert cursor==len(proposals) and poll_cursor==len(polls)
    assert summary['eligible_geometry_count']==len(eligible)
    winner=min(eligible,key=rank) if eligible else None
    assert summary['selected_index']==(None if winner is None else winner['index'])
    if winner is None: assert selected is None
    else:
        assert selected['evaluation_index']==winner['index'] and selected['geometry']==winner['geometry']
        for key,value in winner['best_candidate'].items(): assert selected[key]==value
        for key in ('root_isolation_complete_for_rounded_polynomial','representable_candidate_construction_complete'):
            assert selected[key] is winner[key]
    expected_procedural=dict(evaluated_geometries=len(records),
        root_isolation_complete_for_rounded_polynomial=all(x['root_isolation_complete_for_rounded_polynomial'] for x in records),
        representable_candidate_construction_complete=all(x['representable_candidate_construction_complete'] for x in records),
        root_unresolved_geometries=sum(not x['root_isolation_complete_for_rounded_polynomial'] for x in records),
        candidate_construction_incomplete_geometries=sum(not x['representable_candidate_construction_complete'] for x in records),
        rounded_original_discrepancy_geometries=sum(bool(x['rounded_original_discrepancies']) for x in records),
        numerical_unresolved_geometries=sum(bool(x['numerical_unresolved_reasons']) for x in records),
        rounded_empty_geometries=sum(bool(x['inner']['rounded_feasible_set_empty']) for x in records))
    assert procedural==expected_procedural
    completed=kinds('search_completed');assert len(completed)==1
    assert completed[0]['summary']==summary and completed[0]['procedural']==procedural and completed[0]['selected']==selected


def main():
    start=time.perf_counter()
    local=ROOT/'local'
    manifest_path=ROOT/'input-manifest.json'
    manifest=json.loads(manifest_path.read_bytes())
    assert manifest['schema']=='t68-compact-mixture-capacity-freeze-v1'
    assert manifest['maximum_scientific_child_invocations']==1
    assert manifest['child_timeout_seconds']==LIMIT and manifest['observed_peak_working_set_limit_bytes']==CAP
    assert manifest['required_available_physical_bytes']==REQUIRED
    assert manifest['expected_python']=='3.12.14' and manifest['expected_numpy']=='2.3.5'
    assert manifest['expected_rule_orders']==[3,2,8,6,16,12] and manifest['expected_rule_nodes']==47
    assert manifest['expected_input_npz_files']==2 and manifest['expected_input_arrays']==12
    assert manifest['expected_rules_constructed']==manifest['expected_rule_eigh_calls']==6
    assert manifest['expected_polynomial_integrals']==2
    assert len(manifest['inputs'])==len({x['path'] for x in manifest['inputs']})>0
    assert {x['path'] for x in manifest['inputs'] if Path(x['path']).suffix.lower() in {'.npz','.npy'}}==RAW_INPUTS
    assert manifest['raw_input_allowlist']==sorted(RAW_INPUTS)
    assert manifest['memory_sample_interval_seconds']==INTERVAL
    assert manifest['count_caps'] and manifest['root_contract']
    assert manifest['prior_scientific_child_seconds']==PRIOR
    assert all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    exe=Path(manifest['executable']['path'])
    assert identity(exe)=={k:manifest['executable'][k] for k in ('bytes','sha256')}
    assert not (ROOT/'result.json').exists() and not (ROOT/'execution.json').exists()
    assert not (local/'execution-started.json').exists()
    for name in ('work.jsonl','worker-failure.json','stdout.txt','stderr.txt','memory.jsonl'):
        assert not (local/name).exists(), name
    preflight=json.loads((ROOT/'preflight.json').read_bytes())
    assert preflight['schema']=='t68-os-preflight-v1' and preflight['passed'] is True
    assert preflight['source']==identity(MEMORY_SOURCE)
    spec=importlib.util.spec_from_file_location('t68_memory',MEMORY_SOURCE)
    memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
    command=[str(exe),'-I','-B','-u','-X','utf8',str(ROOT/'measure.py')]
    env=dict(os.environ)
    limits={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    env.update(limits)
    receipt=dict(schema='t68-compact-mixture-capacity-execution-v1',started_utc=now(),command=command,cwd=str(REPO),
        child_timeout_seconds=LIMIT,observed_peak_working_set_limit_bytes=CAP,
        required_available_physical_bytes=REQUIRED,memory_sample_interval_seconds=INTERVAL,
        thread_environment_overrides=limits,scientific_child_invocations=0,new_scientific_trajectories=0,
        complete_result_validated=False,numerical_qualified=False,candidate_verdict=None,capacity_witness=None,formal_exclusion=False,
        prior_scientific_child_seconds=PRIOR,T61_qualification_seconds=.9663960000034422,
        prior_scientific_series_scope=manifest['prior_scientific_series_scope'],
        scientific_series_is_total_project_cost=False,
        T60_history_reclassified=False,input_manifest_identity=identity(manifest_path),
        supervisor_identity=identity(Path(__file__)),worker_identity=identity(ROOT/'measure.py'),weight_solver_identity=identity(ROOT/'weight_solver.py'),
        memory_observer_identity=identity(MEMORY_SOURCE),executable_identity=identity(exe),
        memory_samples=0,peak_observed_working_set_bytes=0,max_observed_private_bytes=0,
        max_observed_peak_pagefile_bytes=0)
    receipt['launch_memory']=memory.host_memory()
    write(local/'execution-started.json',receipt)
    child=None;handle=None;begin=None
    with (local/'stdout.txt').open('xb') as stdout,(local/'stderr.txt').open('xb') as stderr, (local/'memory.jsonl').open('x',encoding='utf-8',newline='\n') as observations:
        def sample(final=False):
            values=memory.process_memory(handle)
            elapsed=time.perf_counter()-begin
            record=dict(elapsed_seconds=elapsed,final=final,**values)
            observations.write(json.dumps(record,allow_nan=False)+'\n');observations.flush()
            receipt['memory_samples']+=1
            receipt['peak_observed_working_set_bytes']=max(receipt['peak_observed_working_set_bytes'],values['peak_working_set_bytes'])
            receipt['max_observed_private_bytes']=max(receipt['max_observed_private_bytes'],values['private_usage_bytes'])
            receipt['max_observed_peak_pagefile_bytes']=max(receipt['max_observed_peak_pagefile_bytes'],values['peak_pagefile_usage_bytes'])
            receipt['last_memory_sample_elapsed_seconds']=elapsed
            return values['peak_working_set_bytes']<=CAP
        if receipt['launch_memory']['available_physical_bytes']<REQUIRED:
            receipt['status']='insufficient_launch_memory_no_invocation'
        else:
            begin=time.perf_counter();receipt['scientific_child_invocations']=1
            try:
                child=subprocess.Popen(command,cwd=REPO,env=env,stdout=stdout,stderr=stderr,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                receipt['child_pid']=child.pid
                handle=memory.open_process(child.pid)
                while True:
                    code=child.poll()
                    if code is not None:
                        receipt.update(returncode=code,status='exited_pending_readback')
                        try:
                            if not sample(final=True):receipt['status']='memory_limit_no_retry'
                        except Exception as exc:
                            receipt['final_memory_query_unavailable']=repr(exc)
                        break
                    if time.perf_counter()-begin>=LIMIT:
                        receipt['status']='timeout_no_retry';break
                    try:
                        if not sample():receipt['status']='memory_limit_no_retry';break
                    except Exception as exc:
                        if child.poll() is not None:
                            receipt.update(returncode=child.returncode,status='exited_pending_readback',final_memory_query_unavailable=repr(exc))
                        else:
                            receipt.update(status='live_memory_observer_error_no_retry',observer_error=repr(exc))
                        break
                    try:
                        child.wait(timeout=min(INTERVAL,max(.001,LIMIT-(time.perf_counter()-begin))))
                    except subprocess.TimeoutExpired:
                        pass
            except Exception as exc:
                receipt.update(status='launch_or_observer_setup_error_no_retry',error=repr(exc))
            finally:
                if child is not None:
                    if child.poll() is None:child.kill()
                    receipt['returncode']=child.wait()
                if handle is not None:memory.kernel.CloseHandle(handle)
    receipt['scientific_child_supervised_seconds']=time.perf_counter()-begin if begin is not None else 0.
    receipt['cumulative_scientific_child_seconds']=PRIOR+receipt['scientific_child_supervised_seconds']
    receipt['inputs_unchanged']=all(identity(REPO/x['path'])=={k:x[k] for k in ('bytes','sha256')} for x in manifest['inputs'])
    receipt['input_manifest_unchanged']=identity(manifest_path)==receipt['input_manifest_identity']
    receipt['executable_unchanged']=identity(exe)==receipt['executable_identity']
    receipt['logs']=[dict(path='local/'+name,**identity(local/name)) for name in ('stdout.txt','stderr.txt','memory.jsonl')]
    receipt['partial_artifacts']=[dict(path=p.relative_to(ROOT).as_posix(),**identity(p)) for p in sorted(local.iterdir())
        if p.is_file() and p.name in ('work.jsonl','worker-failure.json')]
    receipt['worker_failure_exists']=(local/'worker-failure.json').exists()
    if receipt['worker_failure_exists']:
        try:
            failure=json.loads((local/'worker-failure.json').read_bytes())
            assert failure['schema']=='t68-compact-mixture-capacity-failure-v1'
            assert failure['status']=='numerical_failure' and failure['numerical_qualified'] is False
            assert failure['capacity_witness'] is False
            receipt['worker_failure_summary']={k:failure[k] for k in
                ('active_phase','error_type','error','counters','checks','phases_seconds','elapsed_seconds')}
            if receipt['status']=='exited_pending_readback':receipt['status']='worker_numerical_failure_no_retry'
        except Exception as exc:
            receipt['worker_failure_read_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='worker_failure_record_error_no_retry'
    receipt['result_exists']=(ROOT/'result.json').exists()
    if receipt['result_exists']:
        receipt['result_identity']=identity(ROOT/'result.json')
        try:
            result=json.loads((ROOT/'result.json').read_bytes())
            assert result['schema']=='t68-compact-mixture-capacity-v1'
            assert result['status'] in set(QUALIFIED_STATUSES)|{'numerical_failure'}
            assert result['formal_exclusion'] is False
            if receipt['status']=='exited_pending_readback':
                if result['status']=='numerical_failure':
                    assert receipt['returncode']==2 and result['numerical_qualified'] is False
                    assert result['candidate_verdict'] in (None,'numerical_failure') and result['capacity_witness'] in (None,False)
                    receipt['status']='numerical_failure_no_retry'
                else:
                    assert receipt['returncode']==0
                    assert receipt['scientific_child_supervised_seconds']<=LIMIT
                    assert receipt['memory_samples']>0 and receipt['peak_observed_working_set_bytes']<=CAP
                    assert receipt['inputs_unchanged'] and receipt['input_manifest_unchanged'] and receipt['executable_unchanged']
                    validate_result(result,manifest,receipt,exe,manifest_path)
                    receipt.update(status='completed_'+result['status'],complete_result_validated=True,numerical_qualified=True,
                        candidate_verdict=result['candidate_verdict'],capacity_witness=result['capacity_witness'],formal_exclusion=False)
        except Exception as exc:
            receipt['result_read_error']=repr(exc)
            if receipt['status']=='exited_pending_readback':receipt['status']='failed_result_validation_no_retry'
    elif receipt['status']=='exited_pending_readback':
        receipt['status']='missing_result_no_retry'
    if not all(receipt[k] for k in ('inputs_unchanged','input_manifest_unchanged','executable_unchanged')):
        receipt.update(status='failed_preservation_no_retry',complete_result_validated=False,numerical_qualified=False,
            candidate_verdict=None,capacity_witness=None,formal_exclusion=False)
    receipt['supervisor_elapsed_before_receipt_write_seconds']=time.perf_counter()-start
    receipt['finished_utc']=now()
    write(ROOT/'execution.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('status','scientific_child_invocations','scientific_child_supervised_seconds',
        'candidate_verdict','peak_observed_working_set_bytes','inputs_unchanged')},indent=2))

if __name__=='__main__':main()
