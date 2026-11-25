"""Draw the actual authored edit and native first-event records on the CC0 tree."""
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import reportlab
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE=Path(__file__).resolve().parent
DATA=HERE.parents[1]/"tasks"/"t92-transfer-workload"


def read(path):
    v=path.read_bytes()
    return json.loads(gzip.decompress(v) if path.suffix==".gz" else v)


def material_view(xyz, region, brush, a, b):
    width,height=790,323
    x=xyz[:,0]
    y=.93*xyz[:,1]-.37*xyz[:,2]
    scale=min((width-24)/(x.max()-x.min()),(height-36)/(y.max()-y.min()))
    px=(width/2+(x-(x.min()+x.max())/2)*scale).astype(int)
    py=(height/2-(y-(y.min()+y.max())/2)*scale).astype(int)
    depth=.37*xyz[:,1]+.93*xyz[:,2]
    shades=(90+100*(depth-depth.min())/(depth.max()-depth.min())).astype(int)
    image=Image.new("RGB",(width,height),"white")
    draw=ImageDraw.Draw(image)
    region=set(region); brush=set(brush)
    for i in np.argsort(depth):
        c=int(shades[i])
        if i in brush: color=(135,58,29)
        elif i in region: color=(229,150,86)
        else: color=(c-7,c+1,c+5)
        draw.ellipse((px[i]-1,py[i]-1,px[i]+1,py[i]+1),fill=color)
    return image,[(px[i]/width,1-py[i]/height) for i in (a,b)]


def main():
    cfg=read(DATA/"recipe.json")
    raw=(DATA/"local/scene.ply").read_bytes()
    k=raw.index(b"end_header\n")+len(b"end_header\n")
    xyz=np.frombuffer(raw[k:],dtype="<f4").reshape(cfg["material_count"],-1)[:,:3]
    shells=read(DATA/"shell-ids.json.gz")
    a,b=cfg["picks"]
    im,labels=material_view(xyz,shells["B"],b["initial_geometric_neighbors"],a["site"],b["site"])
    fonts=Path(reportlab.__file__).parent/"fonts"
    pdfmetrics.registerFont(TTFont("EditRegular",str(fonts/"Vera.ttf")))
    pdfmetrics.registerFont(TTFont("EditBold",str(fonts/"VeraBd.ttf")))
    c=Canvas(str(HERE/"edit-query.pdf"),pagesize=(504,152),invariant=True,initialFontName="EditRegular")
    c.setTitle("The exterior-brush query on a fallen tree")
    def txt(x,y,string,size=8,bold=False,color="#243640"):
        c.setFillColor(HexColor(color));c.setFont("EditBold" if bold else "EditRegular",size);c.drawString(x,y,string)
    txt(4,139,"(a) Where did the second brush ignite?",10,True)
    txt(4,125,"Tree geometry and the A then B brush placement",7.5)
    w,h=235,96
    c.drawImage(ImageReader(im),3,24,width=w,height=h)
    for name,(u,v) in zip(("A","B"),labels):
        x,y=3+w*u,24+h*v
        c.setFillColor(HexColor("#0d303e"));c.circle(x,y,2.2,fill=1,stroke=0)
        txt(x-4,max(24+h+1 if y>100 else y+9,37),name,8,True)
    for x,col,label in [(5,"#873a1d","Second brush"),(99,"#e59656","Exterior shell")]:
        c.setFillColor(HexColor(col));c.rect(x,9,8,6,fill=1,stroke=0);txt(x+12,8,label,7.5)
    txt(257,139,"(b) When does the fire cross the brush?",10,True)
    txt(257,125,"Cumulative new ignitions in the second brush's shell",7.5)
    traces={}
    for arm in ("AB","BA"):
        shell=set(shells[arm[1]])
        rows=read(DATA/"evidence"/f"{arm}-trace.json.gz")
        trace=[0]
        for f in rows[180:360]: trace.append(trace[-1]+len(shell.intersection(f["new_ids"])))
        traces[arm]=trace
    x0,x1,y0,y1=283,494,34,107
    top=int(np.ceil(max(t[-1] for t in traces.values())/100)*100)
    for value in [0,top//2,top]:
        y=y0+(y1-y0)*value/top;c.setStrokeColor(HexColor("#d2dada"));c.setLineWidth(.45);c.line(x0,y,x1,y)
        txt(x0-24,y-2,str(value),7)
    for sec in range(4): txt(x0+(x1-x0)*sec/3-2,y0-10,str(sec),7)
    txt(355,y0-20,"Seconds after the edit",7.5)
    for n,(arm,col) in enumerate([("AB","#9e4421"),("BA","#00656d")]):
        points=traces[arm]; curve=c.beginPath();curve.moveTo(x0,y0)
        for j in range(1,len(points)):
            x=x0+(x1-x0)*j/180;curve.lineTo(x,y0+(y1-y0)*points[j-1]/top);curve.lineTo(x,y0+(y1-y0)*points[j]/top)
        c.setLineWidth(1.3);c.setStrokeColor(HexColor(col));c.drawPath(curve)
        txt(291+91*n,113,"A then B" if arm=="AB" else "B then A",7.5,True,col)
    c.save()
    print({k:(next(i for i,x in enumerate(v) if x>0),v[-1]) for k,v in traces.items()})

if __name__=="__main__": main()
