"""Compare a binary16 half-progress reconstruction with the slower native surface."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "t151-surface-preignition" / "evidence"
MIN_NORMAL = float(np.finfo(np.float16).tiny)


def halve_progress(fast):
    if fast.dtype != np.dtype("<f2") or fast.ndim != 4 or fast.shape[-1] != 4:
        raise ValueError("Expected a native little-endian RGBA binary16 atlas")
    replica = fast.copy()
    # Every finite half is exactly representable in float32. Scale first and round once on storage.
    replica[..., 1] = fast[..., 1].astype(np.float32) * np.float32(0.5)
    return replica


def word(x):
    return f"0x{int(x):04x}"


def compare_atlas(fast, slow):
    if fast.dtype != slow.dtype or fast.shape != slow.shape:
        raise ValueError("Different native atlas layouts")
    replica = halve_progress(fast)
    original_bits = fast.view("<u2")
    actual_bits = slow.view("<u2")
    reconstructed_bits = replica.view("<u2")
    changed = reconstructed_bits != actual_bits
    counts = changed.sum(axis=(0, 1, 2)).tolist()
    p = fast[..., 1]
    # Only canonical cold/dry values and the registered positive safe range qualify.
    zeros = original_bits[..., 1] == 0
    in_range = zeros | ((p >= 2 * MIN_NORMAL) & (p < 1))
    finite = bool(np.isfinite(fast).all() and np.isfinite(slow).all() and np.isfinite(replica).all())
    violators = int(np.count_nonzero(~in_range))
    witness = None
    max_abs = 0.0
    if any(counts):
        pos = np.unravel_index(np.argmax(changed), changed.shape)
        witness = dict(zyxc=[int(v) for v in pos], fast=word(original_bits[pos]),
                       reconstructed=word(reconstructed_bits[pos]), slow=word(actual_bits[pos]))
        if finite:
            max_abs = float(np.max(np.abs(replica.astype(np.float32) - slow.astype(np.float32))))
        else:
            max_abs = None
    return dict(words=int(fast.size), changed_by_channel=counts, changed_words=sum(counts),
                max_abs=max_abs, first_witness=witness, fast_outside_range=violators, finite=finite,
                fast_nonzero_progress=int(np.count_nonzero(p)),
                reconstructed_sha256=hashlib.sha256(replica.tobytes()).hexdigest(),
                slow_sha256=hashlib.sha256(slow.tobytes()).hexdigest())


def decode_states(folder, arm, prefix):
    """Decode native XOR deltas in acquisition order and bind each to its original digest."""
    emitted = 0
    previous = None
    with (folder / f"{arm}-atlas.zlib").open("rb") as stream, (folder / f"{arm}.jsonl").open("rb") as ledger:
        for line in ledger:
            row = json.loads(line)
            if "atlas" not in row:
                continue
            if row["index"] > prefix:
                break
            if row["index"] != emitted:
                raise ValueError(f"Missing dense boundary {emitted} in {arm}")
            spec = row["atlas"]
            if stream.tell() != spec["offset"] or np.dtype(spec["dtype"]) != np.dtype("<f2"):
                raise ValueError(f"Unexpected atlas encoding at {emitted}")
            delta = np.frombuffer(zlib.decompress(stream.read(spec["size"])), dtype=np.uint8)
            previous = delta.copy() if previous is None else np.bitwise_xor(previous, delta)
            if hashlib.sha256(previous).hexdigest() != spec["sha256"]:
                raise ValueError(f"Original atlas digest disagrees at {emitted}")
            yield row, previous.view("<f2").reshape(spec["shape"])
            emitted += 1
    if emitted != prefix + 1:
        raise ValueError(f"Incomplete native atlas prefix for {arm}")


def measure(folder):
    qualification = json.loads((folder/"SCORE.json").read_bytes())
    prefix = qualification["guaranteed_prefix_updates"]
    if any(json.loads((folder/f"{arm}.json").read_bytes())["status"] != "complete" for arm in ("default","slow")):
        raise ValueError("The two native ordinary runs must be complete")
    qualified = {s["index"]: s for s in qualification["aligned_observations"] if s["index"] <= prefix}
    records = []
    first_abstention = None
    for (a, fast), (b, slow) in zip(decode_states(folder,"default",prefix), decode_states(folder,"slow",prefix), strict=True):
        i = a["index"]
        if any(a[k] != b[k] for k in ("index","kind","substep","frame")):
            raise ValueError("Unaligned native boundaries")
        if a["state"] != b["state"] or qualified[i]["changed_checkpoint_fields"] or any(qualified[i]["lit"]):
            raise ValueError("Inputs outside the registered common gas prefix")
        cmp = compare_atlas(fast, slow)
        if not cmp["finite"] or np.any(fast[...,1] < 0) or np.any(slow[...,1] < 0):
            raise ValueError("The qualified native interval must be finite and dry")
        if i == 0 and (np.any(fast[...,1]) or np.any(slow[...,1]) or cmp["changed_words"]):
            raise ValueError("Initial native states must coincide at zero progress")
        if cmp["fast_outside_range"] and first_abstention is None:
            first_abstention = i
        records.append(dict(index=i, frame=a["frame"], substep=a["substep"], time=a["state"]["time"],
                            fast_sha256=a["atlas"]["sha256"], stored_range_history_admits=first_abstention is None, **cmp))
    first_mismatch = next((r["index"] for r in records if r["changed_words"]), None)
    return dict(catch_seconds=[0.35,0.70], smallest_normal_half=MIN_NORMAL, safe_nonzero_min=2*MIN_NORMAL,
                guaranteed_gas_steps=prefix, first_outside_range=first_abstention,
                first_reconstructed_mismatch=first_mismatch, exact_boundaries=sum(r["changed_words"]==0 for r in records),
                boundaries=records)


def controls():
    unit = 2.0**-24
    # Feed native representable float32 increments to the material storage operation in isolation.
    cases = [("normal", 0.375, 0, 0), ("both_round_to_zero", 0.25*unit, 0, 0),
             ("subnormal_exact", 2*unit, 0, 1), ("subnormal_double_round", 1.25*unit, 1, 1),
             ("subnormal_tie", 1.5*unit, 0, 1), ("smallest_safe_stored", 2*MIN_NORMAL, 0, 0)]
    results = []
    for name, step, errors, outside in cases:
        fast = np.zeros((1,1,1,4),dtype="<f2")
        slow = fast.copy()
        fast[...,1] = np.float32(step)
        slow[...,1] = np.float32(step)*np.float32(0.5)
        cmp = compare_atlas(fast, slow)
        if cmp["changed_words"] != errors or cmp["fast_outside_range"] != outside:
            raise ValueError(f"Failed precision control {name}")
        results.append(dict(case=name, increment=step, stored_fast=word(fast.view("<u2")[0,0,0,1]),
                            reconstructed=word(halve_progress(fast).view("<u2")[0,0,0,1]),
                            stored_slow=word(slow.view("<u2")[0,0,0,1]), changed_words=errors,
                            stored_range_admits=outside==0))
    zero = np.zeros((1,1,1,4),dtype="<f2")
    negative_zero = zero.copy()
    negative_zero[...,1] = np.float16(-0.)
    c = compare_atlas(zero, negative_zero)
    if c["changed_words"] != 1 or c["max_abs"] != 0 or c["first_witness"]["slow"] != "0x8000":
        raise ValueError("Signed-zero byte mismatch lost")
    results.append(dict(case="opposite_zero_signs", **c["first_witness"], max_abs=0))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    parser.add_argument("--controls", action="store_true", help="evaluate only offline precision examples")
    parser.add_argument("--write", action="store_true", help="emit scored result in the task directory")
    args = parser.parse_args()
    result = controls() if args.controls else measure(args.native)
    dest = HERE / ("CONTROLS.json" if args.controls else "SCORE.json")
    if args.write:
        dest.write_bytes((json.dumps(result, indent=2, allow_nan=False) + "\n").encode())
    elif json.loads(dest.read_bytes()) != result:
        raise ValueError("Published score differs")
    if args.controls:
        print(f"{len(result)} storage controls passed")
    else:
        print(json.dumps({k:v for k,v in result.items() if k!="boundaries"}, indent=2))
