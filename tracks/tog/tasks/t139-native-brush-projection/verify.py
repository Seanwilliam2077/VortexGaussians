"""Verify the four archived native-style ordered alpha sequences and conditional shot inputs."""
import hashlib
import json
from pathlib import Path
import numpy as np

here=Path(__file__).resolve().parent
report=json.loads((here/"RESULTS.json").read_bytes())
with np.load(here/"contributions.npz",allow_pickle=False) as streams:
    for i,receipt in enumerate(report["nominal"]+report["nearest_pixel_diagnostic"]):
        ids,alpha,buckets=[streams[f"ray_{i}_{k}"] for k in ("ids","alpha","buckets")]
        assert len(ids)==len(alpha)==len(buckets)==receipt["contributors"]
        assert hashlib.sha256(ids.tobytes()).hexdigest()==receipt["source_ids_sha256"]
        assert hashlib.sha256(alpha.tobytes()).hexdigest()==receipt["alpha_sha256"]
        assert np.array_equal(np.lexsort((ids,buckets)),np.arange(len(ids)))
        assert ((alpha>0)&(alpha<=1)).all()
        assert 867267 not in ids
        for key,dtype in (("full",float),("fp16",np.float16)):
            a=0.
            for j,weight in enumerate(alpha):
                prior=a
                a=float(dtype(prior+(1-prior)*float(weight)))
                if a>=.5:
                    assert receipt[key]==dict(id=int(ids[j]),rank=j+1,before=prior,after=a)
                    break
            else:
                raise AssertionError("No crossing")
controls=report["native_input"]
assert controls["view_geometry"][1]["world_depth_A_B"][1]+.26<.2
assert controls["material_count"]==1244819 and controls["geometric_shell_count"]==1041
print([r["full"]["id"] for r in report["nominal"]], "four alpha sequences verified")
