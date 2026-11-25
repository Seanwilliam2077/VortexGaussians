"""Draw the two calibrated views and three time curves from the same woodpile edit."""
import gzip
import json
from pathlib import Path

import reportlab
from PIL import Image, ImageChops
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1]/"tasks"/"t107-visible-burn-progression"/"evidence"
fonts = Path(reportlab.__file__).parent/"fonts"
pdfmetrics.registerFont(TTFont("VeraReg", str(fonts/"Vera.ttf")))
pdfmetrics.registerFont(TTFont("VeraBold", str(fonts/"VeraBd.ttf")))


def main():
    doc = Canvas(str(HERE/"burn-progression.pdf"), pagesize=(510,155),invariant=True,initialFontName="VeraReg")
    doc.setTitle("Projected material ignition in two cameras on one edited trajectory")
    def label(x,y,msg,size=8,bold=False,color="#26353c"):
        doc.setFillColor(HexColor(color))
        doc.setFont("VeraBold" if bold else "VeraReg",size)
        doc.drawString(x,y,msg)
    label(5,142,"The same edit at three seconds",10,True)
    label(248,142,"How much of the shell has ignited?",10,True)
    curves=[]
    for j,(cid,col) in enumerate(((0,"#a14525"),(124,"#007581"))):
        x=5+j*119
        r=json.loads(gzip.decompress((DATA/f"camera-{cid}.json.gz").read_bytes()))["orders"]["AB"]
        curves.append(([v/r["mass"] for v in r["cumulative_mass"]],col))
        im=Image.open(DATA/f"camera-{cid}-AB.png").convert("RGB")
        box=ImageChops.difference(im,Image.new("RGB",im.size,"white")).getbbox()
        im=im.crop(box)
        scale=min(108/im.width,78/im.height)
        width,height=scale*im.width,scale*im.height
        doc.drawImage(ImageReader(im),x+(108-width)/2,45+(78-height)/2,width,height)
        label(x+5,126,f"Camera {cid}",8,True,col)
        label(x+5,34,f"{100*r['cumulative_mass'][-1]/r['mass']:.1f}% of opacity mass",7.3)
    curves.append(([v/r["eligible"] for v in r["counts"]],"#47545d"))
    for x,col,txt in ((9,"#db5020","Ignited shell"),(110,"#2687a7","Remaining shell")):
        doc.setFillColor(HexColor(col)); doc.rect(x,16,8,6,stroke=0,fill=1);label(x+12,15,txt,7)
    x0,x1,y0,y1=277,502,36,120
    for v in (0,.25,.5,.75):
        y=y0+(y1-y0)*v/.75;doc.setStrokeColor(HexColor("#d2dcdc"));doc.setLineWidth(.45)
        doc.line(x0,y,x1,y);label(x0-26,y-2,f"{int(100*v)}%",7)
    for i,(series,color) in enumerate(curves):
        line=doc.beginPath();line.moveTo(x0,y0)
        last=0
        for k,y in enumerate(series,1):
            x=x0+(x1-x0)*k/180
            line.lineTo(x,y0+last/.75*(y1-y0));line.lineTo(x,y0+y/.75*(y1-y0))
            last=y
        doc.setStrokeColor(HexColor(color));doc.setLineWidth(1.3)
        doc.setDash([2,2] if i==2 else []);doc.drawPath(line)
    doc.setDash([])
    for n in range(4): label(x0+(x1-x0)*n/3-2,25,str(n),7)
    label(337,12,"Seconds after the second brush",7.2)
    for i,(a,c) in enumerate((("Camera 0","#a14525"),("Camera 124","#007581"),("Site count","#47545d"))):
        label(273+i*77,127,a,7.3,True,c)
    doc.save()


if __name__ == "__main__":
    main()
