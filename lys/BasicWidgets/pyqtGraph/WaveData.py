import warnings
import pyqtgraph as pg

from LysQt.QtCore import Qt
from LysQt.QtGui import QColor
from lys.errors import NotSupportedWarning
from ..CanvasInterface import LineData


class _PyqtgraphLine(LineData):
    __styles = {'solid': Qt.SolidLine, 'dashed': Qt.DashLine, 'dashdot': Qt.DashDotLine, 'dotted': Qt.DotLine, 'None': Qt.NoPen}
    __symbols = {"circle": "o", "cross": "x", "tri_down": "t", "tri_up": "t1", "tri_right": "t2", "tri_left": "t3", "square": "s", "pentagon": "p", "hexagon": "h", "star": "star", "plus": "+", "diamond": "d", "None": None}

    def __init__(self, canvas, obj):
        self._obj = obj
        super().__init__(canvas, obj)

    def _getLinePen(self):
        p = self._obj.opts['pen']
        if isinstance(p, tuple):
            return pg.mkPen(color=p)
        else:
            return p

    def _getSymbolPen(self):
        p = self._obj.opts['symbolPen']
        if isinstance(p, tuple):
            return pg.mkPen(color=p)
        else:
            return p

    def _getSymbolBrush(self):
        p = self._obj.opts['symbolBrush']
        if isinstance(p, tuple):
            return pg.mkBrush(color=p)
        else:
            return p

    def _setColor(self, color):
        p = self._getSymbolPen()
        p.setColor(QColor(color))
        self._obj.setSymbolPen(p)
        self._obj.setPen(pg.mkPen(color=QColor(color)))

    def _setStyle(self, style):
        p = self._getLinePen()
        p.setStyle(self.__styles[style])
        self._obj.setPen(p)

    def _setWidth(self, width):
        p = self._getLinePen()
        p.setWidth(width)
        self._obj.setPen(p)

    def _setMarker(self, marker):
        if marker in self.__symbols:
            self._obj.setSymbol(self.__symbols[marker])
        else:
            warnings.warn("pyqtGraph does not support marker [" + marker + "]", NotSupportedWarning)

    def _setMarkerSize(self, size):
        self._obj.setSymbolSize(size * 2)

    def _setMarkerThick(self, thick):
        warnings.warn("pyqtGraph does not support set marker thick", NotSupportedWarning)
        #p = self._getSymbolPen()
        # p.setWidth(thick)
        # self._obj.setSymbolPen(p)
        # for refresh
        #p = self._getLinePen()
        # self._obj.setPen(p)

    def _setMarkerFilling(self, filling):
        if filling in ["filled", "full"]:
            c = self._getLinePen().color()
            b = pg.mkBrush(c)
            self._obj.setSymbolBrush(b)
        elif filling == "none":
            self._obj.setSymbolBrush(None)
        else:
            warnings.warn("pyqtGraph does not support filling [" + filling + "]", NotSupportedWarning)

    def _setZ(self, z):
        self._obj.setZValue(z)
