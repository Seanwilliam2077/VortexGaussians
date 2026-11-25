"""Package anonymous, self-contained numerical evidence for regional ignition queries."""
import argparse
import gzip
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

from verify_query_supplement import verify

HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1]/"tasks"
ASSETS = {
    "G1": ("firewoods", "t86-ignition-margin/public"),
    "M2": ("dead-tree", "t92-transfer-workload/evidence"),
    "G3": ("playground", "t101-playground-holdout/evidence"),
}
SUITES = {
    "terminal": "t90-callable-regional-query",
    "multistep": "t94-resumable-gas-query",
    "graph": "t97-ordinary-cached-graph",
    "click": "t98-edit-to-answer",
    "repair": "t100-material-repair",
}
ARMS = ("AB", "BA")
DISALLOWED = re.compile(r"https?://|[a-z]:[\\/]|/(?:users|home|mnt|private|tmp|var|opt|workspaces)/"
                        r"|[\w.+-]+@[\w.-]+\.[a-z]{2,}|vortexgaussians|seanzjxiao|seanwilliam"
                        r"|firewoods|dead.tree|playground|poly.haven", re.I)
SESSION_FIELDS = ("methods", "repeats", "phases_ms", "arms", "queries")
NATIVE_FRAME_FIELDS = ("frame", "new_ids", "retired", "active_count", "gas_count", "random_draws",
                       "step_ms", "observer_ms")
GUIDE = """# Regional ignition queries: numerical supplement

Run `python verify_query_supplement.py` inside the extracted archive with Python 3.9 or later. Verification needs no network, numerical library, browser or scene asset. On a recent CPU the offline checks normally take seconds. Add `--json` to print one row per registered window, medians for all methods and within-session paired ratios. Inspect INDEX.json for material/arm counts and complete native session runtimes. The archive may also be passed directly as the first argument to the verifier.

## Unit and contract

Each asset has two treatment orders A→B and B→A, with the second radius-0.12 brush committed after frame 180. The exterior shell has center distance greater than 0.12 and at most 0.26 in solver world units. One step is 1/60 simulated second. The observed event is a previously unlit, fuel-positive shell member's first spontaneous ignition. All comparisons retain every tied witness at that earliest frame; any one tied ID can serve as the answer. A null first frame denotes right censoring at the specified deadline. Trajectories, first events, horizons and timing repetitions on a scene can overlap. G1 is a trained Gaussian field, M2 uses distinct vertices from a separately produced mesh. G3 in the full archive is a second independently trained field. All use one native coupled particle/material solver and researcher-authored brush pairs.

An early checkpoint preview starts from a live shot with the region already available. Three cuts per shot at 210, 240 and 300 have 1/4/8-step requests. A click trial starts immediately before the second brush, includes committing it again and building the region, and stops at the first regional event or deadline. G1 and M2 have 60/180-step click requests. The separately selected G3 has 30/60/180-step click requests. Offline labels use independent source trajectories through frame 360, both sets of brush contacts and a static geometric shell. The verifier recounts the full trajectory and all regional earliest frames, witness identities and censored answers before scoring.

## Sessions and costs

* terminal compares full replay, a trimmed continuation, native first-event regional replay, the direct one-step heat witness (t91), survivor-rank plus spatial culling (t93), the matching rank-only ablation, and all carriers.
* multistep compares native and terminal controls, resumable rank/spatial gas sweeps, and slice-rank/slice-regional with a stable donor and emission-service guard. Complete continuation audits appear in each arm. When a guard fails the native full prefix is paid.
* graph compares ordinary native and graph-cached propagation with the same ranked final scan. Cold-cache pays its own index setup. Asset-cache can reuse immutable donor-neighbor rows on a page.
* click brings the prior candidates and both graph cache variants into the same loaded-edit timing session. The earlier short-window sweep did not reduce pooled cost on these long requests. The whole-horizon slice qualified on three of the eight G1/M2 requests. The retained ordinary cache won five, including all four longest requests. All eight positives come from four distinct stopping events.
* repair compares asset-cache, fresh and pre-click-anchored active-recipient controls, and restart or deferred repair with both graph backends. A repaired trajectory records its guard checks, ordinary and sliced steps, log allocation, repair timings and continuation audits. Inspect the method's warmup and memory fields together with the session's setup/audit phases.

In the final three-geometry comparison, 14 timed click requests cover six distinct second strokes. Their first events arrive before every requested deadline. The two G3 events arrive after 24 and 15 steps and both precede the first service-boundary repair. On G1 A→B the repair operator crosses boundaries twice; its approximately 164 ms answer compares with 256–265 ms after restart and 163–168 ms for complete stepping with the pre-click active-recipient index. The 36 short checkpoint requests have 15 right-censored cases; the repeated comparison sessions use the same conditions. The three-geometry comparison tested 784 calls including warmups. It contains one edit that exercises repair and zero right-censored queries starting at an actual second stroke.

Time values ending in _ms are elapsed milliseconds. delivered_ms includes synchronous dispatch, calculation, returned data and host delivery. Browser component timings are retained. Complete worker elapsed time includes startup, native replay, all calls and validation. Cache/log bytes are recorded allocation counters, distinct from process RSS. rep=0 is a warmup. Positive rep values form a balanced rotation within each request. Pair methods within a session and window; reducing timings across independent sessions can confound comparisons. No acceptance, performance under a different solver, or creator task preference follows from this experiment. The archive contains the measured event ledgers, calls, transfer and audits; it omits input geometry and an executable renderer.

MANIFEST.json hashes every delivered member other than itself. It provides integrity checking, not external authentication.
"""


def encode(obj):
    return (json.dumps(obj, separators=(",", ":"), allow_nan=False)+"\n").encode()


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def reference(asset):
    _, path = ASSETS[asset]
    base = TASKS/path
    receipt = read(base/"capture-report.json")
    if receipt["status"] != "validated" or receipt["errors"]:
        raise ValueError("Invalid reference "+asset)
    if asset == "G1":
        shells = read(TASKS/"t87-stroke-halo"/"PREDICTIONS.json.gz")["shell_ids"]
    else:
        picks = read(base.parent/"shell-ids.json.gz")
        shells = {arm:picks[arm[1]] for arm in ARMS}
    ref = {}
    for arm, shot in receipt["shots"].items():
        frames = read(base/(arm+"-trace.json.gz"))
        ref[arm] = dict(initial=shot["initial"]["ids"], edit=shot["edit"]["ids"],
            shell=sorted(shells[arm]), pre_edit=shot["pre_edit"], post_edit=shot["post_edit"],
            end=shot["end"], cut_hashes={str(c["frame"]):c["native_hash"] for c in shot["cuts"]},
            frames=[{k:r[k] for k in NATIVE_FRAME_FIELDS} for r in frames])
    return ref


def capture(suite, asset):
    named_asset = ASSETS[asset][0]
    data = read(TASKS/SUITES[suite]/"evidence"/named_asset/"CAPTURE.json")
    if data["status"] != "validated" or data["errors"]:
        raise ValueError("Invalid measured session")
    out = {k:data[k] for k in SESSION_FIELDS}
    out["runtime"] = {k:data["runtime"][k] for k in ("node","playwright_version","browser_version")}
    return out


def build(dest, complete):
    assets = ("G1", "M2", "G3") if complete else ("G1", "M2")
    members = {"README.md":GUIDE.encode(), "verify_query_supplement.py":
               (HERE/"verify_query_supplement.py").read_bytes()}
    index = {"schema":"regional-query-evidence-v1", "assets":list(assets), "sessions":[]}
    for asset in assets:
        members["reference/"+asset+".json"] = encode(reference(asset))
        suites = ["terminal", "multistep", "graph", "click"] if asset != "G3" else []
        if complete:
            suites.append("repair")
        for suite in suites:
            data = capture(suite, asset)
            members["captures/"+suite+"-"+asset+".json"] = encode(data)
            index["sessions"].append(dict(asset=asset, suite=suite,
                window_count=len(data["queries"]), sites=data["arms"]["AB"]["sites"],
                whole_session_seconds=data["phases_ms"]["wall_before_receipt"]/1000))
    members["INDEX.json"] = encode(index)
    manifest = {"schema":"sha256-v1", "sha256":{name:hashlib.sha256(data).hexdigest()
                for name,data in sorted(members.items())}}
    members["MANIFEST.json"] = encode(manifest)
    for name, data in members.items():
        if DISALLOWED.search(name) or DISALLOWED.search(data.decode()):
            raise ValueError("Anonymous member check failed for "+name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=dest.parent) as directory:
        path = Path(directory)/dest.name
        with zipfile.ZipFile(path, "w") as archive:
            for name, data in sorted(members.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
        checked = verify(path)
        path.replace(dest)
    print(f"{dest.name}: {len(index['sessions'])} sessions, {sum(x['calls'] for x in checked)} calls,"
          f" {dest.stat().st_size:,} bytes, sha256={hashlib.sha256(dest.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE/"query-supplement.zip")
    parser.add_argument("--development-only", action="store_true", help="Rebuild the earlier eight-session subset")
    args = parser.parse_args()
    build(args.out, not args.development_only)
