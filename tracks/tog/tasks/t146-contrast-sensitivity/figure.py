"""Draw an anonymous vector figure from the recorded native contrast histograms."""
import argparse
import math
from pathlib import Path
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from measure import measure

TEAL = colors.HexColor("#006d72")
ORANGE = colors.HexColor("#b04613")
INK = colors.HexColor("#24282b")
GRID = colors.HexColor("#d5d8da")


def draw(path):
    score, curves = measure()
    c = canvas.Canvas(str(path), pagesize=(520, 172), invariant=1)
    c.setTitle("Sensitivity of edited-fire choices to the displayed RGB cutoff")
    def line(x, y, x2, y2, color=GRID, width=0.55):
        c.setStrokeColor(color)
        c.setLineWidth(width)
        c.line(x, y, x2, y2)

    def label(x, y, value, size=8, bold=False, anchor="left"):
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[anchor](x, y, value)

    def marker(x, y, full):
        c.setFillColor(ORANGE if full else TEAL)
        if full:
            c.rect(x-2.5, y-2.5, 5, 5, fill=1, stroke=0)
        else:
            c.circle(x, y, 2.6, fill=1, stroke=0)

    label(7, 155, "A   Woodpile, primary camera", 10, True)
    label(297, 155, "B   Maximum coverage at any positive cutoff", 10, True)
    label(7, 139, "Share of target opacity (%)")
    x = lambda v: 31 + 224*v/255
    y = lambda v: 32 + 105*v/85
    for tick in [0, 25, 50, 75]:
        line(x(0), y(tick), x(255), y(tick))
        label(x(0)-4, y(tick)-2, str(tick), anchor="right")
    for tick in [0, 75, 150, 225]:
        line(x(tick), 29, x(tick), 32, INK)
        label(x(tick), 20, str(tick), anchor="center")
    c.setDash(2, 2)
    line(x(16), y(0), x(16), y(83), INK)
    line(x(0), y(25), x(255), y(25), INK)
    c.setDash()
    label(x(16)+3, y(78), "16", size=7)
    label(143, 5, "Display contrast cutoff (RGB levels)", anchor="center")
    for full, curve in enumerate(curves["woodpile_0"]):
        c.setStrokeColor(ORANGE if full else TEAL)
        c.setDash([3, 1.5] if full else [])
        c.setLineWidth(1.4)
        linepath = c.beginPath()
        linepath.moveTo(x(0.25), y(100 * curve[0]))
        for i, fr in enumerate(curve[1:], 2):
            linepath.lineTo(x(i / 4), y(100 * fr))
        c.drawPath(linepath)
    c.setDash()
    label(297, 139, "Share of target opacity (%), logarithmic scale")
    xlog = lambda pct: 344 + 156 * (math.log10(pct) + 4) / 6
    for tick in [0.0001, 0.01, 1, 100]:
        line(xlog(tick), 36, xlog(tick), 115)
        label(xlog(tick), 22, f"{tick:g}", anchor="center")
    c.setDash(2, 2)
    line(xlog(25), 36, xlog(25), 120, INK)
    c.setDash()
    label(xlog(25), 124, "25%", anchor="center")
    for (name, record), yy, title in zip(score["views"].items(), [102, 76, 50],
            ["Wood 0", "Wood 124", "Bonsai 0"], strict=True):
        label(297, yy-3, title)
        for full, fraction in enumerate(record["fraction_at_smallest"]):
            marker(xlog(100*fraction), yy-2.5 if full else yy+2.5, full)
    marker(373, 7, False)
    label(380, 4, "Light")
    marker(425, 7, True)
    label(432, 4, "Full")
    c.showPage()
    c.save()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    draw(p.parse_args().output)
