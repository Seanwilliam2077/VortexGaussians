"""CPU-only controls for acquisition and verification. Never open a native device."""
import argparse
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from verify import alight, controls, decode, load_arm, next_fuel
import capture


def replay_controls(path):
    stage={}
    native_tex=SimpleNamespace(size=(3,2,1))
    zero=SimpleNamespace(size=native_tex.size)
    token=object()
    solver=SimpleNamespace(_k={"react":token},burn_obj=[native_tex],stain=None,aux=None,chem=None,upres=3)
    g=SimpleNamespace(read=lambda dst,origin,box:dst.copy())
    solver.gpu=g
    calls=[]
    def fake_run(kernel,bindings,uniform,size):
        calls.append(bindings[11] is native_tex)
        bindings[6][...,1]=1 if calls[-1] else 0
    batch=SimpleNamespace(run=fake_run,submit=lambda restart:None)
    def ordinary(b,dt,*,fine):
        scale=3 if fine else 1
        params=np.zeros((13,4),dtype="<f4")
        params[2,3]=dt
        params[8,:3]=[9,.5,1]
        params[9,1]=1
        params[12,0]=scale
        dst=np.full((scale,scale,scale,4),2.,dtype=np.float16)
        bindings=[object() for _ in range(15)]
        bindings[11],bindings[6]=native_tex,dst
        b.run(token,bindings,params,(scale,)*3)
        assert np.all(dst[...,1]==1)
    box=((0,0,0),(1,1,1))
    with patch.object(capture,"ROI",box), patch("verify.ROI",box):
        for fine in (False,True):
            capture.contrast(batch,solver,zero,1/24,fine,ordinary,(),path,stage)
        out=controls(path,dict(controls=stage,dims=[1]*3))
    assert calls==[False,True,False,True]
    assert out["coarse"]["changed_by_channel"]==[0,1,0,0] and out["fine"]["changed_by_channel"]==[0,27,0,0]


def main():
    # A floating progress just below one can round onto one before the next input test.
    m=np.array([[[[1., np.float32(.9999), 2., 0.],
                 [1., np.float32(.999), 1., 0.]]]],dtype="<f2")
    lit=alight(m)
    assert lit[0,0].tolist()==[True,False]
    fast=next_fuel(m[...,0],lit,1/24,.2)
    slow=next_fuel(m[...,0],lit,1/24,.1)
    assert fast[0,0,0]<slow[0,0,0]<1 and fast[0,0,1]==slow[0,0,1]==1
    assert capture.lower_after(.151,1/24) is None and capture.lower_after(None,.001) is None
    base=capture.T151/"evidence"
    updates,states,_=load_arm(base,"default")
    elapsed=0
    lower=.75
    for row in updates:
        lower=capture.lower_after(lower,float(np.float32(row["dt"])))
        elapsed+=lower is not None
    assert elapsed==112 and 0.3<lower<.4
    # Known ordinary data can validate the acquisition layout and the exact recurrence
    # where a consecutive default boundary exists. No 10-second native trajectory is used.
    prior=None
    dense=0
    for i,mat in decode(base/"default-atlas.zlib",states):
        if prior is not None and i==last+1:
            ref=next_fuel(prior[...,0],alight(prior),updates[last]["dt"],.2)
            assert np.array_equal(ref.view("<u2"),mat[...,0].view("<u2"))
            dense+=1
        prior,last=mat,i
    with tempfile.TemporaryDirectory(prefix="plateau-probe-") as tmp:
        replay_controls(Path(tmp))
    print(f"Known 5s steps admitted {elapsed}, final conservative lower bound {lower:.8f}, "
          f"known consecutive native fuel matches {dense}. Both matched-input mock controls passed.")


if __name__=="__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
