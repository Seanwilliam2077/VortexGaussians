"""Surface diagram of the measured woodpile with calibrated, opacity-weighted T109 overlays."""
from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
import reportlab

HERE=Path(__file__).resolve().parent
TASK=HERE.parent
WARM=np.array([213,204,187])
ELIGIBLE=np.array([35,129,151])
IGNITED=np.array([244,80,27])
BACKGROUND=np.array([248,248,245])
CORNERS=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)])
TETS=((0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6))


def reconstruct():
    """A custom isosurface from a histogram of material-center locations."""
    g=np.load(HERE/"local/geometric-bins.npz")
    ind=g["indices"];origin=ind.min(axis=0)-3;coords=ind-origin
    density=np.zeros(coords.max(axis=0)+4);density[tuple(coords.T)]=np.minimum(g["count"],3)
    for axis in range(3):
        density=(np.roll(density,1,axis)+2*density+np.roll(density,-1,axis))/4
    # Interpolate a coarse occupancy boundary; surface shape and lighting
    # depend only on spatial bins. No appearance or per-site scale is used.
    value=.18
    cubes=np.stack([density[x:x+density.shape[0]-1,y:y+density.shape[1]-1,z:z+density.shape[2]-1]
                    for x,y,z in CORNERS],axis=-1)
    mask=(cubes.min(axis=-1)<value)&(cubes.max(axis=-1)>=value)
    starts=np.argwhere(mask); vals=cubes[mask]
    triangles=[]
    for tet in TETS:
        vv=vals[:,tet]; xyz=CORNERS[list(tet)]
        for code in range(1,15):
            chosen=np.where(((vv>=value)*[1,2,4,8]).sum(axis=1)==code)[0]
            if not len(chosen):continue
            high=[i for i in range(4) if code&(1<<i)]; low=[i for i in range(4) if not code&(1<<i)]
            def cross(i,j):
                f=(value-vv[chosen,i])/(vv[chosen,j]-vv[chosen,i])
                return starts[chosen]+xyz[i]+f[:,None]*(xyz[j]-xyz[i])
            def face(a,b,c):
                triangles.append(np.stack([a,b,c],axis=1))
            if len(high)==2:
                a,b=high;u,v=low
                p,q,r,s=cross(a,u),cross(a,v),cross(b,u),cross(b,v)
                face(p,q,r);face(q,s,r)
            else:
                inside,outside=(high,low) if len(high)==1 else (low,high)
                face(*(cross(inside[0],j) for j in outside))
    triangles=np.concatenate(triangles)
    # Smoothed occupancy gradient sets a consistent outward normal on all facets.
    grad=np.stack(np.gradient(density),axis=-1)
    centers=triangles.mean(axis=1);idx=np.floor(centers).astype(int);fract=centers-idx
    normals=np.zeros_like(centers)
    for bits in CORNERS:
        w=np.where(bits,fract,1-fract).prod(axis=1)
        normals-=grad[tuple((idx+bits).T)]*w[:,None]
    normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1.e-7)
    return (triangles+origin+.5)*float(g["cell"]),normals


def crop_for(coverage,shell,aspect):
    yy,xx=np.where((coverage>.05)|(shell>0))
    cy=(yy.min()+yy.max())/2;cx=(xx.min()+xx.max())/2
    h=max((yy.max()-yy.min()+1)*1.14,(xx.max()-xx.min()+1)*1.14/aspect)
    w=h*aspect; left=int(np.floor(np.clip(cx-w/2,0,coverage.shape[1]-w)))
    top=int(np.floor(np.clip(cy-h/2,0,coverage.shape[0]-h)))
    return (left,top,min(int(round(left+w)),coverage.shape[1]),min(int(round(top+h)),coverage.shape[0]))


def draw_scene(c,tri,norm,maps):
    size=(780,398)
    crop=crop_for(maps["coverage"],maps["shell"],size[0]/size[1])
    l,t,r,b=crop
    for key in ("light","full","shell"):
        np.testing.assert_allclose(maps[key][t:b,l:r].sum(),maps[key].sum(),rtol=2e-13,atol=1.e-12)
    cols,rows=round(c["width"]/4),round(c["height"]/4)
    rot=np.asarray(c["rotation"])
    camera_tri=(tri-c["position"])@rot
    depth=camera_tri[:,:,2]
    focal=[c["fx"]*cols/c["width"],c["fy"]*rows/c["height"]]
    uv=camera_tri[:,:,:2]/depth[:,:,None]*focal+[(cols-1)/2,(rows-1)/2]
    # Pixel-center-preserving transform from the original registered raster into the crop.
    uv=(uv-[l-.5,t-.5])*[size[0]/(r-l),size[1]/(b-t)]
    normal=norm@rot
    light=np.array([-.38,-.53,-.76]);light/=np.linalg.norm(light)
    lambert=np.maximum(0,normal@light)
    view=np.maximum(0,-normal[:,2])
    factor=.36+.50*lambert+.14*view
    colors=np.clip(WARM*factor[:,None],0,255).astype(np.uint8)
    bg=Image.new("RGB",size,tuple(BACKGROUND));painter=ImageDraw.Draw(bg)
    valid=((depth>0).all(axis=1)&(uv[:,:,0].max(axis=1)>=0)&(uv[:,:,1].max(axis=1)>=0)&
           (uv[:,:,0].min(axis=1)<size[0])&(uv[:,:,1].min(axis=1)<size[1]))
    order=np.flatnonzero(valid);order=order[np.argsort(-depth[order].mean(axis=1))]
    poly=np.rint(uv).astype(int).reshape(-1,6).tolist();rgb=colors.tolist()
    for i in order:painter.polygon(poly[i],fill=tuple(rgb[i]))
    base=np.asarray(bg,dtype=float)
    def zoom(array):
        img=Image.fromarray(array.astype("float32"))
        return np.asarray(img.crop(crop).resize(size,Image.Resampling.BILINEAR),dtype=float)[:,:,None]
    shell=zoom(maps["shell"])
    result={}
    for arm,key in (("AL","light"),("AF","full")):
        lit=zoom(maps[key])
        # T107 contributions already account for every intervening splat, including
        # foreground outside the shell. Do not renormalize by the surviving matte.
        rgb=base*(1-shell)+ELIGIBLE*(shell-lit)+IGNITED*lit
        result[arm]=Image.fromarray(np.uint8(np.rint(np.clip(rgb,0,255))))
    return result,crop


def document(source):
    local=HERE/"local";local.mkdir(exist_ok=True)
    summary=json.loads((HERE/"validation.json").read_bytes())
    cameras={c["id"]:c for c in json.loads((source/"cameras.json").read_bytes())}
    tri,norm=reconstruct()
    fontdir=Path(reportlab.__file__).parent/"fonts"
    for name,file in (("Vera","Vera.ttf"),("VeraBold","VeraBd.ttf")):
        pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    width,height=500,303
    c=Canvas(str(HERE/"woodpile-mattes.pdf"),pagesize=(width,height),invariant=1,pageCompression=1)
    c.setTitle("Camera-weighted ignition of the same woodpile");c.setAuthor("")
    def text(x,y,value,size=8,bold=False,color="#222b33"):
        c.setFont("VeraBold" if bold else "Vera",size);c.setFillColor(HexColor(color));c.drawString(x,y,value)
    def swatch(x,cvalue,label):
        c.setFillColorRGB(*(cvalue/255));c.roundRect(x,289,7,7,1.5,fill=1,stroke=0)
        text(x+10,289,label,7.7)
    swatch(46,WARM*.78,"Material surface");swatch(165,ELIGIBLE,"Eligible shell");swatch(276,IGNITED,"Newly ignited shell at +90 steps")
    text(48,269,"Light brush",9.5,True);text(116,269,"radius 0.06",8.2)
    text(277,269,"Full brush",9.5,True);text(339,269,"radius 0.12",8.2)
    meta={}
    for cam,bottom in ((0,133),(124,2)):
        maps=np.load(local/f"projection-{cam}.npz")
        ims,crop=draw_scene(cameras[cam],tri,norm,maps);meta[str(cam)]=list(crop)
        c.saveState();c.translate(13,bottom+12);c.rotate(90)
        text(0,0,f"Camera {cam}",9,True);c.restoreState()
        for arm,x in (("AL",28),("AF",266)):
            buf=BytesIO();ims[arm].save(buf,format="PNG");buf.seek(0)
            c.drawImage(ImageReader(buf),x,bottom+17,width=221,height=221*398/780)
            # Caption sits on the lower margin of each diagram.
            pct=summary["views"][str(cam)]["mass"][arm]["percent"]
            text(x+3,bottom+4,f"{pct:.2f}%" if cam==0 else f"{pct:.3f}%",9,True,color="#a1371f")
            text(x+50,bottom+4,"of eligible opacity mass",7.3)
    c.showPage();c.save()
    (local/"geometry.json").write_text(json.dumps({"triangles":len(tri),"original_qtr_raster_crops_ltrb":meta},indent=2))
    return meta


if __name__=="__main__":
    ap=ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,default=TASK.parents[4]/"real-asset-ingest")
    document(ap.parse_args().source)
