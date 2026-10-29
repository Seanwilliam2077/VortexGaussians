"""Literal persistence/classification tests, with no scientific-method calls.

Default invocation is plan-only. Explicit --execute imports only evidence.py
and operates in a cleaned system temporary directory. All old/new records are
format sentinels, not sampled rays or a model simulation. One explicitly named
nonphysical old-alpha mismatch covers the joint-classification branch only.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import time
import zlib


HERE = Path(__file__).resolve().parent
FLOATS = ('rgb_r', 'rgb_g', 'rgb_b', 'alpha', 'tau', 'ray_near', 'ray_far',
          'mass_bound', 'prune_delta', 'preparation_seconds', 'output_seconds',
          'comparison_seconds')
INTS = ('status', 'retained_count', 'arm_id', 'rgb_class', 'alpha_class', 'partition_ok')
FIELDS = FLOATS + INTS
NEW = struct.Struct('<12d6I')
OLD = struct.Struct('<31d10I')
DELIVERY = struct.Struct('<13d6I')
EPS = .0010000001

# Independent positional expectations, never constructed from module.FIELDS.
BLACK = (0., 0., 0., 0., 0., .125, 99.5, 0., 0., .01, .02, .03,
         1, 0, 0, 1, 1, 1)
HDR = (1.125, .625, 1.375, .75, 1.3862943611198906, .25, 123.125,
       0., 0., .01, .02, .03, 1, 2, 0, 1, 1, 1)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def payload(row, arm=0, rgb_class=None, alpha_class=None):
    changed = list(row)
    changed[14] = arm
    if rgb_class is not None:
        changed[15] = rgb_class
    if alpha_class is not None:
        changed[16] = alpha_class
    return {name: value for name, value in zip(FIELDS, changed) if name != 'status'}


def legacy_rows():
    # The old blue slot deliberately contains far; reference-blue slots 6/9
    # retain a distinct valid literal. No scene or historical binary is read.
    black = (0., 0., 99.5, 0., 0., 0., 0., 0., 0., 0.,
             0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
             0., 0., 0., 0., .125, 99.5, .01, .02, .03, .04, .05,
             1, 0, 1, 1, 0, 0, 0, 0, 0, 1)
    hdr = (1.125, .625, 123.125, .75,
           1.1248779296875, .6248779296875, 1.3748779296875,
           1.1251220703125, .6251220703125, 1.3751220703125,
           .75, .75, 0., 0., 0., 0., 0., 0., 0., 0.,
           0., 0., 0., 0., .25, 123.125, .01, .02, .03, .04, .05,
           1, 2, 3, 3, 8, 0, 0, 1, 0, 1)
    require(len(black) == len(hdr) == 41, 'Independent legacy field count')
    require(hdr[2] == hdr[25] != 1.375, 'Literal historical blue/far collision')
    require(black[3] == black[10] and hdr[3] == hdr[10], 'Ordinary sentinel alpha identity')
    return [black, hdr, black]


def legacy_bytes(rows):
    return b''.join(OLD.pack(*row) for row in rows)


def delivery_bytes():
    # The comparison reader is entitled only to committed display RGB here.
    black = (0., 0., 0., 0., .125, 99.5, 0., 0., .01, .02, .03,
             0., 0., 1, 0, 1, 0, 1, 1)
    hdr = (1.125, .625, 1.375, .75, .25, 123.125, 0., 0., .01, .02, .03,
           .0001220703125, 0., 1, 2, 3, 8, 1, 1)
    return DELIVERY.pack(*black) + DELIVERY.pack(*hdr) + DELIVERY.pack(*black)


def rejected(operation):
    try:
        operation()
    except (ValueError, TypeError, struct.error):
        return
    raise AssertionError('Malformed contract accepted')


def png_rgb(path):
    data = path.read_bytes()
    require(data[:8] == b'\x89PNG\r\n\x1a\n', 'PNG signature')
    position, shape, compressed, ended = 8, None, bytearray(), False
    while position < len(data):
        length = struct.unpack_from('>I', data, position)[0]
        tag = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        crc = struct.unpack_from('>I', data, position + 8 + length)[0]
        require((zlib.crc32(tag + body) & 0xffffffff) == crc, 'PNG CRC')
        position += length + 12
        if tag == b'IHDR':
            shape = struct.unpack('>IIBBBBB', body)
        elif tag == b'IDAT':
            compressed.extend(body)
        elif tag == b'IEND':
            ended = True
            break
    require(ended and position == len(data), 'PNG end')
    require(shape == (3, 1, 8, 2, 0, 0, 0), 'Literal PNG dimensions/layout')
    scan = zlib.decompress(compressed)
    require(len(scan) == 10 and scan[0] == 0, 'PNG filter/row')
    return bytes(scan[1:])


def load_storage():
    spec = importlib.util.spec_from_file_location('t37_literal_storage_only', HERE / 'evidence.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tests():
    started = time.perf_counter()
    paths = [HERE / 'evidence.py', Path(__file__).resolve()]
    before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    module = load_storage()
    cases = []

    def case(name, operation):
        try:
            operation()
            cases.append(dict(name=name, passed=True))
        except Exception as error:
            cases.append(dict(name=name, passed=False, error=type(error).__name__ + ': ' + str(error)))

    def schema():
        require(tuple(module.FLOAT_FIELDS) == FLOATS and tuple(module.INT_FIELDS) == INTS,
                'Exact independent field order')
        require(tuple(module.FIELDS) == FIELDS and len(set(module.FIELDS)) == 18, 'Unique 18 fields')
        require(module.RECORD.format == '<12d6I' and module.RECORD.size == 120, 'New record layout')
        require(module.LEGACY.format == '<31d10I' and module.LEGACY.size == 288, 'Legacy layout')
        require(module.DELIVERY.format == '<13d6I' and module.DELIVERY.size == 128, 'Display baseline layout')
        require(module.EPS == EPS and module.CLASSES == {1: 'qualified', 2: 'definite_failure', 3: 'unresolved'},
                'Independent classification constants')

    def roundtrip():
        named = dict(zip(FIELDS, HDR))
        encoded = module.encode(named)
        require(encoded == NEW.pack(*HDR), 'Independent positional bytes')
        require(module.decode(encoded) == named, 'Literal roundtrip')
        require(NEW.unpack(encoded)[2] == 1.375 and NEW.unpack(encoded)[6] == 123.125,
                'Distinct blue and far slots')

    case('unique_independent_schema', schema)
    case('literal_positional_HDR_roundtrip', roundtrip)
    for name, change in [
        ('missing_field', lambda row: row.pop('rgb_b')),
        ('ambiguous_extra_alias', lambda row: row.update(b=123.125)),
        ('bool_float', lambda row: row.update(rgb_b=True)),
        ('NaN_float', lambda row: row.update(rgb_b=float('nan'))),
        ('infinite_float', lambda row: row.update(rgb_b=float('inf'))),
        ('bool_integer', lambda row: row.update(retained_count=True)),
        ('float_integer', lambda row: row.update(retained_count=2.)),
        ('negative_integer', lambda row: row.update(retained_count=-1)),
        ('overflow_integer', lambda row: row.update(retained_count=2**32)),
    ]:
        row = dict(zip(FIELDS, HDR))
        change(row)
        case('reject_' + name, lambda value=row: rejected(lambda: module.encode(value)))
    for length in (0, 119, 121):
        case('reject_decode_length_' + str(length),
             lambda value=length: rejected(lambda: module.decode(bytes(value))))
    nonfinite = list(HDR)
    nonfinite[2] = float('nan')
    case('reject_nonfinite_saved_payload', lambda: rejected(lambda: module.decode(NEW.pack(*nonfinite))))

    def classes():
        old = legacy_rows()[0]
        require(module.classify([EPS, 0., 0.], 0., old)[:2] == (1, 1), 'Inclusive endpoint threshold')
        require(module.classify([EPS + 1e-12, 0., 0.], 0., old)[:2] == (2, 1), 'Strict outside threshold')
        require(module.classify([EPS - 1e-12, 0., 0.], 0., old)[:2] == (1, 1), 'Below endpoint threshold')
        wider = list(old)
        wider[7] = .003
        require(module.classify([.0015, 0., 0.], 0., wider)[:2] == (3, 1), 'Inside wide interval is unresolved')
        require(module.classify([0., 0., 0.], EPS, old)[1] == 1, 'Inclusive alpha threshold')
        require(module.classify([0., 0., 0.], EPS + 1e-12, old)[1] == 2, 'Strict alpha threshold')

    case('three_classes_and_literal_threshold_boundaries', classes)
    with tempfile.TemporaryDirectory(prefix='t37-storage-literal-') as temporary:
        base = Path(temporary)
        old = legacy_bytes(legacy_rows())
        delivery = delivery_bytes()

        def store(name):
            directory = base / name
            directory.mkdir()
            return directory, module.Evidence(directory, width=3, height=1)

        def finalize(directory, legacy=old, previous=delivery):
            return module.finalize(directory, [2., 2., 2.], 270, legacy, previous, .01,
                                   width=3, height=1)

        def write_pair(storage, alpha_class=1):
            storage.write_pixel(0, payload(BLACK))
            storage.write_pixel(1, payload(HDR, alpha_class=alpha_class))

        def valid_partial():
            directory, storage = store('valid-partial')
            try:
                rejected(lambda: storage.write_pixel(1, payload(BLACK)))
                rejected(lambda: storage.write_pixel(True, payload(BLACK)))
                rejected(lambda: storage.write_pixel(0, dict(payload(BLACK), status=1)))
                require((directory / 'pixels.bin').read_bytes() == bytes(6 * 120), 'Rejected write leaves zero slots')
                write_pair(storage)
            finally:
                storage.close()
            saved = (directory / 'pixels.bin').read_bytes()
            require(len(saved) == 720 and NEW.unpack_from(saved) == BLACK, 'Actual black slot')
            require(NEW.unpack_from(saved, 120) == HDR and saved[240:] == bytes(480), 'Actual HDR/unfinished slots')
            result = finalize(directory)
            summary = result['summary']
            require(summary['committed_records'] == summary['valid_records'] == 2, 'Literal committed records')
            require(summary['invalid_saved_records'] == summary['failed_records'] == 0
                    and summary['uncomputed_records'] == 4, 'Uncomputed records are not black')
            require(summary['saved_validation_pass'] and not summary['all_records_valid']
                    and not summary['any_arm_all_pixels_qualified'], 'Partial is not a whole-frame claim')
            require(summary['arms']['sorted']['rgb_max'] == [1.125, .625, 1.375], 'HDR preserved in summary')
            rgb = png_rgb(directory / 'sorted-rgb.png')
            mask = png_rgb(directory / 'sorted-classification.png')
            require(rgb[:3] == bytes(3) and mask[:3] == bytes([0, 160, 0]), 'Valid black display')
            require(rgb[6:] == bytes([255, 0, 255]) and mask[6:] == bytes([255, 0, 255]), 'Unfinished display')
            require(rgb[5] > rgb[3] > rgb[4], 'Distinct decoded HDR channel order')
            require(png_rgb(directory / 'mixture-classification.png') == bytes([255, 0, 255]) * 3,
                    'Second arm remains unfinished')

        def mutate_rejected(name, offset, data, expected_check):
            directory, storage = store(name)
            try:
                write_pair(storage)
            finally:
                storage.close()
            with (directory / 'pixels.bin').open('r+b') as stream:
                stream.seek(120 + offset)
                require(stream.write(data) == len(data), 'Actual mutation write')
            summary = finalize(directory)['summary']
            require(not summary['saved_validation_pass'] and summary['invalid_saved_records'] == 1,
                    'Saved mutation must be invalid')
            bad = next(record for record in summary['failures'] if record['record_index'] == 1)
            require(expected_check in bad['failed_checks'], 'Specific mutation gate')
            require(png_rgb(directory / 'sorted-rgb.png')[3:6] == bytes([255, 0, 255]),
                    'Invalid data must not be displayed as qualified')

        def complete_three_classes():
            rows = [list(row) for row in legacy_rows()]
            rows[1][4], rows[1][7] = 1.1198779296875, 1.1201220703125
            rows[2][7] = .003
            directory, storage = store('complete-three-classes')
            try:
                for arm in range(2):
                    storage.write_pixel(arm * 3, payload(BLACK, arm=arm))
                    storage.write_pixel(arm * 3 + 1, payload(HDR, arm=arm, rgb_class=2))
                    storage.write_pixel(arm * 3 + 2, payload(BLACK, arm=arm, rgb_class=3))
            finally:
                storage.close()
            summary = finalize(directory, legacy_bytes(rows))['summary']
            require(summary['all_records_valid'] and summary['valid_records'] == 6
                    and not summary['any_arm_all_pixels_qualified'], 'Accuracy failures remain valid evidence')
            for arm in ('sorted', 'mixture'):
                s = summary['arms'][arm]
                require((s['qualified'], s['definite_failure'], s['unresolved']) == (1, 1, 1), 'Three-class counts')
                require(s['definite_failure_bbox'] == [1, 0, 1, 0], 'Literal definite-failure location')
                require(png_rgb(directory / (arm + '-classification.png')) ==
                        bytes([0, 160, 0, 255, 0, 0, 255, 200, 0]), 'Independent class colors')

        def nonphysical_alpha_joint_branch():
            # Explicitly not a legitimate inherited scene: old ordinary alpha
            # remains .75 while old full alpha is changed to .74 only to reach
            # the valid-record joint-classification branch with RGB qualified.
            rows = [list(row) for row in legacy_rows()]
            rows[1][10] = .74
            directory, storage = store('nonphysical-alpha-branch')
            try:
                write_pair(storage, alpha_class=2)
            finally:
                storage.close()
            summary = finalize(directory, legacy_bytes(rows))['summary']
            s = summary['arms']['sorted']
            require(summary['saved_validation_pass'] and s['valid_pixels'] == 2, 'Literal branch inputs recorded')
            require(s['rgb_classes']['qualified'] == 2 and s['alpha_failed'] == 1
                    and s['qualified'] == 1 and s['definite_failure'] == 1, 'Alpha vetoes RGB-qualified joint result')
            require(png_rgb(directory / 'sorted-classification.png')[3:6] == bytes([255, 0, 0]), 'Alpha failure display')

        def failed_marker_and_extents():
            directory, storage = store('failed-marker')
            try:
                storage.write_pixel(0, payload(BLACK))
                storage.mark_failed(1)
            finally:
                storage.close()
            saved = (directory / 'pixels.bin').read_bytes()
            require(NEW.unpack_from(saved, 120)[12] == 2 and NEW.unpack_from(saved, 240)[12] == 0,
                    'Failure and uncomputed remain distinct')
            rejected(lambda: finalize(directory, old[:-1]))
            rejected(lambda: finalize(directory, previous=delivery[:-1]))
            summary = finalize(directory)['summary']
            require((summary['valid_records'], summary['failed_records'], summary['uncomputed_records']) == (1, 1, 4),
                    'Failure/unfinished accounting')
            require(not summary['all_records_valid'], 'Failure prevents a completed delivery')

        case('actual_black_HDR_roundtrip_and_unfinished_two_arms', valid_partial)
        case('actual_saved_blue_equals_far_rejected',
             lambda: mutate_rejected('blue-corruption', 16, struct.pack('<d', 123.125), 'output_range'))
        case('actual_saved_forged_class_rejected',
             lambda: mutate_rejected('class-corruption', 108, struct.pack('<I', 2), 'classification'))
        case('complete_two_arm_three_class_literal_accounting', complete_three_classes)
        case('nonphysical_literal_alpha_joint_veto', nonphysical_alpha_joint_branch)
        case('failed_marker_and_source_extent_rejection', failed_marker_and_extents)
    after = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    case('sources_unchanged', lambda: require(before == after, 'Source changed during literal test'))
    return dict(schema='t37-independent-literal-storage-test-v1',
                passed=bool(cases) and all(row['passed'] for row in cases),
                test_count=len(cases), failure_count=sum(not row['passed'] for row in cases),
                tests=cases, source_sha256_before=before, source_sha256_after=after,
                temporary_directory_cleaned=not base.exists(), temporary_files_inside_scientific_run=False,
                scientific_evaluations=0, methods_imports=0, scene_imports=0, kernel_imports=0,
                projection_imports=0, quadrature_imports=0, reference_imports=0,
                persistence_scalar_alpha_consistency_check=True, nonphysical_literal_alpha_branch=True,
                sentinel_dimensions=[3, 1], sentinel_arms=2, elapsed_seconds=time.perf_counter() - started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(dict(mode='plan_only', scientific_evaluations=0,
                              requires='Explicit authorization and new --out report path')))
        return 0
    if args.out is None or args.out.exists():
        parser.error('--out must be a new report path')
    with args.out.open('x', encoding='utf-8', newline='\n') as output:
        try:
            report = run_tests()
        except Exception as error:
            report = dict(schema='t37-independent-literal-storage-test-v1', passed=False,
                          error=type(error).__name__ + ': ' + str(error), scientific_evaluations=0)
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps({key: report.get(key) for key in ('passed', 'test_count', 'failure_count', 'error')}))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
