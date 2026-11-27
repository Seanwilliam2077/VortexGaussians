"""Check the public Bonsai receipts without launching a second browser."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def verify(directory):
    report = read(directory / "RUN.json")
    exit_receipt = read(directory / "EXIT.json")
    source = read(HERE.parent / "t139-native-brush-projection" / "RESULTS.json")
    cfg = source["native_input"]
    assert report["status"] == "correctness_complete" and not report["errors"]
    assert not exit_receipt["expired"] and exit_receipt["returncode"] == 0
    assert report["elapsed_ms"] <= exit_receipt["elapsed_s"] * 1000 <= exit_receipt["limit_s"] * 1000
    for name, digest in report["sources"].items():
        # Git checkouts may convert text to CRLF. Match the archived byte identity.
        raw = (HERE / name).read_bytes()
        assert digest in {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()}, name

    load = report["load"]
    assert load["kept"] == load["scene_n"] == load["total"] == source["source_rows"]
    assert load["center"] == cfg["source_center"] and load["sha256"] == source["fit_sha256"]
    assert [load["width"], load["height"]] == source["view_size"]
    assert load["sh_degree"] == 3 and load["float_color"] and load["load_gl_error"] == 0
    assert not load["context_lost"]

    first = report["first"]
    ids = first["ids"]
    assert first["frame"] == 0 and first["count"] == len(ids) == cfg["picks"][0]["initial_geometric_count"]
    # The geometric recipe stores membership by ascending original ID; the native brush visits its spatial grid.
    assert len(set(ids)) == len(ids)
    assert hashlib.sha256(struct.pack(f"<{len(ids)}I", *sorted(ids))).hexdigest() == cfg["picks"][0]["member_sha256"]
    assert [r["frame"] for r in report["parent_progress"]] == list(range(30, 181, 30))
    parent = report["parent"]
    assert parent["frame"] == 180 and parent["active"] == report["parent_progress"][-1]["burning"]
    assert parent["particles"] == report["parent_progress"][-1]["gas"]
    shell, matte = report["shell"], report["matte"]
    assert shell["eligible"] == shell["geometric"] == cfg["geometric_shell_count"]
    assert shell["geometric_hash"] == shell["eligible_hash"] == cfg["geometric_shell_sha256"]
    assert matte["stats"]["greenAlpha"] == matte["stats"]["exceed"] == 0
    assert matte["stats"]["tagCount"] == shell["eligible"] and matte["stats"]["sites"] == load["kept"]
    assert matte["stats"]["clock"] == 0 and matte["total"] == matte["stats"]["tagged"] > 0

    prefix = report["pick_audit"]
    assert prefix["sourceCameraId"] == cfg["camera_ids"][0] and prefix["format"] == "RGBA16F"
    for sample, offline in zip(prefix["samples"], source["nearest_pixel_diagnostic"], strict=True):
        assert sample["expectedSourceId"] == offline["fp16"]["id"]
        assert sample["displayPixel"] == offline["display_pixel_center_xy"]
        assert sample["fullMatches"] and sample["fullStaticAlpha"] == sample["originalSceneAlpha"]
        assert sample["actual"]["before"] < 0.5 <= sample["actual"]["through"]
        assert sample["matched"] == (sample["actual"]["id"] == sample["expectedSourceId"])
    assert [s["matched"] for s in prefix["samples"]] == [True, False]
    assert [s["actual"]["id"] for s in prefix["samples"]] == [p["site"] for p in cfg["picks"][:2]]

    actions = report["actions"]
    assert [(r["method"], r["audit"]) for r in actions] == [
        ("ordinary-native", True), ("ordinary-indexed", True), ("transport", True),
        ("ordinary-indexed", False), ("transport", False)]
    references = actions[0]["branches"]
    gas_on_hashes = set()
    expected_receipts = []
    for branch in references:
        assert branch["endpoint"]["frame"] == 270 and branch["successor"]["frame"] == 271
        on, off = branch["result"]["hashes"]
        assert on["full_display_rgba_sha256"] != off["full_display_rgba_sha256"]
        gas_on_hashes.add(on["full_display_rgba_sha256"])
    assert len(gas_on_hashes) == 2 and references[0]["endpoint"] != references[1]["endpoint"]
    for row in actions:
        assert row["secondary"] == "undefined"
        k = min(90, (parent["active"] - 1 - parent["cursor"]) // cfg["params"]["spreadFeedCap"])
        assert row["shared_steps"] == row["reused_steps"] == (k if row["method"] == "transport" else 0)
        choices = []
        assert [b["name"] for b in row["branches"]] == ["L", "F"]
        for b, ref, pick in zip(row["branches"], references, cfg["picks"][1:], strict=True):
            result = b["result"]
            assert b["clicked"] == pick["initial_geometric_count"]
            assert result["mass"] == 0 and result["denominator"] == matte["total"]
            assert result["fraction"] == result["mass"] / result["denominator"]
            assert result["passes"] == (4 * result["mass"] >= result["denominator"])
            if result["passes"]:
                choices.append(b["name"])
            if row["audit"]:
                assert b == ref
                expected_receipts.append({"method": row["method"], "branch": b})
        assert row["choice"] == (choices[0] if choices else "none")
    assert expected_receipts == report["finished_audit_branches"]
    print(f"{load['kept']:,} sites; native pick IDs 205385/437231; target mass {matte['total']:.6f}; "
          f"both edits score zero; {k} reused steps; 6 endpoint and successor pairs checked.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=HERE / "evidence")
    verify(parser.parse_args().evidence)
