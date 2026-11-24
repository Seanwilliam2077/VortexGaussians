"""Export per-site T84 ignition times with the observation-window censoring flags."""
import csv
import gzip
import io
import json
import sys

sys.dont_write_bytecode = True
from clock_preview import (
    CUTS, END, HERE, POLICIES, PUBLIC, RECIPE, START, digest, onset_comparison,
    reconstruct, require, score,
)

DEST = HERE / 'material_onsets.csv.gz'
COLUMNS = ('policy', 'material_id', 'direct_B', 'A_onset_frame', 'A_status',
           'AB_onset_frame', 'AB_status')


def observed(data, idx):
    if idx in data['prefix_burning']:
        return START, 'left_censored'
    if idx in data['direct']:
        return START, 'direct_stroke'
    if idx in data['onset']:
        return data['onset'][idx], 'observed'
    return '', 'right_censored'


def validate_table(table, reference):
    records = list(csv.DictReader(io.StringIO(table)))
    ids = {(r['policy'], r['material_id']) for r in records}
    require(len(records) == len(ids), 'duplicate exported ID for policy')
    for policy in POLICIES:
        rows = [r for r in records if r['policy'] == policy]
        require(all(r['direct_B'] in ('0', '1') for r in rows), 'invalid edit indicator')
        direct = {r['material_id'] for r in rows if r['direct_B'] == '1'}
        masks = {}
        for take in ('A', 'AB'):
            births = [[] for _ in range(END - START + 1)]
            for r in rows:
                frame, status = r[take + '_onset_frame'], r[take + '_status']
                if status == 'right_censored':
                    require(frame == '', 'right censor must have empty time')
                    continue
                t = int(frame)
                if status == 'left_censored':
                    require(t == START, 'invalid left censor')
                elif status == 'direct_stroke':
                    require(take == 'AB' and t == START and r['direct_B'] == '1', 'invalid direct stroke')
                else:
                    require(status == 'observed' and START < t <= END, 'invalid event time')
                births[t - START].append(r['material_id'])
            active = set()
            masks[take] = {}
            for j, sites in enumerate(births):
                active.update(sites)
                require(len(active) == reference['arms'][policy + '-' + take]['active_counts_frames_180_through_360'][j],
                        f'{policy} {take} frame {START + j}: exported onset mismatch')
                if j in CUTS or j == END - START:
                    masks[take][j] = set(active)
        a = masks['A'][END - START]
        ab = masks['AB'][END - START]
        require({r['material_id'] for r in rows} == a | ab, policy + ' union of active IDs')
        # score() uses numeric material indices for off-stroke masks.
        def indices(material_ids):
            return {int(i.removeprefix('ply:')) for i in material_ids}
        for cut in CUTS:
            held = masks['AB'][cut]
            for name, pred in [('hold_observed_AB', held), ('union_cached_A_endpoint', held | a)]:
                metrics = score(indices(pred), indices(ab), indices(a), indices(direct))
                require(metrics == reference['scores'][policy][str(cut)][name], policy + ' signed endpoint mismatch')
    return len(records)


def main():
    reference = json.loads((HERE / 'CLOCK.json').read_bytes())
    meta = (PUBLIC / 'MANIFEST.json').read_bytes()
    recipe_raw = RECIPE.read_bytes()
    require(digest(meta) == reference['manifest_sha256'] and digest(recipe_raw) == reference['recipe_sha256'],
            'archived inputs differ from CLOCK.json')
    manifest = {f['file']: f for f in json.loads(meta)['files']}
    recipe = json.loads(recipe_raw)
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, lineterminator='\n')
    writer.writerow(COLUMNS)
    for policy in POLICIES:
        a = reconstruct(policy + '-A', manifest, recipe)
        ab = reconstruct(policy + '-AB', manifest, recipe)
        require(a['checks'] == reference['arms'][policy + '-A'] and ab['checks'] == reference['arms'][policy + '-AB'],
                policy + ' clock evidence mismatch')
        require(onset_comparison(a, ab) == reference['onsets'][policy], policy + ' signed timeline mismatch')
        for idx in sorted(a['endpoint'] | ab['endpoint']):
            writer.writerow([policy, f'ply:{idx}', int(idx in ab['direct']), *observed(a, idx), *observed(ab, idx)])
    table = buf.getvalue()
    rows = validate_table(table, reference)
    packed = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=packed, mode='wb', mtime=0, compresslevel=9) as handle:
        handle.write(table.encode('utf-8'))
    data = packed.getvalue()
    require(gzip.decompress(data).decode('utf-8') == table, 'gzip roundtrip failed')
    if DEST.exists():
        # Deflate streams can vary across zlib builds. The archived CSV is canonical.
        data = DEST.read_bytes()
        require(gzip.decompress(data).decode('utf-8') == table, 'existing event table differs')
    else:
        with DEST.open('xb') as handle:
            handle.write(data)
    print(json.dumps({'rows': rows, 'compressed_bytes': len(data), 'csv_sha256': digest(table.encode()),
                      'gzip_sha256': digest(data)}))


if __name__ == '__main__':
    main()
