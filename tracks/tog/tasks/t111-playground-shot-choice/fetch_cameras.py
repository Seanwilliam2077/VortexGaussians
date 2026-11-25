"""Fetch only the official calibrated Playground camera member via the verified range reader."""
import importlib.util
import json
import hashlib
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
def fetch():
    spec = importlib.util.spec_from_file_location("archive_reader", HERE.parent/"t101-playground-holdout"/"fetch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.MEMBER = "Playground/cameras.json"
    mod.OFFSET, mod.PACKED, mod.SIZE, mod.CRC = 3265585, 39564, 123582, 3892802308
    out = HERE/"local"/"cameras.json"
    out.parent.mkdir(exist_ok=True)
    raw = out.read_bytes() if out.exists() else mod.fetch()
    assert len(raw) == mod.SIZE and zlib.crc32(raw) == mod.CRC
    if not out.exists():
        out.write_bytes(raw)
    cameras = sorted(json.loads(raw),key=lambda row:row["id"])
    print(len(cameras), [cameras[0]["id"],cameras[len(cameras)//2]["id"]], hashlib.sha256(raw).hexdigest())
if __name__ == "__main__":
    fetch()
