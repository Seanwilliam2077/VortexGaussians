"""Recreate the released scene's requested/fitted detail without requesting a GPU."""
import argparse
import json
from pathlib import Path
import sys
from observe import json_hash


def probe(source):
    sys.path.insert(0,str(source))
    from blackbody.scene.presets import make
    from blackbody.engine.solids import Solids
    scene=make("flag_wind",fps=24)
    return dict(preset=json_hash(scene.to_dict()),settings_detail=scene.data["render"]["upres"],
                auto_resolution=scene.data["render"]["auto_resolution"],effective_detail=scene.upres_for(True),
                planned=scene.memory_plan(True),base=scene.sim_layout(True),enabled_fabrics=len(scene.fabric_specs()),
                moving_bodies=Solids.wanted(scene),strands=len(scene.strands),moving_colliders=scene.colliders_animated(),
                grow=scene.data["domain"]["grow"])


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    a=parser.parse_args()
    report=json.dumps(probe(a.source),indent=2)+"\n"
    if a.output:
        a.output.write_text(report,encoding="utf8")
    print(report,end="")
