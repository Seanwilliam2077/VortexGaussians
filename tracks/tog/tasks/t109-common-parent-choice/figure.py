"""Draw measured native trajectories with a common overview scale and a labeled inset."""
from pathlib import Path
import json
import reportlab
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE=Path(__file__).resolve().parent
FONT=Path(reportlab.__file__).parent/"fonts"
for name, filename in (("Vera","Vera.ttf"),("VeraBold","VeraBd.ttf")):
    pdfmetrics.registerFont(TTFont(name,str(FONT/filename)))
rows={(q["arm"],q["camera"]):q for q in json.loads((HERE/"REFERENCE.json").read_bytes())["queries"]}
W,H=500,184
c=Canvas(str(HERE/"brush-choice.pdf"),pagesize=(W,H),pageCompression=1,invariant=1)
c.setAuthor("");c.setTitle("Two second-stroke alternatives from a shared parent")
ink="#202936";muted="#56616d";grid="#d9dfe3";colors={"AL":"#167a81","AF":"#a43c24"}


def label(x,y,value,size=8,align="left",bold=False,color=ink):
    c.setFillColor(HexColor(color));c.setFont("VeraBold" if bold else "Vera",size)
    {"left":c.drawString,"right":c.drawRightString,"center":c.drawCentredString}[align](x,y,value)


def line(x1,y1,x2,y2,color,width=.6,dash=()):
    c.setLineWidth(width);c.setDash(dash);c.setStrokeColor(HexColor(color));c.line(x1,y1,x2,y2)


def curve(q,x,y,width,height,limit,small=False):
    color=colors[q["arm"]]
    c.setDash([3.0,1.7] if q["arm"]=="AL" else []);c.setStrokeColor(HexColor(color))
    c.setLineWidth(1.15 if small else 1.5)
    pen=c.beginPath();pen.moveTo(x,y);previous=0
    for frame,_,_,mass in q["curve"]:
        xx=x+width*(frame-180)/90
        vv=100*mass/q["total"]
        pen.lineTo(xx,y+height*previous/limit)
        if vv!=previous:pen.lineTo(xx,y+height*vv/limit)
        previous=vv
    c.drawPath(pen,stroke=1);c.setDash([])


def panel(x,cam,title):
    y,w,h=38,190,100
    label(x,151,title,10.2,bold=True)
    for v in (0,10,20,30,40):
        yy=y+h*v/40
        line(x,yy,x+w,yy,grid,.5)
        label(x-5,yy-2.7,str(v),7.1,"right",color=muted)
    for v in (0,30,60,90):
        xx=x+w*v/90;line(xx,y,xx,y-3,muted,.6)
        label(xx,y-12,str(v),7.4,"center",color=muted)
    line(x,y,x,y+h,muted,.6)
    line(x,y+h*25/40,x+w,y+h*25/40,"#626d74",.9,(3,2))
    line(x+w,y,x+w,y+h,"#989fa6",.65,(1,2))
    for a in ("AF","AL"):curve(rows[a,cam],x,y,w,h,40)
    return x,y,w,h


line(82,171,101,171,colors["AL"],1.6,(3,1.7))
label(105,168.5,"Light brush (0.06)",8.4)
line(200,171,219,171,colors["AF"],1.6);label(223,168.5,"Full brush (0.12)",8.4)
line(318,171,337,171,"#626d74",.9,(3,2));label(341,168.5,"25% target",8.4)

x,y,w,h=panel(42,0,"Camera 0  ·  decision view")
full=rows["AF",0];frame=full["first_frame"]-180
px=x+w*frame/90;py=y+h*(100*full["mass"]/full["total"])/40
c.setFillColor(HexColor(colors["AF"]));c.circle(px,py,2.25,stroke=0,fill=1)
line(px-1,py+3,px-8,py+12,colors["AF"],.7)
label(px-8,py+15,"First hit at +"+str(frame),7.4,"right",color=colors["AF"])

x,y,w,h=panel(288,124,"Camera 124  ·  second view")
# The overview keeps the same y scale. Only this explicitly marked panel is enlarged.
ix,iy,iw,ih=x+20,y+16,96,29
c.setFillColor(white);c.rect(ix-7,iy-3,172,ih+15,fill=1,stroke=0)
label(ix,iy+ih+3,"0–90 steps, enlarged to 0.08%",7.1,bold=True,color=muted)
line(ix,iy,ix+iw,iy,grid);line(ix,iy,ix,iy+ih,grid);line(ix,iy+ih,ix+iw,iy+ih,grid,.45)
for arm in ("AF","AL"):
    q=rows[arm,124];curve(q,ix,iy,iw,ih,.08,True)
    pct=100*q["deadline_mass"]/q["total"]
    label(ix+iw+4,iy+ih*pct/.08-2.2,f"{pct:.3f}%",7, color=colors[arm])
label(260,6,"Steps after the second brush (deadline at 90)",8.2,"center")
c.saveState();c.translate(10,88);c.rotate(90);label(0,0,"Ignited opacity mass (%)",8.3,"center");c.restoreState()
c.showPage();c.save()
