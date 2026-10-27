"""One explicit CPU copy from authenticated T12 evidence; no simulation/Torch."""
import argparse
import hashlib
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 't12-ordinary-wind-response-extrema'
SUMMARY_SHA = '8448f30f7a59e8a9332a714799d1f10ed1f0a1d20f23bef9bcff096fbd7cb229'
SELECTION = {
    'reference.npz': {'rho0': 'rho0', 'initial_velocity': 'seed_velocity',
                      'seed_theta': 'seed_theta', 'wind': 'wind', 'potential': 'potential',
                      'observed_uint8': 'observed_uint8', 'lower': 'lower', 'upper': 'upper',
                      'denominator': 'denominator'},
    'qualification/analytic.npz': {'theta': 'start_theta'},
    'qualification/direction-0.npz': {'direction': 'direction0'},
    'qualification/direction-1.npz': {'direction': 'direction1'},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'mode': 'plan', 'selection': SELECTION, 'summarySHA256': SUMMARY_SHA,
                          'note': 'Explicit CPU-only copy; requires original local T12 raw once.'}, indent=2))
        return
    import numpy as np
    tick = time.perf_counter()
    target, manifest_path = HERE / 'inputs.npz', HERE / 'inputs-manifest.json'
    if target.exists() or manifest_path.exists():
        raise FileExistsError('Input pack/manifest already exists; no overwrite')
    root = OLD / 'runs/run-01/worker'
    summary_path = root / 'summary.json'
    if sha(summary_path) != SUMMARY_SHA:
        raise ValueError('Original summary SHA mismatch')
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    if not (summary['status'] == 'completed' and summary['sourcesUnchanged']
            and summary['runtimeInputsUnchanged'] and summary['qualification']['passed']):
        raise ValueError('Original T12 evidence is incomplete or changed')
    packed, records, original = {}, {}, {}
    for filename, keys in SELECTION.items():
        path = root / filename
        descriptor = summary['raw'][filename]
        if sha(path) != descriptor['sha256']:
            raise ValueError('Original NPZ SHA mismatch: ' + filename)
        original[filename] = {'sha256': descriptor['sha256'], 'bytes': path.stat().st_size}
        with np.load(path, allow_pickle=False) as archive:
            for source_key, target_key in keys.items():
                value = np.ascontiguousarray(archive[source_key])
                actual = {'shape': list(value.shape), 'dtype': value.dtype.str,
                          'rawSHA256': hashlib.sha256(value.tobytes()).hexdigest()}
                if actual != descriptor['arrays'][source_key]:
                    raise ValueError('Original array descriptor mismatch: ' + source_key)
                if value.dtype.hasobject or not np.isfinite(value).all():
                    raise ValueError('Unsafe/nonfinite input')
                packed[target_key] = value.copy()
                records[target_key] = dict(actual, sourceFile=filename, sourceKey=source_key)
    with target.open('xb') as stream:
        np.savez_compressed(stream, **packed)
    # One readback proves the portable pack preserved the selected dtype/bytes.
    with np.load(target, allow_pickle=False) as archive:
        if set(archive.files) != set(packed):
            raise ValueError('Pack keys differ')
        for key, value in packed.items():
            copied = archive[key]
            if copied.dtype != value.dtype or copied.shape != value.shape or copied.tobytes() != value.tobytes():
                raise ValueError('Pack byte-copy mismatch: ' + key)
    unchanged = sha(summary_path) == SUMMARY_SHA and all(sha(root / name) == row['sha256'] for name, row in original.items())
    result = {'schema': 't13-portable-inputs-v1', 'status': 'prepared',
              'producerSHA256': sha(__file__), 'sourceTask': OLD.name,
              'sourceSummarySHA256': SUMMARY_SHA, 'originalFiles': original,
              'originalEvidence': {'status': summary['status'], 'sourcesUnchanged': summary['sourcesUnchanged'],
                                   'runtimeInputsUnchanged': summary['runtimeInputsUnchanged'],
                                   'G0Passed': summary['qualification']['passed']},
              'pack': {'path': target.name, 'sha256': sha(target), 'bytes': target.stat().st_size},
              'arrays': records, 'sourcesUnchangedAfter': unchanged,
              'secondsCPUCopyIncludingIO': time.perf_counter() - tick,
              'simulationEvaluations': 0, 'scope': 'Byte-preserving selected-array copy; not a new reference or trajectory.'}
    manifest_path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not unchanged:
        raise ValueError('Original evidence changed during copy')
    print(json.dumps({'status': result['status'], 'bytes': result['pack']['bytes'],
                      'sha256': result['pack']['sha256'], 'manifestSHA256': sha(manifest_path)}))


if __name__ == '__main__':
    main()
