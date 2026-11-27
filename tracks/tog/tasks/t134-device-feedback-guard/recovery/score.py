"""Verify recovery evidence, including both directly read original input pairs."""
import json
from itertools import islice

from run import HERE, LIMIT, controls, digest, expected, shader_hashes
from verify import verify, require


def score(folder):
    result = verify(folder, limit_s=LIMIT)
    row = json.loads((folder / "measurements.json").read_bytes())
    require(row["recovery_shaders"] == shader_hashes(), "Recovery shader identity")
    if "diagnostic" in row:
        for actual, (name, a, b) in zip(row["diagnostic"]["cases"], islice(controls(), 2), strict=True):
            require(actual["name"] == name and actual["expected"] == expected(a, b) and
                    actual["inputs_match"] == (actual["input_sha256"] == [digest(a), digest(b)]),
                    "Diagnostic input provenance")
            for key in ("raw", "full"):
                require(actual[key]["returned"] in ("raw", "axis", "split") and
                        0 <= actual[key]["direct_storage_word"] <= 2**32-1, "Diagnostic readback")
    return result


if __name__ == "__main__":
    print(json.dumps(score(HERE / "evidence"), indent=2))
