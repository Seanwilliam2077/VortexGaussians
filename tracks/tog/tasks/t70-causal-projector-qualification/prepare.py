"""T70 root-invoked standard-library preparation. Default mode only prints the plan."""
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
PARENT = '2d8f9b771cea425ca22bc65d676c3a809a2dc376'
BRANCH = 'research/dual-track-exploration'
MEMORY = 'tracks/tog/tasks/t57-finer-short-reference/memory.py'
MEMORY_ID = dict(bytes=2231, sha256='4b83a89eff664dc0d86fb0c71b39c99d71720c1d18c5f93557e279d0ca3745fd')
EXE = dict(path='C:/Users/seanzjxiao/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
    bytes=107312, sha256='5640e9be2fd33d05a1a9ae1228e2354609a69ab831605995ec4e2bd6da8fff5e')
CHECKS = ['frozen_identity_runtime', 'rule_initial_operator', 'full_self_cross_evaluator',
    'independent_weight_controls', 'complete_prescribed_searches',
    'selected_direct_confirmation_moments', 'complete_work_accounting', 'final_identity_preservation']
SOURCE = 'tracks/tog/tasks/t69-causal-mixture-startup'
INPUTS = [TASK + '/' + name for name in ('.gitignore', 'PROTOCOL.md', 'physics.py', 'search.py',
    'measure.py', 'run_once.py', 'prepare.py', 'preflight.json')]
INPUTS += [SOURCE + '/' + name for name in ('.gitignore', 'README.md', 'ANALYSIS.md',
    'COMPARATOR.md', 'DECISION.md', 'evidence.json', 'audit-manifest.json')]
INPUTS += ['tracks/validation/t69-causal-mixture-review.md',
    'tracks/tog/tasks/t54-scalar-verification/result.json', MEMORY]
SCIENTIFIC_INPUTS = ['tracks/tog/tasks/t54-scalar-verification/result.json']
PRIOR_SCOPE = ['T56', 'T57', 'T58', 'T59', 'T60', 'T63', 'T65', 'T66', 'T68']


def identity(path):
    path = Path(path)
    if path.suffix.lower() in {'.npz', '.npy'}:
        raise ValueError('T70 forbids raw-array reads/hashes')
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
    spec = importlib.util.spec_from_file_location('t70_memory_preflight', REPO / MEMORY)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    host = observer.host_memory()
    result = dict(schema='t70-os-preflight-v1', created_utc=now(), memory=host,
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
                 'local/result.json', 'local/journal.jsonl', 'local/failure.json'):
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
    assert len(entries) == 1365 and len(other) == 1362 and len(arrays) == 18
    index = {}
    for item in git('ls-files', '--stage', '-z').split(b'\0'):
        if item:
            meta, path = item.split(b'\t', 1)
            mode, oid, stage = meta.split()
            assert stage == b'0'
            index[path.decode()] = oid.decode()
    assert all(index[x['path']] == x['blob_id'] for x in entries)
    assert len(INPUTS) == len(set(INPUTS)) == 18
    inputs = [record(path) for path in sorted(INPUTS)]
    for name in ('physics.py', 'search.py', 'measure.py', 'run_once.py', 'prepare.py'):
        source = (HERE / name).read_text(encoding='utf-8')
        ast.parse(source)
        if name == 'run_once.py':
            assert 'static adaptation incomplete' not in source
    pre = json.loads((HERE / 'preflight.json').read_bytes())
    assert pre['schema'] == 't70-os-preflight-v1' and pre['passed'] is True
    assert pre['source'] == MEMORY_ID
    assert pre['preparation_script'] == identity(Path(__file__))
    assert identity(Path(EXE['path'])) == {k: EXE[k] for k in ('bytes', 'sha256')}
    result = dict(schema='t70-causal-projector-freeze-v1', created_utc=now(), parent_commit=PARENT,
        inputs=inputs, executable=EXE, scientific_input_paths=SCIENTIFIC_INPUTS,
        expected_python='3.12.14', expected_numpy='2.3.5', maximum_scientific_child_invocations=1,
        child_timeout_seconds=120, observed_peak_working_set_limit_bytes=536870912,
        required_available_physical_bytes=1073741824, memory_sample_interval_seconds=.25,
        expected_rule_orders=[64, 96, 128, 192, 256], expected_rule_nodes=736, expected_rule_eigh_calls=5,
        heat_orders=[64, 128, 256], step_sizes=[.0625, .03125], expected_check_names=CHECKS,
        dimensional_atol=1e-10, dimensional_rtol=1e-9, dimensionless_atol=1e-8,
        search_caps_per_step=dict(proposals=2280, component_bases=1199, weight_control_attempts=9121,
            initial_pairs=1128, neighbor_proposals=1152, starts=4, levels=3, polls_per_level=8),
        fixed_work=dict(rule_count=5, rule_nodes=736, rule_eigh_calls=5, root_scalar_control_calls=7,
            phys_field_calls=30, phys_field_spatial_points=319566, phys_field_component_points=479349,
            phys_field_heat_integrand_points=71582784, phys_field_ordered_pair_points=798915,
            phys_initial_exact_calls=1, phys_initial_exact_points=13),
        total_work_caps=dict(search_proposals=4560, search_component_evaluations=2398,
            phys_cross_calls=2434, phys_cross_ordered_pair_integrals=2461, phys_cross_integrand_points=316352),
        prior_scientific_child_seconds=1990.3707298998488,
        prior_evidence_qualification_seconds=.9663960000034422, prior_scientific_series_scope=PRIOR_SCOPE,
        prior_scientific_series_is_total_project_cost=False, preparation_scientific_invocations=0,
        input_arrays_read=0, input_arrays_saved=0, new_flow_trajectories_permitted=0,
        parent_preservation=dict(tracked_count=1365, nonstate_count=1362, nonarray_nonstate_count=1344,
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
        scientific_input_paths=SCIENTIFIC_INPUTS, maximum_scientific_child_invocations=1,
        execution='Not started; root must explicitly run preflight, then freeze after review.'), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
