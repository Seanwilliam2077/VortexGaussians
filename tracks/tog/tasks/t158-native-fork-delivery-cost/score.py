"""Verify each complete delivery and apply the predeclared blockwise decisions."""
import argparse
import json
from pathlib import Path
from statistics import median

from bench import HERE, LIMIT, ORDERS, file_sha, t154


def load(path):
    return json.loads(path.read_bytes())


def comparison(runs, a, b):
    wins = []; pairs = []; workers = []
    for worker, trials in enumerate(runs):
        times_a = [r[a] for r in trials]
        times_b = [r[b] for r in trials]
        wins.append(sum(x<y for x,y in zip(times_a,times_b,strict=True)))
        workers.append(median(times_a)<median(times_b))
        for i,(x,y) in enumerate(zip(times_a,times_b,strict=True)):
            pairs.append(dict(worker=worker,block=i,delta_s=y-x,ratio=x/y,saving_fraction=(y-x)/y))
    improvement = median(x["saving_fraction"] for x in pairs)
    direction = all(workers) and sum(wins)>=5
    return dict(candidate=a,baseline=b,paired_wins=wins,lower_worker_median=workers,
                median_paired_saving_fraction=improvement,repeatable_direction=direction,
                practical=direction and improvement>.03,pairs=pairs)


def inspect(out, private=None):
    ref = load(t154.HERE/"evidence"/"generate.json")["packets"]
    runs, processes = [], []
    for iw,orders in enumerate(ORDERS):
        data = load(out/f"worker-{iw}.json")
        host = load(out/f"exit-{iw}.json")
        assert data["status"]=="complete" and data["pin"]==t154.PIN
        assert host["exit"]==0 and not host["expired"] and data["elapsed_s"] <= host["wall_s"] <= LIMIT
        assert len(data["cells"])==9 and data["backend_test"]==dict(all_flagged=51200,certified_flagged=0,
                                                                      signed_words=65536,supported_words=14336)
        groups, forks = [], []
        for block, order in enumerate(orders):
            cells = data["cells"][block*3:block*3+3]
            assert "".join(c["method"] for c in cells)==order
            group = {}
            for position,c in enumerate(cells):
                method = c["method"]
                assert (c["block"],c["position"])==(block,position)
                assert 0<sum(c["phases"].values())<=c["seconds"] and set(c["files"])==set(ref)
                for arm,p in c["files"].items():
                    assert all(p[key]==ref[arm][key] for key in ("sha256","bytes","raw_state_bytes"))
                    if private:
                        packet = private/f"w{iw}-b{block}-{position}-{method}-{arm}.bbc"
                        assert packet.stat().st_size==p["bytes"] and file_sha(packet)==p["sha256"]
                if method != "I":
                    f = c["fork"]
                    assert f["split"]==8 and f["common_steps"]==12
                    if method == "S":
                        assert f["guard_dispatches"]==13 and f["native_slow_dispatches"]==0
                        assert f["fallback"]==(f["ambiguous_or_invalid_words"]>0)
                    else:
                        assert f["guard_dispatches"]==0 and f["native_slow_dispatches"]==12
                    forks.append(dict(block=block,method=method,**f))
                group[method] = c["seconds"]
            groups.append(group)
        runs.append(groups)
        med = {m:median(r[m] for r in groups) for m in "IDS"}
        st = data["setup"]
        common_cold = st["device_and_engine_s"]+st["native_prepare_and_one_warm_frame_s"]
        first = {m:common_cold + groups[0][m] + (st["single_atlas_compile_and_test_s"] if m=="S" else 0.)
                 for m in "IDS"}
        processes.append(dict(worker=iw,wall_s=host["wall_s"], common_cold_s=common_cold,
            single_compile_and_test_s=st["single_atlas_compile_and_test_s"], ready_median_s=med,
            first_block_s_with_cold_and_method_setup=first, forks=forks))
    comp = {a+"_vs_"+b:comparison(runs,a,b) for a in "IDS" for b in "IDS" if a!=b}
    directions = [a for a in "IDS" if all(comp[a+"_vs_"+b]["repeatable_direction"] for b in "IDS" if a!=b)]
    practical = [a for a in "IDS" if all(comp[a+"_vs_"+b]["practical"] for b in "IDS" if a!=b)]
    return dict(processes=processes,blocks=runs,comparison=comp,repeatable_winner=directions,
                practical_winner=practical,unique_pairs_delivered=18,total_file_bytes=sum(x["bytes"] for x in ref.values())*18)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=HERE/"evidence")
    p.add_argument("--private",type=Path)
    p.add_argument("--write",action="store_true")
    args = p.parse_args()
    result = inspect(args.out,args.private)
    target = args.out/"SCORE.json"
    if args.write:
        t154.save(target,result)
    else:
        assert result==load(target)
    print(json.dumps({k:v for k,v in result.items() if k not in ("processes","comparison")},indent=2))
