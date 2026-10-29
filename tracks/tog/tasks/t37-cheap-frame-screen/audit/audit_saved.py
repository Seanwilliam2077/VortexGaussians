"""Independent saved-data audit. No method, reference or persistence imports.

Default plan only. Stored tau/alpha is checked with scalar expm1, and PNG
encoding is checked from saved RGB. Neither operation generates scientific
samples, a new scene output, Gaussian CDFs, density bounds, or integrals.
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
PRIOR=ROOT/'tracks/tog/tasks/t35-first-complete-frame/run-01'
DELIVERY=ROOT/'tracks/tog/tasks/t36-ordinary-output-replay/run-01'
REC=struct.Struct('<12d6I');OLD=struct.Struct('<31d10I');BASE=struct.Struct('<13d6I')
FLOATS=['rgb_r','rgb_g','rgb_b','alpha','tau','ray_near','ray_far','mass_bound','prune_delta',
        'preparation_seconds','output_seconds','comparison_seconds']
INTS=['status','retained_count','arm_id','rgb_class','alpha_class','partition_ok']
ARMS=['sorted','mixture'];LABELS={1:'qualified',2:'definite_failure',3:'unresolved'}
WIDTH,HEIGHT,COUNT=256,192,49152
EPS,ALLOW,PRUNE,CAP=.001+1e-10,1e-10,.00025+1e-10,16*1024*1024
OLD_SHA='e19dde61545fb792ec50cf9e815d4626943acc78704cba6d9a48d7965dc3c835'
BASE_SHA='0450c3ffee1b8d9a4afad17ff1467c0e1f8e9cbee6418b8f8933bb9d7990d3e6'


def digest(data):return hashlib.sha256(data).hexdigest()
def ident(path):
    data=path.read_bytes();return {'bytes':len(data),'sha256':digest(data)}
def read_json(path):return json.loads(path.read_bytes())


class Audit:
    def __init__(self):self.counts=Counter();self.failure_count=0;self.failures=[]
    def check(self,ok,kind,detail=None):
        self.counts[kind]+=1
        if not ok:
            self.failure_count+=1
            if len(self.failures)<200:self.failures.append({'kind':kind,'detail':detail})
        return bool(ok)
    def equal(self,left,right,kind,detail=None):return self.check(left==right,kind,detail)


def frozen_check(a,freeze):
    seen=set();out=[]
    for item in freeze['artifacts']:
        path=(ROOT/item['path']).resolve()
        a.check(path.is_relative_to(ROOT) and item['path'] not in seen,'frozen_path',item['path'])
        seen.add(item['path']);got=ident(path)
        a.equal(got,{k:item[k] for k in ['bytes','sha256']},'frozen_identity',item['path'])
        out.append(dict(path=item['path'],**got))
    return out


def png_decode(data):
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
    pos=8;body=bytearray();header=None;ended=False
    while pos<len(data):
        n=struct.unpack_from('>I',data,pos)[0];tag=data[pos+4:pos+8];chunk=data[pos+8:pos+8+n]
        crc=struct.unpack_from('>I',data,pos+8+n)[0]
        if zlib.crc32(tag+chunk)&0xffffffff!=crc:raise ValueError('PNG CRC')
        pos+=12+n
        if tag==b'IHDR':header=struct.unpack('>IIBBBBB',chunk)
        elif tag==b'IDAT':body.extend(chunk)
        elif tag==b'IEND':ended=True;break
    if not ended or pos!=len(data) or header!=(WIDTH,HEIGHT,8,2,0,0,0):raise ValueError('PNG layout')
    scan=zlib.decompress(body);stride=WIDTH*3+1
    if len(scan)!=HEIGHT*stride or any(scan[y*stride]!=0 for y in range(HEIGHT)):raise ValueError('PNG filter')
    return b''.join(scan[y*stride+1:(y+1)*stride] for y in range(HEIGHT))


def byte(value):return int(math.floor(max(0.,min(1.,value))*255+.5))
def display(value):
    y=max(0.,value)/(1+max(0.,value))
    return byte(12.92*y if y<=.0031308 else 1.055*y**(1/2.4)-.055)
def box_extend(box,index):
    x,y=index%WIDTH,index//WIDTH
    return [x,y,x,y] if box is None else [min(box[0],x),min(box[1],y),max(box[2],x),max(box[3],y)]


def saved_input(a,directory,receipt,record,expected_hash):
    info=next(x for x in receipt['evidence']['files'] if x['path']=='pixels.bin.gz')
    data=(directory/'pixels.bin.gz').read_bytes();raw=gzip.decompress(data)
    a.equal(digest(data),expected_hash,'comparison_compressed_pin',directory.name)
    a.equal(dict(bytes=len(data),sha256=digest(data)),{k:info[k] for k in ['bytes','sha256']},'comparison_compressed_identity')
    a.equal(dict(bytes=len(raw),sha256=digest(raw)),dict(bytes=info['raw_bytes'],sha256=info['raw_sha256']),'comparison_raw_identity')
    a.equal(len(raw),COUNT*record.size,'comparison_extent')
    return raw


def perform(run):
    started=time.perf_counter();a=Audit();freeze_path=TASK/'freeze.json';freeze_id=ident(freeze_path)
    freeze=read_json(freeze_path);before=frozen_check(a,freeze)
    result,execution,frame,attempt=(read_json(run/name) for name in ['result.json','execution.json','frame.json','attempt.json'])
    docs={name:ident(run/name) for name in ['result.json','execution.json','frame.json','attempt.json']}
    a.equal(execution['child_still_running'],False,'finished_supervisor')
    for receipt in [result,execution,attempt]:a.equal(receipt['freeze_sha256'],freeze_id['sha256'],'receipt_freeze')
    prior=read_json(PRIOR/'result.json');base_result=read_json(DELIVERY/'result.json')
    old=saved_input(a,PRIOR,prior,OLD,OLD_SHA);base=saved_input(a,DELIVERY,base_result,BASE,BASE_SHA)
    prior_ids={str(p.relative_to(ROOT)).replace('\\','/'):ident(p) for p in
               [PRIOR/'result.json',PRIOR/'frame.json',PRIOR/'pixels.bin.gz',PRIOR/'leaves.bin.gz',
                DELIVERY/'result.json',DELIVERY/'frame.json',DELIVERY/'pixels.bin.gz']}
    a.equal(base_result['status'],'qualified_ordinary_replay_only','diagnostic_delivery_status')
    a.check(base_result['evidence']['summary']['saved_validation_pass'],'diagnostic_saved_validation')
    for source in [prior,base_result]:a.equal(result['runtime'],source['runtime'],'runtime_identity')
    for key in ['frame','view','width','height','particle_count','cmax','mass_budget','camera_params','camera']:
        a.equal(frame[key],read_json(PRIOR/'frame.json')[key],'frame_identity',key)
    a.equal((frame['frame'],frame['view'],frame['width'],frame['height'],frame['particle_count']),
            (90,{'id':'front','yaw':0},WIDTH,HEIGHT,270),'fixed_workload')
    a.equal(frame['arms'],ARMS,'fixed_arms');cmax=frame['cmax'];budget=frame['mass_budget']
    a.equal(result['thresholds'],dict(rgb_alpha=.001,pruning=.00025,numerical_allowance=ALLOW),'fixed_tolerance')
    for k in ['reference_invocations_in_T37','GL_invocations_in_T37','simulations','new_carriers','gpu_runs','retries']:
        a.equal(result[k],0,'scope_zero',k)
    a.equal(result['scientific_invocations_in_T37'],1,'sole_invocation')
    a.equal(result['T35_delivery_status_preserved'],'failed_saved_blue_alias','historical_status')
    a.equal(result['T36_status_preserved'],'qualified_ordinary_replay_only','historical_status')
    for name,previous in [('T35',prior),('T36',base_result)]:
        a.equal(result['prior_paid_costs'][name],dict(computation_seconds=previous['computation_elapsed_seconds'],
                publication_seconds=previous['publication_seconds'],stages_seconds=previous['stage_seconds_including_failed_work']),
                'historical_paid_cost',name)
    for key in ['initial_source_check','final_source_check']:a.check(result[key]['pass'],'worker_source',key)
    for key in ['initial_source_check','post_source_check']:a.check(execution[key]['pass'],'supervisor_source',key)
    a.equal((execution['computation_cap_seconds'],execution['external_wait_seconds'],execution['cleanup_cap_seconds']),(60,90,10),'fixed_budget')
    a.equal((execution['invocation'],execution['retries'],attempt['retry_allowed']),(1,0,False),'one_attempt')
    ev=result['evidence'];a.equal(ev['schema'],'t37-cheap-saved-output-v1','schema')
    a.equal((ev['width'],ev['height'],ev['record_format'],ev['record_bytes'],ev['arms']),(WIDTH,HEIGHT,REC.format,120,ARMS),'schema')
    a.equal(ev['float_fields'],FLOATS,'schema');a.equal(ev['integer_fields'],INTS,'schema')
    a.check(len(FLOATS+INTS)==len(set(FLOATS+INTS))==18,'unique_schema')
    a.equal(ev['class_codes'],{str(k):v for k,v in LABELS.items()},'class_codes')
    images={};raw=None;published=[]
    for item in ev['files']:
        path=run/item['path'];a.check(path.resolve().parent==run.resolve(),'published_path',item['path'])
        data=path.read_bytes();got=dict(bytes=len(data),sha256=digest(data));published.append(dict(path=item['path'],**got))
        a.equal(got,{k:item[k] for k in ['bytes','sha256']},'published_identity',item['path'])
        if item['path']=='pixels.bin.gz':
            raw=gzip.decompress(data)
            a.equal(dict(bytes=len(raw),sha256=digest(raw)),dict(bytes=item['raw_bytes'],sha256=item['raw_sha256']),'raw_identity')
            if (run/'pixels.bin').exists():a.check((run/'pixels.bin').read_bytes()==raw,'raw_gzip_equality')
        elif item['path'].endswith('.png'):images[item['path']]=png_decode(data)
        else:a.check(False,'unexpected_file',item['path'])
    a.equal(set(images),{arm+'-'+suffix+'.png' for arm in ARMS for suffix in ['rgb','classification','display_difference']},'image_set')
    a.equal(len(raw),2*COUNT*REC.size,'pixel_extent');a.equal(ev['raw_binary_bytes'],len(raw),'pixel_extent')
    foreground=sum(OLD.unpack_from(old,pixel*OLD.size)[10]>=.001 for pixel in range(COUNT))
    a.equal(foreground,986,'fixed_foreground_denominator')
    summary=dict(committed_records=0,valid_records=0,invalid_saved_records=0,failed_records=0,uncomputed_records=0,
                 failure_count=0,failures=[],reference_foreground_pixels=foreground,arms={})
    first_uncommitted=None;failed_indices=[];exp_checks=0;arm_counts={};channel_max={};cross_arm_match=0
    for arm_id,arm in enumerate(ARMS):
        s=dict(committed_pixels=0,valid_pixels=0,qualified=0,definite_failure=0,unresolved=0,
               rgb_classes={label:0 for label in LABELS.values()},alpha_failed=0,foreground_pixels=foreground,evaluated_foreground_pixels=0,
               foreground_classes={label:0 for label in LABELS.values()},definite_failure_bbox=None,foreground_definite_failure_bbox=None,
               definite_failure_row_counts=[0]*HEIGHT,max_distance_to_interval=0.,max_distance_to_endpoints=0.,max_alpha_error=0.,
               rgb_min=None,rgb_max=None,display_changed_pixels=0,foreground_display_changed_pixels=0,
               definite_failure_display_changed_pixels=0,max_display_byte_difference=0,stage_seconds={})
        rgb_counts={'1':0,'2':0,'3':0};alpha_counts={'1':0,'2':0};committed_fg=committed_mixed=0
        max_far=[0.]*3;max_near=[0.]*3
        for pixel in range(COUNT):
            index=arm_id*COUNT+pixel;p=REC.unpack_from(raw,index*REC.size)
            o=OLD.unpack_from(old,pixel*OLD.size);b=BASE.unpack_from(base,pixel*BASE.size)
            a.equal(b[13],1,'diagnostic_pixel_committed',pixel)
            a.check(p[12] in (0,1,2),'record_status',index);valid=False
            if p[12]==1:
                a.check(first_uncommitted is None,'row_major_committed_prefix',index)
                summary['committed_records']+=1;s['committed_pixels']+=1
                finite=all(math.isfinite(v) for v in p[:12]);a.check(finite,'record_finite',index)
                upper=[max(abs(p[k]-o[4+k]),abs(p[k]-o[7+k])) for k in range(3)]
                lower=[max(o[4+k]-p[k],0.,p[k]-o[7+k]) for k in range(3)]
                rc=1 if max(upper)<=EPS else 2 if max(lower)>EPS else 3
                ae=abs(p[3]-o[10]);ac=1 if ae<=EPS else 2
                rgb_counts[str(p[15])]=rgb_counts.get(str(p[15]),0)+1;alpha_counts[str(p[16])]=alpha_counts.get(str(p[16]),0)+1
                committed_fg+=int(o[10]>=.001);committed_mixed+=o[38]
                alpha_from_tau=-math.expm1(-p[4]);exp_checks+=1
                same=lambda x,y:abs(x-y)<=1e-12*max(1.,abs(x),abs(y))
                checks={
                    'legacy_status_partition':o[31]==1 and o[40]==1,
                    'legacy_residuals':all(0<=o[k]<=1 for k in [21,22,23]),
                    'legacy_reference_range':all(0<=o[4+k]<=o[7+k] and math.isfinite(o[7+k]) for k in range(3)) and 0<=o[10]<=1,
                    'reproduction':(p[3],p[13],p[7],p[8])==(o[3],o[32],o[18],o[20]),
                    'geometry':same(p[5],o[24]) and same(p[6],o[25]) and 0<=p[5]<p[6],
                    'partition_arm':p[17]==1 and p[14]==arm_id and 0<=p[13]<=270,
                    'output_range':0<=p[3]<=1 and p[4]>=0 and all(-ALLOW<=p[k]<=cmax[k]*p[3]+ALLOW for k in range(3)),
                    'alpha_tau':abs(p[3]-alpha_from_tau)<=ALLOW,
                    'classification':p[15]==rc and p[16]==ac,
                    'omission':0<=p[7]<=budget+ALLOW and 0<=o[19]<=p[7]+ALLOW and 0<=p[8]<=PRUNE and all(c*p[8]<=PRUNE for c in cmax),
                    'stage_times':all(p[k]>=0 for k in [9,10,11])}
                for name,passed in checks.items():a.check(passed,'pixel_'+name,index)
                a.check((p[3],p[5],p[6],p[7],p[8],p[13])==(b[3],b[4],b[5],b[6],b[7],b[14]),'T36_noncolor_reproduction',index)
                if arm_id==1:
                    first=REC.unpack_from(raw,pixel*REC.size)
                    equal=first[12]==1 and (p[3:9],p[13])==(first[3:9],first[13])
                    a.check(equal,'cross_arm_preparation_consistency',pixel);cross_arm_match+=int(equal)
                bad=[k for k,v in checks.items() if not v]
                if bad:
                    summary['invalid_saved_records']+=1;summary['failure_count']+=len(bad)
                    if len(summary['failures'])<100:summary['failures'].append(dict(record_index=index,failed_checks=bad))
                else:
                    valid=finite;summary['valid_records']+=1;s['valid_pixels']+=1
                    rgb=list(p[:3]);s['rgb_min']=rgb if s['rgb_min'] is None else [min(x,y) for x,y in zip(s['rgb_min'],rgb)]
                    s['rgb_max']=rgb if s['rgb_max'] is None else [max(x,y) for x,y in zip(s['rgb_max'],rgb)]
                    joint=2 if ac==2 else rc;label=LABELS[joint];s[label]+=1;s['rgb_classes'][LABELS[rc]]+=1;s['alpha_failed']+=int(ac==2)
                    fg=o[10]>=.001;s['evaluated_foreground_pixels']+=int(fg)
                    if fg:s['foreground_classes'][label]+=1
                    if joint==2:
                        s['definite_failure_bbox']=box_extend(s['definite_failure_bbox'],pixel);s['definite_failure_row_counts'][pixel//WIDTH]+=1
                        if fg:s['foreground_definite_failure_bbox']=box_extend(s['foreground_definite_failure_bbox'],pixel)
                    s['max_distance_to_interval']=max(s['max_distance_to_interval'],*lower)
                    s['max_distance_to_endpoints']=max(s['max_distance_to_endpoints'],*upper)
                    s['max_alpha_error']=max(s['max_alpha_error'],ae)
                    max_far=[max(x,y) for x,y in zip(max_far,upper)];max_near=[max(x,y) for x,y in zip(max_near,lower)]
                    shown=tuple(display(v) for v in p[:3]);diff=tuple(abs(shown[k]-display(b[k])) for k in range(3));changed=any(diff)
                    s['display_changed_pixels']+=int(changed);s['foreground_display_changed_pixels']+=int(fg and changed)
                    s['definite_failure_display_changed_pixels']+=int(joint==2 and changed);s['max_display_byte_difference']=max(s['max_display_byte_difference'],*diff)
                    for slot,name in [(9,'preparation_seconds'),(10,'output_seconds'),(11,'comparison_seconds')]:
                        s['stage_seconds'][name]=s['stage_seconds'].get(name,0.)+p[slot]
            else:
                if first_uncommitted is None:first_uncommitted=index
                summary['failed_records' if p[12]==2 else 'uncomputed_records']+=1
                if p[12]==2:failed_indices.append(index)
            expected={'rgb':bytes(shown),'display_difference':bytes(diff),'classification':bytes({1:(0,160,0),2:(255,0,0),3:(255,200,0)}[joint])} if valid else {k:b'\xff\0\xff' for k in ['rgb','classification','display_difference']}
            for name,want in expected.items():a.check(images[arm+'-'+name+'.png'][pixel*3:pixel*3+3]==want,'PNG_from_saved_values',dict(arm=arm,pixel=pixel,image=name))
        s['all_pixels_qualified']=s['qualified']==COUNT and s['valid_pixels']==COUNT;summary['arms'][arm]=s
        arm_counts[arm]=dict(rgb_classes=rgb_counts,alpha_classes=alpha_counts,committed_foreground=committed_fg,committed_mixed=committed_mixed)
        channel_max[arm]=dict(max_distance_to_endpoints=max_far,max_distance_to_interval=max_near)
    summary['saved_validation_pass']=summary['invalid_saved_records']==0
    summary['all_records_valid']=summary['valid_records']==2*COUNT and summary['saved_validation_pass']
    summary['any_arm_all_pixels_qualified']=any(s['all_pixels_qualified'] for s in summary['arms'].values())
    a.equal(summary,ev['summary'],'complete_summary')
    a.check(len(failed_indices)<=1 and (not failed_indices or failed_indices==[first_uncommitted]),'failed_record_position')
    a.equal(result['completed_records'],summary['committed_records'],'worker_total_records')
    a.equal(result['planned_records'],2*COUNT,'planned_records')
    for report in result['arms']:
        name=report['arm'];s=summary['arms'][name];expected=arm_counts[name]
        a.equal(report['completed_pixels'],s['committed_pixels'],'worker_arm_count',name)
        a.equal(report['rgb_classes'],expected['rgb_classes'],'worker_rgb_class_counts',name)
        a.equal(report['alpha_classes'],expected['alpha_classes'],'worker_alpha_class_counts',name)
        a.equal(report['inherited_nontrivial_pixels'],expected['committed_foreground'],'worker_foreground_count',name)
        a.equal(report['inherited_mixed_pixels'],expected['committed_mixed'],'worker_mixed_count',name)
        counts=report['counters'];a.check(all(isinstance(v,int) and v>=0 for v in counts.values()),'counter_validity',name)
        a.check(not any(k.startswith(('reference_','gl_')) or k=='integration_evaluations' for k in counts),'no_reference_GL_counter',name)
        for small,stage in [('preparation_seconds','preparation'),('output_seconds','output'),('comparison_seconds','comparison')]:
            a.check(s['stage_seconds'].get(small,0)<=result['stage_seconds_including_failed_work'].get(name+'.'+stage,0)+1e-8,'failed_work_accounted',name+'.'+stage)
    complete=result['status']=='completed_cheap_screen'
    if complete:
        a.check(summary['all_records_valid'] and len(result['arms'])==2,'complete_screen')
        a.check(execution['success'] and execution['returncode']==0 and not execution['timed_out'] and not execution['errors'],'complete_execution')
        a.check(result['publication_status']=='packaged' and result['failure_path'] is None and result['computation_elapsed_seconds']<=60,'complete_scope')
        for report in result['arms']:
            a.equal(report['counters'].get('cheap_calls'),COUNT,'complete_arm_call_count',report['arm'])
            a.equal(report['counters'].get('bvh_input_primitives'),270,'independent_arm_tree',report['arm'])
    else:a.equal(execution['success'],False,'failed_screen_stays_failed')
    times=result['stage_seconds_including_failed_work']
    a.check(all(math.isfinite(v) and v>=0 for v in times.values()) and sum(times.values())<=result['computation_elapsed_seconds']+1e-5,'total_stage_accounting')
    raw_sizes={n:(run/n).stat().st_size for n in ['pixels.bin','frame.json','failure.json','result.json'] if (run/n).exists()}
    raw_sizes.setdefault('pixels.bin',len(raw));raw_total=sum(raw_sizes.values())
    a.equal(raw_total,execution['raw_numeric_bytes'],'raw_size');a.equal(raw_total-raw_sizes['result.json'],result['raw_other_numeric_bytes'],'raw_size')
    a.check(raw_total<=CAP and result['raw_numeric_cap_bytes']==CAP,'raw_cap')
    for name,expected in execution['logs'].items():a.equal(ident(run/name),expected,'log_identity',name)
    after=frozen_check(a,freeze);a.equal(after,before,'sources_before_after');a.equal(ident(freeze_path),freeze_id,'freeze_before_after')
    for name,expected in docs.items():a.equal(ident(run/name),expected,'saved_before_after',name)
    for path,expected in prior_ids.items():a.equal(ident(ROOT/path),expected,'prior_before_after',path)
    for item in published:a.equal(ident(run/item['path']),{k:item[k] for k in ['bytes','sha256']},'published_before_after',item['path'])
    decision='incomplete_or_audit_failed'
    if complete and a.failure_count==0:
        decision='ordinary_arm_qualifies_entire_frame' if summary['any_arm_all_pixels_qualified'] else 'both_arms_have_definite_failures' if all(s['definite_failure']>0 for s in summary['arms'].values()) else 'no_full_qualification_with_remaining_uncertainty'
    return dict(schema='t37-independent-saved-screen-audit-v1',audit_pass=a.failure_count==0,screen_status_preserved=result['status'],
                screen_complete=complete and a.failure_count==0,accuracy_decision=decision,check_count=sum(a.counts.values()),checks=dict(a.counts),
                failure_count=a.failure_count,failures=a.failures,failure_list_truncated=a.failure_count>len(a.failures),
                freeze=freeze_id,frozen_identities=before,saved_identities=docs,prior_identities=prior_ids,published_identities=published,
                summary_recomputed=summary,per_channel_maxima=channel_max,cross_arm_noncolor_equal_pixels=cross_arm_match,
                failed_record_indices=failed_indices,raw_numeric_sizes=raw_sizes,raw_numeric_total=raw_total,
                worker_arms=result['arms'],timings={k:result[k] for k in ['computation_elapsed_seconds','stage_seconds_including_failed_work','publication_seconds','worker_elapsed_before_result_seconds','prior_paid_costs']},
                execution_scope={k:execution[k] for k in ['success','returncode','timed_out','errors','process_and_cleanup_seconds','cleanup_seconds','packaging_needed']},
                stored_tau_alpha_expm1_checks=exp_checks,scientific_module_imports=0,new_scene_samples=0,new_CDF_or_integral_evaluations=0,
                audit_seconds=time.perf_counter()-started,
                limitations=['Completion is two full classified outputs, not accuracy success of either arm.',
                             'Foreground is the fixed 986 pixels defined by T35 full alpha, not a selected subset of either output.',
                             'T35 intact intervals are reused by identity; old blue remains invalid and the full leaf audit is not repeated.',
                             'T36 RGB is used only for fixed unamplified display differences, never as exact truth or to select an arm.',
                             'Scalar expm1 checks stored tau-alpha algebra and display powers check encoding; neither recomputes method output or reference.',
                             'The original source-array projection and omitted-mass evidence is inherited, not independently regenerated.',
                             'No fallback, reference refinement, best-arm oracle method, optimized-baseline speedup or TOG contribution follows from these counts.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true')
    parser.add_argument('--run-dir',type=Path,default=TASK/'run-01');parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='plan_only',requires='Finished supervisor and packaged saved outputs',new_scene_samples=0)));return 0
    if args.out is None or args.out.exists():parser.error('--out must be a new report')
    with args.out.open('x',encoding='utf-8') as output:
        try:report=perform(args.run_dir)
        except Exception as error:report=dict(schema='t37-independent-saved-screen-audit-v1',audit_pass=False,error=type(error).__name__+': '+str(error),new_scene_samples=0)
        json.dump(report,output,separators=(',',':'),allow_nan=False);output.write('\n')
    print(json.dumps({k:report.get(k) for k in ['audit_pass','screen_status_preserved','accuracy_decision','check_count','failure_count','error']}))
    return 0 if report['audit_pass'] else 2


if __name__=='__main__':raise SystemExit(main())
