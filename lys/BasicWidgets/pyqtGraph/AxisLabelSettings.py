
import warnings
from LysQt.QtGui import QFont

from lys.errors import NotSupportedWarning
from .AxisSettings import *
from ..CanvasInterface import CanvasFont, CanvasAxisLabel, CanvasTickLabel

opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}


class _PyqtgraphAxisLabel(CanvasAxisLabel):
    def _setAxisLabel(self, axis, text):
        ax = self.canvas().fig.getAxis(axis.lower())
        ax.setLabel(text)
        self.setAxisLabelVisible(axis, self.getAxisLabelVisible(axis))

    def _setAxisLabelVisible(self, axis, b):
        ax = self.canvas().fig.getAxis(axis.lower())
        ax.showLabel(b)

    def _setAxisLabelCoords(self, axis, pos):
        ax = self.canvas().fig.getAxis(axis.lower())
        if axis in ['Left', 'Right']:
            ax.setStyle(tickTextWidth=int(-pos * 100), autoExpandTextSpace=False)
        else:
            ax.setStyle(tickTextHeight=int(-pos * 100), autoExpandTextSpace=False)

    def _setAxisLabelFont(self, axis, family, size, color):
        ax = self.canvas().fig.getAxis(axis.lower())
        css = {'font-family': family, 'font-size': str(size) + "pt", "color": color}
        ax.setLabel(**css)
        self.setAxisLabel(axis, self.getAxisLabel(axis))


class _PyqtgraphTickLabel(CanvasTickLabel):
    def _setTickLabelVisible(self, axis, tf, mirror=False):
        if mirror:
            ax = self.canvas().fig.getAxis(opposite[axis])
        else:
            ax = self.canvas().fig.getAxis(axis.lower())
        ax.setStyle(showValues=tf)

    def _setTickLabelFont(self, axis, family, size, color):
        ax = self.canvas().fig.getAxis(axis.lower())
        ax.setStyle(tickFont=QFont(family, size))
        if color != "black" and color != "#000000":
            warnings.warn("pyqtGraph does not support changing color of tick.", NotSupportedWarning)


class AxisSettingCanvas(TickAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self._font = CanvasFont(self)
        self._axisLabel = _PyqtgraphAxisLabel(self)
        self._tickLabel = _PyqtgraphTickLabel(self)

    def __getattr__(self, key):
        if "_font" in self.__dict__:
            if hasattr(self._font, key):
                return getattr(self._font, key)
        if "_axisLabel" in self.__dict__:
            if hasattr(self._axisLabel, key):
                return getattr(self._axisLabel, key)
        if "_tickLabel" in self.__dict__:
            if hasattr(self._tickLabel, key):
                return getattr(self._tickLabel, key)
        return super().__getattr__(key)
