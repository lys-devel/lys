from ..interface import CanvasLegend


class _PyqtgraphLegend(CanvasLegend):
    """Implementation of CanvasLegend for pyqtgraph"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._legend = canvas.getPlotItem().addLegend()
        self._legend.setVisible(False)

    def getLegend(self):
        return self._legend

    def updateLegends(self):
        if len(self._legend.items) == 0:
            self._legend.setVisible(False)
        else:
            self._legend.setVisible(True)
