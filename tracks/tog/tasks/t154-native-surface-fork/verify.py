"""Validate paired numerical receipts; the private packet check is optional on another host."""
import argparse
import hashlib
import json
from pathlib import Path

from run import HERE, LIMITS, MAX_PACKETS, T151, t151_endpoint


def read(path):
    return json.loads(path.read_bytes())


def verify(evidence, private=None):
    generation = read(evidence/"generate.json")
    reopened = read(evidence/"reopen.json")
    endpoints = read(T151/"evidence"/"SCORE.json")
    scale = read(HERE.parent/"t153-catch-state-transfer"/"SCORE.json")
    processes = {}
    for key, row in (("generate", generation), ("reopen", reopened)):
        receipt = read(evidence/(key+"-exit.json"))
        assert row["status"] == "complete" and row["phase"] == "complete" and receipt["exit"] == 0
        assert not receipt["expired"] and 0 < row["elapsed_s"] <= receipt["wall_s"] <= LIMITS[key]
        assert 0 < sum(row["paths"].values()) <= row["elapsed_s"]
        for path, wall in row["paths"].items():
            component = sum(x["s"] for x in row["costs"] if x["path"] == path)
            assert 0 <= component <= wall
        processes[key] = receipt["wall_s"]
    assert generation["pin"] == reopened["pin"] and generation["adapter"] == reopened["adapter"]
    fork = generation["fork"]
    frames = fork["frames"]
    assert [r["frame"] for r in frames] == list(range(1, fork["split"]+1))
    assert fork["shared_steps"] == sum(r["n"] for r in frames) == endpoints["guaranteed_prefix_updates"]
    upper = 0.0
    for row in frames:
        for _ in range(row["n"]):
            upper = upper + row["dt"] / .35 + 1/1024
        assert upper == row["upper"] < 1
    future = fork["next_frame"]
    assert future["frame"] == fork["split"]+1 and upper + future["n"]*(future["dt"]/.35 + 1/1024) >= 1
    assert fork["scale_mismatch_words"] == scale["boundaries"][fork["shared_steps"]]["changed_words"]
    split = str(fork["split"])
    left, right = [generation["fork_receipts"][k] for k in ("default","slow")]
    assert set(left) == set(right) == {"state","ember_state","thermal"}
    assert left["thermal"] == right["thermal"] and left["ember_state"] == right["ember_state"]
    assert {k for k in left["state"] if left["state"][k] != right["state"][k]} == {"burn_obj"}
    packets = generation["packets"]
    assert sum(p["raw_state_bytes"] for p in packets.values()) <= MAX_PACKETS
    assert sum(p["bytes"] for p in packets.values()) <= MAX_PACKETS
    for arm in ("default", "slow"):
        own = generation["ordinary"][arm]
        assert generation["fork_receipts"][arm] == own[split]
        assert set(own["36"]["state"]) == {"burn", "burn_obj", "scal", "scal_fine", "vel", "p", "dims",
                                           "upres", "time", "steps", "max_speed", "h", "origin"}
        assert set(own["36"]["thermal"]) == {"temperatures","contacts","radiant_counts","live_radiant","grid","built","cleared"}
        assert {k:own["36"][k] for k in ("state","ember_state")} == t151_endpoint(arm)
        for frame in ("36","37"):
            assert generation["states"][arm][frame] == reopened["states"][arm][frame] == own[frame]
        if private:
            filename = private / (arm+"-36.bbc")
            assert filename.stat().st_size == packets[arm]["bytes"]
            with filename.open("rb") as stream:
                assert hashlib.file_digest(stream, "sha256").hexdigest() == packets[arm]["sha256"]
    assert generation["ordinary"]["default"]["36"]["state"]["scal_fine"] != generation["ordinary"]["slow"]["36"]["state"]["scal_fine"]
    p, r = generation["paths"], reopened["paths"]
    return dict(split=int(split), common_steps=fork["shared_steps"], scaled_words_different=fork["scale_mismatch_words"],
                first_uncovered_scale_history=scale["first_outside_range"],
                cold_init_s=p["cold"] + p["cold_prepare"], ordinary_pair_s=p["ordinary_default"] + p["ordinary_slow"],
                common_and_both_packet_paths_s=p["fork_prefix"] + p["continue_default"] + p["continue_slow"],
                reopen_cold_init_s=r["cold"]+r["cold_prepare"],
                reopen_both_paths_s=r["cold_continue_default"]+r["cold_continue_slow"],
                process_wall_s=processes, raw_bytes={k:v["raw_state_bytes"] for k,v in packets.items()},
                packed_bytes={k:v["bytes"] for k,v in packets.items()})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private", type=Path)
    p.add_argument("--out", type=Path, default=HERE/"evidence")
    args = p.parse_args()
    print(json.dumps(verify(args.out, args.private), indent=2))

