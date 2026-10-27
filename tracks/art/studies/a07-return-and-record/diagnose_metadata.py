"""Read saved A07 records only; no probe, decode, encode or simulation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'run-01'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

if __name__ == '__main__':
    dest = OUT / 'inspection-addendum.json'
    if dest.exists():
        raise FileExistsError(dest)
    original = json.loads((OUT / 'result.json').read_text(encoding='utf-8'))
    inspection = json.loads((OUT / 'inspection.json').read_text(encoding='utf-8'))
    paths = list(original['sourceBefore']) + [str(HERE / 'inspect.py'), str(HERE / 'diagnose_metadata.py'), str(OUT / 'result.json'), str(OUT / 'inspection.json'), str(OUT / 'study.mp4')]
    before = {p: sha(p) for p in paths}
    raw = (OUT / 'video-probe.json').read_bytes()
    try:
        json.loads(raw)
        parse_error = None
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    ffmpeg = inspection['probeCommand'][0].replace('ffprobe.exe', 'ffmpeg.exe')
    commands = [[ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-ss', str(row['seconds']), '-i', str(OUT / 'study.mp4'), '-frames:v', '1', row['file']] for row in inspection['frames']]
    result = {
        'scope': 'Read-only supplement; no additional media process executed',
        'sourceBefore': before,
        'originalSourceBefore': original['sourceBefore'],
        'originalSourceAfter': original['sourceAfter'],
        'originalSourcePinsMatchCurrent': all(before[p] == value == original['sourceAfter'][p] for p, value in original['sourceBefore'].items()),
        'priorInspectionCommands': {'probe': inspection['probeCommand'], 'decode': commands, 'decodeWorkingDirectory': str(OUT), 'provenance': 'Reconstructed exactly from executed inspect.py loop and its recorded timestamps, not a new execution'},
        'originalProbe': {'sha256': sha(OUT / 'video-probe.json'), 'bytes': len(raw), 'tailUtf8': raw[-120:].decode('utf-8'), 'parseError': parse_error},
        'diagnosis': 'Saved stdout closes the inner format object but lacks the final outer JSON brace. edit.py saves probe.stdout without slicing before json.loads. Available records do not establish why that stdout is incomplete; cause unknown. The alternate flat probe does not resolve that cause.',
        'metadataAndFrameHashes': {'metadata': inspection['metadata'], 'frames': inspection['frames']},
        'videoSHA256': sha(OUT / 'study.mp4'),
    }
    result['sourceAfter'] = {p: sha(p) for p in paths}
    result['sourcesUnchanged'] = result['sourceBefore'] == result['sourceAfter']
    assert result['sourcesUnchanged'] and result['originalSourcePinsMatchCurrent']
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(dest), 'sha256': sha(dest), 'sourcesUnchanged': True}))
