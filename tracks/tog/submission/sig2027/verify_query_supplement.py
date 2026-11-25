"""Verify the regional-query numerical supplement with the Python standard library."""
import argparse
import hashlib
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
from statistics import median

ARMS = ("AB", "BA")
SHORT_CUTS = (210, 240, 300)
METHODS = {
    "terminal": ("full", "trim", "regional", "t91", "t93", "rank-only", "all-carriers"),
    "multistep": ("full", "trim", "regional", "rank-only", "t93", "sweep-rank",
                  "sweep-spatial", "slice-rank", "slice-regional"),
    "graph": ("rank-only", "plain", "cold-cache", "asset-cache"),
    "click": ("regional", "rank-only", "sweep-spatial", "slice-rank", "cold-cache", "asset-cache"),
    "repair": ("asset-cache", "active-fresh", "active-anchor", "restart-cache",
               "repair-cache", "restart-active", "repair-active"),
}


def check(condition, label):
    if not condition:
        raise ValueError(label)


def validate_reference(ref):
    for arm in ARMS:
        shot = ref[arm]
        frames = shot["frames"]
        seen = set(shot["initial"])
        charred = 0
        check(len(seen) == len(shot["initial"]), "duplicate initial contact")
        check(set(shot["initial"]).isdisjoint(shot["edit"]), "repeat brush contact")
        check(len(shot["shell"]) == len(set(shot["shell"])), "duplicate region member")
        check([r["frame"] for r in frames] == list(range(1, 361)), "native time axis")
        for r in frames:
            if r["frame"] == 181:
                check(len(seen) == shot["pre_edit"]["burning"] + shot["pre_edit"]["charred"],
                      "pre-click native population")
                check(seen.isdisjoint(shot["edit"]), "second click already burned")
                seen.update(shot["edit"])
                check(len(seen) == shot["post_edit"]["burning"] + shot["post_edit"]["charred"],
                      "post-click native population")
            new = set(r["new_ids"])
            check(len(new) == len(r["new_ids"]) and new.isdisjoint(seen), "repeated onset")
            seen.update(new)
            charred += r["retired"]
            check(len(seen)-charred == r["active_count"], "full trajectory population")
        check(shot["end"]["burning"] == len(seen)-charred and shot["end"]["charred"] == charred,
              "native endpoint population")


def ground_truth(shot, cut, horizon):
    lit = set(shot["initial"]) | set(shot["edit"])
    for row in shot["frames"][:cut]:
        lit.update(row["new_ids"])
    eligible = set(shot["shell"]) - lit
    for row in shot["frames"][cut:cut+horizon]:
        hits = eligible.intersection(row["new_ids"])
        if hits:
            return eligible, row["frame"], hits
    return eligible, None, set()


def check_audits(arm, suite, a, shot):
    if suite == "multistep":
        for c in SHORT_CUTS:
            audit = a["resume_checks"][str(c)]
            check([r["frame"] for r in audit["sweep"]] == list(range(c+1,c+9)), "resumable gas audit")
            diag = audit["slice"]
            check(diag["cut"] == c and [r["h"] for r in diag["checks"]] == [4,8], "material guard audit")
            for row in diag["frames"]:
                check(row["particles"] > 0 and row["particle_fields"] >= row["particles"]
                      and row["recipient_states"] > 0, "intermediate slice audit")
    if suite == "graph":
        for c in SHORT_CUTS:
            audited = a["ordinary_state_audits"][str(c)]
            check(len(audited) == 8, "ordinary continuation duration")
            for row, original in zip(audited,shot["frames"][c:c+8]):
                check(row["active"] == original["active_count"] and row["draws"] == original["random_draws"],
                      "ordinary continuation state")
    if suite != "repair":
        return
    active = a["active_audit"]
    runs = active["runs"]
    check(active["frames"] == 8 and [r["method"] for r in runs] ==
          ["native","active-fresh","active-anchor","active-anchor"], "active audit schedule")
    check([r["anchor_built"] for r in runs] == [None,False,True,False], "anchor reuse")
    for key in ("matched_particles","matched_particle_fields","matched_material_and_frontier_values"):
        check(runs[1][key]>0 and len({r[key] for r in runs[1:]})==1, "active audit evidence")
    for audit in a["repair_audits"]:
        check(all(audit[k] == v for k,v in audit["active_backend"].items()), "repair backend discrepancy")
        if audit["status"] == "event_before_expiry":
            _, frame, ids = ground_truth(shot, audit["cut"], 180)
            check(frame == audit["event"] and audit["witness"] in ids, "repair audit first event")
        elif audit["status"] == "matched_expiry_and_continuation":
            check(audit["cut"]+audit["length"] == audit["repair_frame"] and audit["sample_count"]>0
                  and len(audit["repair_hash"])==len(audit["next_hash"])==8, "repair continuation")
            known = shot["cut_hashes"].get(str(audit["repair_frame"]))
            check(known is None or known == audit["repair_hash"], "independent repair checkpoint")


def verify_capture(ref, cap, suite, asset):
    methods = METHODS[suite]
    check(cap["methods"] == list(methods) and cap["repeats"] == len(methods), "registered methods")
    short = suite in ("terminal", "multistep", "graph")
    cuts = SHORT_CUTS if short else (180,)
    horizons = (1, 4, 8) if short else ((30, 60, 180) if asset == "G3" else (60, 180))
    expected_keys = {(arm,c,h) for arm in ARMS for c in cuts for h in horizons}
    check(len(cap["queries"]) == len(expected_keys), "registered number of requests")
    for arm in ARMS:
        a = cap["arms"][arm]
        check(a["verified_frames"] == 360 and a["endpoint"] == ref[arm]["end"], "native continuation")
        check(a["cut_hashes"] == ref[arm]["cut_hashes"], "native checkpoint hashes")
        check_audits(arm, suite, a, ref[arm])
        if short:
            check(a["shell_ids"] == ref[arm]["shell"], "independent registered region")
        else:
            post_set = sorted(ground_truth(ref[arm], 180, 1)[0])
            encoded = json.dumps(post_set, separators=(",", ":")).encode()
            check(a["post_click_eligible"] == dict(count=len(post_set),
                  sha256=hashlib.sha256(encoded).hexdigest()), "fresh post-click region")

    rows = []
    for qi, query in enumerate(cap["queries"]):
        arm, cut, horizon = (query[k] for k in ("arm", "cut", "horizon"))
        expected_keys.remove((arm, cut, horizon))
        eligible, frame, ids = ground_truth(ref[arm], cut, horizon)
        check(query["first_frame"] == frame and set(query["expected_ids"]) == ids,
              "reference frame or tied witnesses differ")
        by_method = defaultdict(list)
        check(len(query["trials"]) == (1+len(methods))*len(methods), "incomplete timing blocks")
        for k, trial in enumerate(query["trials"]):
            rep, slot = divmod(k, len(methods))
            m = methods[(slot+rep+qi)%len(methods)]
            check(trial["rep"] == rep and trial["method"] == m, "unbalanced rotation")
            check(trial["yes"] is bool(ids) and trial["first_frame"] == frame, "answer")
            check(trial["witness"] in ids if ids else trial["witness"] is None, "witness identity")
            measured = [v for key,v in trial.items() if key.endswith("_ms")]
            check(all(math.isfinite(v) and v >= 0 for v in measured) and trial["delivered_ms"] > 0,
                  "invalid timing")
            if not short:
                check(trial["clicked"] == len(ref[arm]["edit"]), "stroke contact count")
            if rep:
                by_method[m].append(trial["delivered_ms"])
        if not short and suite != "repair":
            check(all(trial["prefix_steps"] == (horizon if frame is None else frame-cut)
                      for trial in query["trials"]), "actual click time-to-event")
        rows.append(dict(arm=arm, cut=cut, horizon=horizon, eligible=len(eligible), first_frame=frame,
                         tied=len(ids), median_ms={m:median(by_method[m]) for m in methods}))
    check(not expected_keys, "registered requests missing")
    return rows


def load_archive(path):
    if path.is_dir():
        manifest = json.loads((path/"MANIFEST.json").read_bytes())
        return manifest, {name:(path/name).read_bytes() for name in manifest["sha256"]}
    with zipfile.ZipFile(path) as archive:
        check(len(set(archive.namelist())) == len(archive.namelist()), "duplicate member")
        manifest = json.loads(archive.read("MANIFEST.json"))
        check(set(archive.namelist()) == set(manifest["sha256"]) | {"MANIFEST.json"}, "member set")
        return manifest, {name:archive.read(name) for name in manifest["sha256"]}


def verify(path):
    manifest, files = load_archive(path)
    for name, data in files.items():
        check(hashlib.sha256(data).hexdigest() == manifest["sha256"][name], "hash for "+name)
    index = json.loads(files["INDEX.json"])
    references = {}
    for asset in index["assets"]:
        ref = json.loads(files["reference/"+asset+".json"])
        validate_reference(ref)
        references[asset] = ref
    assets = tuple(index["assets"])
    check(assets in (("G1","M2"),("G1","M2","G3")), "asset roster")
    expected = {(a,s) for a in assets[:2] for s in ("terminal","multistep","graph","click")}
    if "G3" in assets:
        expected.update((a,"repair") for a in assets)
    check(len(index["sessions"]) == len(expected), "expected session count")
    summaries = []
    for spec in index["sessions"]:
        asset, suite = spec["asset"], spec["suite"]
        expected.remove((asset,suite))
        cap = json.loads(files["captures/"+suite+"-"+asset+".json"])
        check(spec["window_count"] == len(cap["queries"]) and spec["whole_session_seconds"] ==
              cap["phases_ms"]["wall_before_receipt"]/1000, "session accounting")
        windows = verify_capture(references[asset], cap, suite, asset)
        baseline = {"terminal":"regional", "multistep":"regional", "graph":"rank-only",
                    "click":"asset-cache", "repair":"active-anchor"}[suite]
        ratios = {m:median(q["median_ms"][m]/q["median_ms"][baseline] for q in windows)
                  for m in METHODS[suite]}
        summaries.append(dict(asset=asset, suite=suite, windows=windows, baseline=baseline,
            median_paired_ratios=ratios, right_censored=sum(q["first_frame"] is None for q in windows),
            calls=sum(len(q["trials"]) for q in cap["queries"])))
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, nargs="?", default=Path(__file__).resolve().parent)
    parser.add_argument("--json", action="store_true", help="Print all window medians and ratios")
    args = parser.parse_args()
    out = verify(args.bundle)
    if args.json:
        print(json.dumps(out, indent=2, allow_nan=False))
    else:
        for result in out:
            print(result["asset"], result["suite"], len(result["windows"]), "windows,",
                  result["right_censored"], "censored,", result["calls"], "calls verified")
        print("Verified",sum(r["calls"] for r in out),"warmup and measured calls.")
