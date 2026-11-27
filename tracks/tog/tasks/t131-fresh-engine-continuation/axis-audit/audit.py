"""Post-hoc inactive-axis audit of two existing native grids. No device work."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "effective"))
from measure import ROOT, compare, read_grid


def qualify(first, second):
    """Sufficient predicates, evaluated independently for each velocity component."""
    modes = []
    for a in range(3):
        area0, area1 = first[..., a], second[..., a]
        mo0, mo1 = first[..., a + 9], second[..., a + 9]
        if (area0 < 0).any() or (area1 < 0).any():
            mode = "unqualified"
        elif not area0.any() and not area1.any():
            mode = "no_projected_area"
        elif not mo0.any() and not mo1.any() and np.array_equal(area0 > 0, area1 > 0):
            mode = "shared_zero_impulse_and_area_support"
        elif all(np.array_equal(first[..., k], second[..., k]) for k in (a, a + 3, a + 9)):
            mode = "identical_inputs"
        else:
            mode = "unqualified"
        modes.append(mode)
    same_sources = all(np.array_equal(first[..., k], second[..., k]) for k in (6, 7, 8, 12))
    return {"modes_xyz": modes, "scalar_and_steam_equal": same_sources,
            "certified": same_sources and "unqualified" not in modes}


def face_masks(grid, coords, a):
    # q = p/2 - 1/2. Quarter units make even the positive-weight predicate exact.
    q4 = 2 * coords - 1
    q4[:, a] -= 1
    base, frac = np.divmod(q4, 4)
    dims = np.array(grid.shape[2::-1])
    has_area = np.zeros(len(coords), dtype=bool)
    has_impulse = np.zeros_like(has_area)
    for offset_tuple in np.ndindex(2, 2, 2):
        offset = np.array(offset_tuple)
        corner = base + offset
        positive = np.all(np.where(offset, frac, 4 - frac) > 0, axis=1)
        valid = positive & np.all((corner >= 0) & (corner < dims), axis=1)
        x, y, z = corner[valid].T
        has_area[valid] |= grid[z, y, x, a] > 0
        has_impulse[valid] |= grid[z, y, x, a + 9] != 0
    return has_area, has_impulse


def run():
    receipt = json.loads((ROOT / "reference.json").read_bytes())
    first, second = frames = (receipt["native_parent"], receipt["successor"])
    assert [f["frame"] for f in frames] == [1, 2]
    for field in ("dims", "upres", "h", "origin"):
        assert first["gas"][field] == second["gas"][field]
    for field in ("dims", "ready", "wet", "active", "placed"):
        assert first["feedback"][field] == second["feedback"][field]
    assert all(first["feedback"][k] for k in ("ready", "active", "placed"))
    xyz = np.array(first["gas"]["dims"])
    assert np.array_equal(xyz, 2 * np.array(first["feedback"]["dims"]))
    assert all(f["gas"]["vel"]["shape"] == [*list(xyz[::-1] + 1), 4] for f in frames)
    h = np.float32(first["gas"]["h"])
    hc = np.float32(2 * h)
    assert np.isfinite(hc**3) and hc**3 > 0 and h / hc == 0.5
    grids = [read_grid(frame, ROOT / f"reference-{name}.npz")
             for frame, name in zip(frames, ["parent", "successor"])]
    assert all(np.all(g[..., :3] >= 0) for g in grids)
    z, y, x = np.indices(xyz[::-1] + 1)
    coords = np.stack((x, y, z), axis=-1).reshape(-1, 3)
    results = []
    for a in range(3):
        masks = [face_masks(g, coords, a) for g in grids]
        counts = []
        for area, impulse in masks:
            counts.append({"skip": int((~area).sum()), "add_zero": int((area & ~impulse).sum()),
                           "unresolved_nonzero_impulse_stencil": int((area & impulse).sum()),
                           "skipped_with_nonzero_impulse_in_stencil": int((~area & impulse).sum())})
            assert counts[-1]["skip"] + counts[-1]["add_zero"] == len(coords)
        different = int((masks[0][0] != masks[1][0]).sum())
        assert different == 0
        results.append({"axis": "xyz"[a], "frame_1": counts[0], "frame_2": counts[1],
                        "different_branch_faces": different})
    first_grid, second_grid = grids
    tests = {}
    for name, ch, index in [
        ("add_scalar_source", 6, (0, 0, 0)),
        ("add_y_area", 1, tuple(np.argwhere(first_grid[..., 10] != 0)[0])),
        ("add_z_impulse_in_occupied_cell", 11, tuple(np.argwhere(first_grid[..., 2] > 0)[0])),
        ("change_y_impulse_with_absent_area", 10, (0, 0, 0)),
    ]:
        altered = first_grid.copy()
        altered[index + (ch,)] += 1
        tests[name] = qualify(first_grid, altered)["certified"]
    assert list(tests.values()) == [False, False, False, True]
    verdict = qualify(*grids)
    assert verdict["certified"] and not compare(*grids)["operator_certified"]
    return {"scope": "post-hoc, two already opened grids, common finite gas inputs",
            "frame_sha256": [f["feedback"]["grid"]["sha256"] for f in frames],
            "changed_words_by_channel": np.count_nonzero(first_grid != second_grid, axis=(0, 1, 2)).tolist(),
            "registered_guard_passed": False, "post_hoc": verdict,
            "texels_per_axis": len(coords), "texels_on_at_least_one_high_face": int(np.any(coords == xyz, axis=1).sum()),
            "axes": results, "in_memory_controls_certified": tests}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
