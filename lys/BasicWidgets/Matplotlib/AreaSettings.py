#!/usr/bin/env python
from .AxisLabelSettings import *
from ..CanvasInterface import CanvasMargin, CanvasSize


class _MatplotlibMargin(CanvasMargin):
    """Implementation of CanvasMargin for matplotlib"""

    def _setMargin(self, left, right, top, bottom):
        self.canvas().fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)


_unit = 1 / 2.54  # inch->cm


class _MatplotlibCanvasSize(CanvasSize):
    """Implementation of CanvasSize for matplotlib"""

    def _setAuto(self, axis):
        self._adjust()

    def _setAbsolute(self, type, value):
        rat = self._getMarginRatio()
        if type == "Width":
            self.canvas().fig.set_figwidth(value * _unit * rat[0])
        else:
            self.canvas().fig.set_figheight(value * _unit * rat[1])
        self._adjust()

    def _setAspect(self, type, aspect):
        rat = self._getMarginRatio()
        if type == "Width":
            self.canvas().fig.set_figwidth(self.canvas().fig.get_figheight() * (rat[0] / rat[1]) * aspect)
        else:
            self.canvas().fig.set_figheight(self.canvas().fig.get_figwidth() / (rat[0] / rat[1]) * aspect)
        self._adjust()

    def _getSize(self):
        rat = self._getMarginRatio()
        return (self.canvas().fig.get_figwidth() / rat[0] / _unit, self.canvas().fig.get_figheight() / rat[1] / _unit)

    def _getMarginRatio(self):
        m = self.canvas().getMargin()
        wr = 1 / (m[1] - m[0])
        hr = 1 / (m[3] - m[2])
        return (wr, hr)

    def _adjust(self):
        self.canvas().resize(self.canvas().fig.get_figwidth() * 100, self.canvas().fig.get_figheight() * 100)


class AreaSettingCanvas(AxisSettingCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addCanvasPart(_MatplotlibMargin(self))
        self.addCanvasPart(_MatplotlibCanvasSize(self))
