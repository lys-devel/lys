#!/usr/bin/env python
from matplotlib import colors
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
        d.obj.set_cmap(cmap)

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
