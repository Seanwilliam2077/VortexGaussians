"""CPU-only extraction of authenticated T04 G0 arrays; never read optimizer arrays."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "t04-framewise-feasibility"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "g0-proof.npz"
    metadata = HERE / "g0-proof.json"
    if output.exists() or metadata.exists():
        raise FileExistsError("G0 proof already exists")
    source_manifest = OLD / "raw-run-manifest.json"
    records = json.loads(source_manifest.read_text(encoding="utf-8"))["files"]
    names = ["qualification/analytic.npz"] + [f"qualification/direction-{d}.npz" for d in range(2)]
    names += [f"qualification/probe-{d}-{h}-{s}.npz" for d in range(2) for h in range(2) for s in ("plus", "minus")]
    if {name for name in records if name.startswith("qualification/")} != set(names):
        raise ValueError("Unexpected T04 qualification file set")
    arrays, files = {}, {}
    for index, name in enumerate(names):
        path = OLD / "runs" / "run-01" / "worker" / name
        record = records[name]
        if path.stat().st_size != record["bytes"] or sha(path) != record["sha256"]:
            raise ValueError("Source file mismatch: " + name)
        keys = {}
        with np.load(path, allow_pickle=False) as packed:
            if set(packed.files) != set(record["arrays"]):
                raise ValueError("Source array set mismatch")
            for key in packed.files:
                value = packed[key]
                descriptor = {"shape": list(value.shape), "dtype": value.dtype.str,
                    "rawSHA256": hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()}
                if descriptor != record["arrays"][key] or not np.isfinite(value).all():
                    raise ValueError("Source raw array mismatch: " + name + ":" + key)
                if key != "frames":
                    destination = f"f{index:02d}_{key}"
                    arrays[destination] = value.copy()
                    keys[key] = destination
        files[name] = {"original": record, "packedKeys": keys, "omittedArrays": ["frames"] if "frames" in record["arrays"] else []}
    with output.open("xb") as stream:
        np.savez_compressed(stream, **arrays)
    report = {"schema": "t05-partial-g0-proof-v1", "scope": "All non-frame G0 arrays only. Full original files/arrays verified at extraction; no optimizer arrays read. Repacking does not reproduce original NPZ byte hashes.",
        "sourceManifestSHA256": sha(source_manifest), "sourceRunnerSHA256": sha(OLD / "runner.py"),
        "sourceSummarySHA256": sha(OLD / "result-summary.json"), "files": files,
        "proof": {"name": output.name, "sha256": sha(output), "bytes": output.stat().st_size},
        "retainedArrayBytes": sum(a.nbytes for a in arrays.values()),
        "omittedFrameArrayBytes": sum(np.prod(f["original"]["arrays"]["frames"]["shape"]) * 8 for f in files.values() if "frames" in f["original"]["arrays"]),
        "producerSHA256": sha(Path(__file__))}
    metadata.write_text(json.dumps(report, indent=2, default=int) + "\n", encoding="utf-8")
    print(json.dumps({"proofBytes": output.stat().st_size, "arrayCount": len(arrays), "metadataSHA256": sha(metadata)}))


if __name__ == "__main__":
    main()
