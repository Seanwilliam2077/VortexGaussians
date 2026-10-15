"""Tiny P7 audit wiring test and three in-memory negative controls.

Reads only the authored n=4, three-step producer preflight; never executes a
formal-size experiment or changes its evidence. No producer code is imported.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path

import numpy as np

import audit


def run(path):
    raw=audit.read_json(path); text=Path(path).read_text(encoding="utf-8-sig")
    definition=raw["definition"]
    if definition["n"]!=4 or definition["rate"]!=120 or len(raw["frames"])!=3:
        raise ValueError("selftest only accepts n4/rate120/three-step preflight")
    checks=audit.Checks(); f=audit.audit_fixture(raw,definition,text,checks)
    history=raw["history"]; gz=Path(path).parent/history["file"]
    payload=gzip.decompress(gz.read_bytes())
    checks.check("tiny:gzip-authentication",audit.sha(payload)==history["uncompressedSHA256"]
                 and audit.file_sha(gz)==history["compressedSHA256"] and len(payload)==history["uncompressedBytes"])
    states=np.frombuffer(payload,dtype="<f8").reshape(4,64)
    checks.close("tiny:initial-state",states[0],f["initial"],atol=0.,rtol=0.)
    scale=max(1.,audit.thermal_energy(states[0],f["capacity"],f["ns"])["total"])
    replays=[]
    for k,frame in enumerate(raw["frames"],1):
        gas,accepted,error=audit.check_actual_geometry(frame,f["origins"],k,120,f"tiny:geometry{k}",checks)
        reference=audit.allpairs_replay(f["surface"],gas,f["measure"][:32],f["measure"][32:],f["capacity"],states[k-1],1/120)
        checks.close(f"tiny:full-step{k}",states[k],reference["temperature"],atol=1e-9,rtol=0.)
        checks.check(f"tiny:edge-count{k}",frame["graph"]["edgeCount"]==reference["edgeCount"])
        if k==1: audit.check_physical_replay(f,frame,states[0],states[1],120,"tiny:first-full-schema",scale,checks)
        for part in ("surface","gas","total"):
            audit.check_energy(checks,f"tiny:before{k}:{part}",frame["ledger"]["Ebefore"][part],audit.thermal_energy(states[k-1],f["capacity"],32)[part],scale)
            audit.check_energy(checks,f"tiny:after{k}:{part}",frame["ledger"]["Eafter"][part],audit.thermal_energy(states[k],f["capacity"],32)[part],scale)
        replays.append({"step":k,"maxTemperatureErrorK":float(np.max(np.abs(states[k]-reference["temperature"]))),"edgeCount":reference["edgeCount"]})
    for k,T in enumerate(states):
        audit.check_observation(raw["observations"][k],audit.observation(T,f["capacity"],4,k,120),f"tiny:observation{k}",scale,checks)

    fault_rows=[]
    wrong_geometry=copy.deepcopy(raw["frames"][1])
    wrong_geometry["geometryGasPositions"]=wrong_geometry["acceptedGasPositions"]
    fault=audit.Checks(); audit.check_actual_geometry(wrong_geometry,f["origins"],2,120,"wrong-geometry-time",fault)
    fault_rows.append({"name":"prestep-geometry-shifted-to-accepted-time","detected":any(not r["passed"] for r in fault.rows),"checks":fault.rows})

    reset=states[0].copy(); frame=raw["frames"][2]
    reference=audit.allpairs_replay(f["surface"],np.asarray(frame["geometryGasPositions"]),f["measure"][:32],f["measure"][32:],f["capacity"],states[2],1/120)
    fault=audit.Checks(); fault.close("state-reset-between-steps",reset,reference["temperature"],atol=1e-9,rtol=0.)
    fault_rows.append({"name":"temperature-reset-instead-of-state-continuation","detected":any(not r["passed"] for r in fault.rows),"checks":fault.rows})

    wrong_map=copy.deepcopy(raw["observations"][-1])
    wrong_map["display"]=[float(np.mean(states[-1,:32]))]*8192
    fault=audit.Checks(); audit.check_observation(wrong_map,audit.observation(states[-1],f["capacity"],4,3,120),"wrong-display-map",scale,fault)
    fault_rows.append({"name":"constant-average-replaces-bilinear-display-map","detected":any(not r["passed"] for r in fault.rows),"checks":fault.rows})

    # A constant thermal field must map identically even in the clamped strip.
    checks.close("tiny:constant-bilinear-boundary",audit.display_map(np.full(64,317.),4),np.full(8192,317.),atol=0.,rtol=0.)
    # Never permit a zero-rise display denominator to appear accurate.
    zero=audit.observation(np.r_[np.full(32,300.),np.full(32,600.)],f["capacity"],4,0,120)
    zero_obs=[{**zero,"time":k/120} for k in range(121)]
    checks.check("tiny:zero-display-signal-invalid",not audit.compare_observations(zero_obs,zero_obs)["valid"])
    passed=all(r["passed"] for r in checks.rows) and all(r["detected"] for r in fault_rows)
    return {"phase":"P7-auditor-selftest","formal":False,"status":"passed" if passed else "failed",
            "fixture":{"n":4,"rate":120,"steps":3,"stateVectors":4,"nodes":64},
            "replays":replays,"negativeControls":fault_rows,"checks":checks.rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case",type=Path,nargs="?",default=Path(__file__).resolve().parent/"preflight-n4/preflight-n4-r120.json")
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): parser.error("selftest output already exists")
    report=run(args.case)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"negativeControls":[{"name":r["name"],"detected":r["detected"]} for r in report["negativeControls"]]}))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
