"""Publish T11 saved arrays only. Default: stdlib plan; --execute: CPU plotting.

This module never imports the simulator, Torch, or a GPU runtime.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
MAX_COMPACT_BYTES = 5_000_000


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
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if out.exists():
        raise FileExistsError('Fresh publication directory required: ' + str(out))
    if not out.is_relative_to(HERE) or out.is_relative_to(run):
        raise ValueError('Publication must be a new T11 directory outside raw run')
    worker = run / 'worker'
    input_paths = [worker / 'summary.json', worker / 'observations.npz', worker / 'future.npz',
                   run / 'supervisor.json', run / 'stdout.log', run / 'stderr.log',
                   HERE / 'config.json', HERE / 'PROTOCOL.md', HERE / 'freeze.json', Path(__file__)]
    before = {str(p): sha(p) for p in input_paths}
    summary = json.loads((worker / 'summary.json').read_text(encoding='utf-8'))
    supervisor = json.loads((run / 'supervisor.json').read_text(encoding='utf-8'))
    config = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    if summary['status'] != 'completed' or supervisor['status'] != 'completed':
        raise ValueError('Only completed saved runs may be published')
    if not summary['sourcesUnchanged'] or not supervisor['sourcesUnchanged']:
        raise ValueError('Producer source authentication failed')
    for pin in summary['sourcesBefore'].values():
        p = (HERE / pin['path']).resolve()
        if sha(p) != pin['sha256']:
            raise ValueError('Current source differs from saved run: ' + str(p))
        before[str(p)] = sha(p)
    if sha(HERE / 'freeze.json') != summary['freezeSHA256']:
        raise ValueError('Freeze identity mismatch')

    def load_selected(name, keys):
        path = worker / name
        spec = summary['arrays'][name]
        if sha(path) != spec['sha256'] or path.stat().st_size != spec['bytes']:
            raise ValueError('Saved file identity mismatch: ' + name)
        selected = {}
        with np.load(path, allow_pickle=False) as saved:
            for key in keys:
                a = np.ascontiguousarray(saved[key])
                rec = spec['arrays'][key]
                if (list(a.shape) != rec['shape'] or a.dtype.str != rec['dtype'] or
                        hashlib.sha256(a.tobytes()).hexdigest() != rec['rawSHA256']):
                    raise ValueError('Saved array identity mismatch: ' + name + ':' + key)
                if not np.isfinite(a).all():
                    raise ValueError('Nonfinite publication array')
                selected[key] = a
        return selected

    obs = load_selected('observations.npz', ('alpha', 'indices'))
    future = load_selected('future.npz', ('alpha', 'alpha_response', 'source_q', 'density_final',
                                          'g_R', 'response_mass_ratio', 'indices'))
    if obs['alpha'].shape != (2, 21, 64, 64) or future['alpha'].shape != (4, 21, 64, 64):
        raise ValueError('Unexpected fixed T11 image shape')
    if config['future_order'] != ['plus_unedited', 'plus_edited', 'minus_unedited', 'minus_edited']:
        raise ValueError('Unexpected branch order')
    if not np.array_equal(obs['indices'], np.arange(21)) or not np.array_equal(future['indices'], np.arange(21)):
        raise ValueError('Unexpected fixed index schedule')
    derived = np.stack((future['alpha'][1] - future['alpha'][0], future['alpha'][3] - future['alpha'][2]))
    if not np.array_equal(derived, future['alpha_response']):
        raise ValueError('Saved alpha response is not edited minus unedited')
    final_rho = future['density_final']
    right = (np.arange(32) + .5) / 32 >= .5
    final_g = np.asarray([(final_rho[1] - final_rho[0])[right].sum(),
                          (final_rho[3] - final_rho[2])[right].sum()]) / future['source_q'].sum()
    if not np.allclose(final_g, future['g_R'][:, -1], rtol=0, atol=1e-12):
        raise ValueError('Final saved g_R differs from final density recomputation')

    out.mkdir()
    compact = {'observation_alpha': obs['alpha'], 'observation_indices': obs['indices'],
               'future_alpha': future['alpha'], 'future_indices': future['indices'],
               'alpha_response': future['alpha_response'], 'g_R': future['g_R'],
               'response_mass_ratio': future['response_mass_ratio'],
               'source_q': future['source_q'], 'density_final': future['density_final']}
    with (out / 'compact.npz').open('xb') as f:
        np.savez_compressed(f, **compact)
    compact_bytes = (out / 'compact.npz').stat().st_size
    if compact_bytes >= MAX_COMPACT_BYTES:
        raise ValueError('Compact file exceeds predeclared 5 MB budget; preserve output, do not truncate')
    with np.load(out / 'compact.npz', allow_pickle=False) as copied:
        if set(copied.files) != set(compact) or not all(np.array_equal(copied[k], v) for k, v in compact.items()):
            raise ValueError('Compact roundtrip failed')

    obs_diff = obs['alpha'][0] - obs['alpha'][1]
    response_difference = future['alpha_response'][0] - future['alpha_response'][1]
    alpha_max = float(max(obs['alpha'].max(), future['alpha'].max()))
    response_max = float(np.abs(future['alpha_response']).max())
    delta_limit = max(response_max, float(np.abs(response_difference).max()), 1e-15)
    obs_max = float(np.abs(obs_diff).max())
    rho_max = max(r['densityMaxAbsolute'] for r in summary['observationComparisons'])
    t = future['indices'] * config['model']['dt']
    plot_data = {'schema': 't11-saved-publication-v1', 'decisionFromProducer': summary['decision'],
                 'origin': 'lower-left; array row is screen y', 'observationStepShown': 20,
                 'futureIndexShown': 20, 'absoluteStepShown': 40,
                 'observationMaxAlphaAbsolute': obs_max, 'observationMaxDensityAbsolute': rho_max,
                 'alphaColorLimits': [0, alpha_max], 'observationDifferenceColorLimits': [-1e-10, 1e-10],
                 'responseColorLimits': [-delta_limit, delta_limit],
                 'futureModelTime': t.tolist(), 'g_R': future['g_R'].tolist(),
                 'g_R_plus_minus': (future['g_R'][0] - future['g_R'][1]).tolist(),
                 'alphaResponseDifferenceMaxAbsByFrame': np.abs(response_difference).max(axis=(1, 2)).tolist(),
                 'responseMassRatio': future['response_mass_ratio'].tolist(),
                 'finalGRecomputedFromSavedDensity': final_g.tolist(),
                 'scope': 'Analytically constructed same observations; local density source, not wind. No confidence interval or response-size gate.'}
    write_json(out / 'plot-data.json', plot_data)

    plt.rcParams.update({'font.size': 9, 'axes.titlesize': 10, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(3, 4, figsize=(15.5, 11.5), layout='constrained')
    fig.suptitle('T11 | Observation-compatible shear histories and a local tracer source', fontsize=15)

    def panel(ax, a, title, limits, cmap):
        im = ax.imshow(a, origin='lower', interpolation='nearest', extent=(-.5, 63.5, -.5, 63.5),
                       vmin=limits[0], vmax=limits[1], cmap=cmap)
        ax.set_title(title)
        ax.set_xticks([0, 32, 63]); ax.set_yticks([0, 32, 63])
        ax.set_xlabel('screen x (pixel)'); ax.set_ylabel('screen y (pixel)')
        fig.colorbar(im, ax=ax, shrink=.8, pad=.02)

    panel(axes[0, 0], obs['alpha'][0, -1], 'Observation step 20: + shear', (0, alpha_max), 'magma')
    panel(axes[0, 1], obs['alpha'][1, -1], 'Observation step 20: - shear', (0, alpha_max), 'magma')
    panel(axes[0, 2], obs_diff[-1], 'Observation alpha difference (+ minus -)', (-1e-10, 1e-10), 'RdBu_r')
    axes[0, 3].axis('off')
    axes[0, 3].text(0, .96,
        'Preconstructed analytic qualification\n\n'
        'Same x-independent density; opposite\nx shear. Histories computed separately.\n\n'
        f'Observed steps 0-20 max |delta alpha|\n{obs_max:.3e}\n'
        f'Max |delta density|: {rho_max:.3e}\n\n'
        'At step 20: add the same local q.\nThis is a density-source edit, NOT wind.\n\n'
        'PASS concerns numerical qualification.\nNo response-size success threshold.\nNo confidence interval or risk certificate.',
        transform=axes[0, 3].transAxes, va='top', linespacing=1.35)
    for col, title in enumerate(('+ shear | unedited', '+ shear | source added', '- shear | unedited', '- shear | source added')):
        panel(axes[1, col], future['alpha'][col, -1], 'Future +20: ' + title, (0, alpha_max), 'magma')
    panel(axes[2, 0], future['alpha_response'][0, -1], 'Source response: + shear (E - U)', (-delta_limit, delta_limit), 'RdBu_r')
    panel(axes[2, 1], future['alpha_response'][1, -1], 'Source response: - shear (E - U)', (-delta_limit, delta_limit), 'RdBu_r')
    panel(axes[2, 2], response_difference[-1], 'Response difference: (E-U)+ - (E-U)-', (-delta_limit, delta_limit), 'RdBu_r')
    ax = axes[2, 3]
    ax.plot(t, future['g_R'][0], color='#bf5700', marker='o', markersize=3, label='+ shear response')
    ax.plot(t, future['g_R'][1], color='#0072b2', marker='s', markersize=3, label='- shear response')
    ax.plot(t, future['g_R'][0] - future['g_R'][1], color='black', linestyle='--', label='response difference')
    ax.set_title('Right-half response g_R(t)')
    ax.set_xlabel('Model time after source (0.025 per step)')
    ax.set_ylabel('Sum of density response / original sum(q)')
    ax.set_xlim(0, t[-1]); ax.set_ylim(0, 1); ax.grid(alpha=.25); ax.legend(fontsize=8, loc='upper left')
    ax.text(.02, .03, 'R: cell-center x >= 0.5\nNot probability; no mass-conservation claim.', transform=ax.transAxes, fontsize=8)
    fig.savefig(out / 'source-response.png', dpi=170)
    fig.savefig(out / 'source-response.svg')
    plt.close(fig)

    for src, name in ((worker / 'summary.json', 'summary.json'), (run / 'supervisor.json', 'supervisor.json'),
                      (run / 'stdout.log', 'stdout.log'), (run / 'stderr.log', 'stderr.log'),
                      (HERE / 'config.json', 'config.json'), (HERE / 'PROTOCOL.md', 'PROTOCOL.md'),
                      (HERE / 'freeze.json', 'freeze.json')):
        shutil.copyfile(src, out / name)
    final_plus, final_minus = future['g_R'][:, -1]
    readme = f'''# T11 保存结果：局部示踪源响应

这是一次解析输入的数值资格检查，不是新方法、真实重建或创作效益实验。两个符号分支从各自速度独立推进；相同观测来自事先构造的 x 独立密度，而非从真实照片恢复的唯一解释。

![观测与源响应](source-response.png)

原结果为 `{summary['decision']}`，完成 {summary['stepsCompleted']} 次原 core.step。观测0–20步的密度最大绝差 {rho_max:.8g}，alpha最大绝差 {obs_max:.8g}。末端 g_R(+)=**{final_plus:.8f}**、g_R(-)=**{final_minus:.8f}**；末帧两条 alpha 响应最大绝差 **{np.abs(response_difference[-1]).max():.8f}**。响应幅度只作描述，没有响应大小通过门。

图的第一行显示观测 step20，第二行是操作后20步（绝对 step40）的四个实际分支，第三行使用 alpha_E−alpha_U，而非 render(q)。各组共用色标，观测差图固定在±1e−10资格门。图像原点在左下；g_R是世界右半区 x≥0.5 的密度响应除以原始 sum(q)，不是屏幕ROI、概率或置信区间。半拉格朗日推进不保证质量守恒。操作是添加局部密度源，**不是风或障碍**。

worker总时长 {summary['workerWallSeconds']:.6f} s，监督进程 {supervisor['wallSeconds']:.6f} s；观测/续算同步计算含检查、渲染及读回为 {summary['observationSecondsIncludingRenderChecksAndReadback']:.6f}/{summary['futureSecondsIncludingRenderChecksAndReadback']:.6f} s。这些是一次资格执行成本，不是交互性能比较。

## 数据范围与重画

[compact.npz](compact.npz) 为 {compact_bytes:,} B，完整保留两条观测和四条未来的全部21帧alpha、两条alpha响应、g_R及响应质量比、q和四支末密度；所有保留数组与原保存数据逐位相同。未复制完整密度轨迹和速度场，因而这个紧凑发布不能独立重放原PDE或完成全部物理审核。原始NPZ身份、所选数组身份、发布前后来源锁见 [publication.json](publication.json)。[plot-data.json](plot-data.json) 给出曲线、色标及时间含义。

脚本默认仅打印计划，不读取结果或导入绘图库。保持原raw后，可从T11目录运行：

```text
python -I -B publish_saved.py --execute --run runs/run-01 --output publish-NEW
```

需已有 NumPy／Matplotlib，不导入Torch或求解器、不使用GPU；输出必须是全新目录。[summary.json](summary.json)、[supervisor.json](supervisor.json)、日志及冻结合同为原始文件副本。这里的检查只是发布完整性及末端g_R复算，不冒充独立全轨迹物理审核。

此例只证明这套差分观测管线可以呈现已知构造的分歧。它不证明自动发现观测兼容状态、可信覆盖、一般反事实可辨识性或TOG贡献；也不是第三条同类图像编辑目标。
'''
    (out / 'README.md').write_text(readme, encoding='utf-8')
    after = {path: sha(Path(path)) for path in before}
    if after != before:
        raise ValueError('Input changed during publication; output preserved')
    files = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(out.iterdir()) if p.is_file()}
    manifest = {'schema': 't11-publication-v1', 'createdUTC': dt.datetime.now(dt.timezone.utc).isoformat(),
                'status': 'completed', 'inputsBefore': before, 'inputsAfter': after, 'inputsUnchanged': True,
                'run': str(run), 'publisher': str(Path(__file__).resolve()), 'publisherSHA256': sha(Path(__file__)),
                'runtime': {'python': sys.version, 'numpy': np.__version__, 'matplotlib': matplotlib.__version__, 'gpuUsed': False},
                'compactBytes': compact_bytes, 'compactBudgetBytes': MAX_COMPACT_BYTES, 'compactRoundtripExact': True,
                'compactArrays': {k: {'shape': list(v.shape), 'dtype': v.dtype.str, 'bytes': v.nbytes,
                    'rawSHA256': hashlib.sha256(v.tobytes()).hexdigest()} for k, v in compact.items()},
                'scope': 'Saved-result publication; no simulation and no independent full-trajectory PDE audit', 'files': files}
    write_json(out / 'publication.json', manifest)
    print(json.dumps({'status': 'completed', 'output': str(out), 'compactBytes': compact_bytes,
                      'figure': str(out / 'source-response.png'), 'inputsUnchanged': True}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--run', default='runs/run-01')
    parser.add_argument('--output', default='publish-01')
    args = parser.parse_args()
    run, out = (HERE / args.run).resolve(), (HERE / args.output).resolve()
    if not args.execute:
        print(json.dumps({'mode': 'plan', 'run': str(run), 'output': str(out), 'dataRead': False,
                          'numpyImported': 'numpy' in sys.modules, 'gpuUsed': False,
                          'compactBudgetBytes': MAX_COMPACT_BYTES}, ensure_ascii=False))
        return
    publish(run, out)


if __name__ == '__main__':
    main()
