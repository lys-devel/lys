#!/usr/bin/env python
import numpy as np
from matplotlib import cm

from .LineSettings import *


class ImageColorAdjustableCanvas(MarkerStyleAdjustableCanvas):
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.key() == Qt.Key_A:
            ids = [i.id for i in self.getImages()]
            self.autoColorRange(ids)

    def _getColormap(self, d):
        return d.appearance.get('Colormap', 'gray')

    def _getColorLut(self, cmap, gamma):
        import copy
        colormap = copy.deepcopy(cm.get_cmap(cmap))
        if hasattr(colormap, "set_gamma"):
            colormap.set_gamma(gamma)
        lut = np.array(colormap._lut * 255)
        return lut[0:lut.shape[0] - 3, :]

    def _setColormap(self, d, cmap):
        lut = self._getColorLut(cmap, self._getColorGamma(d))
        self.__setColor(d, lut)
        d.appearance['Colormap'] = cmap

    def _getColorGamma(self, d):
        return d.appearance.get("ColorGamma", 1.0)

    def _setColorGamma(self, d, gam):
        lut = self._getColorLut(self._getColormap(d), 1.0 / gam)
        self.__setColor(d, lut)
        d.appearance['ColorGamma'] = gam

    def __setColor(self, d, lut):
        if self._isLog(d):
            d.obj.setImage(np.log(d.filteredWave.data), lut=lut)
        else:
            d.obj.setImage(d.filteredWave.data, lut=lut)

    def _getColorRange(self, d):
        return list(d.obj.getLevels())

    def _setColorRange(self, d, min, max, log):
        if log:
            d.appearance['Log'] = True
            d.obj.setImage(np.log(d.filteredWave.data), levels=(min, max))
        else:
            d.appearance['Log'] = False
            d.obj.setImage(d.filteredWave.data, levels=(min, max))

    def _isLog(self, d):
        return d.appearance.get("Log", False)

    def _getOpacity(self, d):
        return d.obj.opacity()

    def _setOpacity(self, d, value):
        d.obj.setOpacity(value)


class ImageSettingCanvas(ImageColorAdjustableCanvas, RGBColorAdjustableCanvasBase):
    pass
