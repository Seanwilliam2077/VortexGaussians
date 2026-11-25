"""Stage the registered T120 geometry and project two native calibrated foreground mattes."""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INPUT = ROOT / "t120-next-release-registration"


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def write(path, value):
    if path.exists():
        if load(path) != value:
            raise ValueError(f"Frozen file mismatch: {path.name}")
        return
    raw = (json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n").encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def main():
    spec = importlib.util.spec_from_file_location("calibrated_matte", ROOT/"t107-visible-burn-progression/measure.py")
    matte = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matte)
    reg, cfg, shell = (load(INPUT/p) for p in ("REGISTRATION.json", "recipe.json", "shell.json.gz"))
    assert reg["rng"]["uint32"] == cfg["seed"] == 2234068899
    assert [x["id"] for x in reg["camera_choices"]] == [76,230]
    assert hashlib.sha256(matte.np.asarray(shell,dtype="<u4").tobytes()).hexdigest() == reg["b_shell"]["ordered_uint32le_sha256"]
    write(HERE/"recipe.json", cfg)
    write(HERE/"shell.json.gz", shell)
    geom = ROOT/"t101-playground-holdout/local/foreground.ply"
    pos, cov, opacity = matte.splats(geom,cfg["original_sha256"],cfg["material_count"])
    cp = ROOT/"t111-playground-shot-choice/local/cameras.json"
    assert hashlib.sha256(cp.read_bytes()).hexdigest() == reg["acquisition"]["members"][1]["sha256"]
    native = {c["id"]:c for c in load(cp)}
    static, times = {}, {}
    for registered in reg["camera_choices"]:
        cid = registered["id"]
        cam = native[cid]
        assert hashlib.sha256(json.dumps(cam,sort_keys=True,separators=(",",":")).encode()).hexdigest() == registered["source_row_sha256"]
        start = perf_counter()
        proj = matte.projection(pos,cov,cam)
        weights,img,_,checks = matte.raster(proj,opacity,{},{},[p["site"] for p in cfg["picks"][:2]])
        times[cid] = perf_counter()-start
        dest = HERE/f"weights-{cid}.json.gz"
        write(dest, dict(camera_id=cid,asset_count=len(pos),eligible_weights=[[i,float(weights[i])] for i in shell]))
        static[cid] = dict(sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),shell_sites=len(shell),
                           raw_shell_micro_pixels=sum(math.floor(weights[i]*1e6+.5) for i in shell),
                           foreground_pixel_equivalents=float(img.sum()),independent_projected_pixel_checks=checks)
    write(HERE/"STATIC.json",dict(asset_sha256=cfg["asset_sha256"],original_sha256=cfg["original_sha256"],cameras=static))
    if not (HERE/"projection-cost.json").exists():
        write(HERE/"projection-cost.json",times)
    print("Projected", list(static), "on",len(shell),"registered sites")


if __name__ == "__main__":
    main()
