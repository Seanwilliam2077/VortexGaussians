"""Score the two-attempt Firewoods decision using the same complete-action verifier as T111."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
T109=HERE.parent/"t109-common-parent-choice"
T111=HERE.parent/"t111-playground-shot-choice"
# Both experiment modules expose the same verified trace loader. Bind the original
# Firewoods ground-truth builder before importing the shared transaction scorer.
sys.path.insert(0,str(T109))
from reference import build

spec=importlib.util.spec_from_file_location("transaction_verifier",T111/"score.py")
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--capture-dir",type=Path)
    args=p.parse_args()
    result=verifier.score(args.capture_dir or HERE/"evidence/timing",study=T109,ground_truth=build,
                          cameras=(0,124),weight_root=HERE.parent/"t107-visible-burn-progression/evidence")
    dest=(args.capture_dir or HERE)/"SCORE.json"
    dest.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    for q in result["operations"]:print(q["cameras"],q["choices"],{m:round(r["delivered_ms"],2) for m,r in q["methods"].items()})
