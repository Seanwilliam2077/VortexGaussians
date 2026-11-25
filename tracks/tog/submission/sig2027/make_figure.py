"""Build the two-panel vector figure from the archived trial scores (ReportLab)."""
import json
from math import isclose
from pathlib import Path
from statistics import median

import reportlab
from reportlab.lib.colors import Color, HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "t86-ignition-margin"
INK = HexColor("#152D37")
MUTED = HexColor("#415660")
GRID = HexColor("#CAD6D9")
TEAL = HexColor("#005B66")
ORANGE = HexColor("#A94518")


def label(c, x, y, value, size=8, color=INK, align="left", bold=False):
    c.setFillColor(color)
    c.setFont("Vera Bold" if bold else "Vera", size)
    draw = {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}
    draw[align](x, y, value)


def symbol(c, x, y, arm):
    if arm == "AB":
        c.setFillColor(TEAL)
        c.setStrokeColor(white)
        c.setLineWidth(0.45)
        c.circle(x, y, 2.8, fill=1, stroke=1)
    else:
        c.setFillColor(ORANGE)
        c.setStrokeColor(white)
        c.setLineWidth(0.45)
        p = c.beginPath()
        p.moveTo(x, y + 3.4)
        p.lineTo(x-3.3, y-2.6)
        p.lineTo(x+3.3, y-2.6)
        p.close()
        c.drawPath(p, fill=1, stroke=1)


def measures():
    score = json.loads((TASK / "SCORE.json").read_bytes())
    rows = {}
    for window in score["windows"]:
        weighted = window["methods"]["weighted"]
        uniform = window["methods"]["uniform"]["strata"]["all"]
        counted = weighted["strata"]["all"]
        eligible = counted["eligible"]
        assert uniform["eligible"] == eligible and counted["false_certificates"] == 0
        assert weighted["fallback_required"] and counted["abstentions"] > 0
        full = weighted["compute_ms"] + window["native_ms"]
        assert isclose(full, weighted["compute_plus_fallback_ms"])
        key = (window["arm"], window["cut"], window["horizon"])
        assert key not in rows
        rows[key] = (counted["certified"]/eligible,
                     100*(counted["certified"]-uniform["certified"])/eligible,
                     full/window["native_ms"])
    assert set(rows) == {(a,f,h) for a in ("AB","BA") for f in (210,240,300) for h in (1,4,8)}
    assert rows["AB",210,8][0] == 0
    assert isclose(median(v[2] for v in rows.values()),
                   score["summary"]["both"]["methods"]["weighted"]["paired_cost_ratio_median"])
    return rows


def coverage_panel(c, rows):
    label(c, 1, 178, "(a)  Weighted coverage", size=11, bold=True)
    label(c, 1, 163.5, "Percent of currently unlit, fuel-positive sites certified", size=7.5, color=MUTED)
    label(c, 146, 143.5, "Horizon (frames)", size=8, align="center", color=MUTED)
    headers = [(18,"Edit"), (54,"Cut"), (98,"1"), (146,"4"), (194,"8")]
    for x,txt in headers:
        label(c, x, 129.5, txt, size=8.4, align="center", bold=True)
    for i, arm in enumerate(("AB","BA")):
        for j, cut in enumerate((210,240,300)):
            y = 109 - 55*i - 16*j
            if j == 1:
                label(c, 18, y+1, "A then B" if arm=="AB" else "B then A", size=7.2, bold=True, align="center")
            label(c, 54, y+1, str(cut), size=8.2, align="center")
            for k,h in enumerate((1,4,8)):
                x = 98+48*k
                coverage = rows[arm,cut,h][0]
                low, high = (0.952,0.971,0.973), (0.018,0.359,0.400)
                rgb = [a + (b-a)*coverage for a,b in zip(low,high)]
                c.setFillColor(Color(*rgb))
                c.rect(x-23, y-4, 46, 15.3, fill=1, stroke=0)
                # Print the percentage in every cell. Use sufficient contrast independently of color.
                linear = [ch/12.92 if ch <= .04045 else ((ch+.055)/1.055)**2.4 for ch in rgb]
                luminance = sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))
                color = white if luminance < .175 else HexColor("#10242B")
                label(c, x, y+0.2, f"{coverage*100:.1f}", size=8.6, bold=True, align="center", color=color)


def cost_panel(c, rows):
    label(c, 244, 178, "(b)  Coverage gain and exact cost", size=11, bold=True)
    label(c, 244, 163.5, "Prediction plus full native fallback, with setup excluded", size=7.5, color=MUTED)
    symbol(c, 272, 148, "AB")
    label(c, 279, 145.4, "A then B", size=8)
    symbol(c, 329, 148, "BA")
    label(c, 336, 145.4, "B then A", size=8)

    left, right = 282, 501
    bottom, top = 36, 134
    xmin, xmax = -0.8, 22.6
    ymin, ymax = 0.91, 2.25
    px = lambda v: left + (v-xmin)*(right-left)/(xmax-xmin)
    py = lambda v: bottom + (v-ymin)*(top-bottom)/(ymax-ymin)
    for value in (1.0,1.4,1.8,2.2):
        y = py(value)
        c.setStrokeColor(MUTED if value==1 else GRID)
        c.setLineWidth(0.7 if value==1 else 0.4)
        c.setDash([2,2] if value==1 else [])
        c.line(left,y,right,y)
        label(c, left-5, y-2.5, f"{value:.1f}", size=7.2, align="right", color=MUTED)
    c.setDash([])
    label(c, right-2, py(1)+3.5, "Native only", size=7.2, color=MUTED, align="right")
    for value in (0,5,10,15,20):
        x = px(value)
        c.setStrokeColor(GRID)
        c.setLineWidth(0.45)
        c.line(x,bottom-2,x,bottom)
        label(c, x, bottom-11, str(value), size=7.3, align="center", color=MUTED)
    for (arm,cut,h), (_,gain,ratio) in rows.items():
        assert xmin < gain < xmax and ymin < ratio < ymax
        symbol(c, px(gain), py(ratio), arm)
    c.saveState()
    c.translate(253, (bottom+top)/2)
    c.rotate(90)
    label(c, 0, 0, "Exact cost / native cost", size=8.1, align="center")
    c.restoreState()
    label(c, (left+right)/2, 9, "Coverage gain over uniform bound (percentage points)", size=7.7, align="center")


def main():
    fonts = Path(reportlab.__file__).resolve().parent / "fonts"
    for name,file in (("Vera","Vera.ttf"),("Vera Bold","VeraBd.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(fonts/file)))
    rows = measures()
    c = Canvas(str(HERE / "ignition-coverage.pdf"), pagesize=(504,190), invariant=1, pageCompression=1)
    c.setTitle("Ignition certificates across two edit orders")
    c.setAuthor("")
    coverage_panel(c,rows)
    cost_panel(c,rows)
    c.showPage()
    c.save()


if __name__ == "__main__":
    main()
