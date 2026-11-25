"""Build the anonymous numerical supplement from explicitly named evidence files."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1] / "tasks"
T86 = "t86-ignition-margin"
T87 = "t87-stroke-halo"
T88 = "t88-positive-ignition-witness"
T89 = "t89-terminal-scan"
CUTS = (210, 240, 300)
ARMS = ("AB", "BA")
CHECK_REVIEW = re.compile(
    r"https?://|[A-Za-z]:[\\/]|/(?:home|Users|mnt|private|tmp|var|opt|workspaces)/"
    r"|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|vortexgaussians|seanzjxiao|seanwilliam",
    re.IGNORECASE,
)


def clean_json(obj):
    return (json.dumps(obj, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_heat(inputs, asset, members):
    """Export only per-recipient scalar enclosures, without positions or source identities."""
    import numpy as np

    bound = load_module(TASKS / T86 / "predict.py", "temperature_bound")
    pins = bound.geometry
    identities = {}
    recipe = json.loads(pins.checked(pins.RECIPE, pins.RECIPE_SHA, identities))
    world = pins.centers(pins.checked(asset, pins.ASSET_SHA, identities))
    world -= np.asarray(recipe["source_center"])
    world[:, 1] += recipe["params"]["sceneLift"]
    saved = json.loads(gzip.decompress(members[f"{T86}/PREDICTIONS.json.gz"]))
    for arm in ARMS:
        for cut in CUTS:
            name = f"{arm}-{cut}.json.gz"
            raw = inputs.joinpath(name).read_bytes()
            if digest(raw) != saved["inputs"][name]:
                raise ValueError("Checkpoint identity differs: " + name)
            pre = bound.prepare(json.loads(gzip.decompress(raw)), recipe, world)
            steps = []
            native_bound = bound.flame_bound

            def record(prepared, step, method, slabs):
                weighted, count = native_bound(prepared, step, method, slabs)
                steps.append({"weighted": weighted.tolist(), "count": count.tolist()})
                return weighted, count

            # Reuse the original spatial pass. This observation copies only
            # scalar per-site inputs to the subsequent thermal recurrence.
            bound.flame_bound = record
            try:
                masks, _, _ = bound.predict(pre, "weighted")
            finally:
                bound.flame_bound = native_bound
            for q in saved["queries"]:
                if (q["arm"], q["cut"]) == (arm, cut) and masks[q["horizon"]] != q["certified"]["weighted"]:
                    raise ValueError("Projection changed a frozen prediction")
            p = pre["p"]
            data = dict(arm=arm, cut=cut, dt=pre["dt"], rate=p["spreadHeat"],
                        threshold=p["spreadIgnH"], cap=p["spreadSampleCap"],
                        graph=pre["graph"].tolist(), graph_writes=pre["graph_n"].tolist(), steps=steps)
            members[f"thermal-inputs/{name}"] = gzip.compress(clean_json(data), compresslevel=6, mtime=0)


VERIFY = '''"""Rebuild the thermal masks and compare the public calculations to the frozen scores."""
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
T86 = ROOT / "t86-ignition-margin"
sys.dont_write_bytecode = True


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def check(condition, message):
    if not condition:
        raise ValueError(message)


def up(initial, addition, writes):
    return (initial + addition * (1 + 1e-11) + writes * 2.0**-126) / (1 - writes * 2.0**-24)


def verify_thermal():
    saved = read(T86 / "PREDICTIONS.json.gz")
    by_cut = {(q["arm"], q["cut"], q["horizon"]): q for q in saved["queries"]}
    checks = 0
    for arm in ("AB", "BA"):
        for cut in (210, 240, 300):
            state = read(T86 / "public" / f"{arm}-{cut}-eligibility.json.gz")
            x = read(ROOT / "thermal-inputs" / f"{arm}-{cut}.json.gz")
            ids = [i for i, (s, f) in enumerate(zip(state["state"], state["fuel"])) if s == 0 and f > 0]
            check((x["arm"], x["cut"]) == (arm, cut) and len(x["steps"]) == 8, "input identity")
            check(len(x["graph"]) == len(x["graph_writes"]) == len(ids), "graph shape")
            for method in saved["methods"]:
                heat = [state["heat"][i] for i in ids]
                safe = [True] * len(ids)
                for k, step in enumerate(x["steps"], start=1):
                    check(len(step["count"]) == len(step["weighted"]) == len(ids), "gas shape")
                    for j, count in enumerate(step["count"]):
                        writes = x["cap"] if method == "global" else count
                        if method == "weighted":
                            factor = step["weighted"][j]
                        elif method == "support" and count:
                            factor = x["cap"]
                            safe[j] = False
                        else:
                            factor = writes
                        before = up(heat[j], factor * (x["dt"] * x["rate"]), writes)
                        scan = up(0, before * (1 - x["dt"] * .35), 1)
                        safe[j] = safe[j] and scan < x["threshold"]
                        heat[j] = up(scan, x["graph"][j], x["graph_writes"][j])
                    if k in (1, 4, 8):
                        result = [i for i, safe_here in zip(ids, safe) if safe_here]
                        check(result == by_cut[arm, cut, k]["certified"][method], "thermal mask mismatch")
                        checks += 1
    print(f"Rebuilt {checks} exact site-ID masks from scalar enclosures.")


def main():
    manifest = read(ROOT / "manifest.json")
    for name, sha in manifest["sha256"].items():
        check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha, "digest differs " + name)
    verify_thermal()
    for folder, function, filename in manifest["scorers"]:
        task = ROOT / folder
        spec = importlib.util.spec_from_file_location("score_" + folder[:3], task / "score.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = getattr(module, function)()
        reference = read(task / filename)
        check(actual == reference, "score differs " + folder)
        print("Matched all recorded score fields for " + folder)


if __name__ == "__main__":
    main()
'''

README = """# Numerical evidence for the ignition-preview study

Extract this archive into a fresh directory. Run `python -I -B verify.py` there using Python 3.10 or newer. Verification uses the standard library and completes offline.

**Whole-scene material labels (T86).** The six checkpoints represent two stroke orders and three query times on one reconstructed woodpile. For 1, 4 and 8 frames, the verifier reconstructs the global, support, uniform and weighted site masks from the saved site heat, graph heat enclosures, hot-carrier counts and weighted gas enclosures. It compares all 72 ordered ID lists with the frozen predictions. These inputs begin after the spatial enclosure calculation. Regenerating spatial bounds from source particles requires the external scene geometry. This archive excludes geometry, gas trajectories and scene appearance.

**Regional decisions (T87).** The saved shell membership and region-only predictions are independent inputs to the regional scorer. For each of 18 windows it verifies agreement with the full-scene masks restricted to the shell, then checks actual native ignition frames within the region. It compares against ordinary exact early-stop replay and an unchanged-label guess.

**Positive witnesses (T88).** The scorer checks archived residual-heat and graph-witness decisions against the same shell IDs and event windows. It verifies the cost and fallback summaries using the recorded timings. Re-scoring starts from the exported witnesses.

**Terminal scan (T89).** A second run for each stroke order saved two times for every native step. The scorer checks all 720 frames' event identities and discrete counts against the original traces. It recomputes paired full-step and terminal-prefix timings for the whole scene and the regional early-stop query. The simulation completed each step in these measurements.

AB and BA denote the two stroke orders. The complete material event traces contain 360 updates per take. Six eligibility files identify unlit, fuel-positive sites and their stored heat. Public capture receipts are projected to the fields needed by the scorers. SCORE.json files record the expected output. Runtimes are single-machine observations supplied as data. Re-scoring recomputes the reported timing summaries from these measurements. It does not time a new simulation. Repeated site-window queries share sites and simulated frames.
"""


def build(asset):
    members = {}
    scorers = []

    def copy(task, name):
        members[f"{task}/{name}"] = (TASKS / task / name).read_bytes()

    for task in (T86, T87, T88):
        for name in ("score.py", "PREDICTIONS.json.gz", "COSTS.json", "SCORE.json"):
            copy(task, name)
        scorers.append([task, "score", "SCORE.json"])
    for arm in ARMS:
        copy(T86, f"public/{arm}-trace.json.gz")
        for cut in CUTS:
            copy(T86, f"public/{arm}-{cut}-eligibility.json.gz")
    capture = json.loads((TASKS / T86 / "public/capture-report.json").read_bytes())
    if capture["status"] != "validated":
        raise ValueError("Native source validation unavailable")
    terminal = json.loads((TASKS / T89 / "evidence/CAPTURE.json").read_bytes())
    receipt = {"status": capture["status"], "shots": {}}
    paired = {name: terminal[name] for name in ("status", "steps", "errors")}
    paired["shots"] = {}
    endpoint_fields = ("frame", "hash", "particle_hash", "burn_hash", "burning", "charred",
                       "gas_count", "cursor", "random_draws")
    for arm in ARMS:
        source = capture["shots"][arm]
        receipt["shots"][arm] = {key: {"hash": source[key]["hash"]} for key in ("pre_edit", "post_edit")}
        receipt["shots"][arm]["end"] = {k: source["end"][k] for k in endpoint_fields}
        shot = terminal["shots"][arm]
        marker = {k: shot["markers"][k] for k in ("pre_edit", "post_edit")}
        marker["end"] = {k: shot["markers"]["end"][k] for k in endpoint_fields}
        filename = f"{arm}-frames.json.gz"
        if shot["frames"]["file"] != filename:
            raise ValueError("Unexpected terminal ledger path")
        paired["shots"][arm] = {"markers": marker,
                                "frames": {k: shot["frames"][k] for k in ("file", "sha256", "decoded_sha256")}}
        copy(T89, "evidence/" + filename)
    members[f"{T86}/public/capture-report.json"] = clean_json(receipt)
    members[f"{T89}/evidence/CAPTURE.json"] = clean_json(paired)
    for name in ("score.py", "SCORE.json"):
        copy(T89, name)
    scorers.append([T89, "score", "SCORE.json"])
    project_heat(TASKS / T86 / "checkpoints", asset, members)
    members["README.md"] = README.encode()
    members["verify.py"] = VERIFY.encode()
    members["manifest.json"] = clean_json({
        "scorers": scorers,
        "sha256": {name: digest(data) for name, data in sorted(members.items())},
    })
    return members


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", required=True, type=Path, help="Original pinned foreground PLY")
    parser.add_argument("--output", type=Path, default=HERE / "supplement.zip")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    members = build(args.asset)
    for name, data in members.items():
        decoded = gzip.decompress(data) if name.endswith(".gz") else data
        match = CHECK_REVIEW.search(decoded.decode("utf8"))
        if match:
            raise ValueError(f"Review identifying content in {name}: {match.group()}")
    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            compression = zipfile.ZIP_STORED if name.endswith(".gz") else zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=compression)
    print(args.output.name, args.output.stat().st_size, digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
