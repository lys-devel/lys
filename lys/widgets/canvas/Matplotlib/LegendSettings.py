from ..interface import CanvasLegend


class _MatplotlibLegend(CanvasLegend):
    """Implementation of CanvasLegend for matplotlib"""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._family = None
        self._pos = None
        self._vis = True
        self.canvas().dataChanged.connect(self.updateLegends)

    def updateLegends(self):
        lines = [line for line in self.canvas().getLines() if line.getLegendVisible() and line.getVisible()]
        objs = [line._obj for line in lines]
        labels = [line.getLegendLabel() for line in lines]
        kwargs = {}
        if self._pos is not None:
            kwargs["loc"] = "upper left"
            kwargs["bbox_to_anchor"] = (self._pos[0], 1 - self._pos[1])
        if self._family is not None:
            kwargs["prop"] = {"family": self._family, "size": self._size}
            kwargs["labelcolor"] = self._color
        if self._vis is not None:
            kwargs["frameon"] = self._vis
        leg = self.canvas().getAxes("BottomLeft").legend(objs, labels, **kwargs)
        if len(lines) == 0:
            leg.set_visible(False)

    def _setLegendFont(self, font):
        self._family = font.fontName
        self._size = font.size
        self._color = font.color
        self.updateLegends()

    def _setLegendPosition(self, position):
        self._pos = position
        self.updateLegends()

    def _setLegendFrameVisible(self, visible):
        self._vis = visible
        self.updateLegends()
