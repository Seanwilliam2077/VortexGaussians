"""Build the Mandarin research film from the frozen camera observations and native event ledgers."""
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[2] / "tasks"
FIG = TASKS / "t109-common-parent-choice/figure"
T127 = TASKS / "t127-woodpile-native-camera"
T129 = TASKS / "t129-native-image-choice"
W, H, FPS = 1280, 720, 12
PAPER, INK, TEAL, RUST = "#f8f8f5", "#152e30", "#177678", "#ab4228"
PALE, GRAY, LINE = "#e6eae5", "#506665", "#bdcdc7"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    item = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(item)
    return item


def read(path):
    return json.loads(path.read_bytes())


@lru_cache(None)
def font(size, bold=False):
    return ImageFont.truetype(str(FONTDIR / ("msyhbd.ttc" if bold else "msyh.ttc")), size)


def label(d, x, y, message, size, color=INK, bold=False):
    d.text((x, y), message, fill=color, font=font(size, bold), anchor="lt")


def bar(d, x, y, width, value, color, height=9):
    d.rounded_rectangle((x,y,x+width,y+height), radius=height//2, fill=PALE)
    if value:
        d.rounded_rectangle((x,y,x+max(height,round(width*value)),y+height), radius=height//2, fill=color)


def picture(canvas, im, box):
    x,y,w,h = box
    factor = min(w/im.width, h/im.height)
    scaled = im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
    canvas.paste(scaled,(x+(w-scaled.width)//2,y+(h-scaled.height)//2))


def load_visuals(source, private):
    clip = module("native_events_clip",FIG/"clip/make_clip.py")
    scorer = module("native_contrast",T127/"score.py")
    records = {}
    material = clip.panels(source,records)
    cams = {c["id"]:c for c in read(source/"cameras.json")}
    tri,norm = clip.diagram.reconstruct()
    observations = read(T127/"evidence/SCORE.json")
    gas, values = {}, {}
    for row in observations["comparisons"]:
        c,step,brush = row["camera"],row["horizon"],row["brush"]
        with np.load(FIG/f"local/projection-{c}.npz") as maps:
            shell = maps["shell"]
            images = [private/f"{brush}-c{c}-h{step}-{tail}.png" for tail in ("full","wood")]
            for f in images:
                assert hashlib.sha256(f.read_bytes()).hexdigest() == row["sha256"][f.name]
            changed = np.abs(scorer.block_sums(images[0])-scorer.block_sums(images[1])).max(axis=2) >= 64
            weight = shell * changed
            assert math.isclose(float(weight.sum()/shell.sum()), row["fraction"],abs_tol=2e-13)
            result,_ = clip.diagram.draw_scene(cams[c],tri,norm,dict(coverage=maps["coverage"],shell=shell,light=weight,full=weight))
            gas[c,step,brush] = result["AL"]
            values[c,step,brush] = 100*row["fraction"]
    return material,records,gas,values


def header(d, n, title):
    label(d,62,33,"VORTEX GAUSSIANS    /    TECHNICAL PAPERS",17,TEAL,True)
    label(d,1012,33,"2026.11.25     %02d / 06" % n,16,GRAY)
    d.line((62,69,1218,69),fill=LINE,width=2)
    label(d,58,94,title,49,INK,True)


def compare_images(canvas,d,ims,vals,unit):
    for i,(im,pct,name) in enumerate(zip(ims,vals,("轻笔","重笔"))):
        x=62+596*i
        label(d,x,183,name,25,TEAL if not i else RUST,True)
        picture(canvas,im,(x,225,535,236))
        label(d,x+4,480,f"{pct:.2f}%",45,INK,True)
        bar(d,x+6,548,430,min(pct/80,1),RUST)
        mark=x+6+round(430*25/80)
        d.line((mark,540,mark,565),fill=INK,width=3)
    label(d,62,577,unit,19,GRAY)


def captions(text, sec, duration):
    parts = [s for s in re.findall(r"[^。！？；]+[。！？；]?",text) if s]
    cues = []
    for chunk in parts:
        if len(chunk)>34:
            phrases=re.findall(r"[^，、]+[，、]?",chunk)
            line=""
            for phrase in phrases:
                if line and len(line+phrase)>34:
                    cues.append(line)
                    line=""
                line+=phrase
            if line: cues.append(line)
        else:
            cues.append(chunk)
    point = max(0,min(.999,max(0,sec-.14)/duration)) * sum(map(len,cues))
    for cue in cues:
        point-=len(cue)
        if point<=0:return cue
    return cues[-1]


def draw_scene(scene, sec, duration, total_ratio, data, text):
    material,records,gas,values,joint_times = data
    page=Image.new("RGB",(W,H),PAPER)
    d=ImageDraw.Draw(page)
    x=min(1,sec/duration)
    titles=["一笔火，怎样才算烧够？","重笔可以从轻笔的第 24 步接着算","如果要求木头烧到这里","如果要求画面上看得见气体","把真正的画面判断也计入时间","离投稿还有多远？"]
    header(d,scene,titles[scene-1])
    if scene==1:
        picture(page,material[90,0,"AF"],(535,166,675,350))
        label(d,64,214,"木堆镜头",23,TEAL,True)
        label(d,62,275,"同一起点，两种笔画",35,INK,True)
        label(d,62,337,"两台相机，90 步截止",34,INK)
        label(d,62,446,"目标区域覆盖至少四分之一",25,GRAY)
        d.line((64,416,430,416),fill=LINE,width=2)
        label(d,65,573,"画面为实测材质投影的中性重建。蓝绿是目标材质，橙色是已点燃部分。",19,GRAY)
    elif scene==2:
        label(d,65,181,"同一编辑前状态",24,GRAY)
        a,b,end=123,463,1128
        for y in (316,416):
            d.line((a,366,b,y,end,y), fill=LINE,width=5)
        d.line((a,366,b,316), fill=TEAL,width=6)
        d.line((b,316,end,316), fill=TEAL,width=6)
        if x>.2:
            d.line((b,316,b,416),fill=RUST,width=6)
            d.line((b,416,b+(end-b)*min(1,(x-.2)*2.3),416),fill=RUST,width=6)
        for cx,cy,col in ((a,366,INK),(b,316,TEAL),(b,416,RUST),(end,316,TEAL),(end,416,RUST)):
            d.ellipse((cx-8,cy-8,cx+8,cy+8),fill=col)
        label(d,465,242,"保留轻笔的完整状态",23,TEAL,True)
        label(d,503,362,"补入两笔的材质差异",23,RUST,True)
        label(d,92,452,"点火",19,GRAY);label(d,420,452,"第 24 步",19,GRAY);label(d,1070,452,"第 90 步",19,GRAY)
        d.line((64,506,1213,506),fill=LINE,width=2)
        label(d,65,539,"木堆材质选笔省时 9.6%–14.0%",26,INK,True)
        label(d,613,539,"另一编辑：区域 403–414 ms  /  完整 568–577 ms",22,TEAL)
    elif scene==3:
        step=round(min(1,x/.66)*90)
        ims=[material[step,0,arm] for arm in ("AL","AF")]
        vals=[100*records[step,0,a]["integer"]/records[step,0,a]["total"] for a in ("AL","AF")]
        compare_images(page,d,ims,vals,f"主机位 0   ·   第 +{step:02d} 步   ·   橙色表示已点燃的目标材质。竖线为 25% 门槛。")
    elif scene==4:
        camera=0 if x<.78 else 124
        ims=[gas[camera,90,b] for b in ("light","full")]
        vals=[values[camera,90,b] for b in ("light","full")]
        compare_images(page,d,ims,vals,f"机位 {camera}   ·   第 +90 步   ·   橙色表示原生合成中因气体而改变的目标投影。")
        if camera==124:
            for i,v in enumerate(vals):
                d.rectangle((60+i*596,475,340+i*596,533),fill=PAPER)
                label(d,66+i*596,480,f"{v:.5f}%",41,INK,True)
    elif scene==5:
        label(d,65,180,"双机位共同选笔",26,TEAL,True)
        label(d,348,184,"含分支模拟、渲染、像素读回与返回结果",22,GRAY)
        for i,(old,new) in enumerate(joint_times):
            y=254+i*137
            label(d,66,y+18,"进程 "+str(i+1),24,GRAY,True)
            for j,(val,col,kind) in enumerate(((old,"#657978","完整回放"),(new,TEAL,"状态复用"))):
                yy=y+j*46
                label(d,202,yy,kind,20,GRAY)
                bar(d,326,yy+5,540,val/1000,col,15)
                label(d,880,yy-5,f"{val:.0f} ms",25,INK,True)
            label(d,1030,y+12,f"−{(1-new/old)*100:.2f}%",27,RUST,True)
        d.line((64,508,1212,508),fill=LINE,width=2)
        label(d,65,534,"主机位单独选轻笔，提速未稳定出现。",24,INK,True)
        label(d,65,576,"双机位共同的首次投影准备 2.03 秒。每个进程 6 次配对测量，合计 12 次。",19,GRAY)
    else:
        label(d,65,187,"独立的布料与气体求解器",25,TEAL,True)
        label(d,65,245,"336 / 5,832",56,INK,True)
        label(d,68,324,"6 秒时正在燃烧的窗帘顶点",24,GRAY)
        label(d,68,389,"最终图像超时，缺少双笔画面对照。",21,GRAY)
        d.line((616,184,616,484), fill=LINE,width=2)
        label(d,667,187,"两位独立模拟评审",25,TEAL,True)
        label(d,667,252,"SIGGRAPH 会议",24,GRAY)
        label(d,964,238,"4/6    3/6",37,INK,True)
        label(d,667,333,"TOG 期刊",24,GRAY)
        label(d,964,319,"3/6    2/6",37,INK,True)
        label(d,667,410,"已看完最终双机位实验的内部评分",18,GRAY)
        d.line((64,499,1212,499),fill=LINE,width=2)
        label(d,65,527,"研究已暂停  /  论文尚未投稿",30,RUST,True)
        label(d,65,577,"木堆数据  FieryGS / Qianfan Shen 等     ·     独立求解器  Blackbody / gjnail",18,GRAY)
    d.rectangle((0,622,W,H),fill=INK)
    cue=captions(text,sec,duration)
    size=26
    while d.textlength(cue,font=font(size))>1160:size-=1
    d.text((W//2,667),cue,font=font(size),fill="#ffffff",anchor="mm")
    d.rectangle((0,H-5,round(total_ratio*W),H),fill="#f29b63")
    return page


def build(args):
    manifest=read(HERE/"narration.json")
    scenes=manifest["scenes"]
    info=read(T129/"evidence/SCORE.json")
    assert len(info["processes"])==2
    joint_times=[]
    for process in info["processes"]:
        joint=next(q for q in process["queries"] if q["cameras"]==[0,124])
        joint_times.append((joint["median_ms"]["ordinary"],joint["median_ms"]["sibling"]))
    data=(*load_visuals(args.source,args.frames),joint_times)
    counts=[]
    chunks=[]
    for item in scenes:
        with wave.open(str(args.audio/item["wav"]),"rb") as f:
            assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,22050)
            audio=f.readframes(f.getnframes())
        duration=len(audio)/(22050*2)
        assert abs(duration-item["duration_seconds"])<.002
        n=math.ceil((duration+.62)*FPS)
        counts.append(n)
        chunks.append(audio)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        soundtrack=tmp/"speech.wav"
        with wave.open(str(soundtrack),"wb") as f:
            f.setparams((1,2,22050,0,"NONE","not compressed"))
            written=0
            for i,pcm in enumerate(chunks):
                target=round(sum(counts[:i+1])*22050/FPS)
                lead=round(.14*22050)
                f.writeframes(b"\0\0"*lead+pcm+b"\0\0"*(target-written-lead-len(pcm)//2))
                written=target
        cmd=["ffmpeg","-y","-v","error","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{W}x{H}",
             "-framerate",str(FPS),"-i","pipe:0","-i",str(soundtrack),"-c:v","libx264","-preset","veryfast","-crf","18",
             "-pix_fmt","yuv420p","-r","24","-threads","3","-c:a","aac","-b:a","112k","-movflags","+faststart",
             "-metadata","title=Vortex Gaussians · 一笔火，怎样才算烧够？","-metadata:s:a:0","language=zho",str(args.output)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        total=sum(counts);off=0
        with proc.stdin:
            for item,n in zip(scenes,counts):
                for j in range(n):
                    im=draw_scene(item["id"],j/FPS,item["duration_seconds"],(off+j+1)/total,data,item["spoken"])
                    proc.stdin.write(im.tobytes())
                off+=n
        if proc.wait():raise RuntimeError("ffmpeg encoding failed")
    print(json.dumps({"duration":sum(counts)/FPS,"scene_start_seconds":[sum(counts[:i])/FPS for i in range(6)],
                      "video_bytes":args.output.stat().st_size,"sha256":hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("source","frames","audio"):
        parser.add_argument("--"+name,type=Path,required=True)
    parser.add_argument("--fontdir",type=Path,default=Path("C:/Windows/Fonts"))
    parser.add_argument("--output",type=Path,default=HERE/"tech-progress-zh.mp4")
    args=parser.parse_args()
    FONTDIR=args.fontdir
    build(args)
