"""Inspect a sealed timing revision against existing images; CPU, no rollout."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

here = Path(__file__).resolve().parent
track = here.parent.parent
out = here/'review-01'
assert not out.exists(), 'No overwrite'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
files = {
    'approved':track/'fixtures/r22/approved.npz',
    'T02_target':here.parent/'t02-authored-upper-bend/run-01/target-full.npy',
    'T06_target':here/'run-01/target-full.npy',
    'T04_solution':here.parent/'t04-framewise-feasibility/framewise_joint-final.npz',
    'generation':here/'run-01/summary.json',
}
generation = json.loads(files['generation'].read_text(encoding='utf-8'))
assert generation['status']=='completed' and generation['sourcesAndD01Unchanged']
assert sha(files['T06_target'])==generation['outputs']['target-full.npy']['sha256']
data = {}
for name,p in files.items():
    if name=='generation':continue
    if p.suffix=='.npy':data[name]=np.load(p,allow_pickle=False)
    else:
        with np.load(p,allow_pickle=False) as z:data[name]=z['frames'].copy()
assert np.array_equal(data['T06_target'][:9],data['approved'][:9])
assert np.array_equal(data['T06_target'][-1],data['T02_target'][-1])
target = data['T06_target'][:,12:55,10:34]
rois = [(35,13,53,33),(35,33,53,55)]
scores = {}
for name in ['approved','T04_solution']:
    frames=data[name]
    absolute=np.sqrt(np.mean((frames[:,12:55,10:34]-target)**2,axis=(1,2)))
    relative=absolute/np.sqrt(np.mean(target**2,axis=(1,2)))
    passed=(relative<=.05)&(absolute<=.01)
    protected=[]
    for x0,y0,x1,y1 in rois:
        ref=data['approved'][:,y0:y1,x0:x1]
        ae=np.sqrt(np.mean((frames[:,y0:y1,x0:x1]-ref)**2,axis=(1,2)))
        re=ae/np.sqrt(np.mean(ref**2,axis=(1,2)))
        protected.extend(((ae<=.005)&(re<=.02)).tolist())
    scores[name]={'editRelativeRMS':relative.tolist(),'editAbsoluteRMS':absolute.tolist(),
        'editPassingFrames':int(passed.sum()),'editFailingFrameIds':[i+16 for i,p in enumerate(passed) if not p],
        'protectedPassingROIFrames':sum(protected),'imageGatesPass':bool(passed.all() and all(protected))}
out.mkdir()
fig,axes=plt.subplots(3,4,figsize=(11,8.5),layout='constrained')
for r,frame in enumerate([24,32,40]):
    for c,name in enumerate(['approved','T02_target','T06_target','T04_solution']):
        ax=axes[r,c]
        ax.imshow(data[name][frame-16],origin='lower',cmap='gray',vmin=0,vmax=1,extent=(0,64,0,64),interpolation='nearest')
        for roi,color in [((10,12,34,55),'#ffaa33')]+[(r,'#30db9a') for r in rois]:
            x0,y0,x1,y1=roi
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor=color,linewidth=.65))
        ax.set_title(f'{name} | frame {frame}',fontsize=9)
        ax.set_xticks([]);ax.set_yticks([])
fig.suptitle('Timing revision: hold through frame 24, reach the same end target at frame 40\nFixed alpha [0,1]. Researcher-authored development input; no new simulation.',fontsize=11)
fig.savefig(out/'timing-revision.png',dpi=145)
plt.close(fig)
report={'scope':'Saved-image analysis only; no control search or artist validation',
    'scriptSHA256':sha(Path(__file__)),
    'inputs':{k:{'path':str(p.relative_to(track)).replace('\\','/'),'sha256':sha(p)} for k,p in files.items()},
    'invariants':{'frames16to24EqualApproved':True,'frame40EqualT02':True},
    'scoresAgainstT06':scores,
    'oldQualifiedT04NeedsRevision':not scores['T04_solution']['imageGatesPass'],
    'qualificationScope':'Image gates only. T04 control/numerical qualification remains in its original independent audit.',
    'outputSHA256':sha(out/'timing-revision.png')}
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'invariants':report['invariants'],'T04RequiresRevision':report['oldQualifiedT04NeedsRevision'],
    'zeroEditPass':scores['approved']['editPassingFrames'],'T04EditPass':scores['T04_solution']['editPassingFrames'],
    'T04WorstEditRelative':max(scores['T04_solution']['editRelativeRMS']),
    'T04ProtectionPass':scores['T04_solution']['protectedPassingROIFrames']},indent=2))
