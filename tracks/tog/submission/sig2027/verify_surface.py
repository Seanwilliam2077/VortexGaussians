"""Recompute the measured surface, rounding and restart checks from this directory."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
GAS = HERE / "gas" / "evidence"


def read(path):
    return json.loads(path.read_bytes())


def require(ok, explanation):
    if not ok:
        raise ValueError(explanation)


def check_manifest():
    hashes = read(HERE / "manifest.json")
    actual = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    require(actual == set(hashes) | {"manifest.json"}, "Member inventory differs")
    for name, digest in hashes.items():
        require(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, "Member digest differs: " + name)


def original_frame(arm):
    state, end = [json.loads(s) for s in (GAS / (arm + ".jsonl")).read_bytes().splitlines()[-2:]]
    require(state["kind"] == "frame_state" and end["kind"] == "frame_end" and
            state["frame"] == end["frame"] == 36, "Missing independent last frame")
    gas = dict(state["state"])
    gas["burn_obj"] = {k: state["atlas"][k] for k in ("shape", "dtype", "sha256")}
    return {"state": gas, "ember_state": end["embers"]}


def check_restart():
    folder = HERE / "restart"
    generation = read(folder / "generate.json")
    reopened = read(folder / "reopen.json")
    route_wall = {}
    for name, data, budget in (("generate", generation, 720), ("reopen", reopened, 420)):
        receipt = read(folder / (name + "-exit.json"))
        wall = receipt["wall_s"]
        require(data["mode"] == name and data["status"] == data["phase"] == "complete", "Unfinished native process")
        require(receipt["exit"] == 0 and not receipt["expired"] and receipt["limit_s"] == budget and
                0 < sum(data["paths"].values()) <= data["elapsed_s"] <= wall <= budget, "Process accounting differs")
        require(set(data["paths"]) == {c["path"] for c in data["costs"]}, "Missing charged path")
        for path, charged in data["paths"].items():
            details = [c["s"] for c in data["costs"] if c["path"] == path]
            require(all(s >= 0 for s in details) and sum(details) <= charged, "Bad path accounting")
        route_wall[name] = wall
    require(generation["adapter"] == reopened["adapter"] == read(GAS / "default.json")["adapter"], "Adapter changed")
    f = generation["fork"]
    split = str(f["split"])
    require([r["frame"] for r in f["frames"]] == list(range(1, f["split"] + 1)), "Missing shared frame")
    require(sum(r["n"] for r in f["frames"]) == f["shared_steps"] ==
            read(GAS / "SCORE.json")["guaranteed_prefix_updates"], "Wrong common step count")
    upper = 0
    for row in f["frames"]:
        for _ in range(row["n"]):
            upper += row["dt"] / .35 + 1 / 1024
        require(upper == row["upper"] < 1, "Shared beyond the pre-update bound")
    nxt = f["next_frame"]
    require(nxt["frame"] == f["split"] + 1 and upper + nxt["n"] * (nxt["dt"] / .35 + 1 / 1024) >= 1,
            "Fork selection cannot be recovered")
    single = read(HERE / "single" / "SCORE.json")
    require(f["scale_mismatch_words"] == single["boundaries"][f["shared_steps"]]["changed_words"],
            "Fork scale and independent native prediction disagree")
    left, right = [generation["fork_receipts"][a] for a in ("default", "slow")]
    require(left.keys() == right.keys() == {"state", "ember_state", "thermal"} and
            left["state"].keys() == right["state"].keys() and
            {k for k in left["state"] if left["state"][k] != right["state"][k]} == {"burn_obj"} and
            left["thermal"] == right["thermal"] and left["ember_state"] == right["ember_state"], "Fork inventory differs")
    packets = generation["packets"]
    for arm in ("default", "slow"):
        own = generation["ordinary"][arm]
        require(generation["fork_receipts"][arm] == own[split], "Shared fork differs from ordinary branch")
        require(set(own["36"]["state"]) == {"burn","burn_obj","scal","scal_fine","vel","p","dims",
                                           "upres","time","steps","max_speed","h","origin"}, "Incomplete gas inventory")
        thermal = {"temperatures","contacts","radiant_counts","live_radiant","grid","built","cleared"}
        require(set(own["36"]["thermal"]) == thermal, "Incomplete thermal or radiant inventory")
        require({k: own["36"][k] for k in ("state","ember_state")} == original_frame(arm), "Independent frame differs")
        for frame in ("36", "37"):
            require(own[frame] == generation["states"][arm][frame] == reopened["states"][arm][frame],
                    "Ordinary/fork/cold restart state differs")
        scene = json.dumps(read(GAS / (arm + "-scene.json")), sort_keys=True, separators=(",", ":")).encode()
        require(packets[arm]["scene"] == hashlib.sha256(scene).hexdigest(), "Packet scene differs")
    require(generation["ordinary"]["default"]["36"]["state"]["scal_fine"] !=
            generation["ordinary"]["slow"]["36"]["state"]["scal_fine"], "Missing distinct branch futures")
    sizes = {k: sum(p[k] for p in packets.values()) for k in ("bytes", "raw_state_bytes")}
    require(0 < sizes["bytes"] < sizes["raw_state_bytes"] <= 1536 * 1024**2, "Packet budget differs")
    p, r = generation["paths"], reopened["paths"]
    ordinary_updates = sum(generation["ordinary"][arm]["37"]["state"]["steps"] for arm in ("default", "slow"))
    packet_writes = sum(c["s"] for c in generation["costs"] if c["phase"] == "native_packet_write")
    return dict(fork_frame=f["split"], shared_steps=f["shared_steps"], secondary_texture_bytes=f["secondary_texture_bytes"],
                gas_updates_ordinary=ordinary_updates, gas_updates_shared=ordinary_updates - f["shared_steps"],
                extra_atlas_updates=f["shared_steps"], generate_packet_write_s=packet_writes,
                ordinary_paths_s=p["ordinary_default"] + p["ordinary_slow"],
                fork_and_two_packet_paths_s=p["fork_prefix"] + p["continue_default"] + p["continue_slow"],
                cold_start_generate_s=p["cold"] + p["cold_prepare"], cold_start_reopen_s=r["cold"] + r["cold_prepare"],
                reopen_two_paths_s=r["cold_continue_default"] + r["cold_continue_slow"],
                process_wall_s=route_wall, packet_sizes=sizes)


if __name__ == "__main__":
    require(not sys.flags.optimize, "Use normal Python assertions")
    check_manifest()
    for program, args in (("gas/verify.py", ()), ("single/compare.py", ("--controls",)),
                          ("single/compare.py", ()), ("rounding/check.py", ())):
        subprocess.run([sys.executable, "-I", "-B", str(HERE / program), *args], check=True)
    print(json.dumps(check_restart(), indent=2))
