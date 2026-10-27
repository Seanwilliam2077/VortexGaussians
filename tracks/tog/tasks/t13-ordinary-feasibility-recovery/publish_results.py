"""CPU-only publication of saved T13 evidence. Default: stdlib plan only."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
T12 = HERE.parent / 't12-ordinary-wind-response-extrema' / 'publish-01'
T12_PUBLICATION_SHA = '03d37b3cd144cdea2d76c3c02e675cfae3c8fa0c87a58811822829f34535615a'
COMPACT_TARGET_BYTES = 5_000_000  # Recording target, never a reason to omit evidence.
OBS_KEYS = ('observation_alpha', 'theta', 'initial_velocity')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def publish(run, out):
    if out.exists() or not out.is_relative_to(HERE) or out.is_relative_to(run):
        raise ValueError('Use a fresh publication directory inside T13, outside the raw run')
    os.environ['MKL_THREADING_LAYER'] = 'SEQUENTIAL'
    dll = Path(sys.prefix) / 'Library' / 'bin'
    dll_handle = os.add_dll_directory(str(dll)) if os.name == 'nt' and dll.is_dir() else None
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    before = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        digest = sha(path)
        if expected is not None and digest != expected:
            raise ValueError('SHA mismatch: ' + str(path))
        if str(path) in before and before[str(path)] != digest:
            raise ValueError('Input changed during publication: ' + str(path))
        before[str(path)] = digest
        return path

    def read_json(path, expected=None):
        return json.loads(pin(path, expected).read_text(encoding='utf-8'))

    worker = run / 'worker'
    summary = read_json(worker / 'summary.json')
    supervisor = read_json(run / 'supervisor.json')
    if supervisor.get('status') not in ('completed', 'failed', 'timeout') or summary.get('status') not in ('completed', 'failed'):
        raise ValueError('Only terminal saved executions may be published')
    config = read_json(HERE / 'config.json')
    pin(__file__)
    pin(HERE / 'freeze.json', summary['freezeSHA256'])
    for source in summary['sourcesBefore'].values():
        pin(HERE / source['path'], source['sha256'])
    sources_match = (summary.get('sourcesUnchanged') is True and supervisor.get('sourcesUnchanged') is True
                     and summary['sourcesBefore'] == summary['sourcesAfter'])
    if not sources_match or summary.get('runtimeInputsUnchanged') is not True:
        raise ValueError('Producer source/fixed-input identity is not established')

    def array_record(a):
        return {'shape': list(a.shape), 'dtype': a.dtype.str, 'bytes': a.nbytes,
                'rawSHA256': hashlib.sha256(a.tobytes(order='C')).hexdigest()}

    def extract(path, records, mapping, expected_file):
        values = {}
        with np.load(pin(path, expected_file), allow_pickle=False) as archive:
            for original, target in mapping.items():
                a = np.ascontiguousarray(archive[original])
                rec, expected = array_record(a), records[original]
                if any(rec[k] != expected[k] for k in ('shape', 'dtype', 'rawSHA256')):
                    raise ValueError('Array identity mismatch: ' + str(path) + ':' + original)
                if a.dtype.hasobject or not np.isfinite(a).all():
                    raise ValueError('Unsupported/nonfinite saved array: ' + original)
                values[target] = a
        return values

    parent = read_json(T12 / 'publication.json', T12_PUBLICATION_SHA)
    if parent.get('status') != 'completed' or not parent.get('inputsUnchanged'):
        raise ValueError('Fixed T12 publication is incomplete')
    reference_keys = ('observation_alpha', 'theta', 'observed_uint8', 'lower', 'upper', 'denominator')
    # Reference futures are retained only when an alternate has a qualified final verification.
    search = summary.get('search', {})
    success = (summary.get('decision') == 'ORDINARY_NONSEED_FEASIBILITY_FOUND'
               and search.get('finalQualified') is True and search.get('finalNonseed') is True)
    if success:
        reference_keys += ('future_alpha',)
    reference = extract(T12 / 'compact.npz', parent['compactArrays'],
                        {'reference__' + k: k for k in reference_keys}, parent['files']['compact.npz']['sha256'])
    pack_meta = read_json(HERE / config['input_pack']['manifest'], config['input_pack']['manifest_sha256'])
    pack = extract(HERE / config['input_pack']['path'], pack_meta['arrays'],
                   {k: k for k in ('seed_velocity', 'seed_theta', 'start_theta', 'observed_uint8', 'lower', 'upper', 'denominator')},
                   config['input_pack']['sha256'])
    for key in ('observed_uint8', 'lower', 'upper', 'denominator'):
        if pack[key].dtype != reference[key].dtype or pack[key].shape != reference[key].shape or pack[key].tobytes() != reference[key].tobytes():
            raise ValueError('T13 inputs do not match the published T12 reference: ' + key)
    if pack['seed_theta'].tobytes() != reference['theta'].tobytes():
        raise ValueError('Reference theta mismatch')
    reference['initial_velocity'] = pack['seed_velocity']
    data = {'reference': reference}
    raw_sources = {}
    choices = {'initial': 'qualification/analytic.npz', 'least': 'search/least-violating.npz',
               'first': 'search/first-feasible.npz', 'final': 'search/final-verification.npz'}
    for label, filename in choices.items():
        descriptor = summary.get('raw', {}).get(filename)
        if descriptor is None:
            continue
        keys = OBS_KEYS + (('future_alpha', 'd', 'gs') if label == 'final' else ())
        values = extract(worker / filename, descriptor['arrays'], {k: k for k in keys}, descriptor['sha256'])
        data[label] = values
        raw_sources[label] = {'path': filename, 'sha256': descriptor['sha256'], 'bytes': descriptor['bytes']}
    if success and 'final' not in data:
        raise ValueError('Success decision is missing final verification arrays')
    if 'initial' in data and data['initial']['theta'].tobytes() != pack['start_theta'].tobytes():
        raise ValueError('Initial G0 did not use the fixed start theta')
    if search.get('finalPerformed') is False and 'final' in data:
        raise ValueError('Unexpected final raw in no-final execution')

    tolerance = config['gates']['interval_alpha_tolerance']
    roi = config['response']['roi']
    if roi != [28, 26, 36, 56]:
        raise ValueError('Unexpected ROI')
    x0, y0, x1, y1 = roi
    denominator = float(reference['denominator'].reshape(-1)[0])
    if denominator <= 0:
        raise ValueError('Invalid fixed response denominator')
    producer_metrics = {'initial': summary.get('qualification', {}).get('analyticMetrics', {}),
                        'least': search.get('leastViolating', {}).get('metrics', {}),
                        'first': search.get('firstCandidate', {}).get('metrics', {}),
                        'final': search.get('finalMetrics', {})}
    calculated, compact = {}, {}
    for label, values in data.items():
        a = values['observation_alpha']
        if a.shape != (20, 64, 64) or values['initial_velocity'].shape != (3, 32, 32, 32):
            raise ValueError('Unexpected observation/velocity shape: ' + label)
        violation = np.maximum(np.maximum(reference['lower'] - a, a - reference['upper']), 0)
        count = np.count_nonzero(violation > tolerance, axis=(1, 2))
        maximum = violation.max(axis=(1, 2))
        codes = np.floor(255 * a + .5).clip(0, 255).astype(np.uint8)
        velocity_delta = values['initial_velocity'] - reference['initial_velocity']
        row = {'intervalViolatingPixelsPerFrame': count.tolist(),
               'intervalMaxAlphaViolationPerFrame': maximum.tolist(),
               'intervalViolatingPixels': int(count.sum()), 'intervalMaxAlphaViolation': float(maximum.max()),
               'quantizedByteExact': bool(np.array_equal(codes, reference['observed_uint8'])),
               'seedVelocityDifferenceMax': float(np.abs(velocity_delta).max()),
               'seedVelocityDifferenceRelativeL2': float(np.sqrt(np.sum(velocity_delta**2) / np.sum(reference['initial_velocity']**2))),
               'producerMetrics': producer_metrics.get(label, {}), 'dFinal': None,
               'futureExecutedInT13': label == 'final'}
        recorded = row['producerMetrics']
        for key in ('intervalViolatingPixelsPerFrame', 'intervalViolatingPixels', 'quantizedByteExact'):
            if key in recorded and row[key] != recorded[key]:
                raise ValueError('CPU presentation metric differs: ' + label + ':' + key)
        for key in ('intervalMaxAlphaViolation', 'seedVelocityDifferenceMax', 'seedVelocityDifferenceRelativeL2'):
            if key in recorded and not np.isclose(row[key], recorded[key], rtol=1e-12, atol=1e-14):
                raise ValueError('CPU presentation scalar differs: ' + label + ':' + key)
        if 'future_alpha' in values:
            if values['future_alpha'].shape != (2, 20, 64, 64):
                raise ValueError('Unexpected future alpha shape')
            g = values['future_alpha'][:, :, y0:y1, x0:x1].sum(axis=(2, 3)) / denominator
            d = g[1] - g[0]
            row.update(dFinal=float(d[-1]), gByFutureFrame=g.tolist(), dByFutureFrame=d.tolist(),
                       futureInterpretation='qualified witness' if success and label == 'final' else
                       ('archived T12 reference' if label == 'reference' else 'failed verification, not a witness'))
            if 'd' in values and not np.isclose(row['dFinal'], float(values['d'].reshape(-1)[0]), rtol=1e-12, atol=1e-14):
                raise ValueError('Saved d disagrees with alpha reconstruction')
            compact[label + '__g_recomputed'] = g
            compact[label + '__d_recomputed'] = d
        for key, value in values.items():
            compact[label + '__' + key] = value
        compact[label + '__interval_max_by_frame'] = maximum
        compact[label + '__interval_count_by_frame'] = count
        calculated[label] = row

    out.mkdir(parents=True, exist_ok=False)
    with (out / 'compact.npz').open('xb') as stream:
        np.savez_compressed(stream, **compact)
    with np.load(out / 'compact.npz', allow_pickle=False) as archive:
        if set(archive.files) != set(compact) or any(archive[k].dtype != a.dtype or archive[k].shape != a.shape or
                                                  archive[k].tobytes() != a.tobytes() for k, a in compact.items()):
            raise ValueError('Compact readback does not preserve exact array bytes')

    frames = np.arange(1, 21)
    labels = ('reference', 'final') if success else ('reference', 'initial', 'least')
    captions = {'reference': 'Archived T12 reference', 'initial': 'Fixed G0 start',
                'least': 'Least-violating evaluated point\nNOT a feasible witness',
                'final': 'First-qualified: full verification'}
    alpha_max = max(float(data[k]['observation_alpha'].max()) for k in labels if k in data)

    def image(ax, array, title, cmap='magma', low=0, high=alpha_max, draw_roi=False):
        im = ax.imshow(array, origin='lower', extent=(0, 64, 0, 64), interpolation='nearest', cmap=cmap, vmin=low, vmax=high)
        if draw_roi:
            ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, fill=False, edgecolor='cyan', linewidth=1.1))
        ax.set_title(title, fontsize=10)
        ax.set_xticks([0, 32, 64]); ax.set_yticks([0, 32, 64])
        return im

    if success:
        fig = plt.figure(figsize=(15, 11), layout='constrained')
        gs = fig.add_gridspec(3, 4, height_ratios=[1, 1, .85])
        response_max = max(float(np.abs(data[k]['future_alpha'][1, -1] - data[k]['future_alpha'][0, -1]).max()) for k in labels)
        response_max = max(response_max, 1e-15)
        for r, label in enumerate(labels):
            value = data[label]
            ims = [value['observation_alpha'][-1], value['future_alpha'][0, -1], value['future_alpha'][1, -1],
                   value['future_alpha'][1, -1] - value['future_alpha'][0, -1]]
            for c, (a, title) in enumerate(zip(ims, ('observation 20', 'unedited future 20', 'wind future 20', 'wind minus unedited'))):
                ax = fig.add_subplot(gs[r, c])
                im = image(ax, a, captions[label] + '\n' + title, 'coolwarm' if c == 3 else 'magma',
                           -response_max if c == 3 else 0, response_max if c == 3 else alpha_max, c > 0)
                if c == 3: fig.colorbar(im, ax=ax, shrink=.7)
        ax_count = fig.add_subplot(gs[2, :2]); ax_max = fig.add_subplot(gs[2, 2:])
        title = 'T13: first evaluated feasible alternate, then one full verification'
        footer = ('Fixed pixel intervals, not exact floating-point images. First candidate may be a line-search trial.\n'
                  'Velocity nonidentity >1e-10 is not substantial ambiguity. Two saved d values are not confidence bounds.')
    else:
        fig = plt.figure(figsize=(15, 11.5), layout='constrained')
        gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, .95])
        delta_max = max([float(np.abs(data[k]['observation_alpha'][-1] - reference['observation_alpha'][-1]).max()) for k in labels if k in data] + [1e-15])
        for c, label in enumerate(labels):
            ax = fig.add_subplot(gs[0, c]); ax_diff = fig.add_subplot(gs[1, c])
            if label not in data:
                for a in (ax, ax_diff): a.text(.5, .5, 'Not saved / not executed', ha='center'); a.set_axis_off()
                continue
            im = image(ax, data[label]['observation_alpha'][-1], captions[label] + '\nobservation step 20')
            fig.colorbar(im, ax=ax, shrink=.7, label='alpha (common scale)')
            di = image(ax_diff, data[label]['observation_alpha'][-1] - reference['observation_alpha'][-1],
                       'Signed alpha difference from reference', 'coolwarm', -delta_max, delta_max)
            fig.colorbar(di, ax=ax_diff, shrink=.7)
        ax_count = fig.add_subplot(gs[2, 0]); ax_max = fig.add_subplot(gs[2, 1]); text_ax = fig.add_subplot(gs[2, 2])
        text_ax.set_axis_off()
        least = calculated.get('least', {})
        text_ax.text(0, .95, 'No new feasible point found\nin this fixed ordinary search.\n\n'
                     + ('No T13 future was executed.\nNo response range is available.\n\n' if not search.get('finalPerformed') else
                        'First final verification failed.\nNo qualified response range.\n\n')
                     + (f"Least v0 distance:\nmax = {least['seedVelocityDifferenceMax']:.6g}\nrelative L2 = {least['seedVelocityDifferenceRelativeL2']:.4%}\n\n" if least else '')
                     + 'Small image differences can\nstill violate pixel intervals.\nNot evidence of uniqueness.',
                     va='top', fontsize=11)
        title = 'T13: ordinary feasibility recovery did not find an eligible alternate'
        footer = 'Synthetic fixed model; all 20 full-image observation intervals are required. No seed fallback; least-violating is diagnostic only.'
    for label in labels:
        if label not in calculated: continue
        row = calculated[label]
        ax_count.plot(frames, row['intervalViolatingPixelsPerFrame'], marker='.', label=label)
        ax_max.plot(frames, row['intervalMaxAlphaViolationPerFrame'], marker='.', label=label)
    ax_count.set(title='Violating pixels in every observation frame', xlabel='Observation step', ylabel='Count', xlim=(1, 20))
    ax_count.set_ylim(bottom=0); ax_count.grid(alpha=.2); ax_count.legend(fontsize=8)
    ax_max.axhline(tolerance, color='black', ls='--', label='gate tolerance 1e-10')
    ax_max.set(title='Maximum alpha interval violation per frame', xlabel='Observation step', ylabel='Alpha violation', xlim=(1, 20))
    ax_max.set_yscale('symlog', linthresh=tolerance); ax_max.grid(alpha=.2); ax_max.legend(fontsize=8)
    fig.suptitle(title, fontsize=16)
    fig.supxlabel(footer, fontsize=10)
    fig.savefig(out / 'feasibility-recovery.png', dpi=150)
    fig.savefig(out / 'feasibility-recovery.svg')
    plt.close(fig)

    work = summary.get('actualWork', {})
    obs_completed, full_completed = work.get('observationEvaluationsCompleted', 0), work.get('fullEvaluationsCompleted', 0)
    cost = {'actualWork': work, 'completedObservationStepCost': obs_completed * 20,
            'completedFullVerificationStepCost': full_completed * 60,
            'stepsCompletedMatchCompletedEvaluations': work.get('stepsCompleted') == obs_completed*20 + full_completed*60,
            'setup': summary.get('setup', {}), 'G0SecondsIncludingIO': summary.get('qualification', {}).get('secondsIncludingIO'),
            'searchSecondsBeforeFinal': search.get('searchSecondsBeforeFinal'),
            'searchSecondsIncludingFinalAndIO': search.get('secondsIncludingFinalAndIO'),
            'workerWallSeconds': summary.get('workerWallSeconds'), 'supervisorWallSeconds': supervisor.get('wallSeconds'),
            'scope': '20-step observations and 60-step final verifications counted separately; no T12 reference recomputation; not a matched speed comparison.'}
    result = {'schema': 't13-publication-result-v1', 'producerDecision': summary.get('decision'),
              'publicationBranch': 'qualified-alternate' if success else 'no-qualified-alternate',
              'G0Passed': summary.get('qualification', {}).get('passed'), 'sourceIdentityMatches': sources_match,
              'firstCandidate': search.get('firstCandidate'), 'leastViolating': search.get('leastViolating'),
              'selectedWasOptimizerReturned': search.get('selectedWasOptimizerReturned'),
              'nonseedThreshold': config['nonseed_velocity_max_absolute_threshold'],
              'nonseedThresholdMeaning': 'Numerical identity exclusion only, not substantial ambiguity.',
              'calculatedFromSavedArrays': calculated, 'cost': cost, 'rawSources': raw_sources,
              'futureExecuted': bool(search.get('finalPerformed')), 'responseRange': None,
              'independentAudit': 'External independent audit not asserted by this CPU publisher.',
              'scope': 'Ordinary Phase-I fixed-search evidence, not a new inverse method, identifiability proof, calibrated uncertainty interval, or TOG contribution.'}
    write_json(out / 'result.json', result)
    copied = [(worker / 'summary.json', 'summary.json'), (run / 'supervisor.json', 'supervisor.json'),
              (HERE / 'config.json', 'config.json'), (HERE / 'PROTOCOL.md', 'PROTOCOL.md'),
              (HERE / 'freeze.json', 'freeze.json'), (HERE / 'inputs-manifest.json', 'inputs-manifest.json')]
    copied += [(run / name, name) for name in ('stdout.log', 'stderr.log') if (run / name).exists()]
    for source, name in copied:
        pin(source); shutil.copyfile(source, out / name)

    table = ['| 记录 | 像素—帧违例数 | 最大 alpha 违反量 | v0 最大差 | v0 相对 L2 | d |',
             '|---|---:|---:|---:|---:|---:|']
    for label in labels:
        row = calculated.get(label)
        if row is None: continue
        dtext = '未执行/不适用' if row['dFinal'] is None else f"{row['dFinal']:.12g}"
        table.append(f"| {label} | {row['intervalViolatingPixels']} | {row['intervalMaxAlphaViolation']:.12g} | "
                     f"{row['seedVelocityDifferenceMax']:.12g} | {row['seedVelocityDifferenceRelativeL2']:.6%} | {dtext} |")
    verdict = ('一次完整复验保留了第一个被实际评估且合格的非同一速度点；它可能是线搜索试探点，不必是优化器返回点。'
               if success else '这次固定普通搜索没有找到新的合格速度点。least-violating 是诊断点，不是可行见证；这不证明不存在其他合格点或观测唯一。')
    future_text = ('成功图中的未来均为保存的原分支，无重新模拟。两个 d 数值只是已保存状态的响应，不是置信区间或极值保证。'
                   if success else ('本次没有执行未来分支或完整 60 步验证；图和紧凑数据不补造未来、零响应、seed fallback 或新响应范围。'
                                    if not search.get('finalPerformed') else '首点完整验证失败；其保存数组只作为失败诊断，不作为合格反事实见证。'))
    readme = f"""# T13：普通 Phase-I 可行性恢复的保存结果

{verdict}

正式决定：`{summary.get('decision')}`。新 G0 导数/数值资格：`{summary.get('qualification', {}).get('passed')}`；这与观测可行性是不同判断。

![保存结果](feasibility-recovery.png)

图像均来自实际保存的 alpha，原点 lower-left、公共色阶。差图有明确独立量纲；视觉近似相同不替代每帧逐像素区间门。所有 20 帧的违反量和违例计数在下排及 compact 中完整保留。{future_text}

{chr(10).join(table)}

速度差相对同一参考初始速度；`max > 1e-10` 仅排除数值同一，不是实质歧义标准。least 的选择沿冻结的全约束字典序，不是按图片最相似事后挑选，也不必是最后一个优化器接受点。

本次总计 {obs_completed} 个完整 20 步 observation（{obs_completed*20} 步）、{full_completed} 个完整 60 步 verification（{full_completed*60} 步），实际完成 {work.get('stepsCompleted')} 步、{work.get('reverseCalls')} 次反向。搜索自身 {search.get('observationEvaluationsCompleted')} 个 observation、{search.get('backwardCalls')} 次反向、{search.get('returnedSteps')} 次返回；G0 另计。worker {summary.get('workerWallSeconds'):.6f} s，supervisor {supervisor.get('wallSeconds'):.6f} s；不是与 T12 等工作量的速度比较。各分段原值见 [result.json](result.json) 和 [summary.json](summary.json)。

[compact.npz](compact.npz) 保留发布对象完整 20 帧观测、theta、原精度 v0、观测区间及逐帧统计；若实际执行了 final，则保留其两条完整 future alpha。未复制大 3D 末态或密度轨迹，原 raw 身份在 result 中保留。约 5 MB 是记录目标，不因超过目标删证据。所有保存数组逐字节压缩读回，输入/源码首尾 SHA 和输出 SHA 见 [publication.json](publication.json)。本发布的 CPU 数值核对不是独立前向物理复算；独立审计由另一脚本另列，不在此擅称已通过。

复现本出版（仅 CPU，要求带 NumPy/Matplotlib 的既有环境；不运行模型）：

```text
python -I -B publish_results.py --run runs/run-01 --out publish-NEW --execute
```

无 `--execute` 时仅打印 stdlib 计划。fresh 输出拒绝覆盖。执行进程局部设 MKL sequential 和 Conda Library/bin DLL 搜索，不修改全局环境、不导入 Torch。原 T12 [publication](../../t12-ordinary-wind-response-extrema/publish-01/README.md) 仅提供认证参考；没有借用 T12 搜索终点作为 T13 候选。
"""
    (out / 'README.md').write_text(readme, encoding='utf-8')
    after = {path: sha(path) for path in before}
    unchanged = before == after
    if not unchanged:
        raise ValueError('Source/input changed during CPU publication; preserve output as failed')
    manifest = {'schema': 't13-publication-v1', 'status': 'completed',
                'createdUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'command': [sys.executable] + sys.argv, 'publisherSHA256': sha(__file__),
                'producerStatus': summary['status'], 'producerDecision': summary.get('decision'),
                'inputPinsBefore': before, 'inputPinsAfter': after, 'inputsUnchanged': unchanged,
                'sourceIdentityMatches': sources_match, 'T12PublicationSHA256': T12_PUBLICATION_SHA,
                'runtime': {'python': sys.version, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
                            'MKL_THREADING_LAYER': os.environ['MKL_THREADING_LAYER'], 'dllDirectory': str(dll),
                            'torchImported': 'torch' in sys.modules, 'gpuUsed': False},
                'compact': {'bytes': (out/'compact.npz').stat().st_size, 'targetBytes': COMPACT_TARGET_BYTES,
                            'withinTarget': (out/'compact.npz').stat().st_size <= COMPACT_TARGET_BYTES,
                            'targetIsHardGate': False, 'roundtripExact': True},
                'compactArrays': {k: array_record(v) for k, v in compact.items()},
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(out.iterdir()) if p.is_file()}}
    write_json(out / 'publication.json', manifest)
    return {'status': 'completed', 'out': str(out), 'decision': summary.get('decision'),
            'compactBytes': manifest['compact']['bytes'], 'publicationSHA256': sha(out/'publication.json')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', default='runs/run-01')
    parser.add_argument('--out', default='publish-01')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    run, out = (HERE/args.run).resolve(), (HERE/args.out).resolve()
    if not args.execute:
        print(json.dumps({'mode': 'plan', 'run': str(run), 'out': str(out), 'gpu': False,
                          'readsResults': False, 'T12PublicationSHA256': T12_PUBLICATION_SHA,
                          'success': 'Reference and first-qualified final verification, complete observation gates, actual futures/d/v0 distance.',
                          'failure': 'Reference, fixed G0 start, least-violating observations; no invented futures or fallback seed.',
                          'compact': 'All selected 20-frame alpha, theta/v0; future alpha only if present. Original dtype, soft 5 MB target.',
                          'overwrite': False}, indent=2))
        return 0
    tick = time.perf_counter()
    try:
        result = publish(run, out)
    except Exception as exc:
        record = {'status': 'failed', 'error': repr(exc), 'traceback': traceback.format_exc(),
                  'seconds': time.perf_counter()-tick, 'command': [sys.executable]+sys.argv, 'publisherSHA256': sha(__file__)}
        if out.exists() and not (out/'publication.json').exists() and not (out/'publication-failure.json').exists():
            write_json(out/'publication-failure.json', record)
        print(json.dumps(record, ensure_ascii=False)); return 1
    print(json.dumps(dict(result, seconds=time.perf_counter()-tick), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
