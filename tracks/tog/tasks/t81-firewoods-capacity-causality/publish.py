"""Archive successful saved T81 numerical evidence; no browser or simulation."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path.cwd()
HERE = ROOT / 'tracks/tog/tasks/t81-firewoods-capacity-causality'
SOURCE = HERE / 'local/run-01'
DEST = HERE / 'public'
COLUMNS = ['id', 'fuelInitial', 'fuel', 'heat', 'char', 'glow', 'state']


def identity(raw):
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def save(name, raw):
    path = DEST / name
    if path.exists():
        if path.read_bytes() != raw:
            raise RuntimeError('Existing publication differs: ' + name)
    else:
        with path.open('xb') as handle:
            handle.write(raw)
    return {'file': name, **identity(raw)}


def main():
    report = json.loads((SOURCE / 'result.json').read_text())
    summary = json.loads((HERE / 'SUMMARY.json').read_text())
    if report['status'] != 'completed_capture_pending_saved_audit' or not summary['qualification'].startswith('passed_'):
        raise RuntimeError('Require complete capture and successful saved audit')
    manifest = {item['name']: item for item in report['files']}
    DEST.mkdir(exist_ok=True)
    entries = []
    for name, expected in manifest.items():
        is_log = name.endswith('-steps.jsonl.gz')
        is_state = any(name.endswith('-' + tag + '.json.gz') for tag in ['prefix', 'after-intervention', 'endpoint'])
        if not (is_log or is_state):
            continue
        raw = (SOURCE / name).read_bytes()
        if identity(raw) != {k: expected[k] for k in ['bytes', 'sha256']}:
            raise RuntimeError('Original capture identity differs: ' + name)
        decoded = gzip.decompress(raw)
        if identity(decoded) != {'bytes': expected['decoded_bytes'], 'sha256': expected['decoded_sha256']}:
            raise RuntimeError('Original decoded identity differs: ' + name)
        if is_log:
            entry = save(name, raw)
            entry.update(kind='lossless_original_step_log', decoded_bytes=len(decoded),
                         decoded_sha256=hashlib.sha256(decoded).hexdigest())
        else:
            state = json.loads(decoded)
            native = state['native']
            rows = [[point[key] for key in COLUMNS] for point in native['points']]
            if len(rows) != 34687 or len({row[0] for row in rows}) != 34687:
                raise RuntimeError('Material identity/count differs')
            projected = {
                'schema': 't81-public-dynamic-projection-v1',
                'frame': native['frame'], 'time': native['time'], 'seed': native['seed'],
                'original_native_hash': native['hash'],
                'original_particle_state_hash': native['particleStateHash'],
                'random_draws': native['randomDraws'],
                'material_columns': COLUMNS, 'material_rows': rows,
                'frontier': native['frontier'], 'emit_cursor': native['emitCursor'],
                'scene_aggregates': native['scene'], 'gas_aggregates': native['particles'],
                'counters': native['counters'], 'counters_by_group': native['countersByGroup'],
                'gas': state['gas'], 'policy': state['policy'],
                'fixed_B_indices': state['fixedBIndices'], 'newly_B_indices': state['newlyBIndices'],
                'observation_counters': state['observationCounters'],
                'scope': 'All recorded material dynamics and generated gas objects; external scene geometry/appearance/camera/images omitted. No restart API.'}
            output = (json.dumps(projected, separators=(',', ':'), allow_nan=False) + '\n').encode()
            packed = gzip.compress(output, compresslevel=9, mtime=0)
            if gzip.decompress(packed) != output:
                raise RuntimeError('Archive round trip differs')
            entry = save(name.replace('.json.gz', '.dynamic.json.gz'), packed)
            entry.update(kind='documented_dynamic_projection', decoded_bytes=len(output),
                         decoded_sha256=hashlib.sha256(output).hexdigest(), material_rows=len(rows),
                         gas_particles=sum(len(layer['particles']) for layer in state['gas']))
        entry['original'] = {'name': name, **identity(raw)}
        entries.append(entry)
    if len(entries) != 16:
        raise RuntimeError('Expected four logs and twelve checkpoints')
    result = {'schema': 't81-public-evidence-archive-v1', 'files': entries,
              'files_total': len(entries), 'bytes_total': sum(item['bytes'] for item in entries),
              'third_party_geometry_images_included': False,
              'gas_data': 'Project-generated particles, including their simulated coordinates and native fields.',
              'new_scientific_executions': 0,
              'limitations': ['Generated gas is recorded in full; static external scene geometry is omitted.',
                              'Native hashes cover selected fields; not a complete-state certificate.',
                              'Observation labels are emitter provenance, not unique heat-propagation ancestry.']}
    save('MANIFEST.json', (json.dumps(result, indent=2) + '\n').encode())
    print(json.dumps({'files': result['files_total'], 'bytes': result['bytes_total'], 'new_scientific_executions': 0}))


if __name__ == '__main__':
    main()
