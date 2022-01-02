

from matplotlib import lines
from ..CanvasInterface import LineData


class _MatplotlibLine(LineData):
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
