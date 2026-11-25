"""Verify archived field-check receipts against the independent native state ledgers."""
from pathlib import Path
import gzip
import hashlib
import json

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def main():
    report = read(HERE / "evidence/CAPTURE.json")
    assert report["status"] == "validated" and report["errors"] == []
    assert hashlib.sha256((HERE / "transport.js").read_bytes()).hexdigest() == report["sources"]["operator"]
    prefix = read(TASKS / "t117-sibling-prefix-transport/RESULTS.json")
    for name, folder in (("woodpile","t109-common-parent-choice"), ("playground","t111-playground-shot-choice")):
        receipt = report["scenes"][name]
        study = TASKS / folder
        archive = study / "evidence/native"
        native = read(archive / "capture-report.json")["shots"]["AF"]
        trace = read(archive / "AF-trace.json.gz")
        assert receipt["parent"] == native["pre_edit"]
        assert receipt["steps"] == prefix[folder]["certified_steps"]
        assert receipt["extra_sites"] == prefix[folder]["extra_direct_sites"]
        frames = [180+receipt["steps"],181+receipt["steps"],224,270]
        assert [x["frame"] for x in receipt["checks"]] == frames
        for row in receipt["checks"]:
            source = trace[row["frame"]-1]
            assert (row["draws"],row["particles"],row["frontier"]) == (
                source["random_draws"],source["gas_count"],source["active_count"])
            assert row["material_bytes"] == 17 * read(study/"recipe.json")["material_count"]
            assert row["field_count"] == 13
        onsets = [r["new_ids"] for r in trace[180:270]]
        encoded = json.dumps(onsets,separators=(",",":")).encode()
        assert hashlib.sha256(encoded).hexdigest() == receipt["onsets_sha256"]
        assert receipt["verified_onset_frames"] == len(onsets) == 90
        print(f"{name}: four full-state checks, {len(onsets)} verified onset frames, {receipt['extra_sites']} patched sites")


if __name__ == "__main__":
    main()
