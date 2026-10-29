"""Single fixed correctness invocation. Importing this file performs no experiment."""
import datetime
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=HERE/'run-01'
BASE=ROOT/'tracks/tog/tasks/t32-ordinary-volume-entry'
EPS=.001
PRUNE_ERROR=.00025
GL_NOMINAL=.000125
FP_ALLOWANCE=1e-10
RAW_CAP=32*1024*1024


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def require(ok,message):
    if not ok: raise ValueError(message)


def norm_close(a,b):
    return abs(a-b)<=1e-12*max(1,abs(a),abs(b))


def main():
    require((OUT/'attempt.json').exists(),'Supervisor attempt reservation required')
    with (OUT/'worker-start.json').open('x',encoding='utf-8',newline='\n') as f:
        json.dump({'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},f)
        f.write('\n')
    tic=time.perf_counter_ns(); deadline_ns=tic+180_000_000_000
    counters={}; records=[]; groups=[]; active=None; stage='source_check'; failed=None
    timings={}; tree_summaries=[]; cache={}
    frozen_bytes=(HERE/'freeze.json').read_bytes(); freeze=json.loads(frozen_bytes)
    def check_time():
        if time.perf_counter_ns()>=deadline_ns:raise TimeoutError('T33 computation deadline')
    def verify_sources():
        for item in freeze['artifacts']:
            data=(ROOT/item['path']).read_bytes()
            require(len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256'],'Frozen input changed: '+item['path'])
        require((HERE/'freeze.json').read_bytes()==frozen_bytes,'Freeze changed')
    def journal(value):
        with (OUT/'journal.jsonl').open('a',encoding='utf-8',newline='\n') as f:
            f.write(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n')
    status='failed'
    final_source_check=None
    try:
        source_tic=time.perf_counter_ns();verify_sources();check_time()
        timings['initial_source_check_seconds']=(time.perf_counter_ns()-source_tic)/1e9
        import_tic=time.perf_counter_ns()
        adapter=load('t33_adapter',BASE/'adapter.py')
        reference=load('t33_reference',HERE/'reference.py')
        ordinary=load('t33_ordinary',BASE/'ordinary.py')
        kernel=ordinary.load_kernel(ROOT)
        timings['module_import_seconds']=(time.perf_counter_ns()-import_tic)/1e9
        stage='decode_carrier';start=time.perf_counter_ns()
        packed=(ROOT/'tracks/tog/tasks/t31-local-carrier/run-01/carrier.json.gz').read_bytes()
        require(len(packed)==58581 and hashlib.sha256(packed).hexdigest()=='39f4dc758bb790f3b88bb2bbfa65dbe469c030289d4237476f598e29b823dcf2','Carrier compressed identity')
        raw=gzip.decompress(packed)
        require(len(raw)==167310 and hashlib.sha256(raw).hexdigest()=='b2a666a4a54b075e11e0e841a02b5d4768f399c715ea6cad1e331209185e62d1','Carrier raw identity')
        carrier=json.loads(raw)
        require(carrier['width']==256 and carrier['height']==192 and [f['frame'] for f in carrier['frames']]==[90,180],'Unexpected carrier geometry')
        require(carrier['views']==[{'id':'front','yaw':0},{'id':'oblique','yaw':.7},{'id':'side','yaw':1.4}],'Unexpected views')
        timings['decode_seconds']=(time.perf_counter_ns()-start)/1e9
        for frame in carrier['frames']:
            check_time();stage='tree_build';start=time.perf_counter_ns()
            particles=frame['primitives']; n=len(particles)
            require(n==({90:270,180:540}[frame['frame']]),'Particle count changed')
            cmax=[max(p['color'][k] for p in particles) for k in range(3)]
            mass_budget=min([-math.log1p(-PRUNE_ERROR)]+[-math.log1p(-PRUNE_ERROR/c) for c in cmax if c>PRUNE_ERROR])
            tree=adapter.build_bvh(particles,counters)
            tree_summaries.append({'frame':frame['frame'],'tree':tree,'seconds':(time.perf_counter_ns()-start)/1e9,
                                   'cmax':cmax,'pruning_mass_budget':mass_budget})
            for view in carrier['views']:
                check_time();stage='geometry_schedule';start=time.perf_counter_ns()
                camera=adapter.camera(frame['camera_params'],view['yaw'],256,192)
                pixels=adapter.geometric_pixels(camera,particles)
                group={'frame':frame['frame'],'view':view,'pixels':pixels,'camera':camera,'nontrivial_rays':0,
                       'mixed_rays':0,'schedule_seconds':(time.perf_counter_ns()-start)/1e9}
                groups.append(group)
                require(48<=len(pixels)<=56,'Wrong geometric subset count')
                for pixel in pixels:
                    check_time(); stage='ordinary_projection_and_pruning';start=time.perf_counter_ns()
                    active={'frame':frame['frame'],'view_id':view['id'],'i':pixel['i'],'j':pixel['j'],'tags':pixel['tags']}
                    journal({'event':'begin','ray':active})
                    ray=adapter.make_ray(camera,pixel['i'],pixel['j'])
                    selection=adapter.query(tree,ray,mass_budget,counters)
                    ids=selection['kept_ids']; omitted=selection['omitted_ids']
                    require(len(ids)+len(omitted)==n and sorted(ids+omitted)==list(range(n)),'BVH partition not complete/disjoint')
                    p=adapter.project(particles,ids,ray,counters)
                    active.update(ray=ray,selection=selection,ordinary_preparation_seconds=(time.perf_counter_ns()-start)/1e9)
                    stage='ordinary_solve';start=time.perf_counter_ns()
                    answer=ordinary.solve(p,GL_NOMINAL,counters,deadline_ns,cache,kernel)
                    active.update(ordinary=answer,ordinary_seconds=(time.perf_counter_ns()-start)/1e9)
                    journal({'event':'ordinary_complete','ray':active})
                    stage='independent_projection';start=time.perf_counter_ns()
                    ref_ray=reference.independent_ray(frame['camera_params'],view['yaw'],256,192,pixel['i'],pixel['j'])
                    for name in ['origin','direction']:
                        require(all(norm_close(a,b) for a,b in zip(ray[name],ref_ray[name])),'Independent ray mismatch: '+name)
                    require(norm_close(ray['a'],ref_ray['a']) and norm_close(ray['b'],ref_ray['b']),'Independent clip mismatch')
                    require(norm_close(math.fsum(v*v for v in ray['direction']),1.) and ray['a']<ray['b'],'Invalid unit-ray domain')
                    allp=reference.project_all(particles,ref_ray,counters)
                    max_z_error=0.;max_q_error=0.
                    for offset,source in enumerate(ids):
                        dz=abs(p['mu'][offset]-allp['mu'][source]);dq=abs(p['weight'][offset]-allp['weight'][source])
                        max_z_error=max(max_z_error,dz);max_q_error=max(max_q_error,dq)
                        require(norm_close(p['mu'][offset],allp['mu'][source]),'Independent mean mismatch')
                        require(dq<=1e-12+1e-9*abs(allp['weight'][source]),'Independent optical weight mismatch')
                    active.update(reference_ray=ref_ray,max_z_error=max_z_error,max_q_error=max_q_error,
                                  independent_projection_seconds=(time.perf_counter_ns()-start)/1e9)
                    stage='reference_enclosure';start=time.perf_counter_ns()
                    ref=reference.enclose(allp,cmax,tuple(answer['rgb']),EPS+FP_ALLOWANCE,counters,deadline_ns)
                    active.update(reference=ref,reference_seconds=(time.perf_counter_ns()-start)/1e9)
                    stage='qualification';start=time.perf_counter_ns()
                    leaves=ref['leaves']
                    if ref['path']=='enclosure':
                        require(bool(leaves) and leaves[0][0]==ref_ray['a'] and leaves[-1][1]==ref_ray['b'],'Reference leaf domain')
                        require(all(cell[0]<cell[1] for cell in leaves) and all(a[1]==b[0] for a,b in zip(leaves,leaves[1:])),'Reference leaf partition')
                        require(abs(math.fsum(cell[2] for cell in leaves)-ref['retained_alpha'])<=FP_ALLOWANCE,'Reference absorption accounting')
                    else:
                        require(not leaves and ref['path'] in ['empty','equal_color'],'Unexpected analytic reference path')
                    low_sum=[math.fsum([ref['analytic_retained_rgb'][k]]+[c[3+k] for c in leaves]) for k in range(3)]
                    high_sum=[math.fsum([ref['analytic_retained_rgb'][k]]+[c[6+k] for c in leaves]) for k in range(3)]
                    require(all(len(c)==9 and all(math.isfinite(x) for x in c) and c[2]>=0 and all(-FP_ALLOWANCE<=c[3+k]<=c[6+k]+FP_ALLOWANCE and c[6+k]<=c[2]*cmax[k]+FP_ALLOWANCE for k in range(3)) for c in leaves),'Reference cell range')
                    require(all(abs(ref['lower'][k]-max(0,low_sum[k]-ref['omission_rgb_radius'][k]))<=FP_ALLOWANCE and abs(ref['upper'][k]-(high_sum[k]+ref['omission_rgb_radius'][k]))<=FP_ALLOWANCE for k in range(3)),'Reference ledger sum mismatch')
                    alpha=ref['alpha_full'];actual_omitted=math.fsum(ref['finite_masses'][i] for i in omitted)
                    bound=selection['mass_bound'];delta=-math.expm1(-bound)
                    require(bound<=mass_budget+FP_ALLOWANCE and actual_omitted<=bound+FP_ALLOWANCE,'BVH omitted mass exceeds charge/budget')
                    require(delta<=PRUNE_ERROR+FP_ALLOWANCE and all(c*delta<=PRUNE_ERROR+FP_ALLOWANCE for c in cmax),'Pruning radiance/alpha budget')
                    require(all(math.isfinite(r) and r>=0 for r in ref['radius']),'Invalid reference radius')
                    endpoint_error=[max(abs(answer['rgb'][k]-ref['lower'][k]),abs(answer['rgb'][k]-ref['upper'][k])) for k in range(3)]
                    alpha_error=abs(answer['alpha']-alpha)
                    require(ref['endpoint_errors']==endpoint_error and ref['stop_reason']=='output_endpoint_accepted','Reference output decision mismatch')
                    require(max(endpoint_error)<=EPS+FP_ALLOWANCE and alpha_error<=EPS+FP_ALLOWANCE,'Ordinary RGB/alpha exceeds fixed accuracy gate')
                    require(0<=answer['alpha']<=1 and all(math.isfinite(x) for x in answer['rgb']),'Invalid ordinary output')
                    require(all(-FP_ALLOWANCE<=answer['rgb'][k]<=cmax[k]*answer['alpha']+FP_ALLOWANCE for k in range(3)),'Necessary color/alpha range failed')
                    active_sources=[i for i,m in enumerate(ref['finite_masses']) if m>=.0001]
                    mixed=len(active_sources)>=2 and max(max(particles[i]['color'][k] for i in active_sources)-min(particles[i]['color'][k] for i in active_sources) for k in range(3))>.01
                    group['nontrivial_rays']+=int(alpha>=.001);group['mixed_rays']+=int(mixed)
                    active.update(checks={'all_pass':True,'actual_omitted_mass':actual_omitted,'charged_rgb_error':[c*delta for c in cmax],
                          'endpoint_error':endpoint_error,'alpha_error':alpha_error,'mixed_color':mixed},
                          qualification_seconds=(time.perf_counter_ns()-start)/1e9)
                    records.append(active);journal({'event':'qualified','record':active});active=None
        stage='coverage_and_source_recheck';check_time()
        require(len(groups)==6 and all(g['nontrivial_rays']>=1 for g in groups),'Insufficient nontrivial geometric coverage')
        require(sum(g['mixed_rays'] for g in groups)>=1,'Insufficient mixed-color coverage')
        check_time();status='qualified_fixed_subset_only'
    except Exception as error:
        if active is not None and stage in ['ordinary_projection_and_pruning','ordinary_solve','independent_projection','reference_enclosure','qualification']:
            active['failed_stage_seconds']=(time.perf_counter_ns()-start)/1e9
        failed={'stage':stage,'code':getattr(error,'code',type(error).__name__),'error':str(error),'traceback':traceback.format_exc(),'ray':active,
                'reference_diagnostics':getattr(error,'diagnostics',None)}
        journal({'event':'failure','failure':failed})
    finally:
        source_tic=time.perf_counter_ns()
        try:
            verify_sources();final_source_check={'pass':True}
        except Exception as error:
            final_source_check={'pass':False,'error':str(error)}
            if failed is None:
                failed={'stage':'post_source_check','error':str(error),'ray':active}
            status='failed'
        timings['final_source_check_seconds']=(time.perf_counter_ns()-source_tic)/1e9
    numerical_end=time.perf_counter_ns()
    packet={'schema':'t33-output-qualification-results-v1','status':status,'scope':'fixed development subset; not full frame or formal floating-point certificate',
       'thresholds':{'rgb_alpha':EPS,'pruning':PRUNE_ERROR,'gl_nominal':GL_NOMINAL,'reference_stop':'fixed_output_endpoint','numerical_allowance':FP_ALLOWANCE},
       'groups':groups,'trees':tree_summaries,'records':records,'failure':failed,'counters':counters,'timings':timings,
       'completed_rays':len(records),'computation_elapsed_seconds':(numerical_end-tic)/1e9,
       'freeze_sha256':hashlib.sha256(frozen_bytes).hexdigest(),'final_source_check':final_source_check,'runtime':{'python':sys.version,'platform':platform.platform()},
       'simulations':0,'new_carriers':0,'gpu_runs':0,'retries':0,'not_a_delivery_benchmark':True,
       'cumulative_authored_entry_qualification_invocations':2,'T32_status_preserved':'failed'}
    result_info=None;publication_error=None
    serialize_tic=time.perf_counter_ns()
    try:
        result_bytes=(json.dumps(packet,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
        require(len(result_bytes)<=RAW_CAP,'Raw result exceeds32MiB cap')
        packed=gzip.compress(result_bytes,mtime=0)
        with (OUT/'results.json.gz').open('xb') as f:f.write(packed)
        result_info={'path':'results.json.gz','bytes':len(packed),'sha256':hashlib.sha256(packed).hexdigest(),
                     'raw_bytes':len(result_bytes),'raw_sha256':hashlib.sha256(result_bytes).hexdigest()}
    except Exception as error:
        publication_error=str(error);status='failed_publication'
    summary={'schema':'t33-worker-receipt-v1','status':status,'result':result_info,'publication_error':publication_error,
       'completed_rays':len(records),'planned_rays_in_constructed_groups':sum(len(g['pixels']) for g in groups),
       'groups_completed':sum(sum(r['frame']==g['frame'] and r['view_id']==g['view']['id'] for r in records)==len(g['pixels']) for g in groups),
       'failed_stage':None if failed is None else failed['stage'],'error':None if failed is None else failed['error'],
       'computation_elapsed_seconds':(numerical_end-tic)/1e9,'worker_elapsed_before_receipt_seconds':(time.perf_counter_ns()-tic)/1e9,
       'serialization_seconds':(time.perf_counter_ns()-serialize_tic)/1e9,'final_source_check':final_source_check,
       'counters':counters,'freeze_sha256':hashlib.sha256(frozen_bytes).hexdigest(),'retry_allowed':False,
       'failure_code':None if failed is None else failed.get('code',failed['stage']),
       'cumulative_authored_entry_qualification_invocations':2,'T32_status_preserved':'failed'}
    with (OUT/'result.json').open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,allow_nan=False))
    return 0 if status=='qualified_fixed_subset_only' else 2


if __name__=='__main__':
    raise SystemExit(main())
