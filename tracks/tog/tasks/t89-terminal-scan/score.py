"""Audit the uninterrupted runs and compare paired native terminal prefixes."""
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median


HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
T86 = HERE.parent / "t86-ignition-margin" / "public"
T87 = HERE.parent / "t87-stroke-halo"


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def native_times(steps):
    full = sum(r["step_ms"] for r in steps)
    prefix = sum(r["step_ms"] for r in steps[:-1]) + steps[-1]["scan_ms"]
    require(0 < prefix <= full, "Invalid terminal scan measurement")
    return dict(stop_frame=steps[-1]["frame"], complete_final_step_ms=full,
                through_terminal_scan_ms=prefix, saved_final_tail_ms=full-prefix,
                paired_prefix_to_complete=prefix/full)


def score():
    cap=read(EVIDENCE / "CAPTURE.json")
    t86=read(T86 / "capture-report.json")
    shell_query=read(T87 / "PREDICTIONS.json.gz")
    shell_ref=read(T87 / "SCORE.json")
    previous={(r["arm"],r["cut"],r["horizon"]):r for r in shell_ref["queries"]}
    require(cap["status"]=="validated" and cap["steps"]==720 and not cap["errors"], "Capture invalid")
    rows=[]
    checks={}
    for arm in ("AB","BA"):
        file=cap["shots"][arm]["frames"]
        packed=(EVIDENCE/file["file"]).read_bytes()
        require(hashlib.sha256(packed).hexdigest()==file["sha256"], "Compressed time ledger")
        raw=gzip.decompress(packed)
        require(hashlib.sha256(raw).hexdigest()==file["decoded_sha256"], "Decoded time ledger")
        frames=json.loads(raw)
        require([r["frame"] for r in frames]==list(range(1,361)), "Time ledger sequence")
        markers=cap["shots"][arm]["markers"]
        require(markers["end"]==t86["shots"][arm]["end"], "Native endpoint mismatch")
        for field in ("pre_edit","post_edit"):
            require(markers[field]==t86["shots"][arm][field]["hash"], "Native contact fork mismatch")
        old=read(T86 / f"{arm}-trace.json.gz")
        for n,o in zip(frames,old):
            require(all(n[k]==o[k] for k in ("frame","new_ids","retired","active_count","gas_count","random_draws")),
                    "Discrete native trace mismatch")
            require(0 <= n["scan_ms"] <= n["step_ms"], "Clock crossing")
        shell=set(shell_query["shell_ids"][arm])
        for cut in (210,240,300):
            snap=read(T86 / f"{arm}-{cut}-eligibility.json.gz")
            eligible={i for i in shell if snap["state"][i]==0 and snap["fuel"][i]>0}
            require(bool(eligible),"Expected a nonempty T87 shell")
            for h in (1,4,8):
                win=frames[cut:cut+h]
                events=[]
                for frame in win:
                    inside=sorted(eligible.intersection(frame["new_ids"]))
                    if inside:
                        events.append(dict(frame=frame["frame"], ids=inside))
                first=events[0]["frame"] if events else None
                archived=previous[(arm,cut,h)]
                require(archived["events"]==events and archived["first_ignition_frame"]==first, "Regional onset mismatch")
                last=first if events else cut+h
                rows.append(dict(arm=arm,cut=cut,horizon=h,regional_first_event_frame=first,
                                 all_site_labels=native_times(win), shell_any=native_times(frames[cut:last])))
        checks[arm]=dict(native_frames=len(frames),regional_event_queries=9,end_hash=markers["end"]["hash"])
    summary={}
    for op in ("all_site_labels","shell_any"):
        summary[op]={}
        for key in ("all",1,4,8):
            results=[r[op] for r in rows if key=="all" or r["horizon"]==key]
            summary[op][str(key)]=dict(
                windows=len(results),
                median_complete_ms=median(x["complete_final_step_ms"] for x in results),
                median_through_scan_ms=median(x["through_terminal_scan_ms"] for x in results),
                median_saved_tail_ms=median(x["saved_final_tail_ms"] for x in results),
                median_paired_prefix_to_complete=median(x["paired_prefix_to_complete"] for x in results))
    return dict(schema="t89-paired-terminal-scan-v1", checks=checks, summary=summary, windows=rows)


if __name__=="__main__":
    results=score()
    (HERE/"SCORE.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf8")
    print(json.dumps(results["summary"],indent=2))
