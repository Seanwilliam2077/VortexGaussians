"""Fixed binary evidence and display packaging; no renderer or reference imports."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import time
import zlib

FLOAT_FIELDS = ['r','g','b','alpha','lower_r','lower_g','lower_b','upper_r','upper_g','upper_b',
 'full_alpha','retained_alpha','analytic_r','analytic_g','analytic_b','omission_r','omission_g','omission_b',
 'mass_bound','actual_omitted_mass','prune_delta','geometry_ratio','mu_ratio','q_ratio','a','b',
 'preparation_seconds','ordinary_seconds','projection_seconds','reference_seconds','qualification_seconds']
INT_FIELDS = ['status','retained_count','reference_path','ordinary_path','gl_order','leaf_offset','leaf_count','mixed','created_cells','partition_ok']
RECORD = struct.Struct('<31d10I')
LEAF = struct.Struct('<9d')
WIDTH, HEIGHT = 256, 192
RAW_CAP = 32*1024*1024
REF_PATHS = {'empty':1,'equal_color':2,'enclosure':3}
ORD_PATHS = {'computed_zero_mass':1,'ordinary_color_box':2,'gl_no_fallback':3}


class Evidence:
    def __init__(self,out,width=WIDTH,height=HEIGHT):
        if (width,height)!=(WIDTH,HEIGHT): raise ValueError('Fixed frame dimensions')
        self.out=Path(out);self.pixel_file=(self.out/'pixels.bin').open('x+b',buffering=0)
        self.pixel_file.truncate(width*height*RECORD.size)
        self.leaf_file=(self.out/'leaves.bin').open('xb',buffering=0)
        self.leaf_count=0;self.next_index=0

    def write_pixel(self,index,values,leaves):
        if index!=self.next_index or not 0<=index<WIDTH*HEIGHT:raise ValueError('Non-row-major pixel commit')
        if self.leaf_count+len(leaves)>200000:raise ValueError('Leaf cap')
        values=dict(values,status=1,leaf_offset=self.leaf_count,leaf_count=len(leaves))
        if set(values)!=set(FLOAT_FIELDS+INT_FIELDS):raise ValueError('Pixel schema mismatch')
        if not all(math.isfinite(values[k]) for k in FLOAT_FIELDS):raise ValueError('Nonfinite evidence')
        payload=RECORD.pack(*(values[k] if k!='status' else 0 for k in FLOAT_FIELDS+INT_FIELDS))
        ledger=b''.join(LEAF.pack(*cell) for cell in leaves)
        if len(ledger)!=len(leaves)*LEAF.size:raise ValueError('Leaf layout')
        if self.leaf_file.write(ledger)!=len(ledger):raise OSError('Short leaf write')
        self.pixel_file.seek(index*RECORD.size)
        if self.pixel_file.write(payload)!=len(payload):raise OSError('Short pixel write')
        # Commit status last, so a killed/short payload write cannot look valid.
        self.pixel_file.seek(index*RECORD.size+31*8)
        if self.pixel_file.write(struct.pack('<I',1))!=4:raise OSError('Short status write')
        self.leaf_count+=len(leaves);self.next_index+=1

    def mark_failed(self,index):
        if not 0<=index<WIDTH*HEIGHT:raise ValueError('Invalid failed pixel')
        self.pixel_file.seek(index*RECORD.size)
        self.pixel_file.write(RECORD.pack(*([0.]*31+[2]+[0]*9)))

    def close(self):
        self.pixel_file.close();self.leaf_file.close()


def iter_pixels(raw):
    if len(raw)!=WIDTH*HEIGHT*RECORD.size:raise ValueError('Pixel file length')
    names=FLOAT_FIELDS+INT_FIELDS
    for index,values in enumerate(RECORD.iter_unpack(raw)):
        yield index,dict(zip(names,values))


def _png(path,rgb):
    def chunk(tag,data):
        return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
    scan=b''.join(b'\x00'+rgb[y*WIDTH*3:(y+1)*WIDTH*3] for y in range(HEIGHT))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',WIDTH,HEIGHT,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(scan,9))+chunk(b'IEND',b'')
    _publish(path,png)


def _publish(path,data):
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('Existing published evidence differs: '+path.name)
        return
    partial=path.with_name(path.name+'.part')
    partial.write_bytes(data)
    partial.replace(path)


def _byte(x):
    return int(math.floor(max(0.,min(1.,x))*255+0.5))


def _display(x):
    x=max(0.,x)/(1+max(0.,x))
    return _byte(12.92*x if x<=.0031308 else 1.055*x**(1/2.4)-.055)


def identity(path):
    b=path.read_bytes()
    return {'path':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def finalize(out,cmax,particle_count):
    """Package existing evidence once, without evaluating any scientific operator."""
    start=time.perf_counter();out=Path(out)
    raw=(out/'pixels.bin').read_bytes();ledger=(out/'leaves.bin').read_bytes()
    if len(raw)+len(ledger)>RAW_CAP:raise ValueError('Raw evidence extent')
    images={k:bytearray() for k in ['rgb','alpha','retention','valid']}
    summary={'planned_pixels':WIDTH*HEIGHT,'qualified_pixels':0,'failed_pixels':0,'uncomputed_pixels':0,
             'nontrivial_pixels':0,'mixed_pixels':0,'nontrivial_bbox':None,'max_rgb_endpoint_error':0.,
             'max_alpha_error':0.,'rgb_min':None,'rgb_max':None,'alpha_min':None,'alpha_max':None,
             'ordinary_paths':{},'reference_paths':{},'retained_histogram':{},'stage_seconds':{},
             'max_endpoint_pixel':None,'max_alpha_pixel':None,'max_created_cells':0,'stored_leaves':len(ledger)//LEAF.size,
             'partial_leaf_tail_bytes':len(ledger)%LEAF.size}
    expected_offset=0
    for index,p in iter_pixels(raw):
        if p['status'] not in (0,1,2):raise ValueError('Unknown pixel status')
        if p['status']!=1:
            summary['failed_pixels' if p['status']==2 else 'uncomputed_pixels']+=1
            for key in ['rgb','alpha','retention']:images[key].extend((255,0,255))
            images['valid'].extend((0,0,0));continue
        if not all(math.isfinite(p[k]) for k in FLOAT_FIELDS):raise ValueError('Nonfinite valid record')
        if p['leaf_offset']!=expected_offset:raise ValueError('Noncontiguous accepted leaf ownership')
        expected_offset+=p['leaf_count']
        if expected_offset>len(ledger)//LEAF.size:raise ValueError('Leaf extent overflow')
        summary['qualified_pixels']+=1
        summary['mixed_pixels']+=p['mixed']
        i,j=index%WIDTH,index//WIDTH
        if p['full_alpha']>=.001:
            summary['nontrivial_pixels']+=1
            box=summary['nontrivial_bbox']
            summary['nontrivial_bbox']=[i,j,i,j] if box is None else [min(box[0],i),min(box[1],j),max(box[2],i),max(box[3],j)]
        rgb=[p[k] for k in ['r','g','b']]
        summary['rgb_min']=rgb[:] if summary['rgb_min'] is None else [min(a,b) for a,b in zip(summary['rgb_min'],rgb)]
        summary['rgb_max']=rgb[:] if summary['rgb_max'] is None else [max(a,b) for a,b in zip(summary['rgb_max'],rgb)]
        summary['alpha_min']=p['full_alpha'] if summary['alpha_min'] is None else min(summary['alpha_min'],p['full_alpha'])
        summary['alpha_max']=p['full_alpha'] if summary['alpha_max'] is None else max(summary['alpha_max'],p['full_alpha'])
        error=max(max(abs(p[k]-p['lower_'+k]),abs(p[k]-p['upper_'+k])) for k in ['r','g','b'])
        ae=abs(p['alpha']-p['full_alpha'])
        if error>summary['max_rgb_endpoint_error']:summary['max_rgb_endpoint_error']=error;summary['max_endpoint_pixel']=[i,j]
        if ae>summary['max_alpha_error']:summary['max_alpha_error']=ae;summary['max_alpha_pixel']=[i,j]
        summary['max_created_cells']=max(summary['max_created_cells'],p['created_cells'])
        for field,target in [('ordinary_path','ordinary_paths'),('reference_path','reference_paths'),('retained_count','retained_histogram')]:
            key=str(p[field]);summary[target][key]=summary[target].get(key,0)+1
        for key in ['preparation_seconds','ordinary_seconds','projection_seconds','reference_seconds','qualification_seconds']:
            summary['stage_seconds'][key]=summary['stage_seconds'].get(key,0.)+p[key]
        images['rgb'].extend(_display(x) for x in rgb)
        images['alpha'].extend([_byte(p['alpha'])]*3)
        images['retention'].extend([_byte(p['retained_count']/particle_count)]*3)
        images['valid'].extend((255,255,255))
    summary['unreferenced_leaf_tail']=len(ledger)//LEAF.size-expected_offset
    if summary['unreferenced_leaf_tail']<0:raise ValueError('Negative tail')
    # A hard kill may occur between leaf-write and pixel-commit. Such a tail is
    # preserved and explicitly reported, never assigned to a qualified pixel.
    summary['nontrivial_fraction_of_full_frame']=summary['nontrivial_pixels']/(WIDTH*HEIGHT)
    summary['all_pixel_records_qualified']=summary['qualified_pixels']==WIDTH*HEIGHT and summary['failed_pixels']==0
    files=[]
    for name,b in [('pixels.bin',raw),('leaves.bin',ledger)]:
        path=out/(name+'.gz')
        _publish(path,gzip.compress(b,mtime=0))
        info=identity(path);info.update(raw_bytes=len(b),raw_sha256=hashlib.sha256(b).hexdigest());files.append(info)
    for key,b in images.items():
        path=out/(key+'.png');_png(path,bytes(b));files.append(identity(path))
    return {'schema':'t35-fixed-binary-evidence-v1','width':WIDTH,'height':HEIGHT,'record_format':RECORD.format,
            'record_bytes':RECORD.size,'float_fields':FLOAT_FIELDS,'integer_fields':INT_FIELDS,
            'leaf_format':LEAF.format,'leaf_fields':['left','right','W','low_r','low_g','low_b','high_r','high_g','high_b'],
            'status_codes':{'uncomputed':0,'qualified':1,'failed':2},'reference_paths':REF_PATHS,'ordinary_paths':ORD_PATHS,
            'source_cmax':cmax,'particle_count':particle_count,'files':files,'raw_binary_bytes':len(raw)+len(ledger),
            'summary':summary,'display':{'rgb':'L/(1+L) then standard sRGB transfer; exposure1; black background',
            'alpha':'ordinary alpha mapped linearly0..1','retention':'ordinary retained count /270 linearly0..1',
            'invalid':'magenta RGB255,0,255','valid_mask':'qualified white, everything else black',
            'framing':'original256x192, top-down pixel centers, no crop/zoom/exposure fit'},
            'packaging_seconds':time.perf_counter()-start}
