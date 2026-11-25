"""Verify the public shot capture receipts against the archived native runs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
NATIVE = TASKS / "t109-common-parent-choice/evidence/native"


def read_json(path):
    return json.loads(path.read_bytes())


def verify(images=None):
    capture = read_json(HERE / "evidence/CAPTURE.json")
    score = read_json(HERE / "evidence/SCORE.json")
    legacy = read_json(NATIVE / "capture-report.json")
    heavy = read_json(TASKS / "t119-cross-sibling-actions/evidence/firewoods-1/CAPTURE.json")
    assert capture["status"] == "validated_native_capture" and not capture["errors"]
    published = {}
    for arm, run in capture["arms"].items():
        rows = json.loads(gzip.decompress((NATIVE / (arm + "-trace.json.gz")).read_bytes()))
        assert [(r["first"], r["last"]) for r in run["trace_ranges"]] == [(1, 180), (181, 224), (225, 270)]
        for item in run["trace_ranges"]:
            raw = rows[item["first"] - 1:item["last"]]
            rows_without_timing = [{k: v for k, v in row.items() if k not in {"step_ms", "observer_ms"}} for row in raw]
            data = json.dumps(rows_without_timing, separators=(",", ":")).encode()
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
        for moment in ["pre", "post"]:
            assert run["fork"][moment] == legacy["shots"][arm][moment + "_edit"]
        assert run["fork"]["stroke_count"] == legacy["shots"][arm]["edit"]["count"]
        if arm == "AF":
            for frame, state in run["frames"].items():
                assert state == heavy["full_audits"]["sibling"]["physical"][frame]
        files = {r["name"]: r["sha256"] for r in run["images"]}
        assert len(files) == 8
        published.update(files)
        for frame in [224, 270]:
            marker = run["frames"][str(frame)]["marker"]
            series = [r for r in run["renders"] if r["frame"] == frame]
            assert [(r["camera"], r["mode"]) for r in series] == [
                (0, "full"), (0, "wood"), (0, "full"), (124, "full"), (124, "wood"), (124, "full"), (0, "full")]
            for r in series:
                name = "{}-c{}-h{}-{}.png".format("light" if arm == "AL" else "full", r["camera"], frame - 180, r["mode"])
                assert r["sha256"] == files[name] and r["gl_error"] == 0
                assert r["before_state_hash"] == marker["hash"] == r["after_state_hash"]
                assert r["dynamic_instances"] == marker["gas_count"]
    assert set(capture["arms"]) == {"AL", "AF"} and len(published) == 16
    scores = {}
    assert len(score["comparisons"]) == 8
    for r in score["comparisons"]:
        for name, digest in r["sha256"].items():
            assert published[name] == digest
            if images:
                assert hashlib.sha256((images / name).read_bytes()).hexdigest() == digest
        assert r["fraction"] == r["changed_shell_mass"] / r["shell_mass"]
        assert r["passes_quarter"] == (r["fraction"] >= .25)
        if r["horizon"] == 90:
            scores.setdefault(str(r["camera"]), {})[r["brush"]] = r["passes_quarter"]
    for camera, result in score["endpoint_choices"].items():
        assert result["at_90"] == scores[camera]
        choice = next((brush for brush in ["light", "full"] if scores[camera][brush]), "neither")
        assert result["preferred"] == choice
        assert result["matches_both_predictions"] == (scores[camera] == result["prediction"])
    print("Verified 540 native rows, 28 draw records, 16 image identities and eight paired readouts.")
    print("Native gas choice:", {c: r["preferred"] for c, r in score["endpoint_choices"].items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, help="Optional private image directory for byte verification")
    verify(parser.parse_args().images)

