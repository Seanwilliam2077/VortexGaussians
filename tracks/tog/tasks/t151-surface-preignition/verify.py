"""Reconstruct captured surface atlases and test the registered shared prefix."""
import argparse
import hashlib
import json
from pathlib import Path
import zlib

import numpy as np

HERE = Path(__file__).resolve().parent


def read_json(path):
    return json.loads(path.read_bytes())


def verify_arm(directory, arm, catch):
    info = read_json(directory / f"{arm}.json")
    exit_info = read_json(directory / f"{arm}-exit.json")
    assert info["status"] == "complete" and info["frames"] == 36
    assert exit_info["exit"] == 0 and not exit_info["expired"] and exit_info["wall_s"] <= 420
    scene = read_json(directory / f"{arm}-scene.json")
    records = [json.loads(line) for line in (directory / f"{arm}.jsonl").read_bytes().splitlines()]
    updates = [r for r in records if r["kind"] == "update"]
    frames = [r for r in records if r["kind"] == "frame_end"]
    states = {r["index"]: r for r in records if "atlas" in r}
    assert len(updates) == info["updates"] == sum(r["substep"] for r in frames)
    assert [r["frame"] for r in frames] == list(range(1, 37))
    assert [r["index"] for r in updates] == list(range(len(updates)))
    elapsed_steps = 0
    for frame in frames:
        n = frame["substep"]
        span = updates[elapsed_steps:elapsed_steps+n]
        assert frame["index"] == elapsed_steps+n and frame["index"] in states
        assert all(u["frame"] == frame["frame"] for u in span)
        assert [u["substep"] for u in span] == list(range(n))
        assert np.isclose(sum(u["dt"] for u in span), 1/24, rtol=0, atol=1e-12)
        elapsed_steps += n
    assert states[0]["kind"] == "initialized"
    assert len(states) == 1 + frames[11]["index"] + 24
    with (directory / f"{arm}-atlas.zlib").open("rb") as stream:
        prior = None
        for state in states.values():
            a = state["atlas"]
            assert stream.tell() == a["offset"]
            unpacked = np.frombuffer(zlib.decompress(stream.read(a["size"])), dtype=np.uint8)
            prior = unpacked.copy() if prior is None else prior ^ unpacked
            assert hashlib.sha256(prior).hexdigest() == a["sha256"]
            raw = prior.view(np.dtype(a["dtype"])).reshape(a["shape"])
            x,y,z,w = np.moveaxis(raw, -1, 0)
            eligible = (x > 0) & (z > 0.5)
            assert np.isfinite(raw).all() and not np.any(y < 0)
            assert np.count_nonzero(eligible & (y > 0) & (y < 1)) == a["catching"]
            assert np.count_nonzero(eligible & (y >= 1)) == a["lit"]
            assert np.count_nonzero((z > 0.5) & (w > 0)) == a["smouldering"]
            assert np.count_nonzero(eligible) == a["eligible"] and y.max() == a["max_progress"]
            if state["index"] == 0:
                assert a["eligible"] > 0 and not np.any(y) and not np.any(w)
        assert not stream.read(1)
    remaining = 0.0
    for u in updates:
        assert u["catch_time"] == catch
        if remaining is not None:
            candidate = remaining + u["dt"] / .35 + 1/1024
            remaining = candidate if 0 < u["dt"] < .35 and candidate < 1 else None
        assert u["upper_after"] == remaining
        if remaining is not None:
            boundary = states[u["index"]+1]["atlas"]
            assert not boundary["lit"] and not boundary["smouldering"] and boundary["max_progress"] <= remaining
    return info, scene, updates, states, frames


def score(directory):
    ai, ascene, au, ast, af = verify_arm(directory, "default", .35)
    bi, bscene, bu, bst, bf = verify_arm(directory, "slow", .70)
    assert ai["base_scene"] == bi["base_scene"] == ai["edited_scene"] != bi["edited_scene"]
    assert ai["dims"] == bi["dims"] and ai["fine_upres"] == bi["fine_upres"]
    assert ai["features"] == bi["features"] and ai["adapter"] == bi["adapter"]
    # Compare complete scene fields and localize the edit without relying on scene-key layout.
    def differences(a, b, path=""):
        if a == b:
            return []
        if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
            return sum((differences(a[k], b[k], path+"/"+k) for k in a), [])
        return [(path, a, b)]
    edit = differences(ascene,bscene)
    assert len(edit) == 1 and edit[0][0].endswith("/catch_time") and edit[0][1:] == (.35,.70)
    assert ast[0]["state"] == bst[0]["state"] and ast[0]["atlas"] == bst[0]["atlas"]
    def same_update(a, b):
        return all(a[k] == b[k] for k in ("frame","substep","index","dt","forcing"))
    first_unaligned = next((i for i,(a,b) in enumerate(zip(au,bu)) if not same_update(a,b)), min(len(au),len(bu)))
    qualified = sum(u["upper_after"] is not None for u in au)
    assert qualified > 0 and qualified <= first_unaligned
    observations = []
    for i in sorted(set(ast) & set(bst)):
        a,b = ast[i],bst[i]
        if a["frame"] != b["frame"] or a["substep"] != b["substep"] or i > first_unaligned:
            continue
        assert set(a["state"]) == set(b["state"])
        diff = sorted(k for k in a["state"] if a["state"][k] != b["state"][k])
        observations.append(dict(index=i,frame=a["frame"],substep=a["substep"],
            time=a["state"]["time"], material_equal=a["atlas"]["sha256"] == b["atlas"]["sha256"],
            lit=[a["atlas"]["lit"], b["atlas"]["lit"]], changed_checkpoint_fields=diff))
        if i <= qualified:
            assert not diff and a["atlas"]["lit"] == b["atlas"]["lit"] == 0
    assert all(i in (x["index"] for x in observations) for i in range(qualified+1))
    material = next((x["index"] for x in observations if not x["material_equal"]),None)
    different = sum(not x["material_equal"] and x["index"] < qualified for x in observations)
    frame_rows = []
    for ar,br in zip(af,bf,strict=True):
        a,b = ast[ar["index"]],bst[br["index"]]
        gas_fields = [k for k in ("vel","scal","p","aux","chem","scal_fine") if k in a["state"]]
        unequal_gas = [k for k in gas_fields if a["state"][k] != b["state"][k]]
        if ar["index"] == br["index"] <= qualified:
            assert ar["embers"] == br["embers"]
        frame_rows.append(dict(frame=ar["frame"],updates=[ar["index"],br["index"]],
            lit=[a["atlas"]["lit"],b["atlas"]["lit"]],catching=[a["atlas"]["catching"],b["atlas"]["catching"]],
            max_progress=[a["atlas"]["max_progress"],b["atlas"]["max_progress"]],
            gas_fields=gas_fields,unequal_gas_fields=unequal_gas,gas_equal=not unequal_gas,
            full_checkpoint_except_atlas_equal=a["state"]==b["state"],embers_equal=ar["embers"]==br["embers"]))
    return dict(edit=edit, dims=ai["dims"], upres=ai["fine_upres"], updates=[len(au),len(bu)],
        first_unaligned_update=first_unaligned if first_unaligned < max(len(au),len(bu)) else None,
        guaranteed_prefix_updates=qualified, first_unequal_material_boundary=material,
        guaranteed_updates_starting_with_different_material=different, extra_after_one_lag=max(0,different-1),
        first_sampled_gas_difference=next((x for x in observations if x["changed_checkpoint_fields"]),None),
        aligned_observations=observations, frame_endpoints=frame_rows)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence", type=Path, default=HERE/"evidence")
    p.add_argument("--write", action="store_true")
    args = p.parse_args()
    result = score(args.evidence)
    dest = args.evidence / "SCORE.json"
    if args.write:
        dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    else:
        assert json.loads(json.dumps(result)) == read_json(dest)
    print(json.dumps({k:v for k,v in result.items() if k not in ("aligned_observations","frame_endpoints")}, indent=2))
