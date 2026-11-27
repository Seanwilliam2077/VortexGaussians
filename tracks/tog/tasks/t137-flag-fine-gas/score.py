"""Verify full ordinary coarse/fine input identity and score the first closed window."""
import argparse
import json
from pathlib import Path
from flag import HERE, LIMIT
from verify import compare, verify_raw_fields
from pack_fields import check_public


def correct_detail(row):
    gas=row["gas"]
    factor=gas["upres"]
    if factor==1:
        return "scal_fine" not in gas
    if not isinstance(factor,int) or factor<1 or "scal_fine" not in gas:
        return False
    fine=gas["scal_fine"]
    dims=list(reversed(gas["dims"]))
    return fine["shape"]==[factor*n for n in dims]+[4] and fine["dtype"]=="<f2"


def retrospective_limit(folder,score):
    """Upper bound for these observed adjacent complete gas checkpoints, including the successor."""
    if not all(s["final_observed"] for s in score["arms"].values()) or any(score["alignment_failures"].values()):
        return {"status":"unaligned_or_incomplete"}
    rows=[]
    for arm in ("ordinary","stiffer"):
        seq=[json.loads(line) for line in (folder/f"{arm}-steps.ndjson").read_bytes().splitlines()]
        rows.append([r for r in seq if r["kind"] in ("input","final")])
    end=0
    for i,(a,b) in enumerate(zip(rows[0][:-1],rows[1][:-1])):
        if ((a["frame"],a["substep"],a["dt"],a["forcing"]) != (b["frame"],b["substep"],b["dt"],b["forcing"]) or
                a["gas"]!=b["gas"] or rows[0][i+1]["gas"]!=rows[1][i+1]["gas"]):
            break
        end=i+1
    div=score["first"].get("cloth_difference")
    first_fields={}
    for a,b in zip(*rows):
        for key in a["gas"]:
            if key not in first_fields and a["gas"][key]!=b["gas"][key]:
                first_fields[key]={k:a[k] for k in ("index","frame","substep")}
    return {"observed_matching_input_and_successor_prefix":end,
            "matching_at_observed_cloth_divergence":bool(div and div["index"]<end),
            "matching_steps_beyond_one_lag":max(0,end-div["index"]-1) if div else 0,
            "first_observed_difference_by_gas_field":first_fields}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path,nargs="?",default=HERE/"evidence")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    checker=check_public if (args.folder/"early-index.json").exists() else verify_raw_fields
    outcome=compare(args.folder,correct_detail,LIMIT,checker)
    if "arms" in outcome:
        outcome["retrospective_gas_limit"]=retrospective_limit(args.folder,outcome)
    score=json.dumps(outcome,indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(score,encoding="utf8")
    print(score,end="")
