"""Unique-field ordinary-output persistence and saved-byte qualification.

No renderer, projection or reference implementation is imported here. Legacy
T35 records are read by fixed numeric positions, including far clip at slot25.
"""
import gzip
import hashlib
import math
from pathlib import Path
import struct
import time
import zlib

FLOAT_FIELDS=['rgb_r','rgb_g','rgb_b','alpha','ray_near','ray_far','mass_bound','prune_delta',
              'preparation_seconds','ordinary_seconds','comparison_seconds','max_endpoint_error','alpha_error']
INT_FIELDS=['status','retained_count','ordinary_path','gl_order','partition_ok','replay_match']
FIELDS=FLOAT_FIELDS+INT_FIELDS
assert len(FIELDS)==len(set(FIELDS))==19
assert len(FLOAT_FIELDS)==13 and len(INT_FIELDS)==6
RECORD=struct.Struct('<13d6I')
LEGACY=struct.Struct('<31d10I')
assert RECORD.size==128 and LEGACY.size==288
EPS=.001
FP=1e-10
RAW_CAP=32*1024*1024
ORD_PATHS={'computed_zero_mass':1,'ordinary_color_box':2,'gl_no_fallback':3}


def require(ok,message):
    if not ok:raise ValueError(message)


def encode(values):
    require(len(values)==len(FIELDS) and set(values)==set(FIELDS),'Exact unique field schema required')
    for k in FLOAT_FIELDS:
        require(type(values[k]) in (float,int) and math.isfinite(values[k]),'Finite real field: '+k)
    for k in INT_FIELDS:
        require(type(values[k]) is int and 0<=values[k]<2**32,'uint32 field: '+k)
    return RECORD.pack(*(values[k] for k in FIELDS))


def decode(payload):
    require(len(payload)==128,'Exact128-byte record required')
    values=RECORD.unpack(payload)
    require(all(math.isfinite(x) for x in values[:13]),'Nonfinite decoded field')
    return dict(zip(FIELDS,values))


class Evidence:
    def __init__(self,out,width=256,height=192):
        require(type(width) is int and type(height) is int and width>0 and height>0,'Positive integer dimensions')
        self.out=Path(out);self.width=width;self.height=height;self.next_index=0
        self.file=(self.out/'pixels.bin').open('x+b',buffering=0)
        self.file.truncate(width*height*128)

    def write_pixel(self,index,values):
        require(type(index) is int and index==self.next_index and index<self.width*self.height,'Contiguous pixel commit')
        require('status' not in values,'Status is committed by storage')
        values=dict(values,status=0)
        payload=encode(values)
        self.file.seek(index*128)
        require(self.file.write(payload)==128,'Short payload write')
        self.file.seek(index*128);saved=self.file.read(128)
        # Compare every positional value, independently of a field->dict roundtrip.
        expected=tuple(float(values[k]) for k in FLOAT_FIELDS)+tuple(values[k] for k in INT_FIELDS)
        require(RECORD.unpack(saved)==expected and saved==payload,'Actual saved payload round-trip failed')
        self.file.seek(index*128+104)
        require(self.file.write(struct.pack('<I',1))==4,'Short final status write')
        self.file.seek(index*128);committed=RECORD.unpack(self.file.read(128))
        require(committed[:13]==expected[:13] and committed[13:]==(1,)+expected[14:],'Committed record changed')
        self.next_index+=1

    def mark_failed(self,index):
        require(type(index) is int and 0<=index<self.width*self.height,'Failed pixel index')
        self.file.seek(index*128)
        require(self.file.write(RECORD.pack(*([0.]*13+[2]+[0]*5)))==128,'Short failure marker')

    def close(self):
        self.file.close()


def _same_ray(x,y):
    return abs(x-y)<=1e-12*max(1.,abs(x),abs(y))


def saved_gates(p,old,cmax,particle_count,mass_budget):
    """Arithmetic gates on persisted bytes; no new source-level evaluation."""
    rgb=[p['rgb_r'],p['rgb_g'],p['rgb_b']]
    endpoint=max(max(abs(rgb[k]-old[4+k]),abs(rgb[k]-old[7+k])) for k in range(3))
    alpha_error=abs(p['alpha']-old[10])
    checks={
      'legacy_status_partition':old[31]==1 and old[40]==1,
      'legacy_residuals':all(0<=old[k]<=1 for k in [21,22,23]),
      'legacy_reference_range':all(0<=old[4+k]<=old[7+k] and math.isfinite(old[7+k]) for k in range(3)) and 0<=old[10]<=1,
      'reproduction':(p['rgb_r'],p['rgb_g'],p['alpha'],p['retained_count'],p['ordinary_path'],p['gl_order'],p['mass_bound'],p['prune_delta'])==(old[0],old[1],old[3],old[32],old[34],old[35],old[18],old[20]),
      'geometry':_same_ray(p['ray_near'],old[24]) and _same_ray(p['ray_far'],old[25]) and 0<=p['ray_near']<p['ray_far'],
      'path_flags':p['partition_ok']==1 and p['replay_match']==1 and 0<=p['retained_count']<=particle_count and p['ordinary_path'] in (1,2,3) and (p['gl_order'] in (4,8,16,32,64) if p['ordinary_path']==3 else p['gl_order']==0),
      'output_range':0<=p['alpha']<=1 and all(-FP<=rgb[k]<=cmax[k]*p['alpha']+FP for k in range(3)),
      'endpoint_alpha':endpoint<=EPS+FP and alpha_error<=EPS+FP,
      'reported_error':abs(p['max_endpoint_error']-endpoint)<=FP and abs(p['alpha_error']-alpha_error)<=FP,
      'omission':0<=p['mass_bound']<=mass_budget+FP and 0<=old[19]<=p['mass_bound']+FP and 0<=p['prune_delta']<=.00025+FP and all(c*p['prune_delta']<=.00025+FP for c in cmax),
      'stage_times':all(p[k]>=0 for k in ['preparation_seconds','ordinary_seconds','comparison_seconds'])}
    return checks,endpoint,alpha_error


def _publish(path,data):
    if path.exists():
        require(path.read_bytes()==data,'Conflicting published file: '+path.name);return
    tmp=path.with_name(path.name+'.part');tmp.write_bytes(data);tmp.replace(path)


def _png(path,rgb,width,height):
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    scan=b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    _publish(path,b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan,9))+chunk(b'IEND',b''))


def _byte(x):return int(math.floor(max(0.,min(1.,x))*255+.5))
def _display(x):
    y=max(0.,x)/(1+max(0.,x))
    return _byte(12.92*y if y<=.0031308 else 1.055*y**(1/2.4)-.055)


def identity(path):
    data=path.read_bytes();return dict(path=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def finalize(out,cmax,particle_count,old_raw_pixels,mass_budget,width=256,height=192):
    start=time.perf_counter();out=Path(out);raw=(out/'pixels.bin').read_bytes();count=width*height
    require(len(raw)==count*128 and len(old_raw_pixels)==count*288,'Fixed pixel extents')
    require(len(raw)<=RAW_CAP,'Raw pixel cap')
    images={k:bytearray() for k in ['rgb','alpha','retention','valid']}
    summary=dict(committed_pixels=0,qualified_pixels=0,invalid_saved_pixels=0,failed_pixels=0,uncomputed_pixels=0,
      nontrivial_pixels=0,mixed_pixels=0,nontrivial_bbox=None,max_rgb_endpoint_error=0.,max_alpha_error=0.,
      rgb_min=None,rgb_max=None,alpha_max=0.,ordinary_paths={},retained_histogram={},stage_seconds={},failure_count=0,failures=[])
    for index in range(count):
        p=decode(raw[index*128:(index+1)*128]);old=LEGACY.unpack_from(old_raw_pixels,index*288)
        require(p['status'] in (0,1,2),'Unknown pixel status')
        valid=False
        if p['status']==1:
            summary['committed_pixels']+=1
            checks,err,ae=saved_gates(p,old,cmax,particle_count,mass_budget)
            bad=[name for name,passed in checks.items() if not passed]
            if bad:
                summary['invalid_saved_pixels']+=1;summary['failure_count']+=len(bad)
                if len(summary['failures'])<100:summary['failures'].append(dict(pixel_index=index,failed_checks=bad))
            else:
                valid=True;summary['qualified_pixels']+=1
                rgb=[p[k] for k in ['rgb_r','rgb_g','rgb_b']]
                summary['rgb_min']=rgb[:] if summary['rgb_min'] is None else [min(a,b) for a,b in zip(summary['rgb_min'],rgb)]
                summary['rgb_max']=rgb[:] if summary['rgb_max'] is None else [max(a,b) for a,b in zip(summary['rgb_max'],rgb)]
                summary['max_rgb_endpoint_error']=max(summary['max_rgb_endpoint_error'],err)
                summary['max_alpha_error']=max(summary['max_alpha_error'],ae)
                summary['alpha_max']=max(summary['alpha_max'],old[10])
                summary['mixed_pixels']+=old[38]
                if old[10]>=.001:
                    summary['nontrivial_pixels']+=1;i,j=index%width,index//width;box=summary['nontrivial_bbox']
                    summary['nontrivial_bbox']=[i,j,i,j] if box is None else [min(box[0],i),min(box[1],j),max(box[2],i),max(box[3],j)]
                for field,target in [('ordinary_path','ordinary_paths'),('retained_count','retained_histogram')]:
                    key=str(p[field]);summary[target][key]=summary[target].get(key,0)+1
                for name in ['preparation_seconds','ordinary_seconds','comparison_seconds']:
                    summary['stage_seconds'][name]=summary['stage_seconds'].get(name,0.)+p[name]
        else:summary['failed_pixels' if p['status']==2 else 'uncomputed_pixels']+=1
        if valid:
            images['rgb'].extend(_display(p[k]) for k in ['rgb_r','rgb_g','rgb_b'])
            images['alpha'].extend([_byte(p['alpha'])]*3)
            images['retention'].extend([_byte(p['retained_count']/particle_count)]*3)
            images['valid'].extend((255,255,255))
        else:
            for name in ['rgb','alpha','retention']:images[name].extend((255,0,255))
            images['valid'].extend((0,0,0))
    summary['saved_validation_pass']=summary['invalid_saved_pixels']==0
    summary['all_pixel_records_qualified']=summary['qualified_pixels']==count and summary['saved_validation_pass']
    summary['nontrivial_fraction_of_full_frame']=summary['nontrivial_pixels']/count
    path=out/'pixels.bin.gz';_publish(path,gzip.compress(raw,mtime=0));info=identity(path)
    info.update(raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest());files=[info]
    for name,data in images.items():
        path=out/(name+'.png');_png(path,bytes(data),width,height);files.append(identity(path))
    return dict(schema='t36-ordinary-saved-output-v1',width=width,height=height,record_format=RECORD.format,
      record_bytes=128,float_fields=FLOAT_FIELDS,integer_fields=INT_FIELDS,fields_unique=True,
      status_codes=dict(uncomputed=0,committed=1,failed=2),ordinary_paths=ORD_PATHS,
      reference_source='immutable T35 positional records, endpoints slots4..9 and fullalpha10; far25; never oldblue2',
      files=files,raw_binary_bytes=len(raw),summary=summary,packaging_seconds=time.perf_counter()-start,
      display=dict(rgb='L/(1+L), exposure1, then standard sRGB',alpha='ordinary alpha, linear0..1',
      retention='retained count/270, linear0..1',invalid='magenta255,0,255',valid_mask='saved-output-qualified white; otherwise black',
      framing='original256x192, no crop/zoom/exposure fit'))
