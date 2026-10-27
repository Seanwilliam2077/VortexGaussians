"""A05: CPU-only editorial crop/hold/text from one pinned existing A04 MP4."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', default='run-01')
    args = parser.parse_args()
    plan = json.loads((HERE / 'edit-plan.json').read_text(encoding='utf-8'))
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=False, indent=2)); return
    out = (HERE / args.out).resolve()
    if out.parent != HERE or out == HERE:
        raise ValueError('Output must be a fresh immediate child directory')
    out.mkdir()
    ffmpeg = Path(os.environ.get('FFMPEG_EXECUTABLE', 'C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe'))
    ffprobe = ffmpeg.with_name('ffprobe.exe')
    font = Path(os.environ.get('A05_FONT', 'C:/Windows/Fonts/msyh.ttc'))
    source = (HERE / plan['source']).resolve()
    source_result = (HERE / plan['sourceResult']).resolve()
    pins = [source, source_result, HERE / 'INTENT.md', HERE / 'edit-plan.json', Path(__file__), font, ffmpeg]
    record = {'schema': 'a05-edit-v1', 'scope': 'Agent-edited creative storyboard draft, not real-time recording or human feedback',
              'plan': plan, 'sourceBefore': {str(p): SHA(p) for p in pins}, 'browserOpened': False, 'simulationExecuted': False}
    started = time.perf_counter()
    try:
        assert SHA(source) == plan['sourceSHA256']
        assert SHA(source_result) == plan['sourceResultSHA256']
        record['encoderVersion'] = subprocess.run([str(ffmpeg), '-version'], capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()[0]
        font_filter = font.as_posix().replace(':', '\\:')
        (out / 'footer.txt').write_text(plan['footer'], encoding='utf-8')
        chains = ['[0:v]split=3[s0][s1][s2]']
        for index, segment in enumerate(plan['segments']):
            for kind in ['title', 'subtitle']:
                (out / f'{segment["id"]}-{kind}.txt').write_text(segment[kind], encoding='utf-8')
            x, y, width, height = segment['crop']
            hold = segment['duration'] - (segment['end'] - segment['start'])
            assert hold >= 0
            chain = (f'[s{index}]trim=start={segment["start"]}:end={segment["end"]},setpts=PTS-STARTPTS,'
                     f'crop={width}:{height}:{x}:{y},scale=960:600:force_original_aspect_ratio=decrease:force_divisible_by=2,'
                     f'pad=960:600:(ow-iw)/2:(oh-ih)/2:color=0x141512,setsar=1,fps=25,'
                     f'tpad=stop_mode=clone:stop_duration={hold:.6f},trim=duration={segment["duration"]},setpts=PTS-STARTPTS,'
                     'pad=1024:800:32:110:color=0x141512,')
            text_base = f"drawtext=fontfile='{font_filter}':expansion=none:fontcolor=0xf2eadc:"
            chain += text_base + f'textfile={segment["id"]}-title.txt:fontsize=32:x=32:y=26,'
            chain += text_base + f'textfile={segment["id"]}-subtitle.txt:fontsize=19:x=32:y=72,'
            chain += text_base + f'textfile=footer.txt:fontsize=17:x=32:y=750[v{index}]'
            chains.append(chain)
        chains.append('[v0][v1][v2]concat=n=3:v=1:a=0[outv]')
        (out / 'filter.ffscript').write_text(';\n'.join(chains) + '\n', encoding='utf-8')
        command = [str(ffmpeg), '-hide_banner', '-nostdin', '-i', str(source), '-filter_complex_script', 'filter.ffscript',
                   '-map', '[outv]', '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                   '-threads', '2', '-fps_mode', 'cfr', '-r', '25', '-movflags', '+faststart', 'study.mp4']
        record['command'] = command
        encoded = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=60)
        (out / 'encode.stdout.log').write_text(encoded.stdout, encoding='utf-8')
        (out / 'encode.stderr.log').write_text(encoded.stderr, encoding='utf-8')
        record['encodeReturnCode'] = encoded.returncode
        encoded.check_returncode()
        video = out / 'study.mp4'
        probe = subprocess.run([str(ffprobe), '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_name,width,height,nb_frames,duration',
                                '-of', 'json', str(video)], capture_output=True, text=True, check=True, timeout=10)
        (out / 'video-probe.json').write_text(probe.stdout, encoding='utf-8')
        record['video'] = {'file': 'study.mp4', 'bytes': video.stat().st_size, 'sha256': SHA(video), 'probe': json.loads(probe.stdout)}
        record['inspectionFrames'] = []
        for segment, timestamp in zip(plan['segments'], plan['inspectionSeconds']):
            name = f'check-{segment["id"]}.png'
            subprocess.run([str(ffmpeg), '-hide_banner', '-loglevel', 'error', '-nostdin', '-ss', str(timestamp), '-i', str(video),
                            '-frames:v', '1', name], cwd=out, capture_output=True, check=True, timeout=15)
            record['inspectionFrames'].append({'file': name, 'seconds': timestamp, 'sha256': SHA(out / name)})
        record['status'] = 'completed'
    except Exception as exc:
        record['status'] = 'failed'; record['error'] = repr(exc)
        raise
    finally:
        record['sourceAfter'] = {str(p): SHA(p) for p in pins}
        record['sourcesUnchanged'] = record['sourceBefore'] == record['sourceAfter']
        record['wallSeconds'] = time.perf_counter() - started
        (out / 'result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': record.get('status'), 'video': record.get('video'), 'sourcesUnchanged': record['sourcesUnchanged'], 'out': str(out)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
