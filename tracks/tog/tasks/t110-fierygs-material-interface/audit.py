"""Audit an independently recorded full FieryGS run against its source and occupied wood components."""
import argparse
import ast
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
UPSTREAM_SHA = "4165031ae0ba8970981fd207491d20102b9a990bd7436aaeaf39b13239bbce4e"
STEPS = [0, 3, 10, 30, 60]


def components(coords):
    remaining = set(map(tuple, coords.tolist()))
    sizes = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            i,j,k = stack.pop()
            size += 1
            for near in ((i+1,j,k),(i-1,j,k),(i,j+1,k),(i,j-1,k),(i,j,k+1),(i,j,k-1)):
                if near in remaining:
                    remaining.remove(near)
                    stack.append(near)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def main():
    root = HERE.parents[4]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native",type=Path,default=root/"fierygs-native128-plume-staging"/"run-01")
    parser.add_argument("--source",type=Path,default=root/"baselines"/"FieryGS"/"simulation"/"fire_main.py")
    parser.add_argument("--out",type=Path,default=HERE)
    args = parser.parse_args()
    src = args.source.read_bytes()
    assert hashlib.sha256(src).hexdigest() == UPSTREAM_SHA
    tree = ast.parse(src.decode("utf8"))
    methods = {m.name:m for c in tree.body if isinstance(c,ast.ClassDef) for m in c.body if isinstance(m,ast.FunctionDef)}
    contract = {}
    for name in ("sample","update_wood_temperature","update_occupancy","update_coef","step"):
        node = methods[name]
        refs = sorted({n.attr for n in ast.walk(node) if isinstance(n,ast.Attribute) and
                       isinstance(n.value,ast.Name) and n.value.id == "self"})
        contract[name] = dict(line=node.lineno,self_fields_or_methods=refs)
    assert set(contract["update_wood_temperature"]["self_fields_or_methods"]) == {
        "occupancy","T_ign_wood","T_max_wood","sample","inv_dx","beta","T_air_wood","c_m"}
    assert not ({"velocities_pair","temperature_pair","dens_pair","pressures_pair"} &
                set(contract["update_occupancy"]["self_fields_or_methods"]))
    manifest = json.loads((args.native/"worker-result.json").read_bytes())
    assert manifest["completedSteps"] == 60
    by_step = {r["step"]:r for r in manifest["checkpoints"]}
    observations = {r["step"]:r["exposure"] for r in manifest["observations"]}
    outputs = []
    payload = {}
    baseline = None
    for step in STEPS:
        entry = by_step[step]
        fields = {}
        for name in ("occupancy","wood_temperature_current"):
            # NPY metadata and raw values are independently pinned by the original native receipt.
            matches = [v for v in entry.values() if isinstance(v,dict) and name in v and isinstance(v[name],dict) and "file" in v[name]]
            assert len(matches) == 1
            desc = matches[0][name]
            path = args.native/desc["file"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == desc["sha256"]
            arr = np.load(path)
            assert arr.shape == (128,128,128) and np.isfinite(arr).all()
            fields[name] = arr
        occupancy = fields["occupancy"]
        if baseline is None:
            baseline = occupancy.copy()
            coords = np.argwhere(occupancy > 0)
            payload["flat_ids"] = np.flatnonzero(occupancy > 0).tolist()
            sizes = components(coords)
        assert np.array_equal(occupancy,baseline)
        vals = fields["wood_temperature_current"][occupancy>0]
        burned = np.flatnonzero(vals>=1).tolist()
        exp = observations[step]
        assert len(burned) == exp["occupiedIgnitedWoodCells"] and len(vals) == exp["occupiedCells"]
        payload[str(step)] = burned
        outputs.append(dict(step=step,occupied=len(vals),ignited=len(burned),
                            occupancy_sha256=hashlib.sha256(occupancy.tobytes()).hexdigest(),
                            wood_sha256=hashlib.sha256(fields["wood_temperature_current"].tobytes()).hexdigest()))
    result = dict(upstream_file_sha256=UPSTREAM_SHA, contract=contract, checkpoints=outputs,
                  material_cells=int(len(coords)),domain_cells=128**3,component_sizes=sizes)
    args.out.mkdir(exist_ok=True)
    for name,data in (("CHECK.json",result),("occupied-and-ignited.json.gz",payload)):
        dest = args.out/name
        raw=(json.dumps(data,separators=(",",":"))+"\n").encode()
        if dest.exists():
            prior = gzip.decompress(dest.read_bytes()) if name.endswith(".gz") else dest.read_bytes()
            assert raw == prior
        else:
            dest.write_bytes(gzip.compress(raw,mtime=0) if name.endswith(".gz") else raw)
    print(len(coords),len(sizes),sizes[:12],[(r["step"],r["ignited"]) for r in outputs])


if __name__ == "__main__":
    main()
