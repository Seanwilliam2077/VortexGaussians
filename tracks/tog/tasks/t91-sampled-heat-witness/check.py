"""Check already-saved definite one-step answers and their H-window interpretation."""
import gzip
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
transfer = "--transfer" in sys.argv
prefix = "TRANSFER-" if transfer else ""
inputs = json.loads((HERE / (prefix + "PREDICTIONS.json")).read_bytes())
if transfer:
    task = HERE.parent / "t92-transfer-workload"
    by_pick = json.loads(gzip.decompress((task / "shell-ids.json.gz").read_bytes()))
    regions = {arm: by_pick[arm[1]] for arm in ("AB", "BA")}
    trace_dir = task / "evidence"
else:
    regions = json.loads(gzip.decompress((HERE.parent / "t87-stroke-halo/PREDICTIONS.json.gz").read_bytes()))["shell_ids"]
    trace_dir = HERE.parent / "t86-ignition-margin/public"
results = []
for arm in ("AB", "BA"):
    shell = set(regions[arm])
    frames = json.loads(gzip.decompress((trace_dir / f"{arm}-trace.json.gz").read_bytes()))
    for row in [r for r in inputs["rows"] if r["arm"] == arm]:
        cut = row["cut"]
        assert len(shell) == row["shell_n"]
        immediate = shell.intersection(frames[cut]["new_ids"])
        for h in (1, 4, 8):
            actual = set().union(*(shell.intersection(step["new_ids"]) for step in frames[cut:cut+h]))
            answers = {}
            for name, method in row["methods"].items():
                ans = method["decision"]
                if ans == "yes":
                    assert method["witness"] in immediate
                elif ans == "no":
                    assert not immediate and method["witness"] is None
                    if h > 1:
                        ans = "abstain"
                else:
                    assert ans == "abstain" and method["witness"] is None
                assert ans == "abstain" or (ans == "yes") == bool(actual)
                answers[name] = ans
            results.append(dict(arm=arm, cut=cut, horizon=h, actual=bool(actual),
                                immediate_ids=sorted(immediate), decisions=answers))
summary = {m: {s: sum(q["decisions"][m] == s for q in results) for s in ("yes", "no", "abstain")}
           for m in ("allHot", "sampled")}
(HERE / (prefix + "SCORE.json")).write_text(json.dumps({"summary":summary,"queries":results}, indent=2)+"\n")
print(summary)
