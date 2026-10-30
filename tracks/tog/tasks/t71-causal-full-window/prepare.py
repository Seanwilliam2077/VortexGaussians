"""T71 root-invoked standard-library preparation. Default mode only prints the plan."""
import argparse
import ast
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK = HERE.relative_to(REPO).as_posix()
PARENT = '2d1c075d4c91fcb3e8118a39d176de86205d7fac'
BRANCH = 'research/dual-track-exploration'
MEMORY = 'tracks/tog/tasks/t57-finer-short-reference/memory.py'
MEMORY_ID = dict(bytes=2231, sha256='4b83a89eff664dc0d86fb0c71b39c99d71720c1d18c5f93557e279d0ca3745fd')
EXE = dict(path='C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    bytes=107312, sha256='5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e')
CHECKS = ['frozen_identity_runtime', 'rules_and_startup_regression',
    'complete_causal_paths_and_counts', 'path_and_checkpoint_evaluator',
    'reference_eligibility_and_score_integration', 'time_comparison_integration_and_moments',
    'complete_work_accounting', 'final_identity_preservation']
T70 = 'tracks/tog/tasks/t70-causal-projector-qualification'
T69 = 'tracks/tog/tasks/t69-causal-mixture-startup'
T60 = 'tracks/tog/tasks/t60-full-window-gaussian-screen'
T61 = 'tracks/tog/tasks/t61-saved-output-qualification'
INPUTS = [TASK + '/' + name for name in ('.gitignore', 'PROTOCOL.md', 'measure.py', 'scorer.py',
    'run_once.py', 'prepare.py', 'preflight.json')]
INPUTS += [T70 + '/' + name for name in ('physics.py', 'search.py', 'PROTOCOL.md', 'DECISION.md',
    'execution.json', 'input-manifest.json', 'audit-manifest.json', 'result.json')]
INPUTS += ['tracks/validation/t70-causal-projector-review.md']
INPUTS += [T69 + '/' + name for name in ('ANALYSIS.md', 'COMPARATOR.md')]
INPUTS += [T60 + '/' + name for name in ('execution.json', 'result.json', 'input-manifest.json',
    'local/S256.json', 'local/S128.json')]
INPUTS += [T60 + '/local/' + name + '-snapshot-' + str(index) + '.json'
    for name in ('S256', 'S128') for index in range(5)]
INPUTS += [T61 + '/' + name for name in ('result.json', 'execution.json', 'input-manifest.json', 'audit-manifest.json')]
INPUTS += ['tracks/validation/t61-saved-output-review.md', MEMORY,
    'tracks/tog/tasks/t55-axisymmetric-reference/TASK.md']
PRIOR_SCOPE = ['T56', 'T57', 'T58', 'T59', 'T60', 'T63', 'T65', 'T66', 'T68', 'T70']
SCORE_TIMES = [0.0, .25, .5, .75, 1.0]
RAW_ARRAY_NAMES = ['q', 'qr', 'qz', 'r', 'rc', 'z']


def identity(path):
    path = Path(path)
    if path.suffix.lower() in {'.npz', '.npy'}:
        raise ValueError('T71 forbids raw-array reads/hashes')
    digest, count = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
            count += len(block)
    return dict(bytes=count, sha256=digest.hexdigest())


def record(path):
    return dict(path=path, **identity(REPO / path))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)


def preflight():
    started = time.perf_counter()
    assert not (HERE / 'preflight.json').exists()
    assert identity(REPO / MEMORY) == MEMORY_ID
    spec = importlib.util.spec_from_file_location('t71_memory_preflight', REPO / MEMORY)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    host = observer.host_memory()
    result = dict(schema='t71-os-preflight-v1', created_utc=now(), memory=host,
        required_available_physical_bytes=1073741824,
        passed=host['available_physical_bytes'] >= 1073741824,
        python=platform.python_version(), executable=sys.executable,
        source=identity(REPO / MEMORY), preparation_script=identity(Path(__file__)),
        scientific_invocations=0, numerical_imports=0,
        elapsed_before_write_seconds=time.perf_counter() - started)
    write(HERE / 'preflight.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 2


def freeze():
    assert git('rev-parse', 'HEAD').decode().strip() == PARENT
    assert git('branch', '--show-current').decode().strip() == BRANCH
    assert not git('diff', '--name-only').strip() and not git('diff', '--cached', '--name-only').strip()
    for name in ('input-manifest.json', 'execution.json', 'local/execution-started.json',
                 'local/result.json', 'local/predictions.json', 'local/journal.jsonl', 'local/failure.json'):
        assert not (HERE / name).exists(), name
    entries = []
    for item in git('ls-tree', '-r', '-z', 'HEAD').split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            mode, kind, oid = meta.split()
            assert kind == b'blob'
            entries.append(dict(path=path.decode(), blob_id=oid.decode()))
    states = {'tracks/STATUS.md', 'tracks/EXPLORATION.md', 'tracks/tog/README.md'}
    other = [x for x in entries if x['path'] not in states]
    arrays = [x for x in other if Path(x['path']).suffix.lower() in {'.npz', '.npy'}]
    assert len(entries) == 1387 and len(other) == 1384 and len(arrays) == 18
    index = {}
    for item in git('ls-files', '--stage', '-z').split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            mode, oid, stage = meta.split()
            assert stage == b'0'
            index[path.decode()] = oid.decode()
    assert all(index[x['path']] == x['blob_id'] for x in entries)
    assert len(INPUTS) == len(set(INPUTS)) == 40
    inputs = [record(path) for path in sorted(INPUTS)]
    for name in ('scorer.py', 'measure.py', 'run_once.py', 'prepare.py'):
        source = (HERE / name).read_text(encoding='utf-8')
        ast.parse(source)
        if name == 'run_once.py':
            assert 'static adaptation incomplete' not in source
    pre = json.loads((HERE / 'preflight.json').read_bytes())
    assert pre['schema'] == 't71-os-preflight-v1' and pre['passed'] is True
    assert pre['source'] == MEMORY_ID
    assert pre['preparation_script'] == identity(Path(__file__))
    assert identity(Path(EXE['path'])) == {k: EXE[k] for k in ('bytes', 'sha256')}
    # Inherit ten raw identities from three saved metadata sources; never open NPZ.
    receipt = json.loads((REPO / T60 / 'execution.json').read_bytes())
    qualification = json.loads((REPO / T61 / 'result.json').read_bytes())
    qualification_freeze = json.loads((REPO / T61 / 'input-manifest.json').read_bytes())
    assert qualification['accepted_saved_evidence'] is True
    assert qualification['reference_qualified_full_window'] is True
    assert qualification['T60_history_reclassified'] is False
    assert qualification['original_failed_receipt'] == record(T60 + '/execution.json')
    assert qualification['original_numerical_result'] == record(T60 + '/result.json')
    assert qualification['input_manifest'] == identity(REPO / T61 / 'input-manifest.json')
    assert receipt['status'] == 'failed_result_validation_no_retry' and receipt['complete_result_validated'] is False
    old_inputs = {x['path']: x for x in qualification_freeze['inputs']}
    old_raw = {T60 + '/' + x['path']: dict(x, path=T60 + '/' + x['path']) for x in receipt['raw_files']}
    old_metadata = {T60 + '/' + x['path']: dict(x, path=T60 + '/' + x['path'])
        for x in receipt['validated_checkpoint_records']}
    reference_records, raw_inputs = [], []
    for name in ('S256', 'S128'):
        for index, score_time in enumerate(SCORE_TIMES):
            metadata_path = T60 + '/local/' + name + '-snapshot-' + str(index) + '.json'
            meta_identity = record(metadata_path)
            assert meta_identity == old_inputs[metadata_path] == old_metadata[metadata_path]
            metadata = json.loads((REPO / metadata_path).read_bytes())
            assert metadata['schema'] == 't60-partial-snapshot-v1'
            assert (metadata['name'], metadata['index'], metadata['time']) == (name, index, score_time)
            assert metadata['whole_task_qualified'] is False
            assert Path(metadata['raw']['path']).name == name + '-snapshot-' + str(index) + '.npz'
            raw_path = T60 + '/local/' + metadata['raw']['path']
            raw_identity = dict(metadata['raw'], path=raw_path)
            assert raw_identity == old_raw[raw_path] == old_inputs[raw_path]
            raw_inputs.append(raw_identity)
            reference_records.append(dict(name=name, index=index, time=score_time,
                raw=raw_identity, metadata=meta_identity))
    assert len(raw_inputs) == len({x['path'] for x in raw_inputs}) == 10
    result = dict(schema='t71-causal-full-window-freeze-v1', created_utc=now(), parent_commit=PARENT,
        inputs=inputs, raw_inputs=raw_inputs, reference_records=reference_records, executable=EXE,
        raw_identity_origin='T60 execution + snapshot metadata + T61 frozen qualification inputs; raw files not opened during freeze',
        prediction_source_paths=[T70 + '/physics.py', T70 + '/search.py'],
        post_prediction_reference_paths=[x['metadata']['path'] for x in reference_records],
        raw_array_names=RAW_ARRAY_NAMES, expected_python='3.12.14', expected_numpy='2.3.5',
        maximum_scientific_child_invocations=1, child_timeout_seconds=120,
        observed_peak_working_set_limit_bytes=536870912, required_available_physical_bytes=1073741824,
        memory_sample_interval_seconds=.25, expected_rule_orders=[2,3,6,8,12,16,64,96,128,192,256],
        expected_rule_nodes=783, expected_rule_eigh_calls=11, heat_orders=[64,128,256],
        step_sizes=[.0625,.03125], steps_per_path=[16,32], score_times=SCORE_TIMES,
        expected_projection_steps=48, expected_input_npz_files=10, expected_input_arrays=60,
        expected_check_names=CHECKS, dimensional_atol=1e-10, dimensional_rtol=1e-9,
        score_integration_atol=1e-8, physical_field_limit=.1, physical_centroid_limit=.1,
        physical_covariance_limit=.1, time_field_limit=.01, time_centroid_limit=.01,
        time_covariance_limit=.01, reference_field_limit=.01, reference_centroid_limit=.01,
        reference_covariance_limit=.01,
        search_caps_per_step=dict(proposals=2280, component_bases=1199, weight_control_attempts=9121,
            initial_pairs=1128, neighbor_proposals=1152, starts=4, levels=3, polls_per_level=8),
        search_total_caps=dict(proposals=109440, component_bases=57552,
            weight_control_attempts=437808, ordered_heat_integrals=230208),
        prior_scientific_child_seconds=1991.4691072998103,
        prior_evidence_qualification_seconds=.9663960000034422, prior_scientific_series_scope=PRIOR_SCOPE,
        prior_scientific_series_is_total_project_cost=False, preparation_scientific_invocations=0,
        preparation_raw_array_reads=0, preparation_raw_array_hashes=0,
        new_reference_trajectories_permitted=0, ordinary_causal_paths=2,
        parent_preservation=dict(tracked_count=1387, nonstate_count=1384, nonarray_nonstate_count=1366,
            historical_array_count=18, historical_array_paths_not_opened=arrays,
            git_tree_index_match=True, tracked_working_diff_empty=True,
            scope='Git metadata/status only here; complete publication byte preservation is separate'),
        freezer=record(TASK + '/prepare.py'))
    write(HERE / 'input-manifest.json', result)
    print(json.dumps(dict(inputs=len(inputs), manifest=record(TASK + '/input-manifest.json'))))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', nargs='?', choices=('plan', 'preflight', 'freeze'), default='plan')
    args = parser.parse_args()
    if args.mode == 'preflight':
        return preflight()
    if args.mode == 'freeze':
        return freeze()
    print(json.dumps(dict(task=TASK, parent_commit=PARENT, planned_inputs=INPUTS,
        raw_reference_files_inherited_only=10, maximum_scientific_child_invocations=1,
        execution='Not started; root must explicitly run preflight, then freeze after review.'), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
