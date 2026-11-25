"""Recheck the public camera diagnostics without the upstream PLY or NumPy."""
import gzip
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "t86-ignition-margin" / "public"


def data(p):
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes())


def main():
    shells = data(HERE.parent/"t87-stroke-halo"/"PREDICTIONS.json.gz")["shell_ids"]
    references = data(NATIVE/"capture-report.json")["shots"]
    root = HERE/"evidence"
    for cid in (0,124):
        full = data(root/f"camera-{cid}.json.gz")
        weights = data(root/f"weights-{cid}.json.gz")
        assert weights["eligible_weights"] == full["eligible_weights"]
        lookup = dict(weights["eligible_weights"])
        for arm, q in full["orders"].items():
            trace = data(NATIVE/f"{arm}-trace.json.gz")
            used = set(references[arm]["initial"]["ids"]) | set(references[arm]["edit"]["ids"])
            for frame in trace[:180]:
                used.update(frame["new_ids"])
            rem = set(shells[arm]) - used
            assert len(rem) == q["eligible"] and set(rem).issubset(lookup)
            total = math.fsum(lookup[i] for i in rem)
            assert math.isclose(total,q["mass"],rel_tol=1e-12)
            count = 0
            reached = []
            count_curve, matte_curve = [], []
            for frame in trace[180:]:
                onset = rem.intersection(frame["new_ids"])
                assert len(onset) <= len(rem)
                rem.difference_update(onset)
                reached.extend(lookup[i] for i in onset)
                count += len(onset)
                count_curve.append(count)
                matte_curve.append(math.fsum(reached))
            assert count_curve == q["counts"] and all(math.isclose(a,b,rel_tol=3e-13,abs_tol=2e-12)
                       for a,b in zip(matte_curve,q["cumulative_mass"]))
            for key,y,t in (("first_site",count_curve,1),("quarter_sites",count_curve,q["eligible"]/4),
                            ("quarter_matte",matte_curve,total/4)):
                got = next((i+1 for i,v in enumerate(y) if v>=t),None) if t>0 else None
                assert got == q[key], (cid,arm,key)
            print(cid,arm,q["first_site"],q["quarter_sites"],q["quarter_matte"])


if __name__ == "__main__":
    main()
