"""Verify the extracted supplement using only the Python 3.10+ standard library."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


def need(value, reason):
    if not value:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def manifest(root):
    expected = {}
    for line in (root / "MANIFEST.sha256").read_text("ascii").splitlines():
        sha, name = line.split("  ")
        need(name not in expected, "Duplicate manifest entry")
        expected[name] = sha
    actual = {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in root.rglob("*")
              if p.is_file() and p != root / "MANIFEST.sha256"}
    need(actual == expected, "File inventory or SHA-256 mismatch")


def flag_rows(folder, arm):
    rows = [json.loads(s) for s in (folder / f"{arm}.ndjson").read_bytes().splitlines()]
    inputs = [r for r in rows if r["kind"] == "input"]
    frames = [r for r in rows if r["kind"] == "frame_complete"]
    need(len(rows) == 169 and [r["frame"] for r in frames] == list(range(-23, 25)), "Flag frame coverage")
    need([r["index"] for r in inputs] == list(range(120)), "Flag substep coverage")
    need(sum(r["frame"] <= 0 for r in inputs) == 42, "Flag preroll")
    for f in frames:
        selected = [r for r in inputs if r["frame"] == f["frame"]]
        need([r["substep"] for r in selected] == list(range(f["substeps"])) and
             f["next_index"] == selected[-1]["index"] + 1, "Flag substep order")
    need(rows[-1]["kind"] == "final" and rows[-1]["index"] == 120 and rows[-1]["frame"] == 24, "Flag final")
    return inputs + [rows[-1]]


CELL = struct.Struct("<13i")
HEADER = struct.Struct("<II")
U32 = struct.Struct("<I")
ZERO = (0,) * 13


def grid(stream, meta):
    cells, occupied = HEADER.unpack(stream.read(HEADER.size))
    need(cells == math.prod(meta["dims"]) and cells * CELL.size == meta["raw_bytes"], "Feedback dimensions")
    data = bytearray(cells * CELL.size)
    sparse = {}
    last = -1
    for _ in range(occupied):
        index, = U32.unpack(stream.read(4))
        payload = stream.read(CELL.size)
        need(last < index < cells and len(payload) == CELL.size and any(payload), "Sparse cell encoding")
        data[index * CELL.size:(index + 1) * CELL.size] = payload
        sparse[index] = CELL.unpack(payload)
        last = index
    need(digest(data) == meta["sha256"], "Reconstructed native feedback checksum")
    return sparse


def qualify(left, right):
    # Missing entries on both sides are thirteen zeros and obey every condition.
    pairs = [(left.get(i, ZERO), right.get(i, ZERO)) for i in left.keys() | right.keys()]
    changed = [sum(a[k] != b[k] for a, b in pairs) for k in range(13)]
    passed = not any(changed[k] for k in (6, 7, 8, 12))
    axes = []
    for axis in range(3):
        if any(a[axis] < 0 or b[axis] < 0 for a, b in pairs):
            mode = "fails"
        elif all(a[axis] == b[axis] == 0 for a, b in pairs):
            mode = "zero_area"
        elif all(a[axis+9] == b[axis+9] == 0 and (a[axis] > 0) == (b[axis] > 0) for a, b in pairs):
            mode = "zero_impulse_equal_support"
        elif not any(changed[k] for k in (axis, axis+3, axis+9)):
            mode = "identical"
        else:
            mode = "fails"
        axes.append(mode)
    return passed and "fails" not in axes, axes, changed


def boundary_values(folder, left, right):
    stats = read(folder / "early-field-statistics.json")["inputs"]
    need([s["index"] for s in stats] == list(range(4)), "Early state inventory")
    for field in ("X", "V"):
        arms = []
        for label, row in (("ordinary", left[1]), ("stiffer", right[1])):
            raw = (folder / f"first-cloth-{label}-{field}.f32").read_bytes()
            desc = row["cloth"][field]
            need(digest(raw) == desc["sha256"] and desc["shape"] == [1148,4] and
                 desc["dtype"] == "<f4" and len(raw) == 1148*4*4, "First cloth field values")
            arms.append(list(struct.iter_unpack("<4f", raw)))
        receipt = stats[1]["fields"]["cloth."+field]
        for axis in range(3):
            diff = [a[axis] - b[axis] for a, b in zip(*arms)]
            need(sum(v != 0 for v in diff) == receipt["changed"][axis] and
                 max(map(abs, diff)) == receipt["max_abs"][axis] and
                 close(math.sqrt(math.fsum(v*v for v in diff)/len(diff)), receipt["rms"][axis]),
                 "First cloth difference magnitude")
    fields = read(folder / "first-gas-word-pairs.json")
    for field, width, components in (("p", 1, 1), ("vel", 4, 3)):
        observations = fields[field]
        for kind in ("first", "max_abs"):
            need(len(observations[kind]) == components, "First gas witness inventory")
            for axis, (index, a, b) in enumerate(observations[kind]):
                u, v = struct.unpack("<2f", struct.pack("<2I", a, b))
                need(index % width == axis and 0 <= index < math.prod(left[3]["gas"][field]["shape"]) and
                     math.isfinite(u) and math.isfinite(v) and u != v, "First gas difference witness")
                if kind == "max_abs" and field == "vel":
                    need(abs(u-v) == stats[3]["fields"]["gas.vel"]["max_abs"][axis], "Velocity maximum witness")


def flag(folder):
    runs = read(folder / "runs.json")
    scenes = [read(folder / f"{arm}-scene.json") for arm in ("ordinary", "stiffer")]
    for arm, scene in zip(("ordinary", "stiffer"), scenes):
        s = runs[arm]
        native_json = json.dumps(scene, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        need(digest(native_json) == s["settings"] and s["gas_updates"] == 120 and s["cloth_vertices"] == 1148
             and s["status"] == "complete" and s["exit"] == 0 and not s["timeout"], "Flag native run")
    need(scenes[0]["fabrics"][0]["bend"] == 1 and scenes[1]["fabrics"][0]["bend"] == 2, "Flag treatment")
    scenes[1]["fabrics"][0]["bend"] = 1.0
    need(scenes[0] == scenes[1] and runs["ordinary"]["original_settings"] == runs["stiffer"]["original_settings"],
         "Other scene changes")
    left, right = (flag_rows(folder, arm) for arm in ("ordinary", "stiffer"))
    boundary_values(folder, left, right)
    aa = read(folder / "repeat-grid-digests.json")
    need((folder / "ordinary.ndjson").read_bytes() == (folder / "repeat.ndjson").read_bytes() and
         runs["repeat"]["complete"] and runs["repeat"]["grid_pairs"] == 121 and
         aa["original_file_sha256"] == aa["repeat_file_sha256"], "Independent replay")
    same_gas = []
    rules = []
    first_fields = {}
    first_cloth = first_raw = first_fail = None
    with (folder / "ordinary.sparse").open("rb") as ls, (folder / "stiffer.sparse").open("rb") as rs:
        for i, (a, b) in enumerate(zip(left, right, strict=True)):
            ma, mb = a["feedback"], b["feedback"]
            ga, gb = grid(ls, ma), grid(rs, mb)
            need(all(ma[k] == mb[k] for k in ("dims", "ready", "wet", "placed", "active", "layout_ok", "steam_smothers")),
                 "Feedback latch or layout mismatch")
            for r in (a, b):
                g = r["gas"]
                need(g["dims"] == [n * 2 for n in ma["dims"]] == [144, 88, 72] and g["upres"] == 3 and
                     g["scal_fine"]["shape"] == [216, 264, 432, 4] and g["scal_fine"]["dtype"] == "<f2"
                     and math.isfinite(g["h"]) and g["h"] > 0, "Flag gas input layout")
            need(all(a[k] == b[k] for k in ("kind", "index", "frame", "substep")), "Pair alignment")
            if i < 120:
                need(a["forcing"] == b["forcing"] and a["dt"] == b["dt"], "External forcing or step schedule")
            if first_cloth is None and a["cloth"] != b["cloth"]:
                first_cloth = i
            if first_raw is None and ga != gb:
                first_raw = i
            same_gas.append(a["gas"] == b["gas"])
            for k in a["gas"].keys() | b["gas"].keys():
                if a["gas"].get(k) != b["gas"].get(k):
                    first_fields.setdefault(k, i)
            if i == 120:
                break
            if not all(ma[k] for k in ("active", "ready", "placed", "layout_ok")):
                rule = "inactive"
            elif ga == gb:
                rule = "raw"
            else:
                ok, axes, changed = qualify(ga, gb)
                rule = "axis" if ok else "fails"
                if first_fail is None and not ok:
                    first_fail = (i, axes, changed)
            rules.append(rule)
        need(not ls.read(1) and not rs.read(1), "Trailing sparse frames")
    prefix = next((i for i, rule in enumerate(rules) if rule == "fails" or not same_gas[i]), len(rules))
    oracle = next((i for i in range(120) if not (same_gas[i] and same_gas[i+1])), 120)
    need(first_cloth == first_raw == prefix == 1 and Counter(rules) == {"inactive": 1, "fails": 119}, "Guard window")
    need(first_fail == (1, ["zero_area", "zero_area", "fails"], [0,0,8,0,0,0,0,0,0,2,1,0,0]), "First feedback change")
    need(first_fields == {"p": 3, "max_speed": 3, "vel": 3, "scal_fine": 4, "scal": 6} and
         same_gas[:-1].count(False) == 117 and not same_gas[-1], "Gas field boundaries")
    extra = max(0, oracle - first_cloth - 1)
    need(oracle == 2 and extra == 0, "Post-divergence endpoint window")
    return f"120 substeps; 121 feedback grids per arm; repeat matches; guard {prefix}, endpoint upper bound {oracle}, beyond one lag {extra}."


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10)


def woodpile(folder):
    hist, cap, s, old = (read(folder / n) for n in ("contrast.json", "draws.json", "endpoints.json", "prior.json"))
    draws, tags = cap["draws"], s["tag_counts"]
    need(tags == {"eligible": 2371, "light": 190, "full": 493} and cap["source"] == old["source"], "Woodpile inputs")
    expected = [(c, b, False) for c in (0, 124) for b in ("eligible", "light", "full")] + [(0, "eligible", True)]
    need([(d["camera"], d["kind"], d["repeat"]) for d in draws] == expected and draws[0]["hashes"] == draws[-1]["hashes"],
         "Native opacity repeat or coverage")
    for d in draws:
        r = d["stats"]
        need(r["sites"] == 34687 and r["tagCount"] == tags[d["kind"]] and r["clock"] == r["dynamic"] == r["suppressed"] == 0
             and r["greenAlpha"] <= .004 and r["exceed"] <= .004 and [r["sourceWidth"], r["sourceHeight"]] == [940, 528],
             "Native tag draw")
    need(len(hist) == len(old["gas"]) == len(s["gas"]) == 8 and len(s["material"]) == len(old["material"]) == 4,
         "Woodpile endpoints")
    log = []
    for camera in (0, 124):
        key = str(camera)
        d = {r["kind"]: r for r in draws if r["camera"] == camera and not r["repeat"]}
        need(len({r["hashes"]["all"] for r in d.values()}) == 1, "Opacity invariant under tags")
        total = d["eligible"]["stats"]["tagged"]
        need(close(total, s["views"][key]["native_total"]) and s["views"][key]["previous_total"] == old["denominators"][key],
             "Woodpile denominator")
        votes = {"gas": {}, "material": {}}
        for brush, arm in (("light", "AL"), ("full", "AF")):
            for h in (44, 90):
                same = lambda row: (row["camera"], row["brush"], row["horizon"]) == (camera, brush, h)
                r, = filter(same, s["gas"])
                prior, = filter(same, old["gas"])
                bins = hist[f"{brush}-c{camera}-h{h}"]
                counts, weights = bins["counts"], bins["weights"]
                need(len(counts) == len(weights) == 1021 and min(counts) >= 0 and min(weights) >= 0 and
                     sum(counts) == 470*264 and close(math.fsum(weights), total), "Nonspatial bins")
                num = math.fsum(weights[64:])
                need(sum(counts[64:]) == prior["changed_pixels"] == r["changed_cells"] and
                     close(num, r["changed_mass"]) and close(num/total, r["fraction"]) and
                     r["previous_fraction"] == prior["fraction"] and r["passes"] == (4*num >= total), "Gas coverage")
                if h == 90:
                    votes["gas"][brush] = r["passes"]
            prior, = (p for p in old["material"] if (p["camera"], p["arm"]) == (camera, arm))
            r, = (p for p in s["material"] if (p["camera"], p["brush"]) == (camera, brush))
            num = d[brush]["stats"]["tagged"]
            need(prior["final"][0] == 270 and r["hit_sites"] == prior["final"][2] and
                 r["previous_fraction"] == prior["final"][3]/prior["total"] and close(num, r["native_hit_mass"])
                 and close(num/total, r["fraction"]) and r["passes"] == (4*num >= total), "Material coverage")
            votes["material"][brush] = r["passes"]
        choices = {}
        for label, passes in votes.items():
            choices[label] = next((b for b in ("light", "full") if passes[b]), "neither")
            need(s["endpoint"][key][label] == choices[label] and s["endpoint"][key][label+"_votes"] == passes,
                 "Endpoint decision")
        baseline = {"gas": "light", "material": "full"} if camera == 0 else {"gas": "neither", "material": "neither"}
        need(choices == baseline, "Woodpile registered decisions")
        log.append(f"camera {camera}: gas {choices['gas']}, material {choices['material']}")
    return "8 x 1,021 contrast bins; " + "; ".join(log) + "."


def bonsai(folder):
    cfg, r = (read(folder / n) for n in ("fixed-input.json", "native.json"))
    load, picks = r["load"], cfg["picks"]
    need(load["kept"] == load["scene_n"] == load["total"] == cfg["source_rows"] == 1244819 and
         load["center"] == cfg["source_center"] and load["sha256"] == cfg["fit_sha256"] and
         [load["width"], load["height"]] == cfg["view_size"] and load["sh_degree"] == 3 and
         load["float_color"] and not load["context_lost"] and load["load_gl_error"] == 0, "Bonsai load")
    first = r["first"]
    ids = first["ids"]
    need(first["frame"] == 0 and first["count"] == len(ids) == len(set(ids)) == picks[0]["initial_geometric_count"] and
         digest(struct.pack(f"<{len(ids)}I", *sorted(ids))) == picks[0]["member_sha256"], "Initial brush membership")
    parent, progress, shell, matte = (r[k] for k in ("parent", "parent_progress", "shell", "matte"))
    need([p["frame"] for p in progress] == list(range(30, 181, 30)) and parent["frame"] == 180 and
         parent["active"] == progress[-1]["burning"] and parent["particles"] == progress[-1]["gas"], "Common parent")
    need(shell["eligible"] == shell["geometric"] == cfg["geometric_shell_count"] and
         shell["eligible_hash"] == shell["geometric_hash"] == cfg["geometric_shell_sha256"] and
         matte["stats"]["greenAlpha"] == matte["stats"]["exceed"] == matte["stats"]["clock"] == 0 and
         matte["stats"]["sites"] == load["kept"] and matte["stats"]["tagCount"] == shell["eligible"] and
         matte["total"] == matte["stats"]["tagged"] > 0 and matte["nonzero_cells"] == 2996, "Target matte")
    prefix = r["prefix"]
    need(prefix["sourceCameraId"] == cfg["camera_ids"][0] and prefix["format"] == "RGBA16F" and
         prefix["threshold"] == .5 and len(prefix["samples"]) == 2, "Native pixel receipt")
    for s, offline in zip(prefix["samples"], cfg["offline_nearest_pixels"], strict=True):
        need(s["expectedSourceId"] == offline["fp16"]["id"] and s["displayPixel"] == offline["display_pixel_center_xy"]
             and s["fullMatches"] and s["fullStaticAlpha"] == s["originalSceneAlpha"] and
             s["actual"]["before"] < .5 <= s["actual"]["through"] and
             s["matched"] == (s["actual"]["id"] == s["expectedSourceId"]), "Native pick crossing")
    need([s["matched"] for s in prefix["samples"]] == [True, False] and
         [s["actual"]["id"] for s in prefix["samples"]] == [p["site"] for p in picks[:2]] == [205385, 437231] and
         prefix["samples"][1]["expectedThrough"] < .5, "Offline pixel discrepancy")
    actions = r["actions"]
    need([(x["method"], x["audit"]) for x in actions] == [("ordinary-native", True), ("ordinary-indexed", True),
         ("transport", True), ("ordinary-indexed", False), ("transport", False)], "Action inventory")
    k = min(90, (parent["active"] - 1 - parent["cursor"]) // cfg["feed_cap"])
    need(k == 35 and cfg["camera_ids"] == [0,146] and
         cfg["view_geometry"][1]["world_depth_A_B"][1] + cfg["shell_outer_radius"] < 0,
         "Reuse bound and secondary view")
    native = actions[0]["branches"]
    need(native[0]["endpoint"] != native[1]["endpoint"] and native[0]["result"]["hashes"][0] != native[1]["result"]["hashes"][0],
         "Bonsai nonidentical alternatives")
    for action in actions:
        need(action["shared_steps"] == action["reused_steps"] == (k if action["method"] == "transport" else 0)
             and action["secondary"] == "undefined" and [b["name"] for b in action["branches"]] == ["L","F"],
             "Bonsai procedure")
        for branch, reference, pick in zip(action["branches"], native, picks[1:], strict=True):
            outcome = branch["result"]
            need(branch["clicked"] == pick["initial_geometric_count"] and outcome["mass"] == 0 and
                 outcome["denominator"] == matte["total"] and outcome["fraction"] == outcome["mass"]/outcome["denominator"]
                 and outcome["passes"] == (4*outcome["mass"] >= outcome["denominator"]), "Visible decision")
            if action["audit"]:
                need(branch == reference and branch["endpoint"]["frame"] == 270 and branch["successor"]["frame"] == 271 and
                     len(branch["endpoint"]["material"]) == len(branch["successor"]["material"]) == 5 and
                     outcome["hashes"][0]["full_display_rgba_sha256"] != outcome["hashes"][1]["full_display_rgba_sha256"],
                     "Independent action, displayed-frame or continuation digest")
        choices = [b["name"] for b in action["branches"] if b["result"]["passes"]]
        need(action["choice"] == (choices[0] if choices else "none"), "Action choice")
    return f"{k}/90 shared; both scores 0/{matte['total']:.6f}; two branches x three audited methods agree at 270 and 271."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", nargs="?", type=Path, default=Path(__file__).resolve().parent)
    root = parser.parse_args().folder
    manifest(root)
    for title, function in (("flag", flag), ("woodpile", woodpile), ("bonsai", bonsai)):
        print(f"{title}: {function(root / title)}")
