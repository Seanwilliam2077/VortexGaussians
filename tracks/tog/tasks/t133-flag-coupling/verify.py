"""Reconstruct the registered contiguous prefix from the two ordinary native ledgers."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import zlib

import numpy as np

from observe import HERE, PIN, arrays_and_values, digest, json_hash, require

sys.path.insert(0, str(HERE.parent / "t131-fresh-engine-continuation" / "axis-audit"))
from audit import qualify

FLAGS = ("dims", "ready", "wet", "placed", "active", "layout_ok", "steam_smothers")


def verify_raw_fields(folder, arm, row):
    expected = {f"{group}.{name}":desc for group in ("gas","cloth") for name,desc in row[group].items()
                if isinstance(desc,dict) and "sha256" in desc}
    with np.load(folder/f"{arm}-{row['index']:03d}-fields.npz",allow_pickle=False) as file:
        require(arrays_and_values(dict(file))==expected, "Unverified initial gas/cloth samples")


def evidence(folder, arm, check_fields=verify_raw_fields):
    read = lambda suffix: json.loads((folder/f"{arm}{suffix}.json").read_bytes())
    summary = read("")
    scene = read("-scene")
    require(summary["settings"]==json_hash(scene) and summary["pin"]==PIN, "Settings or pin mismatch")
    ledger = [json.loads(line) for line in (folder/f"{arm}-steps.ndjson").read_bytes().splitlines()]
    frames = [row for row in ledger if row["kind"]=="frame_complete"]
    inputs = [row for row in ledger if row["kind"]=="input"]
    require([v["index"] for v in inputs]==list(range(len(inputs))), "Input coverage")
    counter = Counter(v["frame"] for v in inputs)
    for row in frames:
        require(counter[row["frame"]]==row["substeps"],"Missing in-frame input")
        matching = [r for r in inputs if r["frame"]==row["frame"]]
        require([r["substep"] for r in matching]==list(range(row["substeps"])) and
                matching[-1]["index"]+1==row["next_index"], "Broken native frame ordering")
    final = [row for row in ledger if row["kind"]=="final"]
    if summary["status"]=="complete":
        require([v["frame"] for v in frames]==list(range(-23,25)) and len(final)==1 and
                final[0]["frame"]==24 and final[0]["index"]==len(inputs) and summary["gas_updates"]==len(inputs),
                "Truncated complete trajectory")
    for row in inputs[:4]:
        check_fields(folder,arm,row)
    return summary, scene, inputs, final


def grid(row, stream):
    meta = row["feedback"]
    require(stream.tell()==meta["offset"], "Noncontiguous archive")
    raw = zlib.decompress(stream.read(meta["compressed_bytes"]))
    require(len(raw)==meta["raw_bytes"] and digest(raw)==meta["sha256"], "Invalid feedback")
    nx,ny,nz = meta["dims"]
    return np.frombuffer(raw,"<i4").reshape(nz,ny,nx,13)


def coords(row):
    return {k:row[k] for k in ("index","frame","substep")}


def basic_layout(row):
    return row["gas"]["upres"]==1


def compare(folder, check_detail=basic_layout, limit=240, check_fields=verify_raw_fields):
    exits=json.loads((folder/"workers.json").read_bytes())
    first_ledger=folder/"ordinary-steps.ndjson"
    if set(exits)=={"ordinary"} and (not first_ledger.exists() or not first_ledger.stat().st_size):
        setup=json.loads((folder/"ordinary.json").read_bytes())
        scene=json.loads((folder/"ordinary-scene.json").read_bytes())
        require((setup["status"]=="error" or exits["ordinary"]["timeout"]) and setup["pin"]==PIN and setup["settings"]==json_hash(scene) and
                exits["ordinary"]["exit"]!=0 and exits["ordinary"]["limit_s"]==limit and
                not (folder/"stiffer.json").exists(),"Unverified zero-step disposition")
        return dict(status="observer_setup_failure",completed_arms=0,observed_gas_inputs=0,
                    window=None,workers=exits,reason=setup.get("error","deadline"),phase=setup["last_phase"])
    data = [evidence(folder,arm,check_fields) for arm in ("ordinary","stiffer")]
    a,b = [d[0] for d in data]
    scenes = [d[1] for d in data]
    require(scenes[0]["fabrics"][0]["bend"]==1 and scenes[1]["fabrics"][0]["bend"]==2,"Wrong treatments")
    scenes[1]["fabrics"][0]["bend"]=1.0
    require(scenes[0]==scenes[1] and a["original_settings"]==b["original_settings"], "Additional scene edit")
    require(a["adapter"]==b["adapter"] and a["gas_dims"]==b["gas_dims"] and a["h"]==b["h"] and
            a["features"]==b["features"],"Different device or gas configuration")
    require(len({v["pid"] for v in exits.values()})==2,"Processes must be independent")
    for s in (a,b):
        exit_row=exits[s["arm"]]
        require(exit_row["limit_s"]==limit and (s["status"]!="complete" or
                (exit_row["exit"]==0 and not exit_row["timeout"])), "Unexpected worker status")
    rows=[d[2]+d[3] for d in data]
    compared=[]
    for arm,records in zip(("ordinary","stiffer"),rows):
        with (folder/f"{arm}-grids.zlib").open("rb") as stream:
            for row in records:
                grid(row,stream)
            # A forcibly stopped final write can leave a trailing record without a ledger entry.
            if (a if arm=="ordinary" else b)["status"]=="complete":
                require(not stream.read(1),"Trailing feedback")
    indices=[{(r["kind"],r["frame"],r["substep"]):r for r in rs} for rs in rows]
    first={}
    prefix=[]
    closed=False
    with (folder/"ordinary-grids.zlib").open("rb") as left, (folder/"stiffer-grids.zlib").open("rb") as right:
        for l in rows[0]:
            key=(l["kind"],l["frame"],l["substep"])
            r=indices[1].get(key)
            if r is None:
                first.setdefault("missing_matching_observation",coords(l))
                closed=True
                continue
            observed=coords(l)
            grids=[]
            for row,stream in ((l,left),(r,right)):
                stream.seek(row["feedback"]["offset"])
                grids.append(grid(row,stream))
            same_raw=np.array_equal(*grids)
            flags_equal=all(l["feedback"][k]==r["feedback"][k] for k in FLAGS)
            dims=l["feedback"]["dims"]
            layout=flags_equal and list(l["gas"]["dims"])==[2*x for x in dims] and check_detail(l) and check_detail(r)
            active=all(l["feedback"][k] for k in ("active","ready","placed","layout_ok"))
            require(np.isfinite(l["gas"]["h"]) and l["gas"]["h"]>0, "Invalid spacing")
            guard=qualify(*grids) if layout and active and not same_raw else None
            same_cloth=l["cloth"]==r["cloth"]
            gas_diff=[k for k in sorted(l["gas"].keys()|r["gas"].keys()) if l["gas"].get(k)!=r["gas"].get(k)]
            for kind,found in (("cloth_difference",not same_cloth),("raw_difference",not same_raw),
                               ("gas_difference",bool(gas_diff))):
                if found and kind not in first:
                    first[kind]=dict(**observed,fields=gas_diff) if kind=="gas_difference" else observed
            if key[0]=="final":
                continue
            force_equal=l["forcing"]==r["forcing"]
            timing_equal=l["dt"]==r["dt"] and l["index"]==r["index"]
            if not force_equal:
                first.setdefault("forcing_difference",observed)
            if not timing_equal:
                first.setdefault("step_schedule_difference",observed)
            rule=("inactive" if not active else "raw" if same_raw else "axis" if guard and guard["certified"] else "fails")
            if rule=="fails":
                first.setdefault("failed_axis_rule",dict(**observed,axes=guard["modes_xyz"] if guard else [],
                                 changed_words=np.count_nonzero(grids[0]!=grids[1],axis=(0,1,2)).tolist()))
            ok = layout and not gas_diff and force_equal and timing_equal and rule!="fails"
            if not ok and not closed:
                first["failed_joint_check"]=dict(**observed,rule=rule,layout=layout,gas_equal=not gas_diff,
                                                forcing_equal=force_equal,schedule_equal=timing_equal)
                closed=True
            if not closed:
                prefix.append(dict(index=l["index"],rule=rule))
            compared.append(dict(**observed,rule=rule,gas_equal=not gas_diff,cloth_equal=same_cloth,
                            forcing_equal=force_equal,schedule_equal=timing_equal))
    div=first.get("cloth_difference")
    post=[p for p in prefix if div and p["index"]>=div["index"]]
    lag=[p for p in post if p["index"]==div["index"]]
    useful=[p for p in post if p not in lag]
    return dict(scene="flag_wind",arms={s["arm"]:dict(status=s["status"],observed_inputs=len(d[2]),
                final_observed=bool(d[3]),settings=s["settings"]) for d,s in zip(data,(a,b))},
                workers=exits,matched_gas_inputs=len(compared),alignment_failures={
                "ordinary_only":len(indices[0].keys()-indices[1].keys()),
                "stiffer_only":len(indices[1].keys()-indices[0].keys())},
                first=first,shared_prefix_steps=len(prefix),prefix_admissions=dict(Counter(p["rule"] for p in prefix)),
                divergence_boundary_lag=len(lag),additional_steps_beyond_lag=len(useful),
                useful_by_rule=dict(Counter(p["rule"] for p in useful)),matched_inputs_with_different_gas=
                sum(not row["gas_equal"] for row in compared),diagnostic_rule_counts=dict(Counter(r["rule"] for r in compared)),
                final_gas_equal=(data[0][3][0]["gas"]==data[1][3][0]["gas"] if data[0][3] and data[1][3] else None))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("folder",type=Path,nargs="?",default=HERE/"evidence")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=json.dumps(compare(args.folder),indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(result,encoding="utf8")
    print(result,end="")
