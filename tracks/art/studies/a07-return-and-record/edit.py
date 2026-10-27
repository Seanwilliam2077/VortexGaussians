"""A07: one CPU editorial encode from pinned A06 assets; no browser/simulation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--execute', action='store_true'); parser.add_argument('--out', default='run-01')
    args = parser.parse_args()
    plan = json.loads((HERE / 'edit-plan.json').read_text(encoding='utf-8'))
    sources = {name: (HERE / row['file']).resolve() for name, row in plan['sources'].items()}
    for name, path in sources.items():
        if sha(path) != plan['sources'][name]['sha256']:
            raise ValueError('Input SHA mismatch: ' + name)
    if not args.execute:
        print(json.dumps({'plan': plan, 'inputHashesMatch': True}, ensure_ascii=False, indent=2)); return
    out = (HERE / args.out).resolve()
    if out.parent != HERE or out == HERE: raise ValueError('Output must be a fresh immediate child')
    out.mkdir()
    encoder = Path(os.environ.get('FFMPEG_EXECUTABLE', 'C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe'))
    font = Path(os.environ.get('A07_FONT', 'C:/Windows/Fonts/msyh.ttc'))
    pins = [*sources.values(), HERE / 'INTENT.md', HERE / 'edit-plan.json', Path(__file__), encoder, font]
    record = {'schema': 'a07-edit-result-v1', 'scope': 'Agent-edited formal draft; static layout is not original simultaneous UI or a memory claim',
              'sourceBefore': {str(p): sha(p) for p in pins}, 'plan': plan, 'browserOpened': False, 'simulationExecuted': False}
    started = time.perf_counter()
    try:
        for name in ['title', 'footer']:
            (out / (name + '.txt')).write_text(plan[name], encoding='utf-8')
        for segment in plan['segments']:
            (out / (segment['id'] + '.txt')).write_text(segment['label'], encoding='utf-8')
        (out / 'receipt-label.txt').write_text(plan['segments'][-1]['receiptLabel'], encoding='utf-8')
        font_filter = font.as_posix().replace(':', '\\:')
        text = f"drawtext=fontfile='{font_filter}':expansion=none:fontcolor=0xf2eadc:"
        def titles(label):
            return (text + 'textfile=title.txt:fontsize=34:x=40:y=25,' +
                    text + f'textfile={label}.txt:fontsize=21:x=40:y=76,' +
                    text + 'textfile=footer.txt:fontsize=18:x=40:y=930')
        def scene_chain(input_tag, segment, output_tag, timing):
            x,y,w,h=segment['crop']; sw,sh=segment['scale']; px,py=segment['position']
            return (input_tag + timing + f',crop={w}:{h}:{x}:{y},scale={sw}:{sh},setsar=1,fps=25,'
                    f'pad=1280:960:{px}:{py}:color=0x141512,' + titles(segment['id']) + f',settb=AVTB{output_tag}')
        initial,burn,reset,together = plan['segments']
        graph = ['[2:v]split=2[resetfull][resetfinal]']
        graph.append(scene_chain('[1:v]',initial,'[v0]',f'trim=duration={initial["duration"]},setpts=PTS-STARTPTS'))
        graph.append(scene_chain('[0:v]',burn,'[v1]',f'trim=start={burn["start"]}:end={burn["end"]},setpts=PTS-STARTPTS'))
        graph.append(scene_chain('[resetfull]',reset,'[v2]',f'trim=duration={reset["duration"]},setpts=PTS-STARTPTS'))
        x,y,w,h=together['sceneCrop']; sw,sh=together['sceneScale']
        graph.append(f'[resetfinal]trim=duration={together["duration"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale={sw}:{sh},setsar=1[scene]')
        x,y,w,h=together['receiptCrop']; sw,sh=together['receiptScale']
        graph.append(f'[3:v]trim=duration={together["duration"]},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale={sw}:{sh},setsar=1[receipt]')
        sx,sy=together['scenePosition']; rx,ry=together['receiptPosition']
        graph.append(f'color=c=0x141512:s=1280x960:r=25:d={together["duration"]}[base]')
        graph.append(f'[base][scene]overlay={sx}:{sy}:shortest=1[mid]')
        graph.append(f'[mid][receipt]overlay={rx}:{ry}:shortest=1,' + titles('together') + ',' +
                     text + 'textfile=receipt-label.txt:fontsize=20:x=40:y=668,fps=25,settb=AVTB[v3]')
        graph.append('[v0][v1][v2][v3]concat=n=4:v=1:a=0[outv]')
        (out / 'filter.ffscript').write_text(';\n'.join(graph) + '\n', encoding='utf-8')
        command=[str(encoder),'-hide_banner','-nostdin','-i',str(sources['video'])]
        for key in ['initial','reset','receipt']:
            command += ['-loop','1','-framerate','25','-i',str(sources[key])]
        command += ['-filter_complex_threads','2','-filter_complex_script','filter.ffscript','-map','[outv]','-an','-c:v','libx264',
                    '-preset','medium','-crf','18','-pix_fmt','yuv420p','-threads','2','-fps_mode','cfr','-r','25','-movflags','+faststart','study.mp4']
        record['command']=command
        encoded=subprocess.run(command,cwd=out,capture_output=True,text=True,timeout=60)
        (out/'encode.stdout.log').write_text(encoded.stdout,encoding='utf-8'); (out/'encode.stderr.log').write_text(encoded.stderr,encoding='utf-8')
        record['encodeReturnCode']=encoded.returncode; encoded.check_returncode()
        video=out/'study.mp4'
        probe=subprocess.run([str(encoder.with_name('ffprobe.exe')),'-v','error','-show_entries','format=duration,size:stream=codec_name,width,height,nb_frames,duration',
                              '-of','json',str(video)],capture_output=True,text=True,check=True,timeout=10)
        (out/'video-probe.json').write_text(probe.stdout,encoding='utf-8')
        record['video']={'file':'study.mp4','bytes':video.stat().st_size,'sha256':sha(video),'probe':json.loads(probe.stdout)}
        record['inspectionFrames']=[]
        for segment,timestamp in zip(plan['segments'],plan['inspectionSeconds']):
            name='check-'+segment['id']+'.png'
            subprocess.run([str(encoder),'-hide_banner','-loglevel','error','-nostdin','-ss',str(timestamp),'-i',str(video),'-frames:v','1',name],
                           cwd=out,capture_output=True,check=True,timeout=15)
            record['inspectionFrames'].append({'file':name,'seconds':timestamp,'sha256':sha(out/name)})
        record['status']='completed'
    except Exception as exc:
        record['status']='failed';record['error']=repr(exc);raise
    finally:
        record['sourceAfter']={str(p):sha(p) for p in pins};record['sourcesUnchanged']=record['sourceBefore']==record['sourceAfter']
        record['wallSeconds']=time.perf_counter()-started
        (out/'result.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':record.get('status'),'video':record.get('video'),'sourcesUnchanged':record['sourcesUnchanged'],'out':str(out)},ensure_ascii=False))

if __name__ == '__main__':
    main()
