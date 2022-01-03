
import copy
from matplotlib import lines, cm, colors
from ..CanvasInterface import LineData, ImageData, RGBData, VectorData, ContourData


class _MatplotlibLine(LineData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, obj):
        self._obj = obj
        super().__init__(canvas, obj)

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

    def _setZ(self, z):
        self._obj.set_zorder(z)


class _MatplotlibImage(ImageData):
    """Implementation of LineData for matplotlib"""

    def __init__(self, canvas, obj):
        self._obj = obj
        super().__init__(canvas, obj)

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
        if self.isLog:
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
    def __init__(self, canvas, obj):
        super().__init__(canvas, obj)


class _MatplotlibRGB(RGBData):
    """Implementation of RGBData for matplotlib"""

    def __init__(self, canvas, obj):
        super().__init__(canvas, obj)


class _MatplotlibContour(ContourData):
    def __init__(self, canvas, obj):
        super().__init__(canvas, obj)
