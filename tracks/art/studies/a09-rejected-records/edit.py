"""A09: render a fixed, selection-driven editorial film; no simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'a06-char-and-reset'/'run-01'
ENCODER=Path('C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe')
PROBE=ENCODER.with_name('ffprobe.exe')
FONT=Path('C:/Windows/Fonts/msyh.ttc')

def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.write('\n')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--out',default='run-01')
    args=parser.parse_args()
    plan=json.loads((HERE/'edit-plan.json').read_bytes())
    assert identity(HERE/'selection.json')==plan['selection']
    selection=json.loads((HERE/'selection.json').read_bytes())
    for name,pin in plan['manifests'].items(): assert identity(HERE/name)==pin
    accepted=json.loads((HERE/'archive-accepted.json').read_bytes())
    rejected=json.loads((HERE/'archive-rejected.json').read_bytes())
    assert [r['id'] for r in accepted['items']]==plan['accepted_ids']==selection['accepted']
    assert [r['id'] for r in rejected['items']]==plan['rejected_ids']==selection['rejected']
    assert [(r['id'],r['decision']) for r in plan['items']]==[(r['id'],r['decision']) for r in selection['items']]
    # This score was written after the actual finite admission check. A different
    # admission result needs a new score, not silently forcing a rejection movie.
    assert not plan['accepted_ids'] and len(plan['rejected_ids'])==5, 'Unmatched score: stop before rendering'
    sources={r['id']:SOURCE/r['file'] for r in plan['items']}
    for row in plan['items']: assert identity(sources[row['id']])==row['identity']
    for row in plan['sources'].values(): assert identity(SOURCE/row['file'])=={k:row[k] for k in ('bytes','sha256')}
    if not args.execute:
        print(json.dumps(dict(execution=False,plan=plan,selection_verified=True),ensure_ascii=False));return 0
    out=(HERE/args.out).resolve()
    assert out.parent==HERE and not out.exists(), 'A fresh direct child output is required'
    out.mkdir();(out/'text').mkdir()
    pins=[*sources.values(),SOURCE/'study.mp4',SOURCE/'result.json',HERE/'INTENT.md',
          HERE/'selection.py',HERE/'selection.json',HERE/'archive-accepted.json',HERE/'archive-rejected.json',
          HERE/'edit-plan.json',Path(__file__),ENCODER,PROBE,FONT]
    before={str(path):identity(path) for path in pins}
    record=dict(schema='a09-rejected-records-result-v1',status='started',source_before=before,
        plan=plan,selection_counts=dict(accepted=len(plan['accepted_ids']),rejected=len(plan['rejected_ids'])),
        browser_opened=False,simulation_executed=False,new_scene_created=False,
        source_deleted=False,archive_membership_overridden=False,
        video_admission_tested=False,encode_attempts=0,commands=[],checks={})
    save(out/'attempt.json',record)
    begin=time.perf_counter()
    def run(label,command,timeout):
        started=time.perf_counter();row=dict(label=label,command=command,timeout_seconds=timeout)
        record['commands'].append(row)
        with (out/(label+'.stdout.log')).open('xb') as stdout,(out/(label+'.stderr.log')).open('xb') as stderr:
            try:
                child=subprocess.run(command,cwd=out,stdout=stdout,stderr=stderr,timeout=timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW)
                row['returncode']=child.returncode;child.check_returncode()
            except BaseException as error:
                row['error']=repr(error);raise
            finally: row['wall_seconds']=time.perf_counter()-started
        return row
    try:
        texts=dict(plan['copy'])
        for index,row in enumerate(plan['items'],1):texts[row['id']]=f'{index:02d}  {row["label"]}'
        for name,value in texts.items():(out/'text'/f'{name}.txt').write_text(value,encoding='utf-8')
        colors=plan['colors'];font=FONT.as_posix().replace(':','\\:')
        graph=[];requests={i:[] for i in range(1,6)};serial=0
        def txt(key,size,x,y,color='offwhite',enable=None):
            s=f"drawtext=fontfile='{font}':expansion=none:textfile=text/{key}.txt:fontsize={size}:fontcolor={colors[color]}:x={x}:y={y}"
            return s+(f":enable='{enable}'" if enable else '')
        def base(label,duration,mode='archive',current=None):
            filters=[txt('title',34,64,45),txt('provenance',15,64,929,'muted')]
            if mode=='entry':
                filters += [txt('condition',27,64,108,'amber'),txt('fiction',18,965,114,'muted')]
            elif mode=='archive':
                filters += [txt('archive',21,64,110,'amber'),
                    f'drawbox=x=214:y=149:w=852:h=532:color={colors["line"]}:t=1',
                    txt('strip',19,64,731,'muted')]
                if current:
                    filters += [txt(current,22,1000,110),
                        txt('rejected',22,960,697,'amber','between(t,4.4,6.2)')]
            elif mode=='return':filters += [txt('return',25,64,110,'amber')]
            elif mode=='hold':filters += [txt('preservation',17,64,110,'muted')]
            graph.append(f'color=c={colors["background"]}:s=1280x960:r=25:d={duration},'+','.join(filters)+f'[{label}]')
        def picture(index,duration,scale=None,dynamic=False):
            nonlocal serial
            serial+=1;raw=f'raw{serial}';tag=f'pic{serial}';requests[index+1].append(raw)
            x,y,w,h=plan['items'][index]['crop']
            filters=[f'trim=duration={duration}','setpts=PTS-STARTPTS','fps=25',f'crop={w}:{h}:{x}:{y}']
            if dynamic:
                p='min(max((t-5)/1.2,0),1)'
                filters += [f"scale=w='trunc((850-650*{p})/2)*2':h='trunc((530-406*{p})/2)*2':eval=frame:flags=lanczos"]
            elif scale:filters += [f'scale={scale[0]}:{scale[1]}:flags=lanczos']
            filters += ['setsar=1']
            graph.append(f'[{raw}]'+','.join(filters)+f'[{tag}]')
            return tag
        def overlay(base_tag,pic,x,y):
            nonlocal serial
            serial+=1;tag=f'over{serial}'
            graph.append(f'[{base_tag}][{pic}]overlay=x=\'{x}\':y=\'{y}\':shortest=1:eval=frame[{tag}]')
            return tag
        def strip(base_tag,duration,ids):
            for record_id in ids:
                i=next(i for i,r in enumerate(plan['items']) if r['id']==record_id)
                slot=plan['rejected_ids'].index(record_id)
                pic=picture(i,duration,(200,124))
                base_tag=overlay(base_tag,pic,100+220*slot,774)
            return base_tag
        def finish(tag,index):graph.append(f'[{tag}]setsar=1,settb=AVTB[v{index}]')
        base('opening',7,'entry')
        finish(overlay('opening',picture(0,7),215,150),0)
        for i,row in enumerate(plan['items']):
            label=f'review{i}';base(label,8,'archive',row['id'])
            prior=[r['id'] for r in plan['items'][:i] if r['decision']=='rejected']
            label=strip(label,8,prior)
            slot=plan['rejected_ids'].index(row['id'])
            target=100+220*slot;p='min(max((t-5)/1.2,0),1)'
            pic=picture(i,8,dynamic=True)
            label=overlay(label,pic,f'215+({target}-215)*{p}',f'150+(774-150)*{p}')
            finish(label,i+1)
        base('empty',8,'archive');finish(strip('empty',8,plan['rejected_ids']),6)
        returned=next(i for i,r in enumerate(plan['items']) if r['id']==plan['return_id'])
        assert plan['return_id'] in plan['rejected_ids']
        base('returnbase',3,'return')
        label=strip('returnbase',3,plan['rejected_ids'])
        finish(overlay(label,picture(returned,3),215,150),7)
        base('burnbase',13,'burn')
        label=strip('burnbase',13,plan['rejected_ids'])
        graph.append('[0:v]fps=25,trim=start=5.10:end=18.10,setpts=PTS-STARTPTS,crop=850:530:40:0,setsar=1[burnpic]')
        finish(overlay(label,'burnpic',215,150),8)
        base('holdbase',5,'hold')
        label=strip('holdbase',5,plan['rejected_ids'])
        finish(overlay(label,picture(returned,5),215,150),9)
        split=[]
        for index,tags in requests.items():
            assert tags
            split.append(f'[{index}:v]split={len(tags)}'+''.join(f'[{t}]' for t in tags))
        graph=split+graph
        graph.append(''.join(f'[v{i}]' for i in range(10))+'concat=n=10:v=1:a=0[outv]')
        (out/'filter.ffscript').write_text(';\n'.join(graph)+'\n',encoding='utf-8')
        command=[str(ENCODER),'-hide_banner','-nostdin','-n','-i',str(SOURCE/'study.mp4')]
        for row in plan['items']:command += ['-loop','1','-framerate','25','-i',str(sources[row['id']])]
        command += ['-filter_complex_threads','2','-filter_complex_script','filter.ffscript','-map','[outv]',
            '-an','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-threads','2',
            '-fps_mode','cfr','-r','25','-movflags','+faststart','study.mp4']
        record['encode_attempts']=1
        row=run('encode',command,120);record['encode_seconds']=row['wall_seconds']
        video=out/'study.mp4'
        run('probe',[str(PROBE),'-v','error','-show_entries',
            'stream=index,codec_type,codec_name,width,height,avg_frame_rate,nb_frames,duration:format=duration,size',
            '-of','flat',str(video)],15)
        flat=(out/'probe.stdout.log').read_text(encoding='utf-8');fields={}
        for line in flat.splitlines():
            key,value=line.split('=',1)
            fields[key]=json.loads(value) if value.startswith('"') else value
        record['probe_flat']=fields
        assert fields['streams.stream.0.codec_type']=='video' and fields['streams.stream.0.codec_name']=='h264'
        assert fields['streams.stream.0.width']=='1280' and fields['streams.stream.0.height']=='960'
        assert fields['streams.stream.0.avg_frame_rate']=='25/1'
        assert int(fields['streams.stream.0.nb_frames'])==1900 and abs(float(fields['format.duration'])-76)<.001
        assert not any(v=='audio' for k,v in fields.items() if k.endswith('.codec_type'))
        record['checks']['flat_metadata']=True
        run('decode',[str(ENCODER),'-hide_banner','-v','error','-nostdin','-xerror','-i',str(video),
            '-map','0:v:0','-an','-f','null','-'],60)
        record['checks']['full_decode']=True
        frames=[]
        for i,t in enumerate(plan['inspection_seconds']):
            filename=f'check-{i+1:02d}-{t:02d}s.png'
            run(f'frame-{i+1:02d}',[str(ENCODER),'-hide_banner','-loglevel','error','-nostdin','-n',
                '-ss',str(t),'-i',str(video),'-frames:v','1','-update','1',filename],15)
            frames.append(dict(file=filename,seconds=t,**identity(out/filename)))
        record['inspection_frames']=frames
        record['checks']['representative_frames_extracted']=len(frames)==9
        record['video']=dict(file='study.mp4',duration_seconds=76,frames=1900,fps=25,
            width=1280,height=960,audio=False,**identity(video))
        record['checks']['selection_drives_destinations']=True
        record['status']='completed_media_checks'
    except BaseException as error:
        record.update(status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        record['source_after']={str(path):identity(path) for path in pins}
        record['sources_unchanged']=record['source_before']==record['source_after']
        if not record['sources_unchanged']:record['status']='failed_source_preservation'
        record['wall_seconds_before_receipt']=time.perf_counter()-begin
        record['visual_inspection']='pending separate nine-frame review; no continuous viewing claimed'
        save(out/'result.json',record)
        print(json.dumps({k:record.get(k) for k in ('status','encode_seconds','video','sources_unchanged','wall_seconds_before_receipt')},ensure_ascii=False))
    return 0 if record['status']=='completed_media_checks' else 2

if __name__=='__main__':raise SystemExit(main())
