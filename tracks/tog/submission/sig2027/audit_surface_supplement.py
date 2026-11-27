"""Rebuild, cold-extract and corrupt the anonymous surface archive without editing source evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from pack_surface_supplement import HERE, canonical, pack


def invoke(folder):
    return subprocess.run([sys.executable, "-I", "-B", str(folder / "verify.py")], cwd=folder,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)


def check():
    target = HERE / "surface-supplement.zip"
    with tempfile.TemporaryDirectory(prefix="surface-archive-") as scratch:
        root = Path(scratch)
        result = pack(root / target.name)
        if target.read_bytes() != (root / target.name).read_bytes():
            raise ValueError("Independent build differs")
        with zipfile.ZipFile(target) as archive:
            if archive.testzip():
                raise ValueError("Bad CRC")
            for iteration in range(2):
                folder = root / f"isolated-{iteration}"
                archive.extractall(folder)
                proc = invoke(folder)
                if proc.returncode:
                    raise ValueError(proc.stdout + proc.stderr)
            cases = (("byte_without_rehash", "gas/evidence/slow-atlas.zlib", "Member digest differs"),
                     ("native_bytes_after_rehash", "gas/evidence/slow-atlas.zlib", "Error -3"),
                     ("rounding_summary_after_rehash", "rounding/SCORE.json", "Saved score disagrees"),
                     ("cold_radiant_after_rehash", "restart/reopen.json", "Ordinary/fork/cold restart state differs"))
            for label, src, expected in cases:
                folder = root / label
                archive.extractall(folder)
                file = folder / src
                if src.endswith(".zlib"):
                    # Damage the zlib header of the first complete native delta.
                    payload = bytearray(file.read_bytes())
                    payload[0] ^= 0xff
                    file.write_bytes(payload)
                else:
                    payload = json.loads(file.read_bytes())
                    if src.startswith("rounding/"):
                        payload["cells"]["unique_signed_words"] += 1
                    else:
                        payload["states"]["slow"]["37"]["thermal"]["live_radiant"]["sha256"] = "0" * 64
                    file.write_bytes(canonical(payload))
                if "after_rehash" in label:
                    manifest = folder / "manifest.json"
                    hashes = json.loads(manifest.read_bytes())
                    hashes[src] = hashlib.sha256(file.read_bytes()).hexdigest()
                    manifest.write_bytes(canonical(hashes))
                proc = invoke(folder)
                if not proc.returncode or expected not in proc.stderr:
                    raise ValueError(f"Mutation {label} produced an unexpected outcome: {proc.stdout} {proc.stderr}")
        result.update(independent_builds_identical=2, clean_isolated_numpy_verifications=2,
                      archive_crc_and_member_sha256_checked=True,
                      corruptions_rejected=[label for label, _, _ in cases])
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    receipt = HERE / "surface-supplement-receipt.json"
    result = check()
    if parser.parse_args().write:
        receipt.write_bytes((json.dumps(result, indent=2) + "\n").encode())
    elif result != json.loads(receipt.read_bytes()):
        raise ValueError("Archive audit disagrees with published receipt")
    print(json.dumps(result, indent=2))
