"""Verify full ordinary coarse/fine input identity and score the first closed window."""
import argparse
import json
from pathlib import Path
from flag import HERE, LIMIT
from verify import compare


def correct_detail(row):
    gas=row["gas"]
    factor=gas["upres"]
    if factor==1:
        return "scal_fine" not in gas
    if not isinstance(factor,int) or factor<1 or "scal_fine" not in gas:
        return False
    fine=gas["scal_fine"]
    dims=list(reversed(gas["dims"]))
    return fine["shape"]==[factor*n for n in dims]+[4] and fine["dtype"]=="<f2"


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder",type=Path,nargs="?",default=HERE/"evidence")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    score=json.dumps(compare(args.folder,correct_detail,LIMIT),indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(score,encoding="utf8")
    print(score,end="")
