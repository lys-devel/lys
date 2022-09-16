
import copy
import numpy as np
from matplotlib import lines, cm, colors
from matplotlib.contour import QuadContourSet
from ..interface import CanvasData, LineData, ImageData, RGBData, VectorData, ContourData


def _setZ(obj, z):
    obj.set_zorder(z - 100000)


class _MatplotlibLine(LineData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj = canvas.getAxes(axis).errorbar(wave.x, wave.data)

    def _updateData(self):
        self.__update()

    def _setVisible(self, visible):
        self._appearance['Visible'] = visible
        self._obj.lines[0].set_visible(visible)
        self.canvas().updateLegends()

    def _setZ(self, z):
        _setZ(self._obj.lines[0], z)
        for line in self._obj.lines[1] + self._obj.lines[2]:
            _setZ(line, z - 1)

    def _setColor(self, color):
        self._obj.lines[0].set_color(color)
        for line in self._obj.lines[1] + self._obj.lines[2]:
            line.set_color(color)
        self.canvas().updateLegends()

    def _setStyle(self, style):
        self._obj.lines[0].set_linestyle(style)
        self.canvas().updateLegends()

    def _setWidth(self, width):
        self._obj.lines[0].set_linewidth(width)
        for line in self._obj.lines[1]:
            line.set_markeredgewidth(width)
        for line in self._obj.lines[2]:
            line.set_linewidth(width)
        self.canvas().updateLegends()

    def _setMarker(self, marker):
        dic = {value: key for key, value in lines.Line2D.markers.items()}
        self._obj.lines[0].set_marker(dic[marker])
        self.canvas().updateLegends()

    def _setMarkerSize(self, size):
        self._obj.lines[0].set_markersize(size)
        self.canvas().updateLegends()

    def _setMarkerThick(self, thick):
        self._obj.lines[0].set_markeredgewidth(thick)
        self.canvas().updateLegends()

    def _setMarkerFilling(self, filling):
        self._obj.lines[0].set_fillstyle(filling)
        self.canvas().updateLegends()

    def __update(self, error=None, direction=None, capsize=None):
        self._obj.remove()
        wave = self.getFilteredWave()
        xerr = yerr = error
        if direction == "x" or direction is None:
            yerr = self._getErrorbarData(self.getErrorbar("y"))
        if direction == "y" or direction is None:
            xerr = self._getErrorbarData(self.getErrorbar("x"))
        if capsize is None:
            capsize = self.getCapSize()
        self._obj = self.canvas().getAxes(self._axis).errorbar(wave.x, wave.data, xerr=xerr, yerr=yerr, capsize=capsize)
        visible = self.getVisible()
        if visible is not None:
            self._setVisible(visible)
        z = self.getZOrder()
        if z is not None:
            self._setZ(z)
        color = self.getColor()
        if color is not None:
            self._setColor(color)
        style = self.getStyle()
        if style is not None:
            self._setStyle(style)
        width = self.getWidth()
        if width is not None:
            self._setWidth(width)
        marker = self.getMarker()
        if marker is not None:
            self._setMarker(marker)
        msize = self.getMarkerSize()
        if msize is not None:
            self._setMarkerSize(msize)
        mthick = self.getMarkerThick()
        if mthick is not None:
            self._setMarkerThick(mthick)
        mfill = self.getMarkerFilling()
        if mfill is not None:
            self._setMarkerFilling(mfill)
        self.canvas().updateLegends()

    def _setErrorbar(self, error, direction):
        self.__update(error, direction, self.getCapSize())

    def _setCapSize(self, capsize):
        self.__update(capsize=capsize)

    def _setLegendVisible(self, visible):
        self._appearance["legendVisible"] = visible
        self.canvas().updateLegends()

    def _setLegendLabel(self, label):
        self._appearance["legendLabel"] = label
        self.canvas().updateLegends()


def _calcExtent2D(wav):
    xstart = wav.x[0]
    xend = wav.x[len(wav.x) - 1]
    ystart = wav.y[0]
    yend = wav.y[len(wav.y) - 1]
    dx = (xend - xstart) / (wav.data.shape[1] - 1)
    dy = (yend - ystart) / (wav.data.shape[0] - 1)
    return (xstart - dx / 2, xend + dx / 2, yend + dy / 2, ystart - dy / 2)


class _MatplotlibImage(ImageData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj = canvas.getAxes(axis).imshow(wave.data.swapaxes(0, 1), aspect='auto', extent=_calcExtent2D(wave), picker=True)

    def _updateData(self):
        self._obj.set_data(self.getFilteredWave().data.swapaxes(0, 1))
        self._obj.set_extent(_calcExtent2D(self.getFilteredWave()))

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)

    def _setColormap(self, cmap):
        colormap = copy.deepcopy(cm.get_cmap(cmap))
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(self.getGamma())
        self._obj.set_cmap(colormap)

    def _setGamma(self, gam):
        colormap = cm.get_cmap(self.getColormap())
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(gam)
        self._obj.set_cmap(colormap)

    def _setColorRange(self, min, max):
        if self.isLog():
            norm = colors.LogNorm(vmin=min, vmax=max)
        else:
            norm = colors.Normalize(vmin=min, vmax=max)
        self._obj.set_norm(norm)

    def _setLog(self, log):
        min, max = self.getColorRange()
        if log:
            norm = colors.LogNorm(vmin=min, vmax=max)
        else:
            norm = colors.Normalize(vmin=min, vmax=max)
        self._obj.set_norm(norm)

    def _setOpacity(self, value):
        self._obj.set_alpha(value)


class _MatplotlibVector(VectorData):
    """Implementation of VectorData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._axis = axis
        xx, yy = np.meshgrid(wave.x, wave.y)
        self._obj = canvas.getAxes(axis).quiver(xx, yy, np.real(wave.data.T), np.imag(wave.data.T), pivot="mid")
        canvas.axisRangeChanged.connect(self._updateData)

    def _updateData(self):
        X, Y = np.meshgrid(self.getFilteredWave().x, self.getFilteredWave().y)
        data_x = np.array(np.real(self.getFilteredWave().data.T))
        data_y = np.array(np.imag(self.getFilteredWave().data.T))
        rx, ry = self.canvas().getAxisRange(self._axis)
        if rx[0] > rx[1]:
            data_x = -data_x
        if ry[0] > ry[1]:
            data_y = -data_y
        self._obj.set_UVC(data_x, data_y)
        self._obj.set_offsets(np.array([X.flatten(), Y.flatten()]).T)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)

    def _setPivot(self, pivot):
        self._obj.pivot = pivot

    def _setScale(self, scale):
        self._obj.scale = scale

    def _setWidth(self, width):
        self._obj.width = width / 100

    def _setColor(self, color):
        self._obj.set_color(color)


class _MatplotlibRGB(RGBData):
    """Implementation of RGBData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        w = self.getRGBWave()
        self._obj = canvas.getAxes(axis).imshow(w.data.swapaxes(0, 1), aspect='auto', extent=_calcExtent2D(w), picker=True)

    def _updateData(self):
        wave = self.getRGBWave()
        self._obj.set_data(wave.data.swapaxes(0, 1))
        self._obj.set_extent(_calcExtent2D(wave))

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)


class _MatplotlibContour(ContourData):
    """Implementation of ContourData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._axis = axis
        self._obj = canvas.getAxes(axis).contour(wave.data.T[::-1, :], [0.5], extent=_calcExtent2D(wave))

    def _updateData(self):
        w = self.getFilteredWave()
        for o in self._obj.collections:
            o.remove()
        self._obj = self.canvas().getAxes(self._axis).contour(w.data.T[::-1, :], [0.5], extent=_calcExtent2D(w))

    def __update(self, level=None):
        if level is None:
            level = self.getLevel()
        for o in self._obj.collections:
            o.remove()
        w = self.getFilteredWave()
        self._obj = self.canvas().getAxes(self._axis).contour(w.data.T[::-1, :], [level], extent=_calcExtent2D(w))
        color = self.getColor()
        style = self.getStyle()
        width = self.getWidth()
        for o in self._obj.collections:
            if color is not None:
                o.set_color(color)
            if style is not None:
                o.set_linestyle(style)
            if width is not None:
                o.set_linewidth(width)

    def _setLevel(self, level):
        self.__update(level=level)

    def _setColor(self, color):
        for o in self._obj.collections:
            o.set_color(color)

    def _setStyle(self, style):
        for o in self._obj.collections:
            o.set_linestyle(style)

    def _setWidth(self, width):
        for o in self._obj.collections:
            o.set_linewidth(width)

    def _setVisible(self, visible):
        for o in self._obj.collections:
            o.set_visible(visible)

    def _setZ(self, z):
        for o in self._obj.collections:
            _setZ(o, z)


class _MatplotlibData(CanvasData):
    def _append1d(self, wave, axis):
        return _MatplotlibLine(self.canvas(), wave, axis)

    def _append2d(self, wave, axis):
        return _MatplotlibImage(self.canvas(), wave, axis)

    def _append3d(self, wave, axis):
        return _MatplotlibRGB(self.canvas(), wave, axis)

    def _appendContour(self, wav, axis):
        return _MatplotlibContour(self.canvas(), wav, axis)

    def _appendVectorField(self, wav, axis):
        return _MatplotlibVector(self.canvas(), wav, axis)

    def _remove(self, data):
        if isinstance(data._obj, QuadContourSet):
            for o in data._obj.collections:
                o.remove()
        else:
            data._obj.remove()
