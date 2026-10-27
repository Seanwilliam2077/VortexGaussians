"""CPU-only T12 saved-result publication. Default is a stdlib plan, not execution."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
COMPACT_TARGET_BYTES = 5_000_000
NAMES = ('reference', 'min', 'max')
RAW_NAMES = ('reference.npz', 'min/final-verification.npz', 'max/final-verification.npz')
# Fixed before reading results: no 3D velocity, density, wind or full constraints.
KEEP = ('observation_alpha', 'future_alpha', 'theta')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def publish(run, out):
    # This function is reached only under explicit --execute. Changes are child-local.
    os.environ['MKL_THREADING_LAYER'] = 'SEQUENTIAL'
    dll = Path(sys.prefix) / 'Library' / 'bin'
    dll_handle = os.add_dll_directory(str(dll)) if os.name == 'nt' and dll.is_dir() else None
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    if out.exists():
        raise FileExistsError('Fresh output required: ' + str(out))
    if not out.is_relative_to(HERE) or out.is_relative_to(run):
        raise ValueError('Publication must be inside T12 and outside raw run')
    worker = run / 'worker'
    summary_path, supervisor_path = worker / 'summary.json', run / 'supervisor.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    supervisor = json.loads(supervisor_path.read_text(encoding='utf-8'))
    if supervisor.get('status') not in ('completed', 'failed', 'timeout'):
        raise ValueError('Supervisor is not terminal; do not read partial results')
    if summary.get('status') not in ('completed', 'failed'):
        raise ValueError('Worker is not terminal; do not read partial results')
    config = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    fixed = [summary_path, supervisor_path, HERE / 'config.json', HERE / 'PROTOCOL.md',
             HERE / 'freeze.json', Path(__file__).resolve()]
    for name in ('stdout.log', 'stderr.log'):
        if (run / name).exists():
            fixed.append(run / name)
    before = {str(p): sha(p) for p in fixed}
    source_match = bool(summary.get('sourcesUnchanged')) and bool(supervisor.get('sourcesUnchanged'))
    for pin in summary['sourcesBefore'].values():
        p = (HERE / pin['path']).resolve()
        before[str(p)] = sha(p)
        source_match = source_match and before[str(p)] == pin['sha256']
    source_match = source_match and sha(HERE / 'freeze.json') == summary['freezeSHA256']

    def selected_npz(name, keys):
        path = worker / name
        spec = summary.get('raw', {}).get(name)
        if spec is None or not path.exists():
            return None
        before[str(path)] = sha(path)
        if before[str(path)] != spec['sha256'] or path.stat().st_size != spec['bytes']:
            raise ValueError('Saved NPZ identity mismatch: ' + name)
        values = {}
        with np.load(path, allow_pickle=False) as f:
            for key in keys:
                a = np.ascontiguousarray(f[key])
                rec = spec['arrays'][key]
                if (list(a.shape) != rec['shape'] or a.dtype.str != rec['dtype'] or
                        hashlib.sha256(a.tobytes()).hexdigest() != rec['rawSHA256']):
                    raise ValueError('Saved array identity mismatch: ' + name + ':' + key)
                values[key] = a
        return values

    data = {}
    for label, raw in zip(NAMES, RAW_NAMES):
        keys = KEEP + (('observed_uint8', 'lower', 'upper', 'denominator') if label == 'reference' else ())
        values = selected_npz(raw, keys)
        if values is not None:
            if values['observation_alpha'].shape != (20, 64, 64) or values['future_alpha'].shape != (2, 20, 64, 64):
                raise ValueError('Unexpected image schedule')
            data[label] = values
    reference = data.get('reference')
    out.mkdir()
    compact, calculated = {}, {}
    arms = {r['extreme']: r for r in summary.get('extremes', [])}
    roi = config['response']['roi']
    x0, y0, x1, y1 = roi
    if roi != [28, 26, 36, 56]:
        raise ValueError('Unexpected fixed ROI')
    denominator = None if reference is None else float(reference['denominator'].reshape(-1)[0])
    for label, values in data.items():
        for key, value in values.items():
            compact[label + '__' + key] = value
        images_finite = bool(np.isfinite(values['observation_alpha']).all() and np.isfinite(values['future_alpha']).all())
        metrics = summary.get('setup', {}).get('referenceMetrics', {}) if label == 'reference' else arms.get(label, {}).get('finalMetrics', {})
        row = {'available': True, 'imagesFinite': images_finite, 'producerMetrics': metrics}
        if images_finite and denominator is not None and denominator > 0:
            g = values['future_alpha'][:, :, y0:y1, x0:x1].sum(axis=(2, 3)) / denominator
            d = g[1] - g[0]
            a = values['observation_alpha']
            violations = np.maximum(reference['lower'] - a, a - reference['upper']).clip(min=0)
            codes = np.floor(255 * a + .5).clip(0, 255).astype(np.uint8)
            cd = np.abs(codes.astype(np.int16) - reference['observed_uint8'].astype(np.int16))
            row.update(gUneditedByFutureFrame=g[0].tolist(), gWindByFutureFrame=g[1].tolist(),
                       dByFutureFrame=d.tolist(), dFinal=float(d[-1]),
                       intervalMaxAlphaViolation=float(violations.max()),
                       intervalViolatingPixels=int(np.count_nonzero(violations > config['gates']['interval_alpha_tolerance'])),
                       quantizedByteExact=bool(not cd.any()), quantizedDifferentPixels=int(np.count_nonzero(cd)),
                       quantizedMaxCodeDifference=int(cd.max()))
            if 'd' in metrics and abs(row['dFinal'] - metrics['d']) > 1e-12:
                raise ValueError('CPU image-based d differs from producer record')
            compact[label + '__g'] = g
            compact[label + '__d'] = d
        calculated[label] = row
    compact_info = None
    if compact:
        with (out / 'compact.npz').open('xb') as f:
            np.savez_compressed(f, **compact)
        with np.load(out / 'compact.npz', allow_pickle=False) as f:
            exact = set(f.files) == set(compact) and all(np.array_equal(f[k], v, equal_nan=True) for k, v in compact.items())
        if not exact:
            raise ValueError('Compact roundtrip mismatch')
        compact_info = {'bytes': (out / 'compact.npz').stat().st_size, 'targetBytes': COMPACT_TARGET_BYTES,
                        'withinTarget': (out / 'compact.npz').stat().st_size <= COMPACT_TARGET_BYTES,
                        'roundtripExact': True, 'scopeFixedBeforeResults': 'All obs/future alpha, theta; reference quantization contract; g/d. No 3D fields.'}
    selected = {}
    for name in ('min', 'max'):
        r = arms.get(name, {})
        selected[name] = {k: r.get(k) for k in (
            'status', 'finalQualified', 'selectedEvaluation', 'selectedOrigin', 'selectedWasInitialSeed',
            'selectedWasOptimizerReturned', 'finalVerificationEvaluation', 'termination',
            'evaluationsStarted', 'evaluationsCompleted', 'backwardCalls', 'returnedSteps',
            'cacheHits', 'cacheMisses', 'searchSecondsBeforeFinal', 'secondsIncludingFinalAndIO', 'softLimitExceeded')}
    valid_endpoints = (source_match and summary.get('runtimeInputsUnchanged') is True and
                       all(selected[n]['finalQualified'] is True and 'dFinal' in calculated.get(n, {}) for n in ('min', 'max')))
    both_seed = all(selected[n]['selectedWasInitialSeed'] is True for n in ('min', 'max'))
    span = calculated['max']['dFinal'] - calculated['min']['dFinal'] if valid_endpoints else None
    finite_images = [v[k] for v in data.values() for k in ('observation_alpha', 'future_alpha') if np.isfinite(v[k]).all()]
    amax = max([float(v.max()) for v in finite_images] + [1e-12])
    deltas = {name: v['future_alpha'][1, -1] - v['future_alpha'][0, -1]
              for name, v in data.items() if calculated[name]['imagesFinite']}
    rmax = max([float(np.abs(v).max()) for v in deltas.values()] + [1e-12])
    result = {'schema': 't12-saved-publication-v1', 'producerStatus': summary.get('status'),
              'producerDecision': summary.get('decision'), 'sourceIdentityMatches': source_match,
              'runtimeInputsUnchanged': summary.get('runtimeInputsUnchanged'),
              'qualificationG0': summary.get('qualification'), 'setup': summary.get('setup'),
              'actualWork': summary.get('actualWork'), 'workerWallSeconds': summary.get('workerWallSeconds'),
              'supervisorWallSeconds': supervisor.get('wallSeconds'), 'selected': selected, 'imageDerived': calculated,
              'qualifiedEndpointsAvailable': valid_endpoints, 'bothSelectedEndpointsAreSeed': both_seed,
              'foundSignedSpanMaxMinusMin': span,
              'fixedResponseROI': roi, 'imageOrigin': 'lower-left', 'alphaLimits': [0, amax],
              'responseLimits': [-rmax, rmax], 'compact': compact_info,
              'scope': 'Finite-budget witnesses; same public seed; interval feasibility is not quantized byte identity. No confidence interval/global extrema or benefit claim.'}
    write_json(out / 'result.json', result)

    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(15, 13), layout='constrained')
    gs = fig.add_gridspec(4, 4, height_ratios=[1, 1, 1, .7])
    fig.suptitle('T12 | Ordinary wind-response witnesses under a fixed observation interval', fontsize=15)
    for i, label in enumerate(NAMES):
        values = data.get(label)
        status = 'public seed' if label == 'reference' else ('seed retained' if selected[label]['selectedWasInitialSeed'] else str(selected[label]['selectedOrigin']))
        for col in range(4):
            ax = fig.add_subplot(gs[i, col])
            title = ('Observation step 20', 'Future 20: no wind', 'Future 20: wind', 'Wind response: E - U')[col]
            ax.set_title(label + ' | ' + title)
            if values is None or not calculated[label]['imagesFinite']:
                ax.axis('off'); ax.text(.5, .5, 'No finite saved final verification\nNot a successful witness', ha='center', transform=ax.transAxes)
                continue
            image = (values['observation_alpha'][-1] if col == 0 else
                     values['future_alpha'][col - 1, -1] if col < 3 else deltas[label])
            limits = (0, amax) if col < 3 else (-rmax, rmax)
            im = ax.imshow(image, origin='lower', interpolation='nearest', extent=(-.5, 63.5, -.5, 63.5),
                           vmin=limits[0], vmax=limits[1], cmap='magma' if col < 3 else 'RdBu_r')
            ax.add_patch(Rectangle((x0 - .5, y0 - .5), x1 - x0, y1 - y0, fill=False, edgecolor='#00ff99', linewidth=1.1))
            ax.set_xticks([0, 32, 63]); ax.set_yticks([0, 32, 63]); ax.set_xlabel('screen x'); ax.set_ylabel('screen y')
            if col == 0:
                ax.set_xlabel(status, fontsize=8)
            fig.colorbar(im, ax=ax, shrink=.75, pad=.02)
    ax = fig.add_subplot(gs[3, :2])
    for i, label in enumerate(NAMES):
        if 'dFinal' in calculated.get(label, {}):
            ax.plot(calculated[label]['dFinal'], i, 'o', markersize=7, label=label)
    if valid_endpoints:
        ax.plot([calculated['min']['dFinal'], calculated['max']['dFinal']], [1.5, 1.5], color='black', linewidth=2)
    ax.set_yticks(range(3), NAMES); ax.set_ylim(-.5, 2.5); ax.grid(axis='x', alpha=.25)
    ax.set_xlabel('d = (wind - no wind) ROI alpha sum / reference obs20 alpha sum')
    ax.set_title('Found qualified span only; not a confidence interval' if valid_endpoints else 'Saved response values; no verified two-endpoint span')
    ax = fig.add_subplot(gs[3, 2:]); ax.axis('off')
    g0 = summary.get('qualification', {})
    lines = [str(summary.get('decision', 'No final decision')),
             f"New G0 passed: {g0.get('passed')} | eval/reverse: {g0.get('evaluations')}/{g0.get('backwardCalls')}",
             'All 20 observation frames are tested; the green ROI defines only the response.',
             'Observation interval agreement does not imply identical uint8 codes.']
    for name in ('min', 'max'):
        r = selected[name]; seconds = r['secondsIncludingFinalAndIO']
        seconds_text = 'unavailable' if seconds is None else f'{seconds:.3f}s'
        lines.append(f"{name}: qualified={r['finalQualified']}; eval={r['evaluationsCompleted']}; {seconds_text}")
    if span is not None:
        lines.append(f'Found signed span: {span:.8g}; response magnitude has no pass threshold.')
    if both_seed:
        lines.append('Both selected endpoints are the seed: not evidence of uniqueness.')
    lines.append('Synthetic passive density; no real capture, creator evidence, or new method.')
    ax.text(0, .98, '\n'.join(lines), va='top', transform=ax.transAxes, fontsize=9, linespacing=1.45)
    fig.savefig(out / 'wind-response-witnesses.png', dpi=165)
    fig.savefig(out / 'wind-response-witnesses.svg')
    plt.close(fig)

    copies = [(summary_path, 'summary.json'), (supervisor_path, 'supervisor.json')]
    copies += [(HERE / n, n) for n in ('config.json', 'PROTOCOL.md', 'freeze.json')]
    copies += [(run / n, n) for n in ('stdout.log', 'stderr.log') if (run / n).exists()]
    for p, name in copies:
        shutil.copyfile(p, out / name)
    table_rows = []
    for name in ('min', 'max'):
        r = selected[name]; m = calculated.get(name, {})
        table_rows.append(f"| {name} | {r['finalQualified']} | {r['selectedOrigin']} / eval {r['selectedEvaluation']} | {r['selectedWasInitialSeed']} | {m.get('dFinal')} | {r['evaluationsCompleted']} / {r['backwardCalls']} | {r['secondsIncludingFinalAndIO']} |")
    size_text = '无可发布数组' if compact_info is None else f"{compact_info['bytes']:,} B；建议5MB内：{compact_info['withinTarget']}"
    readme = f'''# T12：普通风响应极值搜索的保存结果

原执行状态：**{summary.get('status')}**；决策：`{summary.get('decision')}`。本页只发布实际保存值，不把执行完成、G0通过或 seed 合格当作发现显著歧义。

![实际观测、未来与差分](wind-response-witnesses.png)

三行分别为公开reference、min、max的最终核验。第一列为观测step20；之后是future20（绝对step40）的无风、有风及实际alpha差分。所有alpha图共用色标，所有差图共用零中心色标，原点在左下。绿色半开ROI为[28,26,36,56]，只定义响应量；原观测约束覆盖完整20帧全部像素。

| 臂 | 最终qualified | selected origin / ID | 保留seed | 实际d | 完整eval / reverse | 臂耗时s（含末验/IO） |
|---|---|---|---|---|---|---|---|
{chr(10).join(table_rows)}

合格双端可用：**{valid_endpoints}**；找到的max−min跨度：**{span}**；两端均保留seed：**{both_seed}**。若两端都是seed，只能说本轮没有选出优于seed的新合格极值见证，不能说区间收敛为零、没有歧义，或仅据最终选择断言每个非seed候选都不合格；后者需独立检查全部实际eval记录。这不是全局极值或覆盖区间，不含任何概率／置信保证。两臂从同一公开seed独立开始，最优见证允许来自实际付费的line-search trial；是否为优化器返回点及重新验证ID见 [result.json](result.json)。只有seed或未得到合格末验时也如实保留。没有响应幅度通过门。

新G0：passed={g0.get('passed')}，完整eval={g0.get('evaluations')}、reverse={g0.get('backwardCalls')}，耗时（含IO）={g0.get('secondsIncludingIO')} s。完整worker={summary.get('workerWallSeconds')} s，监督进程={supervisor.get('wallSeconds')} s。所有reference、资格、搜索和末验成本见result/summary；它们不是交互速度胜出证据。缺失／失败项不补造数值。

观测验收针对8bit码对应区间并允许冻结的1e−10 alpha容差，不等于重新量化逐码一致。result分别列区间违反量、码差数量和byteExact。本页以NumPy从实际alpha重算g/d及观测区间指标，不重新求解PDE，不替代独立完整field审核。

## 紧凑数据与复现出版

compact.npz：{size_text}。执行前已固定只保留三套完整obs/future alpha、theta，reference observed_uint8/lower/upper/denominator及g/d；**不含3D初速、末密度、风场或完整约束向量**。完整原NPZ文件身份及保留数组raw SHA记录于 [publication.json](publication.json)。保留数组使用原dtype并逐位压缩往返验证，不因大小或结果改变范围。未得到的最终核验不会用best trial或seed文件冒充替代。

在T12目录中，使用已有gs-sph-3d环境：

```text
C:/Users/seanzjxiao/miniconda3/envs/gs-sph-3d/python.exe -I -B publish_saved.py --execute --run runs/run-01 --output publish-NEW
```

默认不加--execute只打印stdlib计划。显式执行时仅在子进程设置MKL SEQUENTIAL和Library/bin DLL路径，使用已有NumPy/Matplotlib，不导入Torch、不启动GPU或新轨迹；输出拒绝覆盖。

这是固定模型和有限预算下的见证搜索记录，不是真实重建、人类创作需求、已辨识真实速度、新优化器或TOG贡献。若没有新的合格见证，不能把搜索失败等同唯一性或专用零空间方法的必要性。
'''
    (out / 'README.md').write_text(readme, encoding='utf-8')
    after = {path: sha(Path(path)) for path in before}
    if before != after:
        raise ValueError('Input changed during publication; output preserved')
    manifest = {'schema': 't12-publication-v1', 'createdUTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status': 'completed', 'producerStatus': summary.get('status'), 'producerDecision': summary.get('decision'),
                'inputsBefore': before, 'inputsAfter': after, 'inputsUnchanged': True,
                'sourceIdentityMatches': source_match, 'publisherSHA256': sha(Path(__file__)),
                'runtime': {'python': sys.version, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__,
                            'MKL_THREADING_LAYER': os.environ['MKL_THREADING_LAYER'], 'dllDirectory': str(dll),
                            'torchImported': 'torch' in sys.modules, 'gpuUsed': False},
                'compact': compact_info,
                'compactArrays': {k: {'shape': list(v.shape), 'dtype': v.dtype.str, 'bytes': v.nbytes,
                    'rawSHA256': hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()} for k, v in compact.items()},
                'files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(out.iterdir()) if p.is_file()},
                'scope': 'CPU publication and image-derived quantities only, not independent full-PDE verification'}
    write_json(out / 'publication.json', manifest)
    print(json.dumps({'status': 'completed', 'output': str(out), 'compact': compact_info, 'producerDecision': summary.get('decision')}, ensure_ascii=False))
    _ = dll_handle  # Keep Windows DLL search handle alive through all NumPy operations.


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--run', default='runs/run-01')
    p.add_argument('--output', default='publish-01')
    args = p.parse_args()
    run, out = (HERE / args.run).resolve(), (HERE / args.output).resolve()
    if not args.execute:
        print(json.dumps({'mode': 'plan', 'dataRead': False, 'numpyImported': 'numpy' in sys.modules,
                          'gpuUsed': False, 'run': str(run), 'output': str(out),
                          'compactTargetBytes': COMPACT_TARGET_BYTES, 'retainedArrayKeys': KEEP,
                          'omitted': ['3D velocity', '3D density', 'wind', 'full constraint vectors']}, ensure_ascii=False))
        return
    publish(run, out)


if __name__ == '__main__':
    main()
