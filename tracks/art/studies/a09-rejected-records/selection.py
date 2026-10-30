"""A09 finite supplied-material inspection; standard library, no simulation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import time
import zlib

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'a06-char-and-reset' / 'run-01'
FILES = ('02-loaded.png', '03-ignited.png', '04-ten-seconds-scene.png',
         '06-reset-scene.png', '07-reset-receipt.png')
LABELS = ('载入', '点火', '十秒', '重置', '回执')

def identity(path):
    data = path.read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')

def inspect_png(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    offset = 8
    chunks = []
    dimensions = None
    while offset < len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset+4:offset+8]
        end = offset + 12 + length
        assert end <= len(data)
        payload = data[offset+8:offset+8+length]
        stored_crc = struct.unpack_from('>I', data, offset+8+length)[0]
        assert zlib.crc32(kind+payload) & 0xffffffff == stored_crc
        name = kind.decode('ascii')
        chunks.append(dict(type=name, bytes=length, crc_verified=True))
        if name == 'IHDR':
            width,height,depth,color,compression,filtering,interlace = struct.unpack('>IIBBBBB', payload)
            dimensions = dict(width=width,height=height,bit_depth=depth,color_type=color,
                              compression=compression,filtering=filtering,interlace=interlace)
        offset = end
        if name == 'IEND': break
    assert offset == len(data), 'Uninspected trailing PNG bytes'
    assert dimensions and chunks[-1]['type'] == 'IEND'
    allowed = {'IHDR','IDAT','IEND','sRGB','gAMA','cHRM','pHYs'}
    unknown = [c for c in chunks if c['type'] not in allowed]
    assert not unknown, 'Unreviewed PNG ancillary payload: stop, do not reject automatically'
    return dict(dimensions=dimensions,chunks=chunks,unreviewed_payloads=unknown,
                image_pixels_decoded_by_this_script=False,
                scope='PNG structure/CRC only; separate visual inspection is not a resume test')

def inspect_json(value):
    paths = []
    keys = set()
    numeric_sequences = []
    large_strings = []
    def walk(item,path):
        if isinstance(item,dict):
            paths.append(dict(path=path,type='object',keys=list(item)))
            keys.update(item)
            for key,child in item.items(): walk(child,path+'.'+key)
        elif isinstance(item,list):
            types = Counter(type(x).__name__ for x in item)
            paths.append(dict(path=path,type='array',length=len(item),element_types=dict(types)))
            if item and all(type(x) in (int,float) for x in item):
                numeric_sequences.append(dict(path=path,length=len(item)))
            for index,child in enumerate(item): walk(child,f'{path}[{index}]')
        else:
            if isinstance(item,str) and len(item)>4096:
                large_strings.append(dict(path=path,length=len(item)))
    walk(value,'$')
    suspected = sorted(k for k in keys if any(token in k.lower() for token in
        ('checkpoint','resume_payload','particlestate','statebuffer','restart_payload')))
    assert not suspected and not numeric_sequences and not large_strings, \
        'Possible state payload requires manual review; no automatic all-rejection'
    return dict(top_level_keys=list(value),structures=paths,
                distinct_field_names=sorted(keys),numeric_sequence_payloads=numeric_sequences,
                large_string_payloads=large_strings,suspected_state_payload_keys=suspected)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    args=parser.parse_args()
    if not args.execute:
        print('Plan only: inspect five fixed PNG structures and A06 result JSON; no output written.')
        return
    started=time.perf_counter()
    outputs=[HERE/name for name in ('selection.json','archive-accepted.json','archive-rejected.json')]
    assert not any(path.exists() for path in outputs), 'Exclusive selection output required'
    inputs=[SOURCE/name for name in (*FILES,'result.json')]
    before={path.name:identity(path) for path in inputs}
    result=json.loads((SOURCE/'result.json').read_bytes())
    assert result['status']=='completed' and result['sourcesUnchanged'] is True
    structure=inspect_json(result)
    snapshots={s['file']:s for s in result['snapshots']}
    rows=[]
    for index,(name,label) in enumerate(zip(FILES,LABELS),1):
        png=inspect_png(SOURCE/name)
        snapshot=snapshots[name]
        assert snapshot['sha256']==before[name]['sha256']
        # A positive admission requires an actual resume payload. None is supplied
        # in the fully enumerated JSON objects or non-image PNG chunks above.
        rows.append(dict(id=f'A09-{index:02d}',label=label,file=name,identity=before[name],
            input_type='PNG page screenshot plus observation/action/identity JSON context',
            png=png,matched_snapshot=snapshot,
            supported=['Visible screen pixels at the recorded capture',
                'Reported displayed counts/time and capture timing',
                'Nearby recorded action names and completion timestamps',
                'Content identity; not a reconstruction algorithm'],
            missing_supplied_basis=['No serialized time-indexed simulation-state payload',
                'No declared restore schema or state-to-engine mapping',
                'Source file hashes are references, not embedded source/assets/state'],
            decision='rejected',admission_claim='restorable state not supplied in these checked materials',
            not_claimed=['Impossible recovery from the full repository',
                         'Impossible future replay or inference','Deletion of source material']))
    accepted=[r['id'] for r in rows if r['decision']=='accepted']
    rejected=[r['id'] for r in rows if r['decision']=='rejected']
    assert len(accepted)+len(rejected)==5 and not set(accepted)&set(rejected)
    after={path.name:identity(path) for path in inputs}
    assert before==after
    selection=dict(schema='a09-supplied-record-selection-v1',rule='Only a supplied record carrying a complete restorable simulation-state payload is admitted to the fictional restorable archive.',
        rule_status='authored fictional positive-evidence admission rule, not an institution',
        supplied_scope=list(before),input_identities_before=before,input_identities_after=after,
        inputs_unchanged=True,json_structure=structure,
        log_context=dict(actions=result['actions'],console=result['console'],errors=result['errors'],
            playObservations=result['playObservations'],receipt=result['receipt'],afterReset=result['afterReset']),
        source_references_opened=False,simulation_or_restore_attempted=False,
        items=rows,accepted=accepted,rejected=rejected,
        total_items=5,source_files_deleted=False,
        limitation='This is a finite supplied-format admission audit, not a proof of information-theoretic impossibility. Screenshot-heavy supply makes rejection unsurprising.',
        elapsed_seconds_before_output_write=time.perf_counter()-started)
    for path,kind,ids in ((outputs[1],'accepted',accepted),(outputs[2],'rejected',rejected)):
        save(path,dict(schema='a09-archive-list-v1',kind=kind,
            items=[dict(id=r['id'],file=r['file'],identity=r['identity']) for r in rows if r['id'] in ids],
            meaning='Membership in the fictional restorable archive only; rejected source files remain available'))
    selection['manifests']={path.name:identity(path) for path in outputs[1:]}
    save(outputs[0],selection)
    print(json.dumps(dict(accepted=len(accepted),rejected=len(rejected),selection=identity(outputs[0]),
                         elapsed_seconds=time.perf_counter()-started),ensure_ascii=False))

if __name__=='__main__': main()
