"""Independent saved-byte audit only; no scientific or packaging module imports.

Default is a plan. --execute requires a finished supervisor receipt and writes
one exclusive JSON report. No new projection, CDF, exponential, integration,
density-bound evaluation, model generation, or scientific retry is performed.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import zlib

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parents[3]
FLOATS = ['r','g','b','alpha','lower_r','lower_g','lower_b','upper_r','upper_g','upper_b',
          'full_alpha','retained_alpha','analytic_r','analytic_g','analytic_b',
          'omission_r','omission_g','omission_b','mass_bound','actual_omitted_mass','prune_delta',
          'geometry_ratio','mu_ratio','q_ratio','a','b','preparation_seconds','ordinary_seconds',
          'projection_seconds','reference_seconds','qualification_seconds']
INTS = ['status','retained_count','reference_path','ordinary_path','gl_order','leaf_offset',
        'leaf_count','mixed','created_cells','partition_ok']
PIXEL, LEAF = struct.Struct('<31d10I'), struct.Struct('<9d')
WIDTH, HEIGHT, TOTAL = 256, 192, 49152
ALLOW, EPS, PRUNE = 1e-10, .001 + 1e-10, .00025 + 1e-10
CAP = 32 * 1024 * 1024
STAGE_MAP = {'preparation_seconds':'ordinary_projection_and_pruning',
             'ordinary_seconds':'ordinary_solve','projection_seconds':'independent_projection',
             'reference_seconds':'reference_enclosure','qualification_seconds':'qualification'}


def identity(path):
    data = path.read_bytes()
    return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def read_json(path):
    return json.loads(path.read_bytes())


class Audit:
    def __init__(self):
        self.counts, self.failures, self.failure_count = Counter(), [], 0

    def check(self, condition, category, detail=None):
        self.counts[category] += 1
        if not condition:
            self.failure_count += 1
            if len(self.failures) < 200:
                self.failures.append({'category':category,'detail':detail})

    def equal(self, actual, expected, category, detail=None):
        self.check(actual == expected, category,
                   detail if actual == expected else {'context':detail,'actual':actual,'expected':expected})


def png_pixels(data):
    """Only decode the saved RGB PNG layout and CRC; do not render any field."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('PNG signature')
    pos, payload, shape, ended = 8, bytearray(), None, False
    while pos < len(data):
        length = struct.unpack_from('>I', data, pos)[0]
        tag = data[pos+4:pos+8]
        body = data[pos+8:pos+8+length]
        crc = struct.unpack_from('>I', data, pos+8+length)[0]
        if zlib.crc32(tag + body) & 0xffffffff != crc:
            raise ValueError('PNG CRC')
        pos += 12 + length
        if tag == b'IHDR':
            shape = struct.unpack('>IIBBBBB', body)
        elif tag == b'IDAT':
            payload.extend(body)
        elif tag == b'IEND':
            ended = True
            break
    if shape != (WIDTH, HEIGHT, 8, 2, 0, 0, 0) or not ended or pos != len(data):
        raise ValueError('PNG dimensions/layout')
    scan = zlib.decompress(payload)
    stride = 1 + WIDTH*3
    if len(scan) != HEIGHT*stride or any(scan[y*stride] != 0 for y in range(HEIGHT)):
        raise ValueError('PNG scanline/filter')
    return b''.join(scan[y*stride+1:(y+1)*stride] for y in range(HEIGHT))


def verify_freeze(audit, freeze, phase):
    identities = []
    seen = set()
    for item in freeze['artifacts']:
        path = (ROOT / item['path']).resolve()
        audit.check(path.is_relative_to(ROOT) and item['path'] not in seen, 'freeze_paths', phase)
        seen.add(item['path'])
        got = identity(path)
        audit.equal(got, {k:item[k] for k in ['bytes','sha256']}, 'freeze_identity', item['path'])
        identities.append(dict(path=item['path'], **got))
    return identities


def ledger_check(audit, cells, a, b, retained_alpha, analytic, omission, lower, upper, cmax, label,
                 require_partition=True):
    """Arithmetic only on stored leaf entries; never recompute their density bounds."""
    if require_partition:
        audit.check(bool(cells) and cells[0][0] == a and cells[-1][1] == b,
                    'leaf_domain', label)
        audit.check(all(cells[i][1] == cells[i+1][0] for i in range(len(cells)-1)),
                    'leaf_adjacency', label)
        audit.check(abs(math.fsum(c[2] for c in cells)-retained_alpha) <= ALLOW,
                    'leaf_absorption', label)
    for j, c in enumerate(cells):
        audit.check(len(c) == 9 and all(math.isfinite(x) for x in c) and c[0] < c[1]
                    and c[2] >= 0 and all(-ALLOW <= c[3+k] <= c[6+k]+ALLOW
                    and c[6+k] <= c[2]*cmax[k]+ALLOW for k in range(3)),
                    'leaf_range', [label,j])
    for k in range(3):
        low = max(0., math.fsum([analytic[k]]+[c[3+k] for c in cells])-omission[k])
        high = math.fsum([analytic[k]]+[c[6+k] for c in cells])+omission[k]
        audit.check(abs(low-lower[k]) <= ALLOW and abs(high-upper[k]) <= ALLOW,
                    'leaf_endpoint_reconstruction', [label,k])


def audit_failed_reference(audit, failed, cmax):
    diag = failed.get('reference_diagnostics')
    ray = failed.get('ray') or {}
    returned = ray.get('reference')
    d = diag or returned
    if not d:
        return {'available':False,'reason':'No packaged reference bounds; no new evaluation attempted.'}
    summary = {k:d.get(k) for k in ['partial_unqualified','bounds_available','failure_kind','failure_cause',
                                    'stop_reason','created_cells','max_depth','endpoint_errors',
                                    'disjoint_channels','output_disproved'] if k in d}
    summary['available'] = True
    summary['kind'] = 'thrown_diagnostic' if diag else 'returned_reference_before_later_failure'
    cells = d.get('leaves', [])
    summary['stored_leaves'] = len(cells)
    bounds = all(k in d for k in ['lower','upper','analytic_retained_rgb','omission_rgb_radius'])
    rr = ray.get('reference_ray')
    if bounds and rr:
        ledger_check(audit, cells, rr['a'], rr['b'], d['retained_alpha'],
                     d['analytic_retained_rgb'], d['omission_rgb_radius'], d['lower'], d['upper'],
                     cmax, 'failed_reference', require_partition=bool(cells))
        answer = d.get('answer_rgb', (ray.get('ordinary') or {}).get('rgb'))
        if answer is not None:
            tol = d['tolerance']
            errors = [max(abs(answer[k]-d['lower'][k]),abs(answer[k]-d['upper'][k])) for k in range(3)]
            disjoint = [k for k in range(3) if d['upper'][k] < answer[k]-tol or d['lower'][k] > answer[k]+tol]
            audit.equal(d.get('endpoint_errors'),errors,'failed_reference_saved_endpoint_errors')
            if 'disjoint_channels' in d:
                audit.equal(d['disjoint_channels'],disjoint,'failed_reference_disjoint')
                audit.equal(d['output_disproved'],bool(disjoint),'failed_reference_disproof_flag')
            summary.update(recomputed_endpoint_errors=errors,recomputed_disjoint_channels=disjoint,
                           half_widths=[(hi-lo)*.5 for lo,hi in zip(d['lower'],d['upper'])],
                           saved_bounds_qualify=all(x<=tol for x in errors),
                           failed_run_remains_failed=True)
    if d.get('failure_kind') == 'unresolved':
        audit.check(d.get('stop_reason') != 'reference_output_inaccurate', 'failed_scope_kind')
    return summary


def perform(run):
    started = time.perf_counter()
    audit = Audit()
    freeze_path = HERE/'freeze.json'
    freeze_id = identity(freeze_path)
    freeze = read_json(freeze_path)
    before = verify_freeze(audit, freeze, 'before')
    # A final supervisor receipt is required; never inspect an active run as final.
    execution = read_json(run/'execution.json')
    audit.equal(execution.get('child_still_running'),False,'supervisor_child_stopped')
    result, frame, attempt = (read_json(run/name) for name in ['result.json','frame.json','attempt.json'])
    docs = {name:identity(run/name) for name in ['execution.json','result.json','frame.json','attempt.json']}
    for obj in [execution,result]:
        audit.equal(obj['freeze_sha256'],freeze_id['sha256'],'freeze_receipt')
    audit.equal(frame['frame'],90,'fixed_frame')
    audit.equal(frame['view'],{'id':'front','yaw':0},'fixed_view')
    audit.equal((frame['width'],frame['height'],frame['particle_count']),(WIDTH,HEIGHT,270),'fixed_dimensions')
    cmax = frame['cmax']
    audit.check(len(cmax)==3 and all(math.isfinite(x) and x>=0 for x in cmax),'frame_cmax')
    audit.equal(result['thresholds'],{'rgb_alpha':.001,'pruning':.00025,'gl_nominal':.000125,'numerical_allowance':ALLOW},'fixed_thresholds')
    audit.equal(result['planned_pixels'],TOTAL,'planned_pixels')
    audit.equal(result['initial_source_check']['pass'],True,'worker_initial_source')
    audit.equal(result['final_source_check']['pass'],True,'worker_final_source')
    audit.equal(execution['initial_source_check']['pass'],True,'supervisor_initial_source')
    audit.equal(execution['post_source_check']['pass'],True,'supervisor_post_source')
    audit.equal(execution['invocation'],1,'sole_invocation')
    audit.equal(execution['retries'],0,'no_retries')
    audit.equal(execution['computation_cap_seconds'],600,'fixed_budget')
    audit.equal(execution['external_wait_seconds'],630,'fixed_budget')
    audit.equal(execution['cleanup_cap_seconds'],10,'fixed_budget')
    for name, state in [('T32_status_preserved','failed'),('T33_status_preserved','failed'),('T34_status_preserved','qualified_fixed_subset_only')]:
        audit.equal(result[name],state,'historical_status',name)
    audit.check(all(result[k]==0 for k in ['simulations','new_carriers','gpu_runs','retries']), 'no_new_scientific_scope')
    ev = result['evidence']
    audit.equal(ev['schema'],'t35-fixed-binary-evidence-v1','evidence_schema')
    audit.equal((ev['width'],ev['height'],ev['record_format'],ev['record_bytes'],ev['leaf_format']),
                (WIDTH,HEIGHT,PIXEL.format,PIXEL.size,LEAF.format),'binary_schema')
    audit.equal(ev['float_fields'],FLOATS,'binary_schema')
    audit.equal(ev['integer_fields'],INTS,'binary_schema')
    audit.equal(ev['source_cmax'],cmax,'source_cmax')
    audit.equal(ev['particle_count'],270,'particle_count')
    payloads, images, file_ids = {}, {}, []
    for item in ev['files']:
        path = run/item['path']
        audit.check(path.parent.resolve()==run.resolve(),'publication_path',item['path'])
        data = path.read_bytes()
        got = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        audit.equal(got,{k:item[k] for k in ['bytes','sha256']},'publication_identity',item['path'])
        file_ids.append(dict(path=item['path'],**got))
        if item['path'].endswith('.gz'):
            raw = gzip.decompress(data)
            audit.equal({'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
                        {'bytes':item['raw_bytes'],'sha256':item['raw_sha256']},'raw_identity',item['path'])
            name = item['path'][:-3]
            if (run/name).exists():
                audit.check((run/name).read_bytes()==raw,'raw_gzip_equal',name)
            payloads[name] = raw
        elif item['path'].endswith('.png'):
            images[item['path']] = png_pixels(data)
    audit.equal(set(payloads),{'pixels.bin','leaves.bin'},'binary_files')
    audit.equal(set(images),{'rgb.png','alpha.png','retention.png','valid.png'},'display_files')
    pixels, ledger = payloads['pixels.bin'],payloads['leaves.bin']
    audit.equal(len(pixels),TOTAL*PIXEL.size,'pixel_extent')
    audit.equal(ev['raw_binary_bytes'],len(pixels)+len(ledger),'binary_extent')
    summary = {'planned_pixels':TOTAL,'qualified_pixels':0,'failed_pixels':0,'uncomputed_pixels':0,
               'nontrivial_pixels':0,'mixed_pixels':0,'nontrivial_bbox':None,'max_rgb_endpoint_error':0.,
               'max_alpha_error':0.,'rgb_min':None,'rgb_max':None,'alpha_min':None,'alpha_max':None,
               'ordinary_paths':{},'reference_paths':{},'retained_histogram':{},'stage_seconds':{},
               'max_endpoint_pixel':None,'max_alpha_pixel':None,'max_created_cells':0,
               'stored_leaves':len(ledger)//LEAF.size,'partial_leaf_tail_bytes':len(ledger)%LEAF.size}
    used_leaves, created, refinement, initial, enclosures = 0,0,0,0,0
    failure_indices, first_invalid, row_qualified = [],None,[0]*HEIGHT
    for index, values in enumerate(PIXEL.iter_unpack(pixels)):
        p = dict(zip(FLOATS+INTS,values)); status=p['status']; xy=[index%WIDTH,index//WIDTH]
        audit.check(status in (0,1,2),'pixel_status',index)
        if status != 1:
            if first_invalid is None:first_invalid=index
            summary['failed_pixels' if status==2 else 'uncomputed_pixels']+=1
            if status==2:failure_indices.append(index)
            audit.check(images['valid.png'][index*3:index*3+3]==b'\0\0\0','valid_mask',index)
            for name in ['rgb.png','alpha.png','retention.png']:
                audit.check(images[name][index*3:index*3+3]==b'\xff\0\xff','invalid_display',index)
            continue
        audit.check(first_invalid is None,'qualified_row_major_prefix',index)
        audit.check(images['valid.png'][index*3:index*3+3]==b'\xff\xff\xff','valid_mask',index)
        audit.check(all(math.isfinite(p[k]) for k in FLOATS),'pixel_finite',index)
        audit.check(p['partition_ok']==1 and p['mixed'] in (0,1) and 0<=p['retained_count']<=270,
                    'pixel_discrete_fields',index)
        audit.check(p['reference_path'] in (1,2,3) and p['ordinary_path'] in (1,2,3), 'path_codes',index)
        audit.check((p['gl_order'] in (4,8,16,32,64)) if p['ordinary_path']==3 else p['gl_order']==0,
                    'gl_path_order',index)
        audit.check(p['a']<p['b'] and all(0<=p[k]<=1 for k in ['geometry_ratio','mu_ratio','q_ratio']),
                    'stored_geometry_residuals',index)
        audit.check(all(0<=p[k]<=1 for k in ['alpha','full_alpha','retained_alpha']), 'alpha_range',index)
        audit.check(all(p[k]>=0 for k in STAGE_MAP), 'stage_time_nonnegative',index)
        audit.check(0<=p['mass_bound']<=frame['mass_budget']+ALLOW and
                    0<=p['actual_omitted_mass']<=p['mass_bound']+ALLOW, 'pruning_mass_gates',index)
        audit.check(0<=p['prune_delta']<=PRUNE and all(c*p['prune_delta']<=PRUNE for c in cmax),
                    'pruning_rgb_alpha_gates',index)
        rgb=[p[k] for k in 'rgb']; low=[p['lower_'+k] for k in 'rgb']; high=[p['upper_'+k] for k in 'rgb']
        analytic=[p['analytic_'+k] for k in 'rgb']; omitted=[p['omission_'+k] for k in 'rgb']
        audit.check(all(lo>=-ALLOW and lo<=hi and o>=0 for lo,hi,o in zip(low,high,omitted)), 'reference_range',index)
        audit.check(all(-ALLOW<=x<=c*p['alpha']+ALLOW for x,c in zip(rgb,cmax)), 'ordinary_rgb_range',index)
        error=max(max(abs(x-lo),abs(x-hi)) for x,lo,hi in zip(rgb,low,high)); ae=abs(p['alpha']-p['full_alpha'])
        audit.check(error<=EPS and ae<=EPS, 'ordinary_endpoint_alpha_gates',index)
        audit.equal(p['leaf_offset'],used_leaves,'leaf_ownership',index)
        end=(p['leaf_offset']+p['leaf_count'])*LEAF.size
        audit.check(end<=len(ledger),'leaf_extent',index)
        cells=list(LEAF.iter_unpack(ledger[p['leaf_offset']*LEAF.size:end]))
        used_leaves+=p['leaf_count']; created+=p['created_cells']
        if p['reference_path']==3:
            enclosures+=1
            audit.check(0<p['leaf_count']<=p['created_cells']<=8192 and p['created_cells']<=2*p['leaf_count'],
                        'reference_created_leaf_accounting',index)
            refinement+=p['created_cells']-p['leaf_count']
            initial+=2*p['leaf_count']-p['created_cells']
        else:
            audit.check(not cells and p['created_cells']==0,'analytic_reference_ledger',index)
        ledger_check(audit,cells,p['a'],p['b'],p['retained_alpha'],analytic,omitted,low,high,cmax,index,
                     require_partition=p['reference_path']==3)
        summary['qualified_pixels']+=1; summary['mixed_pixels']+=p['mixed']; row_qualified[xy[1]]+=1
        if p['full_alpha']>=.001:
            summary['nontrivial_pixels']+=1; box=summary['nontrivial_bbox']
            summary['nontrivial_bbox']=[*xy,*xy] if box is None else [min(box[0],xy[0]),min(box[1],xy[1]),max(box[2],xy[0]),max(box[3],xy[1])]
        summary['rgb_min']=rgb[:] if summary['rgb_min'] is None else [min(a,b) for a,b in zip(summary['rgb_min'],rgb)]
        summary['rgb_max']=rgb[:] if summary['rgb_max'] is None else [max(a,b) for a,b in zip(summary['rgb_max'],rgb)]
        summary['alpha_min']=p['full_alpha'] if summary['alpha_min'] is None else min(summary['alpha_min'],p['full_alpha'])
        summary['alpha_max']=p['full_alpha'] if summary['alpha_max'] is None else max(summary['alpha_max'],p['full_alpha'])
        if error>summary['max_rgb_endpoint_error']:summary['max_rgb_endpoint_error']=error;summary['max_endpoint_pixel']=xy
        if ae>summary['max_alpha_error']:summary['max_alpha_error']=ae;summary['max_alpha_pixel']=xy
        summary['max_created_cells']=max(summary['max_created_cells'],p['created_cells'])
        for field,key in [('ordinary_path','ordinary_paths'),('reference_path','reference_paths'),('retained_count','retained_histogram')]:
            value=str(p[field]);summary[key][value]=summary[key].get(value,0)+1
        for field in STAGE_MAP:summary['stage_seconds'][field]=summary['stage_seconds'].get(field,0.)+p[field]
    summary['unreferenced_leaf_tail']=len(ledger)//LEAF.size-used_leaves
    summary['nontrivial_fraction_of_full_frame']=summary['nontrivial_pixels']/TOTAL
    summary['all_pixel_records_qualified']=summary['qualified_pixels']==TOTAL and summary['failed_pixels']==0
    audit.equal(summary,ev['summary'],'aggregate_summary')
    audit.check(len(failure_indices)<=1 and (not failure_indices or failure_indices==[first_invalid]),'failed_pixel_position')
    for field,source in [('completed_pixels','qualified_pixels'),('nontrivial_pixels','nontrivial_pixels'),('mixed_pixels','mixed_pixels')]:
        audit.equal(result[field],summary[source],'worker_binary_counts',field)
    for field,stage in STAGE_MAP.items():
        audit.check(summary['stage_seconds'].get(field,0)<=result['stage_seconds_including_failed_work'].get(stage,0)+1e-8,
                    'timing_includes_failed_work',stage)
    audit.check(all(math.isfinite(x) and x>=0 for x in result['stage_seconds_including_failed_work'].values()),'total_stage_time_valid')
    audit.check(sum(result['stage_seconds_including_failed_work'].values())<=result['computation_elapsed_seconds']+1e-5,'total_stage_time_accounting')
    counts=result['counters']; get=lambda k:counts.get(k,0)
    audit.check(all(isinstance(v,int) and v>=0 for v in counts.values()),'counter_range')
    audit.check(created<=get('reference_created_cells')<=200000,'global_reference_created_cap')
    audit.equal(get('reference_cdf_calls'),2*get('reference_cdf_intervals'),'cdf_counter_identity')
    audit.equal(get('reference_cdf_calls'),get('reference_erf_calls')+get('reference_erfc_calls'),'cdf_counter_identity')
    audit.check(get('reference_expm1_calls')<=get('reference_exp_calls'),'exp_counter_inclusion')
    complete=result['status']=='qualified_first_complete_frame_only'
    if complete:
        audit.equal(get('reference_created_cells'),created,'complete_cell_accounting')
        audit.equal(get('reference_refinements'),refinement,'complete_cell_accounting')
        audit.equal(get('reference_initial_segments'),initial,'complete_cell_accounting')
        audit.equal(get('reference_box_sort_calls'),3*enclosures,'complete_box_accounting')
        channels=get('reference_box_channel_calls'); positive=channels-get('reference_box_zero_lower_channels')
        products=get('reference_box_product_ops'); corners=get('reference_box_corner_candidates')
        audit.equal(channels,3*created,'complete_box_accounting')
        audit.equal(get('reference_box_scan_calls'),8*positive,'complete_box_accounting')
        audit.equal(get('reference_box_scan_items'),4*products,'complete_box_accounting')
        audit.equal(corners,products+2*positive,'complete_box_accounting')
        audit.equal(get('reference_box_ratio_evaluations'),corners,'complete_box_accounting')
        audit.equal(get('reference_box_support_items'),3*get('reference_density_bound_components')-products//2,'complete_box_accounting')
        audit.equal(get('reference_box_add_sub_ops'),get('reference_box_sort_items')+5*get('reference_box_scan_items')+2*corners+2*positive,'complete_box_accounting')
        audit.equal(get('reference_projected_components'),TOTAL*270,'complete_projection_count')
        audit.check(summary['all_pixel_records_qualified'] and summary['nontrivial_pixels']>=1 and summary['mixed_pixels']>=1,
                    'complete_coverage')
        audit.check(summary['unreferenced_leaf_tail']==0 and summary['partial_leaf_tail_bytes']==0,'complete_leaf_tail')
        audit.check(result['computation_elapsed_seconds']<=600 and execution['returncode']==0
                    and execution['success'] and not execution['timed_out'] and not execution['errors'], 'complete_execution_scope')
        audit.equal(result['publication_status'],'packaged','complete_publication')
        audit.equal(result['failure_path'],None,'complete_no_failure')
    else:
        audit.equal(execution['success'],False,'failed_run_stays_failed')
    raw_names=['pixels.bin','leaves.bin','failure.json','frame.json','result.json']
    raw_sizes={name:(run/name).stat().st_size for name in raw_names if (run/name).exists()}
    # Raw binaries may be removed after lossless packaging; use verified decompressed extents in that event.
    raw_sizes.setdefault('pixels.bin',len(pixels));raw_sizes.setdefault('leaves.bin',len(ledger))
    raw_total=sum(raw_sizes.values())
    audit.equal(raw_total-raw_sizes.get('result.json',0),
                result['raw_other_numeric_bytes'],'raw_other_extent')
    audit.equal(raw_total,execution['raw_numeric_bytes'],'raw_numeric_extent')
    audit.check(raw_total<=CAP and result['raw_numeric_cap_bytes']==CAP,'raw_numeric_cap')
    for name,ident in execution.get('logs',{}).items():
        audit.equal(identity(run/name),ident,'log_identity',name)
    failed_summary=None
    if result.get('failure_path'):
        failed=read_json(run/result['failure_path']); docs['failure.json']=identity(run/result['failure_path'])
        audit.equal(failed['stage'],result['failed_stage'],'failure_receipt')
        audit.equal(failed.get('code'),result['failure_code'],'failure_receipt')
        failed_summary=audit_failed_reference(audit,failed,cmax)
    after=verify_freeze(audit,freeze,'after')
    audit.equal(after,before,'source_identity_before_after')
    audit.equal(identity(freeze_path),freeze_id,'freeze_identity_before_after')
    for name,ident in docs.items():audit.equal(identity(run/name),ident,'saved_identity_before_after',name)
    for item in file_ids:
        audit.equal(identity(run/item['path']),{k:item[k] for k in ['bytes','sha256']},
                    'published_identity_before_after',item['path'])
    limitations=[
        'No new scientific evaluation. Binary64 stored arithmetic is not a formal floating-point certificate.',
        'Complete per-pixel primitive arrays and IDs are not stored: source projection, BVH partition, actual omitted-mass provenance, mixed classification, and component density extrema are worker checks, not independently regenerated here.',
        'Stored pruning delta is checked against budgets, not recomputed with expm1. Stored normalized residuals are checked, not regenerated from camera geometry.',
        'RGB PNG transfer is not reevaluated: identity, dimensions, CRC, valid mask and invalid magenta are audited; the fixed transfer was reviewed statically.',
        'Counters are named implementation operations, not total FLOPs. Full-run box counter equalities are not asserted for an interrupted partial operation.',
        'Successful scope would be one authored first frame, not six groups, new assets, an optimized strong baseline, a speedup benchmark, or a TOG contribution.'
    ]
    return {'schema':'t35-independent-saved-binary-audit-v1','audit_pass':audit.failure_count==0,
            'scientific_status_preserved':result['status'],'complete_frame_claim':complete and audit.failure_count==0,
            'checks':dict(audit.counts),'check_count':sum(audit.counts.values()),'failure_count':audit.failure_count,
            'failures':audit.failures,'failure_list_truncated':audit.failure_count>len(audit.failures),
            'freeze':freeze_id,'frozen_identities':before,'saved_identities':docs,'published_identities':file_ids,
            'summary_recomputed':summary,'row_qualified_counts':row_qualified,'failed_pixel_indices':failure_indices,
            'accepted_ledger_accounting':{'leaves':used_leaves,'created':created,'refinements':refinement,'initial_segments':initial,'enclosure_pixels':enclosures},
            'worker_counters':counts,'failed_reference_audit':failed_summary,'raw_numeric_sizes':raw_sizes,'raw_numeric_total':raw_total,
            'execution_scope':{k:execution.get(k) for k in ['returncode','timed_out','success','errors','process_and_cleanup_seconds','cleanup_seconds','packaging_needed']},
            'timings':{k:result.get(k) for k in ['computation_elapsed_seconds','stage_seconds_including_failed_work','publication_seconds','worker_elapsed_before_result_seconds']},
            'attempt':attempt,'limitations':limitations,'audit_seconds':time.perf_counter()-started,
            'scientific_module_imports':0,'new_scientific_evaluations':0}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute',action='store_true')
    p.add_argument('--run-dir',type=Path,default=HERE/'run-01')
    p.add_argument('--out',type=Path)
    args=p.parse_args()
    if not args.execute:
        print(json.dumps({'mode':'plan_only','requires':'Finished execution.json and packaged result.json before --execute.',
                          'scientific_evaluations':0,'fixed_schema':'<31d10I + <9d'}))
        return 0
    if args.out is None or args.out.exists():
        p.error('--out must name a new file; outputs are never overwritten')
    # Reserve before reading saved evidence. Unhandled errors are recorded as audit failures.
    with args.out.open('x',encoding='utf-8') as stream:
        try:
            report=perform(args.run_dir)
        except Exception as error:
            report={'schema':'t35-independent-saved-binary-audit-v1','audit_pass':False,
                    'error':type(error).__name__+': '+str(error),'new_scientific_evaluations':0}
        json.dump(report,stream,separators=(',',':'),allow_nan=False);stream.write('\n')
    print(json.dumps({k:report.get(k) for k in ['audit_pass','scientific_status_preserved','check_count','failure_count','error']}))
    return 0 if report['audit_pass'] else 2


if __name__=='__main__':
    raise SystemExit(main())
