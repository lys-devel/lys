from ..interface import CanvasLegend


class _MatplotlibLegend(CanvasLegend):
    """Implementation of CanvasLegend for matplotlib"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas().dataChanged.connect(self.updateLegends)

    def updateLegends(self):
        lines = [line for line in self.canvas().getLines() if line.getLegendVisible() and line.getVisible()]
        objs = [line._obj for line in lines]
        labels = [line.getLegendLabel() for line in lines]
        leg = self.canvas().getAxes("BottomLeft").legend(objs, labels)
        if len(lines) == 0:
            leg.set_visible(False)
