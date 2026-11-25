"""Export the verified T127 shell once for both native image-choice methods."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from time import perf_counter


HERE = Path(__file__).resolve().parent
T127 = HERE.parent / "t127-woodpile-native-camera"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE.parents[4] / "real-asset-ingest")
    parser.add_argument("--out", type=Path, required=True, help="A new private output directory")
    args = parser.parse_args()
    if args.out.exists():
        parser.error("The output directory must be new.")
    start_utc = datetime.now(timezone.utc)
    begin = perf_counter()
    implementation = T127 / "score.py"
    spec = importlib.util.spec_from_file_location("native_gas_observer", implementation)
    observer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(observer)
    shells, checks, sources = observer.verified_shells(args.source)
    raster_end = perf_counter()
    args.out.mkdir(parents=True, exist_ok=False)
    views = {}
    for cid, shell in shells.items():
        rows, columns = shell.shape
        payload = shell.astype("<f8", order="C", copy=False).tobytes(order="C")
        path = args.out / f"camera-{cid}.f64"
        path.write_bytes(payload)
        views[str(cid)] = {**checks[cid], "file": path.name, "rows": rows, "columns": columns,
                           "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    receipt = {"schema": "t129-shell-f64-v1", "started_utc": start_utc.isoformat(),
               "encoding": "float64 little-endian, C row-major, top-left origin",
               "observer_sha256": observer.digest(implementation), "source_sha256": sources, "views": views,
               "raster_and_verify_ms": (raster_end - begin) * 1000,
               "cold_prepare_ms": (perf_counter() - begin) * 1000}
    # The outer coordinator can also measure Python start/exit and JSON writing in the host clock.
    (args.out / "weights.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt, separators=(",", ":")))


if __name__ == "__main__":
    main()
