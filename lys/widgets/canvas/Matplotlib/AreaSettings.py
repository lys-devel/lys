from ..interface import CanvasMargin, CanvasSize


class _MatplotlibMargin(CanvasMargin):
    """Implementation of CanvasMargin for matplotlib"""

    def _setMargin(self, left, right, top, bottom):
        self.canvas().getFigure().subplots_adjust(left=left, right=right, top=top, bottom=bottom)


_unit = 1 / 2.54  # inch->cm


class _MatplotlibCanvasSize(CanvasSize):
    """Implementation of CanvasSize for matplotlib"""

    def _setAuto(self, axis):
        self._adjust()

    def _setAbsolute(self, type, value):
        rat = self._getMarginRatio()
        if type == "Width":
            self.canvas().getFigure().set_figwidth(value * _unit * rat[0])
        else:
            self.canvas().getFigure().set_figheight(value * _unit * rat[1])
        self._adjust()

    def _setAspect(self, type, aspect):
        rat = self._getMarginRatio()
        if type == "Width":
            self.canvas().getFigure().set_figwidth(self.canvas().getFigure().get_figheight() * (rat[0] / rat[1]) * aspect)
        else:
            self.canvas().getFigure().set_figheight(self.canvas().getFigure().get_figwidth() / (rat[0] / rat[1]) * aspect)
        self._adjust()

    def _getSize(self):
        rat = self._getMarginRatio()
        return (self.canvas().getFigure().get_figwidth() / rat[0] / _unit, self.canvas().getFigure().get_figheight() / rat[1] / _unit)

    def _getMarginRatio(self):
        m = self.canvas().getMargin()
        wr = 1 / (m[1] - m[0])
        hr = 1 / (m[3] - m[2])
        return (wr, hr)

    def _adjust(self):
        m = self.canvas().getMargin()
        for ax in self.canvas().axisList():
            self.canvas().getAxes(ax).set_position([m[0], m[2], m[1] - m[0], m[3] - m[2]])
        self.canvas().resize(int(self.canvas().getFigure().get_figwidth() * 100), int(self.canvas().getFigure().get_figheight() * 100))
