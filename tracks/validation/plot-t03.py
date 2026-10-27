"""Plot saved T03 results only. No Torch import or simulation."""
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
task = repo / 'tracks/tog/tasks/t03-ordinary-conflict-screen'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--run', type=Path, help='Optional complete local worker archive; default uses the published clone-contained final bundles.')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
summary_path = args.run / 'summary.json' if args.run else task / 'result-summary.json'
report = json.loads(summary_path.read_text(encoding='utf-8'))
if report['status'] != 'completed' or len(report['arms']) != 2:
    raise SystemExit('Requires two completed arms; a failed qualification is not a result image.')
args.out.mkdir(parents=True, exist_ok=False)
files = {
    'approved': repo / 'tracks/tog/fixtures/r22/approved.npz',
    'target': repo / 'tracks/tog/tasks/t02-authored-upper-bend/run-01/target-full.npy',
    'edit_only': args.run / 'edit_only/T02/final.npz' if args.run else task / 'edit_only-final.npz',
    'joint': args.run / 'joint/T02/final.npz' if args.run else task / 'joint-final.npz',
    'summary': summary_path,
}
data = {'approved': np.load(files['approved'], allow_pickle=False)['frames'],
        'target': np.load(files['target'], allow_pickle=False)}
for name in ['edit_only', 'joint']:
    with np.load(files[name], allow_pickle=False) as packed:
        data[name] = packed['frames'].copy()
    expected = report['raw'][f'{name}/T02/final.npz']['sha256'] if args.run else report['publishedFinalArrays'][f'{name}-final.npz']['sha256']
    assert hashlib.sha256(files[name].read_bytes()).hexdigest() == expected
assert all(a.shape == (25, 64, 64) and np.isfinite(a).all() for a in data.values())
fig, axes = plt.subplots(3, 4, figsize=(11, 8.8), layout='constrained')
for r, frame in enumerate([16, 28, 40]):
    for c, name in enumerate(['approved', 'target', 'edit_only', 'joint']):
        ax = axes[r, c]
        ax.imshow(data[name][frame-16], origin='lower', cmap='gray', vmin=0, vmax=1,
                  extent=(0, 64, 0, 64), interpolation='nearest')
        for roi, color in [([10,12,34,55], '#ffaa33'), ([35,13,53,33], '#30db9a'), ([35,33,53,55], '#30db9a')]:
            x0,y0,x1,y1=roi
            ax.add_patch(Rectangle((x0,y0), x1-x0,y1-y0,fill=False,edgecolor=color,linewidth=.65))
        ax.set_title(f'{name} | frame {frame}', fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
fig.suptitle('T03 saved final states; common alpha scale [0,1]\nOrange: edit ROI. Green: protected ROIs. No exposure adjustment.', fontsize=12)
fig.savefig(args.out/'frames.png', dpi=145)
plt.close(fig)

target = data['target'][:,12:55,10:34]
target_scale = np.sqrt(np.mean(target**2, axis=(1,2)))
protected_rois = [(35,13,53,33),(35,33,53,55)]
fig, axes = plt.subplots(2,2,figsize=(10,6.8),layout='constrained')
for name, color in [('edit_only','#c04b20'),('joint','#246fa5')]:
    frames=data[name]
    edit_abs=np.sqrt(np.mean((frames[:,12:55,10:34]-target)**2,axis=(1,2)))
    axes[0,0].plot(range(16,41), edit_abs/target_scale*100, label=name, color=color)
    axes[0,1].plot(range(16,41), edit_abs, label=name, color=color)
    for i,(x0,y0,x1,y1) in enumerate(protected_rois):
        ref=data['approved'][:,y0:y1,x0:x1]
        absolute=np.sqrt(np.mean((frames[:,y0:y1,x0:x1]-ref)**2,axis=(1,2)))
        relative=absolute/np.sqrt(np.mean(ref**2,axis=(1,2)))
        axes[1,0].plot(range(16,41), relative*100, label=f'{name}, ROI {i+1}',color=color,linestyle=['-','--'][i])
        axes[1,1].plot(range(16,41), absolute,label=f'{name}, ROI {i+1}',color=color,linestyle=['-','--'][i])
for ax,title,gate in zip(axes.flat,['Edit relative RMS (%)','Edit absolute alpha RMS','Protection relative RMS (%)','Protection absolute alpha RMS'],[5,.01,2,.005]):
    ax.axhline(gate,color='black',linestyle=':',linewidth=1,label='gate')
    ax.set_title(title); ax.set_xlabel('Accepted frame'); ax.set_ylim(bottom=0); ax.grid(alpha=.2)
    ax.legend(fontsize=7)
fig.suptitle('Both relative and absolute gates apply at every frame; curves are recomputed from saved arrays',fontsize=11)
fig.savefig(args.out/'quality.png',dpi=145)
plt.close(fig)
pins={k:{'path':str(p.relative_to(repo)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in files.items()}
record={'scope':'Saved-array visualization only; no numerical rerun, timing, artist or audience validation',
        'inputs':pins,'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.out.glob('*.png')}}
(args.out/'plot-record.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
