"""Verify the two frozen processes, rescore contrast histograms, and summarize paired costs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REFERENCE = HERE.parent / "t141-bonsai-action" / "evidence" / "RUN.json"


def read_json(path):
    return json.loads(path.read_bytes())


def pack(directory):
    for proc in sorted(directory.glob("process-*")):
        src = (proc / "RUN.json").read_bytes()
        public = json.loads(src)
        # Keep fresh host paths private. The stored original digest covers the unsanitized worker receipt.
        for i, error in enumerate(public["errors"]):
            public["errors"][i] = error.replace(ROOT.as_uri(), "<repo>").replace(str(ROOT), "<repo>")
        dest = proc / "RUN.json.gz"
        data = json.dumps(public, separators=(",", ":"), allow_nan=False).encode("utf8")
        dest.write_bytes(gzip.compress(data, mtime=0))
        (proc / "original_sha256.txt").write_text(hashlib.sha256(src).hexdigest() + "\n", encoding="utf8")


def diagnostic(branch, matte):
    h = branch["result"]["contrast"]
    assert [h["width"], h["height"], h["blockWidth"], h["blockHeight"]] == [1560,1040,780,520]
    pixel, block, masses = h["pixel"], h["block"], h["massByBlockBin"]
    cell_count = matte["nonzero_cells"]
    assert len(pixel["all"]) == len(pixel["target"]) == 256
    assert len(block["all"]) == len(block["target"]) == len(masses) == 1021
    for histogram in [pixel, block]:
        assert all(0 <= t <= a for t,a in zip(histogram["target"],histogram["all"],strict=True))
    assert sum(pixel["all"]) == h["width"]*h["height"] and sum(pixel["target"]) == 4*cell_count
    assert sum(block["all"]) == h["blockWidth"]*h["blockHeight"] and sum(block["target"]) == cell_count
    assert abs(sum(masses)-matte["total"]) < 1e-8
    assert sum(masses[64:]) == branch["result"]["mass"] == 0
    def describe(hist, threshold):
        return {key:dict(changed=sum(hist[key][1:]),at_threshold=sum(hist[key][threshold:]),
                         maximum=max(i for i,n in enumerate(hist[key]) if n))
                for key in ("all","target")} | {"bounds":hist["bounds"]}
    return dict(pixel=describe(pixel,16), block=describe(block,64),
                target_mass_any_change=sum(masses[1:]),target_mass_at_threshold=sum(masses[64:]))


def full(proc, ref):
    actions = proc["actions"]
    audit = actions[:3]
    assert [r["method"] for r in audit] == ["ordinary-native","ordinary-indexed","transport"]
    hist = {}
    for row in audit:
        assert row["audit"] and row["choice"] == "none" and row["secondary"] == "undefined"
        assert len(row["branches"]) == 2
        for b, target in zip(row["branches"],ref["actions"][0]["branches"],strict=True):
            if row["method"] == "ordinary-native":
                hist[b["name"]] = diagnostic(b, proc["matte"])
            assert (b["name"],b["clicked"],b["endpoint"],b["successor"]) == (
                target["name"],target["clicked"],target["endpoint"],target["successor"])
            assert {k:v for k,v in b["result"].items() if k != "contrast"} == target["result"]
    assert [a["timing_role"] for a in actions[3:]] == ["warmup"]*2 + ["measured"]*12
    num = proc["process_number"]
    ordinary, transport = "ordinary-indexed","transport"
    pairs = []
    for wave, index in enumerate(range(5,17,2), start=1):
        pair = actions[index:index+2]
        expected_order = [ordinary,transport] if (num+wave)%2 == 0 else [transport,ordinary]
        assert [r["method"] for r in pair] == expected_order == proc["waves"][wave-1]["order"]
        by_method = {}
        for r in pair:
            assert r["wave"] == wave and r["choice"] == "none" and r["secondary"] == "undefined"
            assert r["reused_steps"] == r["shared_steps"] == (35 if r["method"] == transport else 0)
            for b in r["branches"]:
                assert b["result"]["mass"] == 0 and b["result"]["denominator"] == proc["matte"]["total"]
            by_method[r["method"]] = dict(host=r["host_ms"],physics=r["phases"]["physics_ms"],image=r["phases"]["image_ms"])
        ratio = by_method[transport]["host"] / by_method[ordinary]["host"]
        pairs.append(dict(wave=wave,order=expected_order,ratio=ratio,by_method=by_method))
    medians = {m:median(p["by_method"][m]["host"] for p in pairs) for m in [ordinary,transport]}
    diffs = {k:mean(p["by_method"][ordinary][k]-p["by_method"][transport][k] for p in pairs)
             for k in ["host","physics","image"]}
    return dict(histograms=hist, medians_ms=medians,ratio_of_medians=medians[transport]/medians[ordinary],
                median_paired_ratio=median(p["ratio"] for p in pairs),transport_wins=sum(p["ratio"]<1 for p in pairs),
                paired_mean_delta_ms=diffs, pairs=pairs)


def score(directory):
    ref = read_json(REFERENCE)
    block = []
    for number in [1,2]:
        base = directory / f"process-{number}"
        if not base.exists():
            break
        exit_receipt = read_json(base / "EXIT.json")
        packed = base / "RUN.json.gz"
        proc = json.loads(gzip.decompress(packed.read_bytes())) if packed.exists() else read_json(base/"RUN.json")
        assert proc["schema"] == "t144-bonsai-native-replication-v1"
        assert proc["parent"] == ref["parent"] and proc["shell"] == ref["shell"]
        assert proc["load"]["sha256"] == ref["load"]["sha256"]
        assert proc["pick_audit"]["samples"] == ref["pick_audit"]["samples"]
        row = dict(number=number,status=proc["status"],wall_s=exit_receipt["elapsed_s"],final_phase=proc["final_phase"])
        if proc["status"] == "replication_complete":
            assert not exit_receipt["expired"] and exit_receipt["returncode"] == 0 and not proc["errors"]
            assert proc["matte"]["native_weight_sha256"] == ref["matte"]["native_weight_sha256"]
            row.update(full(proc, ref))
        else:
            assert proc["status"] == "failed" and exit_receipt["returncode"] != 0 and proc["errors"]
            row["last_completed_phase"] = proc["phases"][-1]["name"]
            row["measured_calls"] = sum(a.get("timing_role") == "measured" for a in proc["actions"])
            row["error"] = proc["errors"][0].splitlines()[0]
        block.append(row)
    complete = [r for r in block if r["status"] == "replication_complete"]
    return {"completed_processes":len(complete),"processes":block,"replicated_order_assessable":len(complete)==2}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=HERE/"evidence")
    parser.add_argument("--pack",action="store_true")
    parser.add_argument("--write",action="store_true")
    args = parser.parse_args()
    if args.pack:
        pack(args.evidence)
    result = score(args.evidence)
    score_path = args.evidence/"SCORE.json"
    if args.write:
        score_path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf8")
    else:
        assert result == read_json(score_path)
    print(f"Verified {result['completed_processes']} complete process(es); repeatability assessable: "
          f"{result['replicated_order_assessable']}.")
