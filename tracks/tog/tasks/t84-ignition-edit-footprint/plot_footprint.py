"""Plot the paired T84 material counts from CLOCK.json using ReportLab."""
import json
from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors

HERE = Path(__file__).resolve().parent
INK = colors.HexColor('#20303c')
GRID = colors.HexColor('#d4dce0')


def label(x, y, words, size=10, anchor='start', bold=False):
    return String(x, y, words, fontName='Helvetica-Bold' if bold else 'Helvetica',
                  fontSize=size, fillColor=INK, textAnchor=anchor)


def panel(drawing, timeline, column, y, ymax, step, color, title):
    x0, width, height = 55, 428, 80
    chart = LinePlot()
    chart.x, chart.y = x0, y
    chart.width, chart.height = width, height
    line = [(timeline[0][0], timeline[0][column])]
    for row in timeline[1:]:
        line.extend([(row[0], line[-1][1]), (row[0], row[column])])
    chart.data = [line]
    chart.lines[0].strokeColor = colors.HexColor(color)
    chart.lines[0].strokeWidth = 1.7
    chart.xValueAxis.valueMin, chart.xValueAxis.valueMax = 180, 360
    chart.xValueAxis.valueSteps = list(range(180, 361, 30))
    chart.yValueAxis.valueMin, chart.yValueAxis.valueMax = 0, ymax
    chart.yValueAxis.valueSteps = list(range(0, ymax + 1, step))
    chart.yValueAxis.visibleGrid = True
    chart.yValueAxis.gridStrokeColor = GRID
    chart.yValueAxis.gridStrokeWidth = 0.45
    for axis in (chart.xValueAxis, chart.yValueAxis):
        axis.labels.fontName = 'Helvetica'
        axis.labels.fontSize = 9
        axis.labels.fillColor = INK
        axis.strokeColor = INK
        axis.strokeWidth = .6
    drawing.add(chart)
    drawing.add(label(x0, y + height + 11, title, 11, bold=True))
    drawing.add(label(x0 + width + 8, y + height * timeline[-1][column] / ymax - 3,
                      f'{timeline[-1][column]:,}', 10, bold=True))


def figure():
    result = json.loads((HERE / 'CLOCK.json').read_bytes())
    timeline = result['onsets']['global']['timeline']
    drawing = Drawing(539, 300)
    drawing.add(Rect(0, 0, 539, 300, fillColor=colors.white, strokeColor=None))
    drawing.add(label(55, 279, 'Material response outside the second ignition stroke', 14, bold=True))
    panel(drawing, timeline, 3, 165, 1500, 500, '#006886', 'Burning only in the edited take (sites)')
    panel(drawing, timeline, 4, 38, 40, 10, '#a04423', 'Burning only in the original take (sites)')
    drawing.add(label(269, 7, 'Simulation frame  (stroke applied at 180)', 10, 'middle'))
    return drawing


if __name__ == '__main__':
    renderSVG.drawToFile(figure(), str(HERE / 'footprint.svg'))
