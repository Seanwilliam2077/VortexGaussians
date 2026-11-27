"""Package public numerical records for the native scalar-choice experiments."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1] / "tasks"
FULL = TASKS / "t144-bonsai-repeated-cost"
FIRST = TASKS / "t145-bonsai-crop-choice"
CROP = TASKS / "t147-bonsai-crop-recovery"


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def select(record, keys):
    return {name: record[name] for name in keys.split() if name in record}


def exported_failure(errors):
    if not errors:
        return []
    line, *_ = errors[0].splitlines()
    if line.startswith("Error: EPERM: operation not permitted, rename"):
        return ["EPERM: operation not permitted, rename temporary receipt"]
    if line == "page.evaluate: Error: ROI preconditions changed":
        return [line]
    raise ValueError("Review unexpected exception before exporting its diagnostic")


def process_record(directory):
    run = read(directory / "RUN.json.gz")
    record = select(run, "status actions parent rest shell matte roi roi_setup_ms waves final_phase phases elapsed_ms")
    record["failure"] = exported_failure(run["errors"])
    record["hardware"] = select(run["load"], "sha256 kept renderer width height scene_n sh_degree float_color")
    record["exit"] = select(read(directory / "EXIT.json"), "returncode process elapsed_s limit_s expired")
    return record


def pack(output):
    files = {
        "README.txt": (HERE / "scalar-guide.txt").read_bytes().replace(b"\r\n", b"\n"),
        "verify.py": (HERE / "verify_scalar.py").read_bytes().replace(b"\r\n", b"\n"),
    }
    prior = read(TASKS / "t141-bonsai-action/evidence/RUN.json")
    oracle = select(prior, "parent rest shell matte")
    oracle["branches"] = prior["actions"][0]["branches"]
    files["room/reference.json"] = encode(oracle)
    for group, task in (("full", FULL), ("crop-initial", FIRST), ("crop", CROP)):
        for directory in sorted((task / "evidence").glob("process-*")):
            files[f"room/{group}-{directory.name}.json"] = encode(process_record(directory))

    hist = read(TASKS / "t140-native-shell-sensitivity/evidence/CONTRAST.json.gz")
    files["woodpile/cut-histograms.json"] = encode({
        f"{camera}-{stroke}": hist[f"{stroke}-c{camera}-h90"]
        for camera in (0, 124) for stroke in ("light", "full")
    })
    full = read(FULL / "evidence/SCORE.json")["processes"][0]
    cropped = read(CROP / "evidence/SCORE.json")["processes"]
    intervals = read(TASKS / "t146-contrast-sensitivity/SCORE.json")
    files["published.json"] = encode({
        "full": select(full, "medians_ms ratio_of_medians median_paired_ratio transport_wins histograms"),
        "crop": [select(row, "medians ratio_of_medians median_paired_ratio median_paired_saving_ms transport_wins")
                 for row in cropped],
        "sensitivity": select(intervals, "cutoff_count threshold_scale required_fraction views undefined"),
    })
    files["manifest.json"] = encode({name: hashlib.sha256(value).hexdigest() for name, value in files.items()})
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(output.name, output.stat().st_size, hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=HERE / "scalar-supplement.zip")
    pack(parser.parse_args().output)
