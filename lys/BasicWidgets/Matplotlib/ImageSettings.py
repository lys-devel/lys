#!/usr/bin/env python
from matplotlib import colors
from matplotlib import cm
from .LineSettings import *


class ImageColorAdjustableCanvas(MarkerStyleAdjustableCanvas):
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getImages()]
            self.autoColorRange(ids)

    def _getColormap(self, d):
        return d.obj.get_cmap().name

    def _setColormap(self, d, cmap):
        import copy
        colormap = copy.deepcopy(cm.get_cmap(cmap))
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(self._getColorGamma(d))
        d.obj.set_cmap(colormap)

    def _getColorGamma(self, d):
        return d.appearance.get("ColorGamma", 1.0)

    def _setColorGamma(self, d, gam):
        colormap = cm.get_cmap(self._getColormap(d))
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(1.0 / gam)
        d.obj.set_cmap(colormap)

    def _getColorRange(self, d):
        return d.obj.norm.vmin, d.obj.norm.vmax

    def _setColorRange(self, d, min, max, log):
        if log:
            norm = colors.LogNorm(vmin=min, vmax=max)
        else:
            norm = colors.Normalize(vmin=min, vmax=max)
        d.obj.set_norm(norm)

    def _isLog(self, d):
        return isinstance(d.obj.norm, colors.LogNorm)

    def _getOpacity(self, d):
        val = d.obj.get_alpha()
        if val is None:
            return 1
        else:
            return val

    def _setOpacity(self, d, value):
        d.obj.set_alpha(value)


class ImageSettingCanvas(ImageColorAdjustableCanvas):
    pass
