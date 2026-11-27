"""Deterministic resident-grid inputs and an independent frozen specification."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
T131 = HERE.parent / "t131-fresh-engine-continuation"
sys.path.insert(0, str(T131 / "axis-audit"))
from audit import qualify, read_grid


def captured():
    evidence = T131 / "evidence"
    receipt = json.loads((evidence / "reference.json").read_bytes())
    return [read_grid(receipt[key], evidence / name).reshape(-1, 13)
            for key, name in (("native_parent", "reference-parent.npz"),
                              ("successor", "reference-successor.npz"))]


def expected(first, second):
    if np.array_equal(first, second):
        return "raw"
    return "axis" if qualify(first, second)["certified"] else "split"


def digest(grid):
    return hashlib.sha256(grid.tobytes()).hexdigest()


def controls():
    first, second = captured()
    yield "frame_1_to_2", first, second
    yield "frame_2_identical", second, second.copy()
    neg = np.zeros((1, 13), "<i4")
    neg[0, 0] = -17
    yield "single_negative_identical", neg, neg.copy()
    variant = neg.copy()
    variant[0, 4] = -9
    yield "single_negative_unequal", neg, variant

    base = np.zeros((129, 13), "<i4")
    for channel in (6, 7, 8, 12):
        variant = base.copy()
        variant[-1, channel] = 1
        yield f"source_{channel}_last", base, variant
    for axis in range(3):
        first = np.zeros((65, 13), "<i4")
        first[-1, axis] = 1
        variant = first.copy()
        variant[-1, axis] = 0
        yield f"support_{axis}_tail", first, variant
        # The first group by itself has no area; the second is identical.
        variant = first.copy()
        variant[0, 9 + axis] = -123
        yield f"cross_group_veto_{axis}", first, variant
        first[-1, axis] = 0
        variant[-1, axis] = 0
        yield f"globally_absent_{axis}", first, variant

    first = base.copy()
    first[0, 1] = 4
    first[-1, 2] = 5
    first[-1, 11] = -6
    variant = first.copy()
    variant[0, 9] = 12  # axis 0 has no projected area
    variant[0, 1] = 11  # axis 1 has zero impulse and identical support
    yield "different_mode_each_axis", first, variant
    variant = variant.copy()
    variant[0, 5] = 3  # axis 2 now fails its only qualifying mode
    yield "different_mode_then_fail", first, variant


def workloads():
    frame1, frame2 = captured()
    for repeats in (1, 64):
        a = np.tile(frame1, (repeats, 1))
        b = np.tile(frame2, (repeats, 1))
        yield f"{len(a)}_identical", a, a.copy()
        yield f"{len(a)}_different_axis", a, b
        bad = a.copy()
        bad[-1, 12] += 1
        yield f"{len(a)}_different_source", a, bad
