
import copy
import numpy as np
from matplotlib import lines, cm, colors
from matplotlib.contour import QuadContourSet
from ..CanvasInterface import CanvasData, LineData, ImageData, RGBData, VectorData, ContourData


def _setZ(obj, z):
    obj.set_zorder(z - 100000)


class _MatplotlibLine(LineData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        self._obj, = canvas.getAxes(axis).plot(wave.x, wave.data)
        self._obj.set_pickradius(5)

    def _updateData(self):
        self._obj.set_data(self.getFilteredWave().x, self.getFilteredWave().data)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)

    def _setZ(self, z):
        _setZ(self._obj, z)

    def _setColor(self, color):
        self._obj.set_color(color)

    def _setStyle(self, style):
        self._obj.set_linestyle(style)

    def _setWidth(self, width):
        self._obj.set_linewidth(width)

    def _setMarker(self, marker):
        dic = {value: key for key, value in lines.Line2D.markers.items()}
        self._obj.set_marker(dic[marker])

    def _setMarkerSize(self, size):
        self._obj.set_markersize(size)

    def _setMarkerThick(self, thick):
        self._obj.set_markeredgewidth(thick)

    def _setMarkerFilling(self, filling):
        self._obj.set_fillstyle(filling)


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
        self._obj = canvas.getAxes(axis).contour(wave.data.T[::-1, :], [0.5], extent=_calcExtent2D(wave), colors=['red'])

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
