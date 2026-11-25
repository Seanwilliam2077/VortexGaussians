"""Verify the uncapped four-way run against its changed-policy native labels."""
import hashlib
import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent


def verify(asset,folder=None):
    folder = folder or HERE / "evidence" / asset
    path = folder / "CAPTURE.json"
    raw = json.loads(path.read_bytes())
    geo = json.loads((HERE / "GEOMETRY.json").read_bytes())["assets"][asset]
    assert raw["status"] == "validated" and raw["errors"] == []
    assert raw["sources"]["asset"] == geo["sha256"]
    methods = ["active-fresh", "active-anchor", "component-fresh", "component-anchor"]
    assert raw["methods"] == methods
    result = {}
    for arm_index, arm in enumerate(("AB", "BA")):
        shot = raw["arms"][arm]
        assert shot["stored_pre_restored"] and shot["contract_h"] == 60
        native = shot["native"]
        assert shot["pre"]["frame"] == native["after"]["frame"] == 180 and native["end"]["frame"] == 240
        assert [f["frame"] for f in native["frames"]] == list(range(181,241))
        first = next((f for f in native["frames"] if f["ids"]), None)
        target = first["frame"] if first else None
        eligible=native.get("eligible")
        if native["after"]["burning"]+native["after"]["charred"]==geo["sites"]:
            assert eligible in (None,0) and target is None
            eligible=0
        assert eligible is not None and (target is None or eligible>0)
        domain = geo["arms"][arm]["closure_sites"]
        assert domain == shot["audit"]["domain"] and len(shot["trials"]) == 20
        assert shot["ordinary_audit"]["frames"] == 8
        assert all(r["matched_particles"] and r["matched_material_and_frontier_values"]
                   for r in shot["ordinary_audit"]["runs"][1:])
        groups = {m: [] for m in methods}
        builds = []
        for k, trial in enumerate(shot["trials"]):
            rep, ordinal = divmod(k,4)
            name = methods[(rep+ordinal+arm_index)%4]
            assert (name,rep) == (trial["method"],trial["rep"])
            assert trial["clicked"] == native["edit"]["count"] and trial["first"] == target
            assert trial["witness"] in first["ids"] if first else trial["witness"] is None
            stats = trial["stats"]
            if name.startswith("component"):
                assert stats["domain"] == domain and stats["index_bytes"] == 4*geo["sites"]
                if stats["index_build_ms"] > 0:
                    builds.append(dict(method=name,rep=rep,ms=stats["index_build_ms"],delivered=trial["delivered_ms"]))
                if domain == geo["sites"]:
                    assert stats["fallback"] == "whole-component" and stats["scoped_steps"] == 0
                if stats["fallback"] == "expired":
                    assert 0 < stats["scoped_steps"] == stats["eligible"] < 60
                    assert trial["ordinary"] == (target-180 if first else 60)
                if not stats["fallback"]:
                    assert trial["ordinary"] == 0 and stats["scoped_steps"] == (target-180 if first else 60)
            groups[name].append(trial)
        assert len(builds)==1 and builds[0]["rep"]==0
        rows = {}
        for name, trials in groups.items():
            active=trials[1:]
            first_stats=active[0]["stats"]
            choice={k:first_stats[k] for k in ("domain","scoped_steps","eligible","fallback","new_local","local_donor_steps")}
            assert all(all(t["stats"][k]==v for k,v in choice.items()) for t in active)
            rows[name]=dict(decision=choice,delivered_ms=median(t["delivered_ms"] for t in active),
                measured_range_ms=[min(t["delivered_ms"] for t in active),max(t["delivered_ms"] for t in active)],
                warmup_ms=trials[0]["delivered_ms"],membership_ms=median(t["stats"]["membership_ms"] for t in active),
                guard_ms=median(t["stats"]["guard_ms"] for t in active))
        for backend in ("fresh","anchor"):
            r=rows["component-"+backend]
            r["ratio_to_complete"]=r["delivered_ms"]/rows["active-"+backend]["delivered_ms"]
        result[arm]=dict(first=target,clicked=native["edit"]["count"],eligible_after_click=eligible,
                         initial_burning=native["after"]["burning"],
                         cold_geometry=builds[0],audit=shot["audit"],methods=rows)
    out=dict(asset=asset,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),arms=result)
    (folder/"SCORE.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf8")
    return out


if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset",choices=("firewoods","playground"))
    parser.add_argument("--capture-dir",type=Path)
    args=parser.parse_args()
    print(json.dumps(verify(args.asset,args.capture_dir),indent=2))
