"""Run the fixed stiffness edit with the native final detail plan."""
import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "t133-flag-coupling"))
from observe import require, supervise, worker

LIMIT = 360


def check_scene(engine, scene):
    require(engine.cloth.active and not engine.solids.active and not engine.strands_on and
            not scene.colliders_animated() and not scene.data["domain"]["grow"], "Unexpected non-flag inputs")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--worker",choices=("ordinary","stiffer"))
    args=parser.parse_args()
    source,out=args.source.resolve(),args.out.resolve()
    if args.worker:
        sys.exit(worker(source,out,args.worker,check_scene))
    sys.exit(supervise(source,out,__file__,LIMIT))
