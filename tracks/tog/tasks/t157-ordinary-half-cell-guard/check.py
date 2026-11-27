"""Exhaust the finite half-storage cells and apply the ordinary rule to the recorded replay."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
T153 = HERE.parent / "t153-catch-state-transfer"
sys.path.insert(0, str(T153))
import compare  # T153's native atlas parser and byte comparison


def certified(magnitude):
    return (magnitude >= 0x0800) | ((magnitude & 1) == 0)


def store_bits(x):
    with np.errstate(over="ignore"):
        return x.astype("<f2").view("<u2")


def check_cells():
    mag = np.arange(0x7c00, dtype="<u2")
    stored = mag.view("<f2").astype(np.float32)
    previous = np.concatenate((stored[:1], stored[:-1]))
    # 65536 is the next bin center in an unbounded binary16 exponent range.
    following = np.concatenate((stored[1:], np.array([65536], dtype=np.float32)))
    lower_tie = (previous + stored) * np.float32(0.5)
    upper_tie = (stored + following) * np.float32(0.5)
    odd = (mag & 1) != 0
    lower = np.where(odd, np.nextafter(lower_tie, np.float32(np.inf)), lower_tie)
    upper = np.where(odd, np.nextafter(upper_tie, np.float32(-np.inf)), upper_tie)
    eligible = certified(mag)
    for sign in (0, 0x8000):
        direction = np.float32(-1 if sign else 1)
        lo, hi = direction * lower, direction * upper
        expected = mag | sign
        if not np.array_equal(store_bits(lo), expected) or not np.array_equal(store_bits(hi), expected):
            raise ValueError("An endpoint does not round to the intended fast word")
        if not np.array_equal(store_bits(direction * upper_tie), (mag + odd.astype("<u2")) | sign):
            raise ValueError("Fast midpoint tie, signed zero transition or overflow boundary failed")
        slow_lo, slow_hi = store_bits(lo * np.float32(0.5)), store_bits(hi * np.float32(0.5))
        if not np.array_equal(slow_lo == slow_hi, eligible):
            raise ValueError("Actual ambiguity differs from the proposed ordinary rule")
        half = (direction * stored) * np.float32(0.5)
        if not np.array_equal(store_bits(half)[eligible], slow_lo[eligible]):
            raise ValueError("Predicting from a stored word selected the wrong unique half")
        exact_value = store_bits(half).view("<f2").astype(np.float32)
        if not np.array_equal(exact_value == half, eligible):
            raise ValueError("The induction would lose the exact scale relation")
    examples = []
    for i in (0, 1, 2, 0x02fe, 0x03ff, 0x0400, 0x0401, 0x07ff, 0x0800, 0x0801, 0x7bff):
        examples.append(dict(fast=compare.word(i), low_input=float(lower[i]), high_input=float(upper[i]),
                             slow_from_low=compare.word(store_bits(lower[i] * np.float32(0.5))),
                             slow_from_high=compare.word(store_bits(upper[i] * np.float32(0.5))),
                             certified=bool(eligible[i])))
    safe_count = int(eligible.sum())
    return dict(finite_signed_words=int(2 * mag.size), midpoints_checked=int(2 * mag.size),
                unique_signed_words=2 * safe_count, ambiguous_signed_words=2 * (mag.size - safe_count),
                excluded_nonfinite_words=2 * (0x8000 - mag.size), positive_sign_examples=examples)


def replay():
    native = compare.measure(compare.NATIVE)
    if native != json.loads((T153 / "SCORE.json").read_bytes()):
        raise ValueError("Native bytes disagree with sealed T153 results")
    prefix = native["guaranteed_gas_steps"]
    first_ambiguous = None
    rows = []
    for (row, fast), old in zip(compare.decode_states(compare.NATIVE, "default", prefix), native["boundaries"], strict=True):
        p = fast[..., 1].view("<u2")
        if np.any(p >= 0x3c00):
            raise ValueError("Progress is outside the finite positive-zero, unsaturated contract")
        ambiguous = ~certified(p)
        count = int(ambiguous.sum())
        witness = None
        if count:
            pos = np.unravel_index(np.argmax(ambiguous), p.shape)
            witness = dict(zyx=list(map(int, pos)), word=compare.word(p[pos]))
            if first_ambiguous is None:
                first_ambiguous = row["index"]
        rows.append(dict(index=row["index"], ambiguous_words=count, first_witness=witness,
                         history_admits=first_ambiguous is None, changed_by_channel=old["changed_by_channel"],
                         additional_even_low_nonzero=int(np.count_nonzero((p > 0) & (p < 0x0800) & ~ambiguous))))
    return dict(registered_gas_updates=prefix, first_ambiguous=first_ambiguous,
                history_admitted_updates=prefix if first_ambiguous is None else first_ambiguous - 1,
                exact_boundaries=native["exact_boundaries"], boundaries=rows)


if __name__ == "__main__":
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--write", action="store_true", help="save the checked result")
    result = dict(cells=check_cells(), native_replay=replay())
    dest = HERE / "SCORE.json"
    if args.parse_args().write:
        dest.write_bytes((json.dumps(result, indent=2, allow_nan=False) + "\n").encode())
    elif result != json.loads(dest.read_bytes()):
        raise ValueError("Saved score disagrees with fresh checks")
    print(result["cells"]["unique_signed_words"], "unique signed finite words;",
          result["native_replay"]["history_admitted_updates"], "replay steps admitted")
