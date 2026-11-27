"""Recompute the gas, fuel, source-platform and same-native-reaction observations offline."""
import argparse
import json
from pathlib import Path
import zlib

import numpy as np

from capture import HERE, T151, LIMIT, ROI, atlas_stats, digest, json_hash, lower_after, require


def read(path):
    return json.loads(path.read_bytes())


def load_arm(folder, arm):
    rows = [json.loads(line) for line in (folder / f"{arm}.jsonl").read_bytes().splitlines()]
    updates = [r for r in rows if r["kind"]=="update"]
    states = {r["index"]:r for r in rows if "atlas" in r}
    frames = [r for r in rows if r["kind"]=="frame_end"]
    require(len(states)==sum("atlas" in r for r in rows) and
            [r["index"] for r in updates]==list(range(len(updates))) and
            [r["frame"] for r in frames]==list(range(1,37)), "Missing or duplicated native boundaries")
    return updates,states,frames


def decode(path, records):
    previous = None
    with path.open("rb") as archive:
        for i,row in records.items():
            a = row["atlas"]
            require(archive.tell()==a["offset"] and a["dtype"]=="<f2", "Changed native atlas layout")
            raw = np.frombuffer(zlib.decompress(archive.read(a["size"])), dtype=np.uint8)
            previous = raw if previous is None else previous ^ raw
            require(digest(previous)==a["sha256"], "Native atlas digest mismatch")
            material = previous.view("<f2").reshape(a["shape"])
            require(np.isfinite(material).all() and all(a[k]==v for k,v in atlas_stats(material).items()), "Invalid atlas event counts")
            yield i,material
        require(not archive.read(1), "Excess atlas payload")


def alight(a):
    return (a[...,0] > 0) & (a[...,1] >= 1) & (a[...,2] > .5)


def next_fuel(x, active, dt, rate):
    result = x.copy()
    result[active] = np.maximum(x[active].astype(np.float32)-np.float32(rate)*np.float32(dt),np.float32(0))
    return result


def char_proxy(a):
    x = np.clip(a[...,0].astype(np.float32),0,1)
    active = (a[...,2]>=.5) & ((a[...,2]>=1.5) | (a[...,1]>=1))
    return np.where(active,1-x*x*(3-2*x),0)


def fields(first,second):
    return sorted(k for k in first.keys()|second.keys() if first.get(k)!=second.get(k))


def controls(folder, meta):
    summary = {}
    for label,scale in (("coarse",1),("fine",3)):
        rec = meta["controls"][label]
        origin,size = [[v*scale for v in xyz] for xyz in ROI]
        require(rec["origin"]==origin and rec["size"]==size and rec["grid"]==[v*scale for v in meta["dims"]], "Diagnostic box changed")
        with np.load(folder/(label+"-react.npz"),allow_pickle=False) as file:
            off,on = file["off"],file["on"]
        require(on.dtype==off.dtype==np.float16 and on.shape==off.shape==(*size[::-1],4) and
                np.isfinite(off).all() and np.isfinite(on).all() and
                digest(on)==rec["on_sha256"] and digest(off)==rec["off_sha256"], "Source control readback changed")
        diff = on.view("<u2") != off.view("<u2")
        altered = np.any(diff,axis=-1)
        xyz = witness = None
        if altered.any():
            pos = np.unravel_index(np.argmax(altered),altered.shape)
            xyz = [int(i+o) for i,o in zip(pos[::-1],origin)]
            witness = dict(xyz=xyz, off=off[pos].tolist(), on=on[pos].tolist())
        summary[label] = dict(origin=origin,size=size,changed_cells=int(altered.sum()),
                              changed_by_channel=diff.sum(axis=(0,1,2)).tolist(),witness=witness,
                              max_abs=float(np.max(np.abs(on.astype(np.float32)-off.astype(np.float32)))))
    return summary


def score(folder):
    base = T151/"evidence"
    meta = read(folder/"extended.json")
    orig = read(base/"default.json")
    ex = read(folder/"extended-exit.json")
    require(meta["status"]=="complete" and ex["exit"]==0 and not ex["expired"] and ex["limit_s"]==LIMIT and
            meta["elapsed_s"]<=ex["wall_s"]<=LIMIT and meta["frames"]==orig["frames"]==36, "Native process did not finish on budget")
    require(all(meta[k]==orig[k] for k in ("pin","adapter","features","dims","fine_upres","base_scene")), "Device or setup changed")
    scene = read(folder/"extended-scene.json")
    original = read(base/"default-scene.json")
    require(meta["edited_scene"]==json_hash(scene) and orig["base_scene"]==json_hash(original),"Scene hash differs")
    require(scene["sections"]["spread"]["burn_time"]==10 and original["sections"]["spread"]["burn_time"]==5,"Unexpected duration")
    scene["sections"]["spread"]["burn_time"] = 5.
    require(scene==original, "More than the native burn duration changed")
    new,ns,nf = load_arm(folder,"extended")
    old,os,of = load_arm(base,"default")
    actual_uniforms=[r for r in map(json.loads,(folder/"extended.jsonl").read_bytes().splitlines()) if r["kind"]=="burn_uniform"]
    require(len(actual_uniforms)==len(new) and all(all(a[k]==b[k] for k in ("index","frame","substep","dt_f32","rate_f32"))
            for a,b in zip(actual_uniforms,new)), "Native uniform receipts do not match reported inputs")
    require(len(new)==meta["updates"] and sorted(ns)==list(range(len(new)+1)), "Sparse alternative material stream")
    require(all(np.isclose(sum(r["dt"] for r in new if r["frame"]==fr["frame"]),1/24,rtol=0,atol=1e-12)
                and fr["substep"]==sum(r["frame"]==fr["frame"] for r in new) for fr in nf), "Frame dt or native count differs")
    aligned = next((i for i,(a,b) in enumerate(zip(old,new))
                    if any(a[k]!=b[k] for k in ("index","dt","forcing","substep","frame"))), min(len(old),len(new)))
    checked = {r["index"]:r for r in nf if "state" in r}
    bound=.75
    last_safe=0
    for r in new:
        require(r["rate_f32"]==np.float32(.1) and r["dt_f32"]==np.float32(r["dt"]), "Native f32 differs")
        bound=lower_after(bound,r["dt_f32"])
        require(r["lower_after"]==bound, "A priori fuel bound differs")
        if bound is not None:
            last_safe=r["index"]+1
    default_material = dict(decode(base/"default-atlas.zlib",os))
    observed=[]
    evolution=[]
    stock=previous=first=None
    for i,alt in decode(folder/"extended-atlas.zlib",ns):
        if i==0:
            eligible=alt[...,2]>.5
            require(eligible.any() and alt[...,0][eligible].min()>=.75 and alt[...,0][eligible].max()<=1.25 and
                    not alt[...,1].any() and not alt[...,3].any(), "Initial dry fuel differs")
            stock=alt[...,0].copy()
            first=np.full(stock.shape,-1,dtype=np.int32)
            slow_prediction=stock
        else:
            mask=alight(previous)
            first[(first<0)&mask]=i
            dt=new[i-1]["dt_f32"]
            stock=next_fuel(stock,mask,dt,.2)
            slow_prediction=next_fuel(previous[...,0],mask,dt,.1)
        lit=alight(alt)
        eligible=alt[...,2]>.5
        minfuel=float(alt[...,0][eligible].min())
        slow_errors=int(np.count_nonzero(slow_prediction.view("<u2")!=alt[...,0].view("<u2")))
        proxy_diff=int(np.count_nonzero(stock.view("<u2")!=alt[...,0].view("<u2")))
        if i<=last_safe:
            require(minfuel >= (.75 if i==0 else new[i-1]["lower_after"]) and
                    np.all(alt[...,0][lit]>=np.float32(.15)) and not np.any(alt[...,3]), "Slow guard counterexample")
        evolution.append(dict(index=i,lit=int(lit.sum()),minfuel=minfuel,reconstructed_fast_differs=proxy_diff,
                              native_slow_recurrence_errors=slow_errors,first_decrements=int(np.count_nonzero(first==i))))
        if i in default_material and i<=aligned:
            fast=default_material[i]
            a,b=os[i],ns[i]
            require(all(a[k]==b[k] for k in ("index","frame","substep")),"Different sampled boundary")
            gas=b.get("state",checked.get(i,{}).get("state"))
            require(gas is not None,"Missing matching gas readback")
            changed=(fast.view("<u2")!=alt.view("<u2")).sum(axis=(0,1,2)).tolist()
            fast_lit=alight(fast)
            fast_min=float(fast[...,0][fast[...,2]>.5].min())
            plateau=bool(fast_min>=np.float32(.15) and minfuel>=np.float32(.15) and
                         not np.any(fast[...,3]) and not np.any(alt[...,3]) and np.array_equal(fast_lit,lit))
            observed.append(dict(index=i,frame=a["frame"],substep=a["substep"],time=a["state"]["time"],
                                 changed_material_words=changed, gas_changed=fields(a["state"],gas),
                                 fast_lit=int(fast_lit.sum()),slow_lit=int(lit.sum()),plateau_matches=plateau,
                                 different_char_proxy_texels=int(np.count_nonzero(char_proxy(fast)!=char_proxy(alt))),
                                 fast_fuel_min=fast_min,slow_fuel_min=minfuel,
                                 fast_recurrence_word_errors=int(np.count_nonzero(stock.view("<u2")!=fast[...,0].view("<u2")))))
        previous=alt
    common=min(last_safe,aligned)
    first_diff=next((r["index"] for r in observed if r["changed_material_words"][0]),None)
    end=read(folder/"extended-36.json")
    baseline=read(T151.parent/"t154-native-surface-fork"/"evidence"/"generate.json")["ordinary"]["default"]["36"]
    require(end["state"]["burn_obj"]["sha256"]==ns[len(new)]["atlas"]["sha256"],"Final independent atlas read differs")
    augmented={group:fields(end[group],baseline[group]) for group in baseline}
    ember_different=[a["frame"] for a,b in zip(of,nf,strict=True) if a["embers"]!=b["embers"]]
    measured=sum(r["index"]<common and r["changed_material_words"][0]>0 and r["plateau_matches"]
                 and r["fast_lit"]>0 for r in observed)
    derived=sum(row["index"]<common and row["reconstructed_fast_differs"]>0 and row["lit"]>0 for row in evolution)
    valid_projection=not any(row["native_slow_recurrence_errors"] for row in evolution) and not any(r["fast_recurrence_word_errors"] for r in observed)
    diagnostic=controls(folder,meta)
    controls_positive=all(r["changed_cells"]>0 for r in diagnostic.values())
    matched=all(not (r["gas_changed"] or any(r["changed_material_words"][1:]) or not r["plateau_matches"]) for r in observed if r["index"]<=common)
    mechanism=measured>0 and matched and not ember_different and augmented=={"state":["burn_obj"],"thermal":[],"ember_state":[]}
    return dict(updates=[len(old),len(new)], aligned_updates=aligned, certified_lower_bound_updates=last_safe,
                final_fuel_lower_bound=bound, first_observed_fuel_difference=first_diff,
                directly_witnessed_shared_updates_starting_different_and_lit=measured,
                inferred_shared_updates_starting_different_and_lit=derived if valid_projection else None,
                forward_fuel_recurrence_exact_at_available_references=valid_projection,
                frame_end_ember_differences=ember_different,frame36_changed=augmented,
                native_nonzero_control_on_both_grids=controls_positive,material_and_state_mechanism=mechanism,
                controls=diagnostic, wall_s=ex["wall_s"], observed=observed,evolution=evolution)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence",type=Path,default=HERE/"evidence")
    p.add_argument("--write",action="store_true")
    args=p.parse_args()
    result=score(args.evidence)
    path=args.evidence/"SCORE.json"
    if args.write:
        path.write_bytes((json.dumps(result,indent=2,allow_nan=False)+"\n").encode())
    else:
        require(result==read(path),"Saved score differs")
    print(json.dumps({k:v for k,v in result.items() if k not in ("observed","evolution")},indent=2))
