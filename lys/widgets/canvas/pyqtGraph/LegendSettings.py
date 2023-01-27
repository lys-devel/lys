import pyqtgraph as pg
from ..interface import CanvasLegend


class _PyqtgraphLegend(CanvasLegend):
    """Implementation of CanvasLegend for pyqtgraph"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._legend = canvas.getPlotItem().addLegend()
        self._legend.setVisible(False)
        self.canvas().canvasResized.connect(self.__updatePosition)
        self.canvas().mouseReleased.connect(self.__mouseReleased)

    def getLegend(self):
        return self._legend

    def updateLegends(self):
        if len(self._legend.items) == 0:
            self._legend.setVisible(False)
        else:
            self._legend.setVisible(True)

    def _setLegendFont(self, font):
        for line in self.canvas().getLines():
            line.setLegendText(font={"family": font.fontName, "size": font.size, "color": font.color})

    def _setLegendPosition(self, position):
        h = self.canvas().fig.getAxis('left').height()
        w = self.canvas().fig.getAxis('bottom').width()
        self._legend.anchor(itemPos=(0, 0), parentPos=(0, 0), offset=((position[0] + 0.02) * w, (position[1] + 0.02) * h))

    def __updatePosition(self):
        self.setLegendPosition(self.getLegendPosition())

    def __mouseReleased(self):
        h = self.canvas().fig.getAxis('left').height()
        w = self.canvas().fig.getAxis('bottom').width()
        offset = self._legend.pos()
        offset = offset[0] / w - 0.02, offset[1] / h - 0.02
        self.setLegendPosition(offset)

    def _setLegendFrameVisible(self, visible):
        if visible:
            self._legend.setPen(pg.mkPen())
        else:
            self._legend.setPen(pg.mkPen(None))
