"""No-timestep device and native scene preparation for the exact external curtain runtime."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"t125-nvidia-dx12-admission"))
from admit import save,select


def worker(root,out):
    import mujoco
    assert mujoco.__version__=="3.3.7"
    wheels=json.loads((HERE/"evidence/WHEELS.json").read_text())
    env={x["package"]:importlib.metadata.version(x["package"]) for x in wheels["wheels"]}
    assert all(env[x["package"]]==x["version"] for x in wheels["wheels"])
    t=time.perf_counter();result=dict(environment=env,scene="fabric_curtain",arm="F",simulated_steps=0,renders=0)
    def note(stage,**fields):
        result.update(stage=stage,elapsed_s=time.perf_counter()-t,**fields)
        save(out/"PREPARE.json",result)
    try:
        note("admitting_device")
        card=select(root)
        from blackbody.scene.presets import make
        from blackbody.engine.engine import Engine
        scene=make("fabric_curtain",fps=24)
        note("opening_engine",adapter=card)
        engine=Engine()
        assert engine.gpu.name==card["device"] and engine.gpu.backend==card["backend_type"]
        note("preparing_native_scene")
        engine.prepare(scene,final=True)
        note("prepared",dims=list(engine.solver.dims),cell_size=float(engine.solver.h),
             fabric_vertices=int(engine.cloth.built.n),final_quality=bool(engine.final),
             adapter=card,sim_frame=engine.sim_frame)
        return 0
    except Exception as ex:
        note("failed",exception=type(ex).__name__,reason=str(ex).replace(str(root),"<upstream>").replace(str(Path.home()),"<home>")[:1800])
        return 2


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--source",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True);p.add_argument("--worker",action="store_true")
    a=p.parse_args();out=a.out.resolve();src=a.source.resolve()
    if a.worker:sys.exit(worker(src,out))
    out.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter()
    try:
        r=subprocess.run([sys.executable,__file__,"--worker","--out",str(out),"--source",str(src)],timeout=150)
        save(out/"EXIT.json",dict(exit=r.returncode,limit_s=150,wall_s=time.perf_counter()-t));sys.exit(r.returncode)
    except subprocess.TimeoutExpired:
        save(out/"EXIT.json",dict(status="time_limit",limit_s=150,wall_s=time.perf_counter()-t));sys.exit(2)
