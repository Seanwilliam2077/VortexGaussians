"""Measure newly igniting global sites, including light-only births already set by full."""
from prepare import HERE, load, write


def main():
    native=HERE/"evidence/native"
    shots=load(native/"capture-report.json")["shots"]
    shell=set(load(HERE/"shell.json.gz"))
    ledgers={p:load(native/f"A{p}-trace.json.gz")[180:270] for p in ("L","F")}
    light_direct=set(shots["AL"]["edit"]["ids"])
    full_direct=set(shots["AF"]["edit"]["ids"])
    assert light_direct <= full_direct
    extra=full_direct-light_direct
    rows=[]
    for l,f in zip(ledgers["L"],ledgers["F"],strict=True):
        assert l["frame"]==f["frame"]
        suppressed=[i for i in l["new_ids"] if i in extra]
        common=[i for i in l["new_ids"] if i not in extra]
        assert common==f["new_ids"]
        rows.append(dict(frame=l["frame"],natural_light=len(l["new_ids"]),natural_full=len(f["new_ids"]),
                         newly_active_under_light_already_set_by_full=len(suppressed),shell_births=len(shell.intersection(common))))
    audit=load(HERE/"evidence/physical-precheck/CAPTURE.json")
    assert audit["status"]=="validated" and not audit["errors"]
    s=audit["full_audits"]["sibling"]
    assert not s["fallback"]
    step=s["work"]["steps"]
    assert step==90 and s["frames"]==[270]
    totals={k:sum(row[k] for row in rows) for k in rows[0] if k!="frame"}
    out=dict(direct_extra_sites=len(extra),guard_frames=step,physical_boundary=s["physical"]["270"],totals=totals,
             frames_with_suppressed_birth= [r["frame"] for r in rows if r["newly_active_under_light_already_set_by_full"]],
             per_frame=rows)
    write(HERE/"PREFIX.json",out)
    print(step,len(extra),totals)


if __name__=="__main__":
    main()
