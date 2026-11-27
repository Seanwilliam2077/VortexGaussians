"""Build the anonymous measured surface and material-fork archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1] / "tasks"
GAS = TASKS / "t151-surface-preignition"
TRANSFER = TASKS / "t153-catch-state-transfer"
FORK = TASKS / "t154-native-surface-fork"
CELLS = TASKS / "t157-ordinary-half-cell-guard"


def canonical(data):
    return (json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def textfile(path):
    return path.read_text(encoding="utf-8").encode()


def read_json(path):
    return json.loads(path.read_bytes())


def translated(path, replacements):
    s = path.read_text(encoding="utf-8")
    for old, new in replacements:
        if old not in s:
            raise ValueError(f"Cannot export changed numerical checker at {path.name}")
        s = s.replace(old, new)
    return s.encode()


def pack(output):
    root = GAS / "evidence"
    members = {"README.txt": textfile(HERE / "surface-guide.txt"),
               "verify.py": textfile(HERE / "verify_surface.py"),
               "gas/verify.py": textfile(GAS / "verify.py"),
               "single/compare.py": translated(TRANSFER / "compare.py", [(GAS.name, "gas")]),
               "rounding/check.py": translated(CELLS / "check.py", [(TRANSFER.name, "single"), ("T153", "TRANSFER")])}
    for key, path in (("gas/evidence/SCORE.json", root / "SCORE.json"),
                      ("single/SCORE.json", TRANSFER / "SCORE.json"),
                      ("single/CONTROLS.json", TRANSFER / "CONTROLS.json"),
                      ("rounding/SCORE.json", CELLS / "SCORE.json")):
        members[key] = canonical(read_json(path))
    pins = set()
    for arm in ("default", "slow"):
        raw = read_json(root / (arm + ".json"))
        pins.add(raw.pop("pin"))
        members[f"gas/evidence/{arm}.json"] = canonical(raw)
        for suffix in ("-scene.json", "-exit.json"):
            members[f"gas/evidence/{arm}{suffix}"] = canonical(read_json(root / (arm + suffix)))
        members[f"gas/evidence/{arm}.jsonl"] = textfile(root / (arm + ".jsonl"))
        members[f"gas/evidence/{arm}-atlas.zlib"] = (root / (arm + "-atlas.zlib")).read_bytes()
    for phase in ("generate", "reopen"):
        raw = read_json(FORK / "evidence" / (phase + ".json"))
        pins.add(raw.pop("pin"))
        if raw["phase"] != "complete" or raw["status"] != "complete":
            raise ValueError("Cannot publish an incomplete fork result")
        members[f"restart/{phase}.json"] = canonical(raw)
        members[f"restart/{phase}-exit.json"] = canonical(read_json(FORK / "evidence" / (phase + "-exit.json")))
    if len(pins) != 1:
        raise ValueError("Experiments must use a common fixed engine edition")
    identity = re.compile(rb"(?:github\.com|vortexgaussians|seanzjxiao|Users[\\/]|[A-Za-z]:[\\/]|\bt1[0-9]{2}\b|" +
                          next(iter(pins)).encode() + b")", re.I)
    if any(identity.search(data) for name, data in members.items() if not name.endswith(".zlib")):
        raise ValueError("Archive contains an attribution or host identifier requiring review")
    members["manifest.json"] = canonical({k: hashlib.sha256(v).hexdigest() for k, v in members.items()})
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"file": output.name, "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "members": len(members)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, nargs="?", default=HERE / "surface-supplement.zip")
    print(json.dumps(pack(parser.parse_args().file), indent=2))
