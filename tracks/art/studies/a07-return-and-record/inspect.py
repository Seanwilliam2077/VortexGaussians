"""Inspect an already encoded A07 video. No encoding, browser or simulation."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OUT = HERE / 'run-01'
FFMPEG = Path('C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/Library/bin/ffmpeg.exe')
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__ == '__main__':
    if (OUT / 'inspection.json').exists():
        raise FileExistsError('Inspection already exists')
    original = json.loads((OUT / 'result.json').read_text(encoding='utf-8'))
    assert original['encodeReturnCode'] == 0
    video = OUT / 'study.mp4'
    plan = json.loads((HERE / 'edit-plan.json').read_text(encoding='utf-8'))
    command = [str(FFMPEG.with_name('ffprobe.exe')), '-v', 'error', '-show_entries',
               'format=duration,size:stream=codec_name,width,height,nb_frames,duration', '-of', 'flat', str(video)]
    probe = subprocess.run(command, capture_output=True, text=True, check=True, timeout=10)
    (OUT / 'video-probe-flat.txt').write_text(probe.stdout, encoding='utf-8')
    metadata = {}
    for line in probe.stdout.splitlines():
        if '=' in line:
            key, value = line.split('=', 1); metadata[key] = value.strip('"')
    for required in ['streams.stream.0.codec_name', 'streams.stream.0.width', 'streams.stream.0.height', 'streams.stream.0.nb_frames', 'format.duration', 'format.size']:
        if required not in metadata: raise ValueError('Missing probe key: ' + required)
    record = {'schema': 'a07-post-encode-inspection-v1', 'originalResultSHA256': SHA(OUT / 'result.json'),
              'originalStatus': original['status'], 'originalError': original.get('error'),
              'scope': 'Metadata and frame decode only after successful encoding; original failed metadata record unchanged',
              'videoSHA256Before': SHA(video), 'metadata': metadata, 'probeCommand': command, 'frames': []}
    for segment, timestamp in zip(plan['segments'], plan['inspectionSeconds']):
        name = 'check-' + segment['id'] + '.png'
        subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', '-nostdin', '-ss', str(timestamp), '-i', str(video),
                        '-frames:v', '1', name], cwd=OUT, capture_output=True, check=True, timeout=15)
        record['frames'].append({'file': name, 'seconds': timestamp, 'sha256': SHA(OUT / name)})
    record['allOriginalPinsStillMatch'] = all(SHA(path) == value for path, value in original['sourceAfter'].items())
    record['videoSHA256After'] = SHA(video)
    assert record['videoSHA256Before'] == record['videoSHA256After']
    assert record['allOriginalPinsStillMatch']
    record['status'] = 'decoded_and_authenticated'
    (OUT / 'inspection.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))
