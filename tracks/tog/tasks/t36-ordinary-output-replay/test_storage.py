"""Independent literal-data storage tests; no scene or scientific evaluation.

Default invocation prints a plan. --execute imports only the new persistence
module and operates in an automatically cleaned system temporary directory.
The legacy records below are format sentinels, not a simulated physical scene.
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
EXPECTED_FLOATS = ('rgb_r', 'rgb_g', 'rgb_b', 'alpha', 'ray_near', 'ray_far',
                   'mass_bound', 'prune_delta', 'preparation_seconds',
                   'ordinary_seconds', 'comparison_seconds',
                   'max_endpoint_error', 'alpha_error')
EXPECTED_INTS = ('status', 'retained_count', 'ordinary_path', 'gl_order',
                 'partition_ok', 'replay_match')
EXPECTED = EXPECTED_FLOATS + EXPECTED_INTS
NEW = struct.Struct('<13d6I')
OLD = struct.Struct('<31d10I')

# Independent positional expectations: RGB occupies slots 0..2, clips 4..5,
# and status 13. Do not derive these tuples from the implementation's schema.
BLACK = (0., 0., 0., 0., .125, 99.5, 0., 0., .01, .02, .03, 0., 0.,
         1, 0, 1, 0, 1, 1)
HDR = (1.125, .625, 1.375, .75, .25, 123.125, 0., 0., .01, .02, .03,
       .0001220703125, 0., 1, 2, 3, 8, 1, 1)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def payload(positional):
    return {name: value for name, value in zip(EXPECTED, positional) if name != 'status'}


def legacy_records():
    # Explicit old positions. Slot 2 deliberately contains old far clip;
    # independent blue reference endpoints remain in slots 6 and 9.
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
    require(len(black) == len(hdr) == 41, 'Independent legacy sentinel length')
    require(hdr[2] == hdr[25] != 1.375, 'Legacy sentinel must include the historical collision')
    require(hdr[6] < 1.375 < hdr[9], 'Independent legacy blue endpoints')
    return OLD.pack(*black) + OLD.pack(*hdr) + OLD.pack(*black)


def rejected(function):
    try:
        function()
    except (ValueError, TypeError, struct.error):
        return
    raise AssertionError('Malformed input was accepted')


def png_rgb(path):
    """Decode actual saved PNG bytes independently; no field/display rendering."""
    data = path.read_bytes()
    require(data[:8] == b'\x89PNG\r\n\x1a\n', 'PNG signature')
    position, shape, compressed, ended = 8, None, bytearray(), False
    while position < len(data):
        length = struct.unpack_from('>I', data, position)[0]
        tag = data[position + 4:position + 8]
        body = data[position + 8:position + 8 + length]
        checksum = struct.unpack_from('>I', data, position + 8 + length)[0]
        require((zlib.crc32(tag + body) & 0xffffffff) == checksum, 'PNG CRC')
        position += length + 12
        if tag == b'IHDR':
            shape = struct.unpack('>IIBBBBB', body)
        elif tag == b'IDAT':
            compressed.extend(body)
        elif tag == b'IEND':
            ended = True
            break
    require(ended and position == len(data), 'PNG end')
    require(shape == (3, 1, 8, 2, 0, 0, 0), 'Literal 3 x 1 PNG layout')
    scan = zlib.decompress(compressed)
    require(len(scan) == 10 and scan[0] == 0, 'PNG row/filter')
    return bytes(scan[1:])


def load_storage():
    spec = importlib.util.spec_from_file_location('t36_sentinel_storage_only', HERE / 'evidence.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_tests():
    started = time.perf_counter()
    paths = [HERE / 'evidence.py', Path(__file__).resolve()]
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    module = load_storage()
    cases = []

    def case(name, operation):
        try:
            operation()
            cases.append({'name': name, 'pass': True})
        except Exception as error:
            cases.append({'name': name, 'pass': False,
                          'error': type(error).__name__ + ': ' + str(error)})

    def schema():
        require(tuple(module.FLOAT_FIELDS) == EXPECTED_FLOATS, 'Exact independent float order')
        require(tuple(module.INT_FIELDS) == EXPECTED_INTS, 'Exact independent integer order')
        require(tuple(module.FIELDS) == EXPECTED, 'Exact combined field order')
        require(len(module.FIELDS) == len(set(module.FIELDS)) == 19, 'Unique field names')
        require(module.RECORD.format == '<13d6I' and module.RECORD.size == 128, 'Independent record format')
        require(module.LEGACY.format == '<31d10I' and module.LEGACY.size == 288, 'Independent legacy format')

    def literal_roundtrip():
        named = dict(zip(EXPECTED, HDR))
        encoded = module.encode(named)
        require(encoded == NEW.pack(*HDR), 'Bytes must match independent positional HDR tuple')
        decoded = module.decode(encoded)
        require(decoded == named, 'Named decode must preserve every literal')
        require(decoded['rgb_b'] == 1.375 and decoded['ray_far'] == 123.125,
                'Blue must remain distinct from far clip')

    case('unique_independent_schema', schema)
    case('literal_HDR_positional_roundtrip', literal_roundtrip)
    bad_values = [
        ('missing_field', lambda p: p.pop('rgb_b')),
        ('extra_ambiguous_alias', lambda p: p.update(b=123.125)),
        ('bool_float', lambda p: p.update(rgb_b=True)),
        ('NaN_float', lambda p: p.update(rgb_b=float('nan'))),
        ('bool_integer', lambda p: p.update(retained_count=True)),
        ('float_integer', lambda p: p.update(retained_count=2.0)),
        ('negative_integer', lambda p: p.update(retained_count=-1)),
        ('overflow_integer', lambda p: p.update(retained_count=2**32)),
    ]
    for name, modify in bad_values:
        malformed = dict(zip(EXPECTED, HDR))
        modify(malformed)
        case('reject_' + name, lambda p=malformed: rejected(lambda: module.encode(p)))
    for length in (0, 127, 129):
        case('reject_decode_length_' + str(length),
             lambda n=length: rejected(lambda: module.decode(bytes(n))))
    nonfinite = list(HDR)
    nonfinite[2] = float('nan')
    case('reject_nonfinite_saved_payload', lambda: rejected(lambda: module.decode(NEW.pack(*nonfinite))))

    with tempfile.TemporaryDirectory(prefix='t36-storage-sentinel-') as temporary:
        base = Path(temporary)
        old = legacy_records()

        def new_store(name):
            directory = base / name
            directory.mkdir()
            return directory, module.Evidence(directory, width=3, height=1)

        def finalize(directory, legacy=old):
            return module.finalize(directory, [2., 2., 2.], 270, legacy, .01,
                                   width=3, height=1)

        def valid_black_and_unfinished():
            directory, storage = new_store('valid')
            try:
                rejected(lambda: storage.write_pixel(1, payload(BLACK)))
                rejected(lambda: storage.write_pixel(True, payload(BLACK)))
                rejected(lambda: storage.write_pixel(0, dict(payload(BLACK), status=1)))
                require((directory / 'pixels.bin').read_bytes() == bytes(3 * 128),
                        'Rejected commits must leave all slots uncomputed')
                storage.write_pixel(0, payload(BLACK))
                storage.write_pixel(1, payload(HDR))
            finally:
                storage.close()
            saved = (directory / 'pixels.bin').read_bytes()
            require(len(saved) == 3 * 128, 'Fixed small image extent')
            require(NEW.unpack_from(saved, 0) == BLACK, 'Actual black positional readback')
            require(NEW.unpack_from(saved, 128) == HDR, 'Actual HDR positional readback')
            require(saved[256:] == bytes(128), 'Unfinished slot remains status zero')
            result = finalize(directory)
            summary = result['summary']
            require(summary['committed_pixels'] == summary['qualified_pixels'] == 2,
                    'Both committed literal outputs qualify')
            require(summary['invalid_saved_pixels'] == summary['failed_pixels'] == 0
                    and summary['uncomputed_pixels'] == 1, 'Unfinished is not valid black')
            require(summary['saved_validation_pass'] and not summary['all_pixel_records_qualified'],
                    'Valid partial evidence must not claim a full frame')
            require(summary['rgb_max'] == [1.125, .625, 1.375], 'HDR blue retained in summary')
            rgb, mask = png_rgb(directory / 'rgb.png'), png_rgb(directory / 'valid.png')
            require(rgb[:3] == b'\0\0\0' and mask[:3] == b'\xff\xff\xff', 'Valid black display')
            require(rgb[6:] == b'\xff\0\xff' and mask[6:] == b'\0\0\0', 'Uncomputed display')
            require(rgb[5] > rgb[3] > rgb[4] and mask[3:6] == b'\xff\xff\xff',
                    'Decoded display preserves distinct HDR channel order')

        def corrupted_blue_rejected():
            directory, storage = new_store('blue-corruption')
            try:
                storage.write_pixel(0, payload(BLACK))
                storage.write_pixel(1, payload(HDR))
            finally:
                storage.close()
            # Corrupt the actual saved blue slot, not just the input dictionary.
            with (directory / 'pixels.bin').open('r+b') as stream:
                stream.seek(128 + 2 * 8)
                require(stream.write(struct.pack('<d', 123.125)) == 8, 'Mutation write')
            saved = NEW.unpack_from((directory / 'pixels.bin').read_bytes(), 128)
            require(saved[2] == saved[5] == 123.125, 'Actual blue=far mutation')
            summary = finalize(directory)['summary']
            require(not summary['saved_validation_pass'] and summary['invalid_saved_pixels'] == 1,
                    'Persisted corruption must fail saved gates')
            require(summary['qualified_pixels'] == 1 and not summary['all_pixel_records_qualified'],
                    'Committed corruption must not count as qualified')
            bad = next(item for item in summary['failures'] if item['pixel_index'] == 1)
            require({'output_range', 'endpoint_alpha', 'reported_error'} <= set(bad['failed_checks']),
                    'Independent range, endpoint and recorded-error gates must catch corruption')
            require(png_rgb(directory / 'rgb.png')[3:6] == b'\xff\0\xff'
                    and png_rgb(directory / 'valid.png')[3:6] == b'\0\0\0',
                    'Invalid persisted output must not receive a valid display')

        def failed_marker_and_extent():
            directory, storage = new_store('failed-marker')
            try:
                storage.write_pixel(0, payload(BLACK))
                storage.mark_failed(1)
            finally:
                storage.close()
            saved = (directory / 'pixels.bin').read_bytes()
            require(NEW.unpack_from(saved, 128)[13] == 2 and NEW.unpack_from(saved, 256)[13] == 0,
                    'Failed and uncomputed status codes differ')
            rejected(lambda: finalize(directory, old[:-1]))
            summary = finalize(directory)['summary']
            require(summary['qualified_pixels'] == summary['failed_pixels'] == summary['uncomputed_pixels'] == 1,
                    'Failed/qualified/uncomputed accounting')
            require(not summary['all_pixel_records_qualified'], 'Failed slot forbids a complete-frame claim')
            require(png_rgb(directory / 'rgb.png')[3:] == b'\xff\0\xff' * 2,
                    'Failed and unfinished display remain visibly invalid')

        case('actual_readback_black_HDR_and_unfinished', valid_black_and_unfinished)
        case('actual_saved_blue_equals_far_is_rejected', corrupted_blue_rejected)
        case('failed_marker_and_legacy_extent_rejection', failed_marker_and_extent)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    case('sources_unchanged', lambda: require(before == after, 'Storage/test source changed during tests'))
    return {'schema': 't36-independent-storage-sentinel-v1',
            'passed': bool(cases) and all(item['pass'] for item in cases),
            'test_count': len(cases), 'failure_count': sum(not item['pass'] for item in cases),
            'tests': cases, 'source_sha256_before': before, 'source_sha256_after': after,
            'temporary_directory_cleaned': not base.exists(),
            'temporary_files_inside_scientific_run': False,
            'scientific_evaluations': 0, 'scene_imports': 0,
            'projection_imports': 0, 'quadrature_imports': 0, 'reference_imports': 0,
            'literal_legacy_rows': 3, 'sentinel_dimensions': [3, 1],
            'elapsed_seconds': time.perf_counter() - started}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'mode': 'plan_only', 'scientific_evaluations': 0,
                          'requires': 'Explicit execution authorization and new --out report path'}))
        return 0
    if args.out is None or args.out.exists():
        parser.error('--out must be a new report path')
    with args.out.open('x', encoding='utf-8', newline='\n') as output:
        try:
            report = run_tests()
        except Exception as error:
            report = {'schema': 't36-independent-storage-sentinel-v1', 'passed': False,
                      'error': type(error).__name__ + ': ' + str(error), 'scientific_evaluations': 0}
        json.dump(report, output, indent=2, allow_nan=False)
        output.write('\n')
    print(json.dumps({k: report.get(k) for k in ('passed', 'test_count', 'failure_count', 'error')}))
    return 0 if report['passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
