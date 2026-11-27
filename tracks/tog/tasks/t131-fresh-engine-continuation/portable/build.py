"""Recreate the neutral frame-1 native disk entry and validate an extracted read-only cache on CPU."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from run import PIN, freeze, make_fixture, require

ARCHIVE = HERE / "neutral-frame1.zip"
EVIDENCE = HERE.parent / "evidence"
MEMBERS = ("final/f+0000001.bbc", "final/c+0000001", "final/meta.json", "feedback.bin", "feedback.json")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checkpoint_data(frame, archive):
    state = {}
    with np.load(archive, allow_pickle=False) as arrays:
        for group in ("gas", "cloth", "embers"):
            state[group] = {}
            for name, spec in frame[group].items():
                key = "state." + group + "." + name
                state[group][name] = arrays[key] if key in arrays else spec
            require(freeze(state[group], group, {}) == frame[group], "Checkpoint receipt mismatch")
        feedback = arrays["state.feedback.grid"].tobytes()
        require(digest(feedback) == frame["feedback"]["grid"]["sha256"], "Feedback digest mismatch")
    gas, cloth = state["gas"], state["cloth"]
    entry = {
        "scal": gas["scal"], "time": gas["time"], "upres": gas["upres"], "dims": gas["dims"],
        "origin": gas["origin"], "h": gas["h"], "cloth_X": cloth["X"],
        "cloth_V": cloth["V"].astype(np.float16), "cloth_N": cloth["N"].astype(np.float16),
        "cloth_S": cloth["S"], "cloth_W": cloth["P"][:, 3].astype(np.float16),
        "state": gas, "ember_state": state["embers"], "cloth_state": cloth,
    }
    return entry, feedback


def parent_data(ref):
    return checkpoint_data(ref["native_parent"], EVIDENCE / "reference-parent.npz")


def sidecar_metadata(ref):
    return json.dumps(ref["supplement"]["metadata"], allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode()


def build(root, archive, ref):
    from blackbody.io.simcache import SimCache, write_entry
    entry, feedback = parent_data(ref)
    scene = make_fixture(root)
    require(scene.sim_signature(True) == ref["scene"], "Unexpected fixture signature")
    folder = scene.cache_folder(True)
    disk = SimCache(folder, ref["scene"], about=scene.cache_about(True))
    write_entry(folder / "f+0000001.bbc", entry)
    disk.mark_checkpoint(1)
    (root / "feedback.bin").write_bytes(feedback)
    (root / "feedback.json").write_bytes(sidecar_metadata(ref))
    with ZipFile(archive, "x") as package:
        for member in MEMBERS:
            info = ZipInfo(member)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, (root / member).read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)


def verify(archive, root, ref):
    from blackbody.io.simcache import SimCache
    expected, feedback = parent_data(ref)
    with ZipFile(archive) as package:
        require(sorted(package.namelist()) == sorted(MEMBERS) and package.testzip() is None,
                "Invalid bundle inventory or CRC")
        package.extractall(root)
    scene = make_fixture(root)
    folder = scene.cache_folder(True)
    meta = json.loads((folder / "meta.json").read_bytes())
    require(meta == {"signature": ref["scene"], "format": 1, **scene.cache_about(True)}
            and scene.sim_signature(True) == ref["scene"], "Native metadata does not describe fixture")
    disk = SimCache(folder, ref["scene"], readonly=True)
    require(disk.readonly and disk.frames() == [1] and disk.checkpoints() == [1], "Native disk discovery failed")
    require(freeze(disk.get(1), "entry", {}) == freeze(expected, "entry", {}), "Native decoded fields differ")
    blob = (root / MEMBERS[0]).read_bytes()
    require({"bytes": len(blob), "sha256": digest(blob)} == ref["native_checkpoint"], "Native blob differs")
    raw = (root / "feedback.bin").read_bytes()
    metadata = (root / "feedback.json").read_bytes()
    side = ref["supplement"]
    require(raw == feedback and len(raw) == side["metadata"]["bytes"]
            and digest(raw) == side["metadata"]["sha256"], "Feedback differs")
    require(metadata == sidecar_metadata(ref) and len(metadata) == side["metadata_bytes"], "Metadata differs")
    print(f"{digest(archive.read_bytes())}  {archive.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--build", action="store_true", help="Create a new archive before testing it")
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(args.source), "rev-parse", "HEAD"], text=True).strip()
    require(revision == PIN, "Wrong source revision")
    sys.path.insert(0, str(args.source.resolve()))
    ref = json.loads((EVIDENCE / "reference.json").read_bytes())
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        if args.build:
            build(root / "encode", args.archive, ref)
        verify(args.archive, root / "decode", ref)
