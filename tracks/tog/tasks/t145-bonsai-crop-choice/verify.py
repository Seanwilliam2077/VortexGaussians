"""Recheck the scalar observer receipts, reference pixels, branch states and paired costs."""
import argparse
import gzip
import importlib.util
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / "t141-bonsai-action/evidence/RUN.json"
ORDINARY, TRANSPORT = "ordinary-indexed", "transport"
METHODS = [ORDINARY, TRANSPORT]


def read(path):
    return json.loads(path.read_bytes())


def pack(directory):
    script = next(HERE.parent.glob("t144-*/verify.py"))
    spec = importlib.util.spec_from_file_location("original_receipt_packing", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.pack(directory)


def compare(proc, reference):
    assert proc["load"]["sha256"] == reference["load"]["sha256"]
    for key in ["parent", "rest", "shell", "matte"]:
        assert proc[key] == reference[key]
    assert proc["pick_audit"]["samples"] == reference["pick_audit"]["samples"]
    roi = proc["roi"]
    assert roi["crop"] == proc["matte"]["box"] == dict(x=714, y=418, w=156, h=164)
    assert roi["sceneScissor"] == [713,417,158,166] and roi["viewport"] == [1560,1040]
    assert roi["targetCells"] == proc["matte"]["nonzero_cells"] == 2996
    assert roi["total"] == proc["matte"]["total"] == 411.0941503196955
    assert proc["roi_setup_ms"] > 0
    actions = proc["actions"]
    full = reference["actions"][0]
    crop = {}
    for i, row in enumerate(actions):
        if i < 3:
            assert row["method"] == ["ordinary-native", ORDINARY, TRANSPORT][i] and row["audit"]
        else:
            assert not row["audit"]
        assert row["choice"] == "none" and row["secondary"] == "undefined"
        assert row["shared_steps"] == row["reused_steps"] == (35 if row["method"] == TRANSPORT else 0)
        assert row["host_ms"] > 0
        for b, oracle in zip(row["branches"], full["branches"], strict=True):
            assert (b["name"],b["clicked"]) == (oracle["name"],oracle["clicked"])
            current, historical = b["result"], oracle["result"]
            for field in ["mass","denominator","fraction","passes"]:
                assert current[field] == historical[field]
            if row["audit"]:
                assert b["endpoint"] == oracle["endpoint"] and b["successor"] == oracle["successor"]
            if i == 0:
                assert current["hashes"] == historical["hashes"]
                digests = current["cropHashes"]
                assert len(digests) == 2 and all(len(bytes.fromhex(h)) == 32 for h in digests)
                crop[b["name"]] = digests
            else:
                assert current["hashes"] == []
                assert current["cropHashes"] == (crop[b["name"]] if row["audit"] else [])
    assert len(set(crop["L"] + crop["F"])) == 4
    return crop


def costs(proc):
    actions = proc["actions"]
    assert len(actions) == 17 and len(proc["waves"]) == 6
    num = proc["process_number"]
    assert [r.get("timing_role") for r in actions[3:]] == ["warmup"]*2 + ["measured"]*12
    assert [r["method"] for r in actions[3:5]] == (METHODS if num == 1 else METHODS[::-1])
    pairs = []
    for w in range(1,7):
        block = actions[3+2*w:5+2*w]
        order = METHODS if (num+w)%2 == 0 else METHODS[::-1]
        assert [r["method"] for r in block] == order == proc["waves"][w-1]["order"]
        assert all(r["wave"] == w for r in block)
        by_method = {r["method"]: {"host_ms":r["host_ms"], **r["phases"]} for r in block}
        ordinary, transport = (by_method[m]["host_ms"] for m in METHODS)
        pairs.append(dict(wave=w, order=order, by_method=by_method,
                          ordinary_minus_transport_ms=ordinary-transport, transport_over_ordinary=transport/ordinary))
    medians = {m:{p:median(row["by_method"][m][p] for row in pairs)
                  for p in ["host_ms","physics_ms","image_ms","fork_restore_ms"]} for m in METHODS}
    return dict(medians=medians, median_paired_ratio=median(r["transport_over_ordinary"] for r in pairs),
                ratio_of_medians=medians[TRANSPORT]["host_ms"]/medians[ORDINARY]["host_ms"],
                median_paired_saving_ms=median(r["ordinary_minus_transport_ms"] for r in pairs),
                transport_wins=sum(r["ordinary_minus_transport_ms"]>0 for r in pairs),pairs=pairs)


def score(directory, schema):
    rows = []
    ref = read(REFERENCE)
    for folder in sorted(directory.glob("process-*")):
        receipt = read(folder/"EXIT.json")
        packet = folder/"RUN.json.gz"
        proc = json.loads(gzip.decompress(packet.read_bytes())) if packet.exists() else read(folder/"RUN.json")
        assert proc["schema"] == schema and proc["process_number"] == receipt["process"] == len(rows)+1
        crop = compare(proc,ref)
        row = dict(process=receipt["process"], status=proc["status"], wall_s=receipt["elapsed_s"],
                   crop_sha256=crop, roi=proc["roi"], roi_setup_ms=proc["roi_setup_ms"],
                   measured_calls=sum(r.get("timing_role")=="measured" for r in proc["actions"]))
        if proc["status"] == "replication_complete":
            assert receipt["returncode"] == 0 and not receipt["expired"] and not proc["errors"]
            row.update(costs(proc))
        else:
            assert proc["status"] == "failed" and receipt["returncode"] and proc["errors"]
            row.update(final_phase=proc["final_phase"], error=proc["errors"][0].splitlines()[0])
        rows.append(row)
    assert len(rows) in [1,2] and (len(rows)==2 or rows[0]["status"]=="failed")
    complete = sum(r["status"]=="replication_complete" for r in rows)
    if len(rows)==2:
        assert rows[0]["status"] == "replication_complete"
    return dict(processes=rows, completed_processes=complete, paired_process_direction_assessable=complete==2)


def main(here=HERE,schema="t145-bonsai-scalar-scissor-v1"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=here/"evidence")
    parser.add_argument("--pack",action="store_true")
    parser.add_argument("--write",action="store_true")
    args = parser.parse_args()
    if args.pack:
        pack(args.evidence)
    data = score(args.evidence,schema)
    path = args.evidence/"SCORE.json"
    if args.write:
        path.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n",encoding="utf8")
    else:
        assert data == read(path)
    print("Verified", data["completed_processes"], "complete timing processes.")


if __name__ == "__main__":
    main()
