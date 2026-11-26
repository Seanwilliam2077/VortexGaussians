"""Project the released rest meshes into the shot camera without creating a device or advancing time."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


REVISION = "e2ac951dbfabc6060073943e4c344439ac5f4555"
HERE = Path(__file__).resolve().parent
W, H = 1024, 576


def make_guide(root, font_path, output):
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION or subprocess.check_output(["git", "-C", str(root), "diff", "HEAD", "--", "blackbody"]):
        raise ValueError("Expected clean pinned Blackbody sources")
    sys.path.insert(0, str(root))
    from blackbody.engine import camera, cloth
    from blackbody.scene import presets

    scene = presets.make("wet_towels", fps=24)
    spec, transform = scene.camera(scene.start)
    native_w, native_h = scene.output_size()
    if not np.isclose(native_w / native_h, W / H):
        raise ValueError("Unexpected aspect ratio")
    state = camera.compute(spec, W / H, transform)
    def to_world(points):
        return (np.column_stack((points, np.ones(len(points)))) @ transform.local_to_world().T)[:, :3]

    scale = 2
    screen = Image.new("RGB", (scale*W, scale*H), "#e9ecea")
    paint = ImageDraw.Draw(screen)
    rail = scene.colliders[0]
    pos, half = np.asarray(rail["position"]), np.asarray(rail["size"])
    rail_ends = to_world(pos + np.array([[-half[0],0,0],[half[0],0,0]]))
    uv, ok = camera.project(state, rail_ends, W, H)
    assert all(ok) and rail["shape"] == "box"
    paint.line([tuple(x) for x in uv*scale], fill="#66706d", width=5*scale)
    polys, bounds = [], []
    light = np.array([-.6, .48, .7])
    for fabric, placement in zip(scene.fabric_specs(), scene.fabrics_at(scene.start), strict=True):
        mesh = cloth.panel_mesh(fabric)
        vertices = to_world(cloth.place(mesh.rest, placement))
        xy, ok = camera.project(state, vertices, W, H)
        assert np.all(ok) and np.all(xy>=0) and np.all(xy<[W,H])
        bounds.append([int(len(vertices)),np.round(xy.min(axis=0),2).tolist(),np.round(xy.max(axis=0),2).tolist()])
        for i in (0,len(vertices)//2,-1):
            origin, direction = camera.pixel_ray(state,*xy[i],W,H)
            assert np.linalg.norm(np.cross(vertices[i]-origin,direction))<1e-4
        xyz=vertices[mesh.tris]
        normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
        normals/=np.linalg.norm(normals,axis=1)[:,None]
        normals*=np.where(np.sum(normals*(state.eye-xyz.mean(axis=1)),axis=1)>0,1.,-1.)[:,None]
        rgb=(np.array([142,157,154])*(.67+.33*np.maximum(0,normals@light))[:,None]).astype(int)
        depths=(np.column_stack((vertices,np.ones(len(vertices)))) @ state.view.T)[mesh.tris,2].mean(axis=1)
        polys.extend(zip(depths,(xy[mesh.tris]*scale).round().astype(int),rgb))
    assert len(bounds)==2
    for _,poly,col in sorted(polys,key=lambda row: row[0]):
        paint.polygon([tuple(point) for point in poly],fill=tuple(col))
    card=Image.new("RGB",(1152,779),"#fafaf7")
    card.paste(screen.resize((W,H),Image.Resampling.LANCZOS),(70,109))
    d=ImageDraw.Draw(card)
    def txt(pos,s,size,anchor="lt"):
        d.text(pos,s,font=ImageFont.truetype(str(font_path),size),fill="#233637",anchor=anchor)
    txt((69,30),"镜头参考   /   两块悬挂的棉布",32)
    txt((70,78),"初始静止几何 · 项目相机",17)
    for fraction in (0,.25,.5,.75,1):
        y=109+round(fraction*H)
        x=70+round(fraction*W)
        d.line((64,y,69,y),fill="#5a6765")
        d.line((x,685,x,691),fill="#5a6765")
        txt((56,y),f"{fraction:.0%}",14,"rm")
        txt((x,698),f"{fraction:.0%}",14,"mt")
    txt((70,742),"位置按画幅比例描述，原点在左上角。图中仅显示布片与吊杆的静止位置。",18)
    card.save(output)
    print(json.dumps({"revision":revision,"preset":"wet_towels","projection_px":[W,H],"mesh_vertex_counts_and_bounds":bounds,
                      "image_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
                      "candidate_runs":0,"physics_steps":0},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--font",type=Path,default=Path("C:/Windows/Fonts/msyh.ttc"))
    parser.add_argument("--output",type=Path,default=HERE/"framing.png")
    a=parser.parse_args()
    make_guide(a.source.resolve(),a.font,a.output)
