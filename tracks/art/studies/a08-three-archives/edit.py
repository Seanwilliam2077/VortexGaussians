"""A08: one declared editorial encode, then saved-media checks; stdlib only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import traceback

HERE=Path(__file__).resolve().parent
ENCODER=Path('C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe')
PROBE=ENCODER.with_name('ffprobe.exe')
FONT=Path('C:/Windows/Fonts/msyh.ttc')

def identity(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def save(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--out',default='run-01')
    args=parser.parse_args()
    plan=json.loads((HERE/'edit-plan.json').read_bytes())
    sources={name:(HERE.parent/entry['file']).resolve() for name,entry in plan['sources'].items()}
    for name,path in sources.items():
        assert identity(path)=={k:plan['sources'][name][k] for k in ('bytes','sha256')},name
    metadata=json.loads(sources['metadata'].read_bytes())
    assert metadata['status']=='completed' and metadata['sourcesUnchanged'] is True
    assert metadata['receipt']=={'time':'10.00 s','burning':'3,320','charred':'1,400'}
    assert metadata['afterReset']['burning']==metadata['afterReset']['charred']=='0'
    if not args.execute:
        print(json.dumps(dict(plan=plan,source_identities_match=True,execution=False),ensure_ascii=False));return 0
    out=(HERE/args.out).resolve()
    assert out.parent==HERE and not out.exists()
    out.mkdir();(out/'text').mkdir()
    pins=[*sources.values(),HERE/'INTENT.md',HERE/'edit-plan.json',Path(__file__),ENCODER,PROBE,FONT]
    before={str(path):identity(path) for path in pins}
    record=dict(schema='a08-three-archives-result-v1',status='started',source_before=before,
        plan=plan,browser_opened=False,simulation_executed=False,new_scene_created=False,
        source_deleted=False,encode_attempts=0,commands=[],checks={})
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
            finally:row['wall_seconds']=time.perf_counter()-started
        return row
    try:
        for name,value in plan['copy'].items():(out/'text'/f'{name}.txt').write_text(value,encoding='utf-8')
        color=plan['colors'];font=FONT.as_posix().replace(':','\\:')
        prefix=f"drawtext=fontfile='{font}':expansion=none:"
        def txt(key,size,x,y,tint='offwhite',enable=None):
            item=prefix+f"textfile=text/{key}.txt:fontsize={size}:fontcolor={color[tint]}:x={x}:y={y}:line_spacing=12"
            return item+(f":enable='gte(t,{enable})'" if enable is not None else '')
        def base_headers(chapter):
            return [txt('title',28,64,54),txt(chapter,23,64,110,'amber'),
                'drawbox=x=64:y=151:w=1152:h=1:color='+color['line']+':t=fill',
                txt('provenance',16,64,917,'muted')]
        def scene(tag,duration,chapter,label,video=False,initial=False,extras=()):
            timing='fps=25,trim=start=5.10:end=18.10,setpts=PTS-STARTPTS' if video else f'trim=duration={duration},setpts=PTS-STARTPTS,fps=25'
            y=20 if initial else 0
            filters=[timing,f'crop=850:530:40:{y}','setsar=1',
                'pad=1280:960:215:190:color='+color['background'],
                'drawbox=x=214:y=189:w=852:h=532:color='+color['line']+':t=1',*base_headers(chapter),*extras,'settb=AVTB']
            return tag+','.join(filters)+f'[{label}]'
        graph=['[2:v]split=7[reset][ar1][ar2][ar3][th1][th2][th3]']
        graph.append('color=c='+color['background']+':s=1280x960:r=25:d=4,'+
            ','.join([txt('title',62,'(w-text_w)/2',370),txt('opening',26,'(w-text_w)/2',475,'amber'),
            txt('provenance',16,'(w-text_w)/2',880,'muted'),'settb=AVTB'])+'[v0]')
        graph.append(scene('[1:v]',4,'initial','v1',initial=True))
        graph.append(scene('[0:v]',13,'burn','v2',video=True))
        graph.append(scene('[reset]',4,'reset','v3'))
        graph.append(scene('[ar1]',16,'i','v4'))
        stats=[txt('stats_heading',18,215,758,'muted')]
        for x,key in zip((230,550,870),('time','burning','charred')):
            stats += [txt(key+'_label',18,x,800,'muted'),txt(key,40,x,830)]
        graph.append(scene('[ar2]',14,'ii','v5',extras=stats))
        actions=[txt('action_heading',18,215,758,'muted')]
        for x,key in zip((130,335,550,800,1020),('load','ignite','advance','reinitialize','receipt')):
            actions.append(txt(key,22,x,818,'offwhite',plan['action_reveals_in_archive_iii_seconds'][key]))
        graph.append(scene('[ar3]',14,'iii','v6',extras=actions))
        for i in range(1,4):
            graph.append(f'[th{i}]trim=duration=9,setpts=PTS-STARTPTS,crop=850:530:40:0,scale=340:212:flags=lanczos,setsar=1,fps=25[t{i}]')
        graph.append('color=c='+color['background']+':s=1280x960:r=25:d=9[tripbase]')
        prior='tripbase'
        for i,x in enumerate((80,470,860),1):
            tag=f'trip{i}';graph.append(f'[{prior}][t{i}]overlay={x}:290:shortest=1[{tag}]');prior=tag
        def ending_text(withdrawn=False):
            items=base_headers('compare')
            for x,key in zip((80,470,860),('i','ii','iii')):
                items += [txt(key,23,x,235,'amber'),
                    f'drawbox=x={x-1}:y=289:w=342:h=214:color='+color['line']+':t=1',
                    txt(key+'_evidence',18,x,550,'muted' if key=='i' else 'offwhite')]
            if withdrawn:
                items += [txt('withdrawal',29,'(w-text_w)/2',760),txt('withdrawal_note',18,'(w-text_w)/2',820,'amber')]
            return items
        graph.append(f'[{prior}]'+','.join(ending_text()+['settb=AVTB'])+'[v7]')
        graph.append('color=c='+color['background']+':s=1280x960:r=25:d=6,'+
            ','.join(ending_text(True)+['settb=AVTB'])+'[v8]')
        graph.append(''.join(f'[v{i}]' for i in range(9))+'concat=n=9:v=1:a=0[outv]')
        (out/'filter.ffscript').write_text(';\n'.join(graph)+'\n',encoding='utf-8')
        command=[str(ENCODER),'-hide_banner','-nostdin','-n','-i',str(sources['video'])]
        for key in ('initial','reset'):command += ['-loop','1','-framerate','25','-i',str(sources[key])]
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
        assert int(fields['streams.stream.0.nb_frames'])==2100 and abs(float(fields['format.duration'])-84)<.001
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
        record['checks']['representative_frames_extracted']=len(frames)==7
        record['video']=dict(file='study.mp4',duration_seconds=84,frames=2100,fps=25,
            width=1280,height=960,audio=False,**identity(video))
        record['status']='completed_media_checks'
    except BaseException as error:
        record.update(status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
    finally:
        record['source_after']={str(path):identity(path) for path in pins}
        record['sources_unchanged']=record['source_before']==record['source_after']
        if not record['sources_unchanged']:record['status']='failed_source_preservation'
        record['wall_seconds_before_receipt']=time.perf_counter()-begin
        record['visual_inspection']='pending separate seven-frame review; no continuous viewing claimed'
        save(out/'result.json',record)
        print(json.dumps({k:record.get(k) for k in ('status','encode_seconds','video','sources_unchanged','wall_seconds_before_receipt')},ensure_ascii=False))
    return 0 if record['status']=='completed_media_checks' else 2

if __name__=='__main__':raise SystemExit(main())
