"""Saved-byte audit; no renderer, scientific kernel or evidence module imports.

Default plan only. Execute once after the supervisor has finished. The display
transfer is recomputed only from saved RGB; no scientific color is regenerated.
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

TASK=Path(__file__).resolve().parent.parent
ROOT=TASK.parents[3]
OLD=ROOT/'tracks/tog/tasks/t35-first-complete-frame/run-01'
PIXEL=struct.Struct('<13d6I')
LEGACY=struct.Struct('<31d10I')
WIDTH,HEIGHT,TOTAL=256,192,49152
FLOATS=['rgb_r','rgb_g','rgb_b','alpha','ray_near','ray_far','mass_bound','prune_delta',
        'preparation_seconds','ordinary_seconds','comparison_seconds','max_endpoint_error','alpha_error']
INTS=['status','retained_count','ordinary_path','gl_order','partition_ok','replay_match']
OLD_GZIP_SHA='e19dde61545fb792ec50cf9e815d4626943acc78704cba6d9a48d7965dc3c835'
OLD_RAW_SHA='006ffabaeb79ec7a2f1e32f8875e45298a3e0d2c7fe8d4cecabff394d4304f5c'
EPS,ALLOW,PRUNE,CAP=.001+1e-10,1e-10,.00025+1e-10,32*1024*1024


def sha(data):return hashlib.sha256(data).hexdigest()
def ident(path):
    data=path.read_bytes();return dict(bytes=len(data),sha256=sha(data))
def js(path):return json.loads(path.read_bytes())


class Audit:
    def __init__(self):self.counts=Counter();self.failures=[];self.failure_count=0
    def check(self,ok,kind,detail=None):
        self.counts[kind]+=1
        if not ok:
            self.failure_count+=1
            if len(self.failures)<200:self.failures.append(dict(kind=kind,detail=detail))
        return bool(ok)
    def equal(self,a,b,kind,detail=None):return self.check(a==b,kind,detail)


def sources(audit,freeze):
    items=[];seen=set()
    for item in freeze['artifacts']:
        path=(ROOT/item['path']).resolve()
        audit.check(path.is_relative_to(ROOT) and item['path'] not in seen,'frozen_path',item['path'])
        seen.add(item['path']);got=ident(path)
        audit.equal(got,{k:item[k] for k in ['bytes','sha256']},'frozen_identity',item['path'])
        items.append(dict(path=item['path'],**got))
    return items


def decode_png(data):
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
    offset=8;compressed=bytearray();header=None;ended=False
    while offset<len(data):
        n=struct.unpack_from('>I',data,offset)[0];tag=data[offset+4:offset+8]
        body=data[offset+8:offset+8+n];crc=struct.unpack_from('>I',data,offset+8+n)[0]
        if zlib.crc32(tag+body)&0xffffffff!=crc:raise ValueError('PNG CRC')
        offset+=12+n
        if tag==b'IHDR':header=struct.unpack('>IIBBBBB',body)
        elif tag==b'IDAT':compressed.extend(body)
        elif tag==b'IEND':ended=True;break
    if header!=(WIDTH,HEIGHT,8,2,0,0,0) or not ended or offset!=len(data):raise ValueError('PNG layout')
    scan=zlib.decompress(compressed);stride=WIDTH*3+1
    if len(scan)!=HEIGHT*stride or any(scan[y*stride]!=0 for y in range(HEIGHT)):raise ValueError('PNG scanline')
    return b''.join(scan[y*stride+1:(y+1)*stride] for y in range(HEIGHT))


def byte(x):return int(math.floor(max(0.,min(1.,x))*255+.5))
def display(x):
    v=max(0.,x)/(1+max(0.,x))
    return byte(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055)


def run_audit(run):
    begin=time.perf_counter();a=Audit()
    freeze_path=TASK/'freeze.json';freeze_id=ident(freeze_path);freeze=js(freeze_path)
    before=sources(a,freeze)
    result,execution,frame,attempt=(js(run/name) for name in ['result.json','execution.json','frame.json','attempt.json'])
    saved_ids={name:ident(run/name) for name in ['result.json','execution.json','frame.json','attempt.json']}
    a.equal(execution['child_still_running'],False,'finished_supervisor')
    for receipt in [result,execution,attempt]:a.equal(receipt['freeze_sha256'],freeze_id['sha256'],'receipt_freeze')
    old_comp=(OLD/'pixels.bin.gz').read_bytes();old=gzip.decompress(old_comp)
    a.equal(sha(old_comp),OLD_GZIP_SHA,'legacy_gzip_identity')
    a.equal(sha(old),OLD_RAW_SHA,'legacy_raw_identity')
    a.equal(len(old),TOTAL*LEGACY.size,'legacy_extent')
    prior_result,prior_frame=js(OLD/'result.json'),js(OLD/'frame.json')
    prior_ids={name:ident(OLD/name) for name in ['result.json','frame.json','pixels.bin.gz','leaves.bin.gz']}
    old_manifest=next(x for x in prior_result['evidence']['files'] if x['path']=='pixels.bin.gz')
    a.equal(old_manifest['raw_sha256'],OLD_RAW_SHA,'legacy_manifest_identity')
    a.equal(old_manifest['sha256'],OLD_GZIP_SHA,'legacy_manifest_identity')
    # The intact reference was already fully audited in T35. No leaf re-optimization or re-integration.
    a.equal(result['runtime'],prior_result['runtime'],'runtime_identity')
    for key in ['frame','view','width','height','particle_count','cmax','mass_budget','camera_params','camera','bvh_node_count']:
        a.equal(frame[key],prior_frame[key],'frame_reproduction',key)
    a.equal((frame['frame'],frame['view'],frame['width'],frame['height'],frame['particle_count']),
            (90,{'id':'front','yaw':0},WIDTH,HEIGHT,270),'fixed_workload')
    cmax=frame['cmax'];mass_budget=frame['mass_budget']
    a.equal(result['thresholds'],{'rgb_alpha':.001,'pruning':.00025,'gl_nominal':.000125,'numerical_allowance':ALLOW},'thresholds')
    a.equal(result['reference_invocations_in_T36'],0,'no_reference_invocation')
    a.equal(result['scientific_invocations_in_T35_T36'],2,'cumulative_invocations')
    a.equal(result['T35_delivery_status_preserved'],'failed_saved_blue_alias','old_failure_preserved')
    a.equal(result['prior_T35_paid_cost'],dict(computation_seconds=prior_result['computation_elapsed_seconds'],
            publication_seconds=prior_result['publication_seconds'],stages_seconds=prior_result['stage_seconds_including_failed_work']),
            'prior_cost_retained')
    a.check(all(result[k]==0 for k in ['simulations','new_carriers','gpu_runs','retries']),'no_scope_expansion')
    for key in ['initial_source_check','final_source_check']:a.equal(result[key]['pass'],True,'worker_sources',key)
    for key in ['initial_source_check','post_source_check']:a.equal(execution[key]['pass'],True,'supervisor_sources',key)
    a.equal((execution['computation_cap_seconds'],execution['external_wait_seconds'],execution['cleanup_cap_seconds']),(300,330,10),'fixed_budget')
    a.equal((execution['invocation'],execution['retries'],attempt['retry_allowed']),(1,0,False),'sole_invocation')
    ev=result['evidence'];a.equal(ev['schema'],'t36-ordinary-saved-output-v1','schema')
    a.equal((ev['width'],ev['height'],ev['record_format'],ev['record_bytes']),(WIDTH,HEIGHT,PIXEL.format,PIXEL.size),'schema')
    a.equal(ev['float_fields'],FLOATS,'schema');a.equal(ev['integer_fields'],INTS,'schema')
    a.check(len(FLOATS+INTS)==len(set(FLOATS+INTS))==19 and ev['fields_unique'],'unique_schema')
    pub_ids=[];images={};raw=None
    for item in ev['files']:
        path=run/item['path'];a.check(path.resolve().parent==run.resolve(),'published_path',item['path'])
        data=path.read_bytes();got=dict(bytes=len(data),sha256=sha(data));pub_ids.append(dict(path=item['path'],**got))
        a.equal(got,{k:item[k] for k in ['bytes','sha256']},'published_identity',item['path'])
        if item['path']=='pixels.bin.gz':
            raw=gzip.decompress(data)
            a.equal(dict(bytes=len(raw),sha256=sha(raw)),dict(bytes=item['raw_bytes'],sha256=item['raw_sha256']),'raw_identity')
            if (run/'pixels.bin').exists():a.check((run/'pixels.bin').read_bytes()==raw,'raw_gzip_equality')
        elif item['path'].endswith('.png'):images[item['path']]=decode_png(data)
        else:a.check(False,'unexpected_publication',item['path'])
    a.equal(set(images),{'rgb.png','alpha.png','retention.png','valid.png'},'image_set')
    a.equal(len(raw),TOTAL*128,'new_extent');a.equal(ev['raw_binary_bytes'],len(raw),'new_extent')
    summary=dict(committed_pixels=0,qualified_pixels=0,invalid_saved_pixels=0,failed_pixels=0,uncomputed_pixels=0,
                 nontrivial_pixels=0,mixed_pixels=0,nontrivial_bbox=None,max_rgb_endpoint_error=0.,max_alpha_error=0.,
                 rgb_min=None,rgb_max=None,alpha_max=0.,ordinary_paths={},retained_histogram={},stage_seconds={},failure_count=0,failures=[])
    first_invalid=None;failed_indices=[];per_channel_max=[0.,0.,0.];row_counts=[0]*HEIGHT;max_clip_residual=0.
    for index,p in enumerate(PIXEL.iter_unpack(raw)):
        o=LEGACY.unpack_from(old,index*LEGACY.size);status=p[13]
        a.check(status in (0,1,2),'status',index)
        valid=False
        if status==1:
            a.check(first_invalid is None,'row_major_committed_prefix',index);summary['committed_pixels']+=1
            finite=all(math.isfinite(x) for x in p[:13]);a.check(finite,'new_finite',index)
            err=[max(abs(p[k]-o[4+k]),abs(p[k]-o[7+k])) for k in range(3)];ae=abs(p[3]-o[10])
            res=[abs(p[k]-o[q])/(1e-12*max(1.,abs(p[k]),abs(o[q]))) for k,q in [(4,24),(5,25)]]
            max_clip_residual=max(max_clip_residual,*res)
            checks={
                'legacy_status_partition':o[31]==1 and o[40]==1,
                'legacy_residuals':all(0<=o[k]<=1 for k in [21,22,23]),
                'legacy_reference_range':all(0<=o[4+k]<=o[7+k] and math.isfinite(o[7+k]) for k in range(3)) and 0<=o[10]<=1,
                'reproduction':(p[0],p[1],p[3],p[14],p[15],p[16],p[6],p[7])==(o[0],o[1],o[3],o[32],o[34],o[35],o[18],o[20]),
                'geometry':max(res)<=1 and 0<=p[4]<p[5],
                'path_flags':p[17]==1 and p[18]==1 and 0<=p[14]<=270 and p[15] in (1,2,3) and (p[16] in (4,8,16,32,64) if p[15]==3 else p[16]==0),
                'output_range':0<=p[3]<=1 and all(-ALLOW<=p[k]<=cmax[k]*p[3]+ALLOW for k in range(3)),
                'endpoint_alpha':max(err)<=EPS and ae<=EPS,
                'reported_error':abs(p[11]-max(err))<=ALLOW and abs(p[12]-ae)<=ALLOW,
                'omission':0<=p[6]<=mass_budget+ALLOW and 0<=o[19]<=p[6]+ALLOW and 0<=p[7]<=PRUNE and all(c*p[7]<=PRUNE for c in cmax),
                'stage_times':all(p[k]>=0 for k in [8,9,10])}
            for name,passed in checks.items():a.check(passed,'pixel_'+name,index)
            bad=[name for name,passed in checks.items() if not passed]
            valid=finite and not bad
            if bad:
                summary['invalid_saved_pixels']+=1;summary['failure_count']+=len(bad)
                if len(summary['failures'])<100:summary['failures'].append(dict(pixel_index=index,failed_checks=bad))
            if valid:
                summary['qualified_pixels']+=1;row_counts[index//WIDTH]+=1
                summary['mixed_pixels']+=o[38]
                per_channel_max=[max(x,y) for x,y in zip(per_channel_max,err)]
                summary['max_rgb_endpoint_error']=max(summary['max_rgb_endpoint_error'],*err)
                summary['max_alpha_error']=max(summary['max_alpha_error'],ae);summary['alpha_max']=max(summary['alpha_max'],o[10])
                rgb=list(p[:3]);summary['rgb_min']=rgb if summary['rgb_min'] is None else [min(x,y) for x,y in zip(summary['rgb_min'],rgb)]
                summary['rgb_max']=rgb if summary['rgb_max'] is None else [max(x,y) for x,y in zip(summary['rgb_max'],rgb)]
                if o[10]>=.001:
                    summary['nontrivial_pixels']+=1;i,j=index%WIDTH,index//WIDTH;box=summary['nontrivial_bbox']
                    summary['nontrivial_bbox']=[i,j,i,j] if box is None else [min(box[0],i),min(box[1],j),max(box[2],i),max(box[3],j)]
                for slot,key in [(15,'ordinary_paths'),(14,'retained_histogram')]:
                    k=str(p[slot]);summary[key][k]=summary[key].get(k,0)+1
                for slot,key in [(8,'preparation_seconds'),(9,'ordinary_seconds'),(10,'comparison_seconds')]:
                    summary['stage_seconds'][key]=summary['stage_seconds'].get(key,0.)+p[slot]
        else:
            if first_invalid is None:first_invalid=index
            summary['failed_pixels' if status==2 else 'uncomputed_pixels']+=1
            if status==2:failed_indices.append(index)
        expected={'valid.png':b'\xff\xff\xff' if valid else b'\0\0\0'}
        if valid:
            expected.update({'rgb.png':bytes(display(x) for x in p[:3]),'alpha.png':bytes([byte(p[3])]*3),
                             'retention.png':bytes([byte(p[14]/270)]*3)})
        else:expected.update({name:b'\xff\0\xff' for name in ['rgb.png','alpha.png','retention.png']})
        for name,want in expected.items():a.check(images[name][index*3:index*3+3]==want,'display_from_saved_bytes',dict(pixel=index,image=name))
    summary['saved_validation_pass']=summary['invalid_saved_pixels']==0
    summary['all_pixel_records_qualified']=summary['qualified_pixels']==TOTAL and summary['saved_validation_pass']
    summary['nontrivial_fraction_of_full_frame']=summary['nontrivial_pixels']/TOTAL
    a.equal(summary,ev['summary'],'entire_summary')
    a.check(len(failed_indices)<=1 and (not failed_indices or failed_indices==[first_invalid]),'failed_position')
    for field,key in [('completed_pixels','committed_pixels'),('inherited_nontrivial_pixels','nontrivial_pixels'),('inherited_mixed_pixels','mixed_pixels')]:
        a.equal(result[field],summary[key],'worker_binary_counts',field)
    times=result['stage_seconds_including_failed_work']
    for small,big in [('preparation_seconds','ordinary_projection_and_pruning'),('ordinary_seconds','ordinary_solve'),('comparison_seconds','saved_evidence_comparison')]:
        a.check(summary['stage_seconds'].get(small,0)<=times.get(big,0)+1e-8,'failed_work_accounted',big)
    a.check(all(math.isfinite(v) and v>=0 for v in times.values()) and sum(times.values())<=result['computation_elapsed_seconds']+1e-5,'stage_accounting')
    counts=result['counters'];a.check(all(isinstance(v,int) and v>=0 for v in counts.values()),'counter_validity')
    a.check(not any(k.startswith('reference_') for k in counts),'no_reference_counters')
    complete=result['status']=='qualified_ordinary_replay_only'
    if complete:
        a.check(summary['all_pixel_records_qualified'] and summary['nontrivial_pixels']>=1 and summary['mixed_pixels']>=1,'complete_saved_coverage')
        a.check(execution['success'] and execution['returncode']==0 and not execution['timed_out'] and not execution['errors'],'complete_execution')
        a.check(result['computation_elapsed_seconds']<=300 and result['publication_status']=='packaged' and result['failure_path'] is None,'complete_scope')
        a.equal(counts.get('ordinary_calls'),TOTAL,'complete_call_count')
    else:a.equal(execution['success'],False,'failed_stays_failed')
    raw_sizes={name:(run/name).stat().st_size for name in ['pixels.bin','frame.json','failure.json','result.json'] if (run/name).exists()}
    raw_sizes.setdefault('pixels.bin',len(raw));raw_total=sum(raw_sizes.values())
    a.equal(raw_total,execution['raw_numeric_bytes'],'raw_size');a.equal(raw_total-raw_sizes['result.json'],result['raw_other_numeric_bytes'],'raw_size')
    a.check(raw_total<=CAP and result['raw_numeric_cap_bytes']==CAP,'raw_cap')
    for name,expected in execution['logs'].items():a.equal(ident(run/name),expected,'log_identity',name)
    after=sources(a,freeze);a.equal(after,before,'sources_before_after');a.equal(ident(freeze_path),freeze_id,'freeze_before_after')
    for name,expected in saved_ids.items():a.equal(ident(run/name),expected,'saved_before_after',name)
    for name,expected in prior_ids.items():a.equal(ident(OLD/name),expected,'prior_before_after',name)
    for item in pub_ids:a.equal(ident(run/item['path']),{k:item[k] for k in ['bytes','sha256']},'published_before_after',item['path'])
    old_ordinary={k:v for k,v in prior_result['counters'].items() if not k.startswith('reference_')}
    return dict(schema='t36-independent-saved-output-audit-v1',audit_pass=a.failure_count==0,
                scientific_status_preserved=result['status'],new_delivery_qualified=complete and a.failure_count==0,
                check_count=sum(a.counts.values()),checks=dict(a.counts),failure_count=a.failure_count,failures=a.failures,
                failure_list_truncated=a.failure_count>len(a.failures),freeze=freeze_id,frozen_identities=before,
                saved_identities=saved_ids,prior_identities=prior_ids,published_identities=pub_ids,
                summary_recomputed=summary,per_channel_max_endpoint_errors=per_channel_max,
                max_clip_normalized_residual=max_clip_residual,row_qualified_counts=row_counts,failed_pixel_indices=failed_indices,
                raw_numeric_sizes=raw_sizes,raw_numeric_total=raw_total,counters=counts,
                ordinary_counter_reproduction_diagnostic=(counts==old_ordinary),
                timings={k:result[k] for k in ['computation_elapsed_seconds','stage_seconds_including_failed_work','publication_seconds','worker_elapsed_before_result_seconds','prior_T35_paid_cost']},
                execution_scope={k:execution[k] for k in ['success','returncode','timed_out','errors','process_and_cleanup_seconds','cleanup_seconds','packaging_needed']},
                limitations=['T35 remains a failed RGB delivery; new blue is recomputed ordinary output, not recovered old blue.',
                             'Prior reference identity and corresponding endpoints are checked; the already audited complete leaf mathematics is not repeated.',
                             'Source arrays are not regenerated independently: old geometry/projection/omitted-mass evidence is reused under fixed-source deterministic replay.',
                             'Exact unchanged fields, saved-output gates and display encoding are checked independently; no new scientific samples, CDFs, density bounds or integrals.',
                             'Named operation counters and paid reference/replay costs do not establish a speedup, strong baseline, novel method or TOG contribution.',
                             'This remains binary64 qualification for one authored fixed frame, not a formal floating-point certificate or broader scene/task evidence.'],
                audit_seconds=time.perf_counter()-begin,scientific_module_imports=0,new_scientific_evaluations=0)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    parser.add_argument('--run-dir',type=Path,default=TASK/'run-01');parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='plan_only',requires='Finished execution.json and packaged saved output before --execute',scientific_evaluations=0)));return 0
    if args.out is None or args.out.exists():parser.error('--out must be a new file')
    with args.out.open('x',encoding='utf-8') as stream:
        try:report=run_audit(args.run_dir)
        except Exception as error:report=dict(schema='t36-independent-saved-output-audit-v1',audit_pass=False,error=type(error).__name__+': '+str(error),new_scientific_evaluations=0)
        json.dump(report,stream,separators=(',',':'),allow_nan=False);stream.write('\n')
    print(json.dumps({k:report.get(k) for k in ['audit_pass','scientific_status_preserved','check_count','failure_count','error']}))
    return 0 if report['audit_pass'] else 2


if __name__=='__main__':raise SystemExit(main())
