"""Frozen-before-data R20 development scene; synthetic target witnesses only."""
import math
import torch

CONFIG = {
    'version': 'r20-v1', 'n':32, 'steps':40, 'dt':0.025, 'frame_start':16,
    'dtype':'float64', 'control_shape':[4,3,8,8,8],
    'protected_rois':[[35,13,53,33],[35,33,53,55]],
    'edit_roi':[10,12,34,55], 'roi_order':'x0,y0,x1,y1; lower-left; half-open',
    'protect_relative':0.02, 'protect_absolute':0.005,
    'edit_relative':0.05, 'edit_absolute':0.01, 'signal_min':0.01,
    'exposure_relative':0.05, 'exposure_min_frames':8,
    'coefficient_max':0.5, 'coefficient_rms':0.2, 'applied_force_max':0.5,
    'fd_steps':[0.001,0.0005], 'fd_relative_gate':0.001, 'dual_gate':1e-8,
    'derivative_seed':20261026, 'derivative_directions':4,
    'structure_rank':16, 'structure_sketch':32, 'structure_holdout':16,
    'structure_seed':20261027, 'holdout_seed':20261028,
    'structure_relative_median_gate':0.25, 'structure_relative_max_gate':0.5,
    'density':'4 * sum(two xz Gaussians sigma (.055,.075)) * y soft window [.16,.62], softness .025',
    'plume_xz':[[0.32,0.43],[0.67,0.57]],
    'velocity':'ux=.025 sin(2pi y), uy=.12+.02 sin(2pi z), uz=.025 sin(2pi x); MAC project',
    'witness_center':[0.30,0.43,0.43], 'witness_radius':0.22,
    'witness_vectors':[
        [[.12,0,0],[.12,0,0],[0,0,0],[0,0,0]],
        [[-.12,0,0],[-.12,0,0],[0,0,0],[0,0,0]],
        [[0,0,0],[.10,.05,0],[-.10,.05,0],[0,0,0]],
        [[0,0,0],[.08,0,0],[.08,0,.10],[0,0,.10]]],
}

def initial_state(model):
    x,y,z=model.centers.unbind(-1)
    vertical=torch.sigmoid((y-.16)/.025)-torch.sigmoid((y-.62)/.025)
    rho=sum(4*torch.exp(-.5*((x-cx)/.055)**2-.5*((z-cz)/.075)**2)*vertical
            for cx,cz in CONFIG['plume_xz'])
    v=torch.stack([.025*torch.sin(2*math.pi*model.faces[0][...,1]),
                   .12+.02*torch.sin(2*math.pi*model.faces[1][...,2]),
                   .025*torch.sin(2*math.pi*model.faces[2][...,0])])
    return model.project(v),rho

def witnesses(model):
    ijk=torch.stack(torch.meshgrid(*[torch.arange(8,dtype=model.dtype,device=model.device)]*3,indexing='ij'),dim=-1)
    center=model._constant(CONFIG['witness_center'])
    weights=[]
    for offset in model.FACE_OFFSETS:
        points=(ijk+model._constant(offset))/8
        weights.append(torch.clamp(1-((points-center)**2).sum(-1)/CONFIG['witness_radius']**2,min=0)**2)
    w=torch.stack(weights)
    return [model._constant(v)[:,:,None,None,None]*w[None] for v in CONFIG['witness_vectors']]

def crop(frames,roi):
    x0,y0,x1,y1=roi
    return frames[...,y0:y1,x0:x1]

def protect_vector(frames,approved):
    # Each frame/ROI scaled by its fixed RMS and sqrt(pixel count). Thus
    # Euclidean norm squared is the sum of per-region relative MSEs.
    pieces=[]
    for roi in CONFIG['protected_rois']:
        ref=crop(approved,roi)
        scale=ref.square().mean((-2,-1)).sqrt()
        pixels=ref.shape[-1]*ref.shape[-2]
        pieces.append((crop(frames,roi)/(scale[:,None,None]*math.sqrt(pixels))).reshape(-1))
    return torch.cat(pieces)
