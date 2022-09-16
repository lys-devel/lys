import copy
import warnings
import numpy as np
from matplotlib import cm
import pyqtgraph as pg

from lys.Qt import QtCore, QtGui
from lys.errors import NotSupportedWarning
from ..interface import CanvasData, LineData, ImageData, RGBData, VectorData, ContourData


def _setZ(obj, z):
    obj.setZValue(z - 100000)


class _PyqtgraphLine(LineData):
    """Implementation of LineData for pyqtgraph"""
    __styles = {'solid': QtCore.Qt.SolidLine, 'dashed': QtCore.Qt.DashLine, 'dashdot': QtCore.Qt.DashDotLine, 'dotted': QtCore.Qt.DotLine, 'None': QtCore.Qt.NoPen}
    __symbols = {"circle": "o", "cross": "x", "tri_down": "t", "tri_up": "t1", "tri_right": "t2", "tri_left": "t3", "square": "s", "pentagon": "p", "hexagon": "h", "star": "star", "plus": "+", "diamond": "d", "None": None}

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        if wave.data.dtype == complex:
            data = np.absolute(wave.data)
        else:
            data = wave.data
        self._obj = pg.PlotDataItem(x=wave.x, y=data)
        self._err = pg.ErrorBarItem(x=wave.x, y=data, left=0, right=0, top=0, bottom=0, pen=pg.mkPen())
        canvas.getAxes(axis).addItem(self._obj)
        canvas.getAxes(axis).addItem(self._err)

    def _updateData(self):
        wave = self.getFilteredWave()
        if wave.data.dtype == complex:
            data = np.absolute(wave.data)
        else:
            data = wave.data
        self._obj.setData(x=wave.x, y=data)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)

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
        p.setColor(QtGui.QColor(color))
        self._obj.setSymbolPen(p)
        p = self._getLinePen()
        p.setColor(QtGui.QColor(color))
        self._obj.setPen(p)
        p = self._err.opts["pen"]
        p.setColor(QtGui.QColor(color))
        self._err.setData(pen=p)

    def _setStyle(self, style):
        p = self._getLinePen()
        p.setStyle(self.__styles[style])
        self._obj.setPen(p)

    def _setWidth(self, width):
        p = self._getLinePen()
        p.setWidth(width)
        self._obj.setPen(p)
        p = self._err.opts["pen"]
        p.setWidth(width)
        self._err.setData(pen=p)

    def _setMarker(self, marker):
        if marker in self.__symbols:
            self._obj.setSymbol(self.__symbols[marker])
        else:
            warnings.warn("pyqtGraph does not support marker [" + marker + "]", NotSupportedWarning)

    def _setMarkerSize(self, size):
        self._obj.setSymbolSize(size * 2)

    def _setMarkerThick(self, thick):
        warnings.warn("pyqtGraph does not support set marker thick", NotSupportedWarning)
        # p = self._getSymbolPen()
        # p.setWidth(thick)
        # self._obj.setSymbolPen(p)
        # for refresh
        # p = self._getLinePen()
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

    def _setErrorbar(self, error, direction):
        if direction == "y":
            if error is None:
                self._err.setData(bottom=None, top=None)
            elif isinstance(error, float):
                self._err.setData(bottom=error, top=error)
            elif len(np.array(error).shape) == 1:
                self._err.setData(bottom=error, top=error)
            elif len(np.array(error).shape) == 2:
                self._err.setData(bottom=error[0], top=error[1])
        if direction == "x":
            if error is None:
                self._err.setData(left=None, right=None)
            elif isinstance(error, float):
                self._err.setData(left=error, right=error)
            elif len(np.array(error).shape) == 1:
                self._err.setData(left=error, right=error)
            elif len(np.array(error).shape) == 2:
                self._err.setData(left=error[0], right=error[1])

    def _setCapSize(self, capsize):
        self._err.setData(beam=capsize)

    def _setLegendVisible(self, visible):
        leg = self.canvas().getLegend()
        exist = leg.getLabel(self._obj) is not None
        if visible:
            if not exist:
                leg.addItem(self._obj, self.getLegendLabel())
        elif exist:
            leg.removeItem(self._obj)
        self.canvas().updateLegends()

    def _setLegendLabel(self, label):
        leg = self.canvas().getLegend()
        if self.getLegendVisible():
            leg.removeItem(self._obj)
            leg.addItem(self._obj, label)
        self.canvas().updateLegends()


def _calcExtent2D(wav):
    xstart = wav.x[0]
    xend = wav.x[len(wav.x) - 1]
    ystart = wav.y[0]
    yend = wav.y[len(wav.y) - 1]

    dx = (xend - xstart) / (len(wav.x) - 1)
    dy = (yend - ystart) / (len(wav.y) - 1)

    xstart = xstart - dx / 2
    xend = xend + dx / 2
    ystart = ystart - dy / 2
    yend = yend + dy / 2

    xmag = (xend - xstart) / len(wav.x)
    ymag = (yend - ystart) / len(wav.y)
    xshift = xstart
    yshift = ystart
    tr = QtGui.QTransform()
    tr.scale(xmag, ymag)
    tr.translate(xshift / xmag, yshift / ymag)
    return tr


class _PyqtgraphImage(ImageData):
    """Implementation of LineData for pyqtgraph"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj = pg.ImageItem(image=wave.data)
        self._obj.setTransform(_calcExtent2D(wave))
        canvas.getAxes(axis).addItem(self._obj)

    def _updateData(self):
        self._obj.setImage(self.getFilteredWave().data)
        self._obj.setTransform(_calcExtent2D(self.getFilteredWave()))
        r = self.getColorRange()
        if r is not None:
            self.setColorRange(*r)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)

    def _setColormap(self, cmap):
        lut = self.__getColorLut(cmap, self.getGamma())
        self.__setColor(lut, self.getColorRange(), self.isLog())

    def _setGamma(self, gam):
        lut = self.__getColorLut(self.getColormap(), gam)
        self.__setColor(lut, self.getColorRange(), self.isLog())

    def _setColorRange(self, min, max):
        lut = self.__getColorLut(self.getColormap(), self.getGamma())
        self.__setColor(lut, (min, max), self.isLog())

    def _setLog(self, log):
        lut = self.__getColorLut(self.getColormap(), self.getGamma())
        self.__setColor(lut, self.getColorRange(), log)

    def __getColorLut(self, cmap, gamma):
        colormap = copy.deepcopy(cm.get_cmap(cmap))
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(gamma)
        lut = np.array(colormap._lut * 255)
        return lut[0:lut.shape[0] - 3, :]

    def __setColor(self, lut, levels, log):
        if log:
            self._obj.setImage(np.log(self.getFilteredWave().data), lut=lut, levels=tuple(np.log(levels)))
        else:
            self._obj.setImage(self.getFilteredWave().data, lut=lut, levels=levels)

    def _setOpacity(self, opacity):
        self._obj.setOpacity(opacity)


class _PyqtgraphRGB(RGBData):
    """Implementation of RGBData for pyqtgraph"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj = pg.ImageItem(image=wave.data, levels=(0, 1))
        self._obj.setTransform(_calcExtent2D(wave))
        canvas.getAxes(axis).addItem(self._obj)

    def _updateData(self):
        self._obj.setImage(self.getRGBWave().data)
        self._obj.setTransform(_calcExtent2D(self.getFilteredWave()))

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)


class _PyqtgraphContour(ContourData):
    """Implementation of ContourData for pyqtgraph"""
    __styles = {'solid': QtCore.Qt.SolidLine, 'dashed': QtCore.Qt.DashLine, 'dashdot': QtCore.Qt.DashDotLine, 'dotted': QtCore.Qt.DotLine, 'None': QtCore.Qt.NoPen}

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj = pg.IsocurveItem(data=wave.data, level=0.5, pen='r')
        self._obj.setTransform(_calcExtent2D(wave))
        canvas.getAxes(axis).addItem(self._obj)

    def _updateData(self):
        w = self.getFilteredWave()
        self._obj.setData(w.data)
        self._obj.setTransform(_calcExtent2D(w))

    def _setLevel(self, level):
        self._obj.setLevel(level)

    def _getLinePen(self):
        p = self._obj.pen
        if isinstance(p, tuple):
            return pg.mkPen(color=p)
        else:
            return p

    def _setColor(self, color):
        p = self._getLinePen()
        p.setColor(QtGui.QColor(color))
        self._obj.setPen(p)

    def _setStyle(self, style):
        p = self._getLinePen()
        p.setStyle(self.__styles[style])
        self._obj.setPen(p)

    def _setWidth(self, width):
        p = self._getLinePen()
        p.setWidth(width)
        self._obj.setPen(p)

    def _setVisible(self, visible):
        self._obj.setVisible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)


class _PyqtgraphData(CanvasData):
    def _append1d(self, wave, axis):
        return _PyqtgraphLine(self.canvas(), wave, axis)

    def _append2d(self, wave, axis):
        return _PyqtgraphImage(self.canvas(), wave, axis)

    def _append3d(self, wave, axis):
        return _PyqtgraphRGB(self.canvas(), wave, axis)

    def _appendContour(self, wav, axis):
        return _PyqtgraphContour(self.canvas(), wav, axis)

    def _remove(self, data):
        ax = self.canvas().getAxes(data.getAxis())
        ax.removeItem(data._obj)
