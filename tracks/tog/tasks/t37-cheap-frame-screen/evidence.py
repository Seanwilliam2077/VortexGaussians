"""Persist two ordinary approximation outputs; classify saved bytes only."""
import gzip
import hashlib
import math
from pathlib import Path
import struct
import time
import zlib

FLOAT_FIELDS=['rgb_r','rgb_g','rgb_b','alpha','tau','ray_near','ray_far','mass_bound','prune_delta',
              'preparation_seconds','output_seconds','comparison_seconds']
INT_FIELDS=['status','retained_count','arm_id','rgb_class','alpha_class','partition_ok']
FIELDS=FLOAT_FIELDS+INT_FIELDS
assert len(FIELDS)==len(set(FIELDS))==18
RECORD=struct.Struct('<12d6I');LEGACY=struct.Struct('<31d10I');DELIVERY=struct.Struct('<13d6I')
assert RECORD.size==120 and LEGACY.size==288 and DELIVERY.size==128
ARMS=['sorted','mixture'];EPS=.001+1e-10;FP=1e-10;RAW_CAP=16*1024*1024
CLASSES={1:'qualified',2:'definite_failure',3:'unresolved'}


def require(ok,message):
    if not ok:raise ValueError(message)


def encode(values):
    require(len(values)==18 and set(values)==set(FIELDS),'Exact unique field schema required')
    for k in FLOAT_FIELDS:require(type(values[k]) in (float,int) and math.isfinite(values[k]),'Finite real field: '+k)
    for k in INT_FIELDS:require(type(values[k]) is int and 0<=values[k]<2**32,'uint32 field: '+k)
    return RECORD.pack(*(values[k] for k in FIELDS))


def decode(data):
    require(len(data)==120,'Exact120-byte record required')
    row=RECORD.unpack(data);require(all(math.isfinite(x) for x in row[:12]),'Nonfinite decoded field')
    return dict(zip(FIELDS,row))


class Evidence:
    def __init__(self,out,width=256,height=192):
        require(type(width) is int and type(height) is int and width>0 and height>0,'Positive integer dimensions')
        self.out=Path(out);self.count=2*width*height;self.next_index=0
        self.file=(self.out/'pixels.bin').open('x+b',buffering=0);self.file.truncate(self.count*120)

    def write_pixel(self,index,values):
        require(type(index) is int and index==self.next_index and index<self.count,'Contiguous record commit')
        require('status' not in values,'Status is committed by storage')
        values=dict(values,status=0);payload=encode(values)
        self.file.seek(index*120);require(self.file.write(payload)==120,'Short payload write')
        self.file.seek(index*120);saved=self.file.read(120)
        expected=tuple(float(values[k]) for k in FLOAT_FIELDS)+tuple(values[k] for k in INT_FIELDS)
        require(saved==payload and RECORD.unpack(saved)==expected,'Actual saved payload round-trip failed')
        self.file.seek(index*120+96);require(self.file.write(struct.pack('<I',1))==4,'Short status write')
        self.file.seek(index*120);committed=RECORD.unpack(self.file.read(120))
        require(committed[:12]==expected[:12] and committed[12:]==(1,)+expected[13:],'Committed record changed')
        self.next_index+=1

    def mark_failed(self,index):
        require(type(index) is int and 0<=index<self.count,'Failed record index')
        self.file.seek(index*120);require(self.file.write(RECORD.pack(*([0.]*12+[2]+[0]*5)))==120,'Short failure marker')

    def close(self):self.file.close()


def classify(rgb,alpha,old):
    upper=[max(abs(rgb[k]-old[4+k]),abs(rgb[k]-old[7+k])) for k in range(3)]
    lower=[max(old[4+k]-rgb[k],0.,rgb[k]-old[7+k]) for k in range(3)]
    rc=1 if max(upper)<=EPS else 2 if max(lower)>EPS else 3
    ae=abs(alpha-old[10]);ac=1 if ae<=EPS else 2
    return rc,ac,upper,lower,ae


def saved_gates(p,old,cmax,particle_count,mass_budget,arm_id):
    rgb=[p['rgb_r'],p['rgb_g'],p['rgb_b']];rc,ac,upper,lower,ae=classify(rgb,p['alpha'],old)
    same=lambda x,y:abs(x-y)<=1e-12*max(1.,abs(x),abs(y))
    checks={
      'legacy_status_partition':old[31]==1 and old[40]==1,
      'legacy_residuals':all(0<=old[k]<=1 for k in [21,22,23]),
      'legacy_reference_range':all(0<=old[4+k]<=old[7+k] and math.isfinite(old[7+k]) for k in range(3)) and 0<=old[10]<=1,
      'reproduction':(p['alpha'],p['retained_count'],p['mass_bound'],p['prune_delta'])==(old[3],old[32],old[18],old[20]),
      'geometry':same(p['ray_near'],old[24]) and same(p['ray_far'],old[25]) and 0<=p['ray_near']<p['ray_far'],
      'partition_arm':p['partition_ok']==1 and p['arm_id']==arm_id and 0<=p['retained_count']<=particle_count,
      'output_range':0<=p['alpha']<=1 and p['tau']>=0 and all(-FP<=rgb[k]<=cmax[k]*p['alpha']+FP for k in range(3)),
      'alpha_tau':abs(p['alpha']+math.expm1(-p['tau']))<=FP,
      'classification':p['rgb_class']==rc and p['alpha_class']==ac,
      'omission':0<=p['mass_bound']<=mass_budget+FP and 0<=old[19]<=p['mass_bound']+FP and 0<=p['prune_delta']<=.00025+FP and all(c*p['prune_delta']<=.00025+FP for c in cmax),
      'stage_times':all(p[k]>=0 for k in ['preparation_seconds','output_seconds','comparison_seconds'])}
    return checks,dict(rgb_class=rc,alpha_class=ac,upper=upper,lower=lower,alpha_error=ae)


def _publish(path,data):
    require(not path.exists(),'Publication already exists: '+path.name)
    temp=path.with_name(path.name+'.part');temp.write_bytes(data);temp.replace(path)


def _png(path,rgb,width,height):
    def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    scan=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    _publish(path,b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan,9))+chunk(b'IEND',b''))


def _byte(x):return int(math.floor(max(0.,min(1.,x))*255+.5))
def _display(x):
    y=max(0.,x)/(1+max(0.,x));return _byte(12.92*y if y<=.0031308 else 1.055*y**(1/2.4)-.055)


def identity(path):
    data=path.read_bytes();return dict(path=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def _box(box,index,width):
    x,y=index%width,index//width
    return [x,y,x,y] if box is None else [min(box[0],x),min(box[1],y),max(box[2],x),max(box[3],y)]


def finalize(out,cmax,particle_count,old_raw_pixels,t36_raw_pixels,mass_budget,width=256,height=192):
    start=time.perf_counter();out=Path(out);raw=(out/'pixels.bin').read_bytes();count=width*height
    require(len(raw)==2*count*120 and len(old_raw_pixels)==count*288 and len(t36_raw_pixels)==count*128,'Fixed record extents')
    require(len(raw)<=RAW_CAP,'Raw pixel cap')
    foreground_total=sum(LEGACY.unpack_from(old_raw_pixels,i*288)[10]>=.001 for i in range(count))
    summary=dict(committed_records=0,valid_records=0,invalid_saved_records=0,failed_records=0,uncomputed_records=0,failure_count=0,failures=[],reference_foreground_pixels=foreground_total,arms={})
    files=[]
    for arm_id,arm in enumerate(ARMS):
        s=dict(committed_pixels=0,valid_pixels=0,qualified=0,definite_failure=0,unresolved=0,
          rgb_classes={k:0 for k in CLASSES.values()},alpha_failed=0,foreground_pixels=foreground_total,evaluated_foreground_pixels=0,
          foreground_classes={k:0 for k in CLASSES.values()},definite_failure_bbox=None,
          foreground_definite_failure_bbox=None,definite_failure_row_counts=[0]*height,
          max_distance_to_interval=0.,max_distance_to_endpoints=0.,max_alpha_error=0.,
          rgb_min=None,rgb_max=None,display_changed_pixels=0,foreground_display_changed_pixels=0,
          definite_failure_display_changed_pixels=0,max_display_byte_difference=0,stage_seconds={})
        images={k:bytearray() for k in ['rgb','classification','display_difference']}
        for pixel in range(count):
            index=arm_id*count+pixel;p=decode(raw[index*120:(index+1)*120])
            old=LEGACY.unpack_from(old_raw_pixels,pixel*288);base=DELIVERY.unpack_from(t36_raw_pixels,pixel*128)
            require(base[13]==1,'T36 display comparison pixel not committed')
            require(p['status'] in (0,1,2),'Unknown record status');valid=False
            if p['status']==1:
                summary['committed_records']+=1;s['committed_pixels']+=1
                checks,m=saved_gates(p,old,cmax,particle_count,mass_budget,arm_id)
                bad=[k for k,v in checks.items() if not v]
                if bad:
                    summary['invalid_saved_records']+=1;summary['failure_count']+=len(bad)
                    if len(summary['failures'])<100:summary['failures'].append(dict(record_index=index,failed_checks=bad))
                else:
                    valid=True;summary['valid_records']+=1;s['valid_pixels']+=1
                    rgb=[p[k] for k in FLOAT_FIELDS[:3]];s['rgb_min']=rgb[:] if s['rgb_min'] is None else [min(a,b) for a,b in zip(s['rgb_min'],rgb)]
                    s['rgb_max']=rgb[:] if s['rgb_max'] is None else [max(a,b) for a,b in zip(s['rgb_max'],rgb)]
                    rc=m['rgb_class'];ac=m['alpha_class'];joint=2 if ac==2 else rc;label=CLASSES[joint]
                    s[label]+=1;s['rgb_classes'][CLASSES[rc]]+=1;s['alpha_failed']+=int(ac==2)
                    fg=old[10]>=.001;s['evaluated_foreground_pixels']+=int(fg)
                    if fg:s['foreground_classes'][label]+=1
                    if joint==2:
                        s['definite_failure_bbox']=_box(s['definite_failure_bbox'],pixel,width);s['definite_failure_row_counts'][pixel//width]+=1
                        if fg:s['foreground_definite_failure_bbox']=_box(s['foreground_definite_failure_bbox'],pixel,width)
                    s['max_distance_to_interval']=max(s['max_distance_to_interval'],*m['lower'])
                    s['max_distance_to_endpoints']=max(s['max_distance_to_endpoints'],*m['upper'])
                    s['max_alpha_error']=max(s['max_alpha_error'],m['alpha_error'])
                    shown=tuple(_display(v) for v in rgb);difference=tuple(abs(shown[k]-_display(base[k])) for k in range(3));changed=any(difference)
                    s['display_changed_pixels']+=int(changed);s['foreground_display_changed_pixels']+=int(fg and changed)
                    s['definite_failure_display_changed_pixels']+=int(joint==2 and changed);s['max_display_byte_difference']=max(s['max_display_byte_difference'],*difference)
                    for key in FLOAT_FIELDS[9:]:s['stage_seconds'][key]=s['stage_seconds'].get(key,0.)+p[key]
            else:summary['failed_records' if p['status']==2 else 'uncomputed_records']+=1
            if valid:
                images['rgb'].extend(shown);images['display_difference'].extend(difference)
                images['classification'].extend({1:(0,160,0),2:(255,0,0),3:(255,200,0)}[joint])
            else:
                for image in images.values():image.extend((255,0,255))
        s['all_pixels_qualified']=s['qualified']==count and s['valid_pixels']==count
        summary['arms'][arm]=s
        for suffix,data in images.items():
            path=out/(arm+'-'+suffix+'.png');_png(path,bytes(data),width,height);files.append(identity(path))
    summary['saved_validation_pass']=summary['invalid_saved_records']==0
    summary['all_records_valid']=summary['valid_records']==2*count and summary['saved_validation_pass']
    summary['any_arm_all_pixels_qualified']=any(s['all_pixels_qualified'] for s in summary['arms'].values())
    path=out/'pixels.bin.gz';_publish(path,gzip.compress(raw,mtime=0));info=identity(path)
    info.update(raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest());files.insert(0,info)
    return dict(schema='t37-cheap-saved-output-v1',width=width,height=height,arms=ARMS,
      record_format=RECORD.format,record_bytes=120,float_fields=FLOAT_FIELDS,integer_fields=INT_FIELDS,
      status_codes=dict(uncomputed=0,committed=1,execution_failed=2),class_codes=CLASSES,
      files=files,raw_binary_bytes=len(raw),summary=summary,packaging_seconds=time.perf_counter()-start,
      display=dict(rgb='exposure1 L/(1+L) then sRGB; original size without crop or fitting',
        classification='joint RGB/alpha: green0,160,0 qualified; red255,0,0 definite failure; yellow255,200,0 unresolved; magenta255,0,255 invalid or unfinished',
        display_difference='absolute 8-bit display difference from qualified T36 output, without amplification; T36 is not exact truth or a perceptual criterion'))
