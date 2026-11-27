"""Recompute the retained-take results from the public per-call receipts."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
METHODS = ["ordinary", "repair", "hybrid", "sibling"]
PHASES = ["host_ms", "selection_ms", "advance_ms", "draw_read_ms", "upload_ms"]


def read(path):
    return json.loads(path.read_bytes())


def verify(folder):
    earlier = read(HERE.parent / "t109-common-parent-choice/REFERENCE.json")["queries"]
    assets = read(HERE.parent / "t109-common-parent-choice/recipe.json")
    original = None
    summary = {"frame_range": [225, 254], "nominal_fps": 60, "processes": []}
    for process in (1, 2):
        dest = folder / f"process-{process}"
        run = read(dest / "RUN.json")
        exit_info = read(folder / f"exit-{process}.json")
        assert run["schema"] == "t150-kept-take-v1" and run["process"] == process
        assert run["pid"] == exit_info["pid"] and exit_info["process"] == process
        assert not exit_info["expired"] and exit_info["exit"] == 0 and exit_info["elapsed_s"] <= 210
        assert run["status"] == "complete" and not run.get("page_errors") and not run.get("network_error")
        assert run["sources"]["asset"] == assets["asset_sha256"]
        for name, digest in run["sources"].items():
            if "/" in name:
                raw = (HERE.parents[3] / name).read_bytes()
                assert digest in (sha256(raw).hexdigest(), sha256(raw.replace(b"\r\n", b"\n")).hexdigest()), name
        base = METHODS if process == 1 else list(reversed(METHODS))
        expected = [("native", True, 0, 0)]
        expected.extend((m, True, 0, i) for i, m in enumerate(base, 1))
        expected.extend((base[(i+wave-1) % 4], False, wave, i+1) for wave in range(1, 5) for i in range(4))
        rows = run["trials"]
        assert [(r["method"], r["audit"], r["wave"], r["position"]) for r in rows] == expected
        oracle = rows[0]
        if original is None:
            original = oracle
        for k in ("answers", "frame_digests", "crossing", "endpoint", "successor"):
            assert oracle[k] == original[k], k
        assert len(oracle["frame_digests"]) == len(set(oracle["frame_digests"])) == 30
        for a in oracle["answers"]:
            ref = next(r for r in earlier if r["camera"] == 0 and r["arm"] == "A"+a["arm"])
            for x,y in (("first","first_frame"),("count","count"),("mass","mass"),("total","total"),("target","target")):
                assert a[x] == ref[y]
        assert oracle["answers"][0]["mass"] < oracle["answers"][0]["target"] <= oracle["answers"][1]["mass"]
        assert oracle["crossing"]["frame"] == 224 and oracle["endpoint"]["frame"] == 254 and oracle["successor"]["frame"] == 255
        for row in rows:
            assert row["chosen"] == "F" and row["answers"] == oracle["answers"]
            assert row["delivered_bytes"] == 940 * 528 * 4 * 30
            for k in ("frame_digests", "endpoint", "successor"):
                assert row[k] == oracle[k], k
            if row["audit"]:
                assert row["crossing"] == oracle["crossing"]
            assert row["handle"]["frame"] == 254
            assert row["work"]["reused"] == (24 if row["method"] == "sibling" else 0)
            assert all(row[k] >= 0 for k in PHASES)
            assert row["host_ms"] >= row["browser_ms"] - 1
        assert len({r["handle"]["serial"] for r in rows}) == len(rows)
        measured = {m:[r for r in rows if not r["audit"] and r["method"] == m] for m in METHODS}
        medians = {m:{k:median(t[k] for t in calls) for k in PHASES} for m,calls in measured.items()}
        ratios = {}
        for m in METHODS[:-1]:
            comparisons = {}
            pairs = list(zip(measured["sibling"], measured[m], strict=True))
            assert [a["wave"] for a,b in pairs if a["wave"] == b["wave"]] == [1,2,3,4]
            for key in ("host_ms", "selection_ms"):
                samples = [a[key]/b[key] for a,b in pairs]
                comparisons[key] = dict(wins=sum(r < 1 for r in samples), median_paired_ratio=median(samples),
                                        ratio_of_medians=medians["sibling"][key]/medians[m][key])
            ratios[m] = comparisons
        summary["processes"].append(dict(process=process, wall_s=exit_info["elapsed_s"], medians=medians,
                                         sibling_vs=ratios, setup_ms=run["setup_ms"]))
    return summary


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--folder", type=Path, default=HERE/"evidence")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    result = verify(args.folder)
    score = args.folder/"SCORE.json"
    if args.write:
        score.write_text(json.dumps(result, indent=2)+"\n", encoding="utf8")
    else:
        assert result == read(score)
    print(json.dumps(result, indent=2))
