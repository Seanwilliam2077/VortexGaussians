"""Visualize the published T07 result; saved arrays only, no simulation."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

repo = Path(__file__).resolve().parents[2]
task = repo / 'tracks/tog/tasks/t07-ordinary-timing-revision'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
files = {
    'approved': repo / 'tracks/tog/fixtures/r22/approved.npz',
    'target': repo / 'tracks/tog/tasks/t06-authored-timing-revision/run-01/target-full.npy',
    'T05_previous': repo / 'tracks/tog/tasks/t05-framewise-cold-start/framewise_joint-final.npz',
    'T07_joint': task / 'framewise_joint-final.npz',
    'summary': task / 'result-summary.json',
}
report = json.loads(files['summary'].read_text(encoding='utf-8'))
assert report['status'] == 'completed' and len(report['arms']) == 1
expected = report['publishedFinalArrays']['framewise_joint-final.npz']['sha256']
assert hashlib.sha256(files['T07_joint'].read_bytes()).hexdigest() == expected
data = {'target': np.load(files['target'], allow_pickle=False)}
for name in ['approved', 'T05_previous', 'T07_joint']:
    with np.load(files[name], allow_pickle=False) as packed:
        data[name] = packed['frames'].copy()
assert all(a.shape == (25, 64, 64) and np.isfinite(a).all() for a in data.values())
args.out.mkdir(parents=True, exist_ok=False)
rois = [([10,12,34,55], '#ffaa33'), ([35,13,53,33], '#30db9a'), ([35,33,53,55], '#30db9a')]
fig, axes = plt.subplots(3, 4, figsize=(11, 8.8), layout='constrained')
for r, frame in enumerate([24, 32, 40]):
    for c, name in enumerate(['approved', 'target', 'T05_previous', 'T07_joint']):
        ax = axes[r, c]
        ax.imshow(data[name][frame-16], origin='lower', cmap='gray', vmin=0, vmax=1,
                  extent=(0,64,0,64), interpolation='nearest')
        for (x0,y0,x1,y1), color in rois:
            ax.add_patch(Rectangle((x0,y0), x1-x0,y1-y0, fill=False, edgecolor=color, linewidth=.65))
        ax.set_title(f'{name} | frame {frame}', fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
fig.suptitle('T07: ordinary solution for the authored timing revision\nCommon alpha scale [0,1]; orange edit ROI, green protected ROIs', fontsize=12)
fig.savefig(args.out/'frames.png', dpi=145)
plt.close(fig)

target = data['target'][:,12:55,10:34]
target_scale = np.sqrt(np.mean(target**2, axis=(1,2)))
fig, axes = plt.subplots(2,2,figsize=(10,6.8),layout='constrained')
metrics = {}
for name, color in [('T05_previous','#bf6732'),('T07_joint','#246fa5')]:
    frames = data[name]
    edit_abs = np.sqrt(np.mean((frames[:,12:55,10:34]-target)**2,axis=(1,2)))
    edit_rel = edit_abs/target_scale
    axes[0,0].plot(range(16,41), edit_rel*100, label=name, color=color)
    axes[0,1].plot(range(16,41), edit_abs, label=name, color=color)
    protection = []
    for i,((x0,y0,x1,y1),_) in enumerate(rois[1:]):
        ref = data['approved'][:,y0:y1,x0:x1]
        absolute = np.sqrt(np.mean((frames[:,y0:y1,x0:x1]-ref)**2,axis=(1,2)))
        relative = absolute/np.sqrt(np.mean(ref**2,axis=(1,2)))
        protection.append(int(((relative <= .02) & (absolute <= .005)).sum()))
        axes[1,0].plot(range(16,41), relative*100, label=f'{name}, ROI {i+1}', color=color, linestyle=['-','--'][i])
        axes[1,1].plot(range(16,41), absolute, label=f'{name}, ROI {i+1}', color=color, linestyle=['-','--'][i])
    metrics[name] = {'editPassingFrames':int(((edit_rel <= .05) & (edit_abs <= .01)).sum()), 'protectionPassingROIFrames':sum(protection)}
assert metrics['T07_joint'] == {'editPassingFrames':25, 'protectionPassingROIFrames':50}
for ax,title,gate in zip(axes.flat,['Edit relative RMS (%)','Edit absolute alpha RMS','Protection relative RMS (%)','Protection absolute alpha RMS'],[5,.01,2,.005]):
    ax.axhline(gate,color='black',linestyle=':',linewidth=1,label='gate')
    ax.set_title(title)
    ax.set_xlabel('Frame')
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.2)
    ax.legend(fontsize=7)
fig.suptitle('Original per-frame gates, recomputed from final saved images\nT07 changes the target and uses paid T05 controls; these curves are not a speed comparison', fontsize=10)
fig.savefig(args.out/'quality.png',dpi=145)
plt.close(fig)
record = {
    'scope':'Saved-array visualization only; no simulation, new timing, artist or audience validation',
    'scriptSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'inputs':{k:{'path':str(p.relative_to(repo)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in files.items()},
    'metrics':metrics,
    'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.glob('*.png')},
}
(args.out/'plot-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
