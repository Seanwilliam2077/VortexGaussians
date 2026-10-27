"""Explicit R20 scene fork: initial_state unchanged; witness recipes removed.

The two plumes and initial velocity are synthetic development data, not
reconstructed observations or a validated artist requirement.
"""
import math
import torch

CONFIG = {"plume_xz": [[0.32, 0.43], [0.67, 0.57]]}

def initial_state(model):
    x,y,z=model.centers.unbind(-1)
    vertical=torch.sigmoid((y-.16)/.025)-torch.sigmoid((y-.62)/.025)
    rho=sum(4*torch.exp(-.5*((x-cx)/.055)**2-.5*((z-cz)/.075)**2)*vertical
            for cx,cz in CONFIG['plume_xz'])
    v=torch.stack([.025*torch.sin(2*math.pi*model.faces[0][...,1]),
                   .12+.02*torch.sin(2*math.pi*model.faces[1][...,2]),
                   .025*torch.sin(2*math.pi*model.faces[2][...,0])])
    return model.project(v),rho
