import warnings
from lys.errors import NotImplementedWarning

from .WaveData import WaveData


class _ColorGenerator(object):
    __ncolor = 0

    def nextColor(self):
        list = ["#17becf", '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', "#7f7f7f"]
        self.__ncolor += 1
        return list[self.__ncolor % 9]


class LineData(WaveData):
    def __init__(self, canvas, obj):
        super().__init__(canvas, obj)
        if not hasattr(canvas, "_lineColorGenerator"):
            self.canvas()._lineColorGenerator = _ColorGenerator()
        color = self.canvas()._lineColorGenerator.nextColor()
        self.setColor(color)

    def __setAppearance(self, key, value):
        self.appearance[key] = value

    def __getAppearance(self, key, default=None):
        return self.appearance.get(key, default)

    def setColor(self, color):
        self._setColor(color)
        self.__setAppearance('LineColor', color)
        self.modified.emit(self)

    def getColor(self):
        return self.__getAppearance('LineColor')

    def setStyle(self, style):
        self._setStyle(style)
        self.__setAppearance('LineStyle', style)
        self.modified.emit(self)

    def getStyle(self):
        return self.__getAppearance('LineStyle')

    def setWidth(self, width):
        self._setWidth(width)
        self.__setAppearance('LineWidth', width)
        self.modified.emit(self)

    def getWidth(self):
        return self.__getAppearance('LineWidth')

    def setMarker(self, marker):
        self._setMarker(marker)
        self.__setAppearance('Marker', marker)
        self.modified.emit(self)

    def getMarker(self):
        return self.__getAppearance('Marker')

    def setMarkerSize(self, size):
        self._setMarkerSize(size)
        self.__setAppearance('MarkerSize', size)
        self.modified.emit(self)

    def getMarkerSize(self):
        return self.__getAppearance('MarkerSize')

    def setMarkerThick(self, thick):
        self._setMarkerThick(thick)
        self.__setAppearance('MarkerThick', thick)
        self.modified.emit(self)

    def getMarkerThick(self):
        return self.__getAppearance('MarkerThick')

    def setMarkerFilling(self, type):
        self._setMarkerFilling(type)
        self.__setAppearance('MarkerFilling', type)
        self.modified.emit(self)

    def getMarkerFilling(self):
        return self.__getAppearance('MarkerFilling')

    def loadAppearance(self, appearance):
        if 'LineColor' in appearance:
            self.setColor(appearance['LineColor'])
        self.setStyle(appearance.get('LineStyle', 'solid'))
        self.setWidth(appearance.get('LineWidth', 1.5))
        self.setMarker(appearance.get('Marker', 'nothing'))
        self.setMarkerSize(appearance.get('MarkerSize', 6))
        self.setMarkerFilling(appearance.get('MarkerFilling', 'full'))
        self.setMarkerThick(appearance.get('MarkerThick', 1))

    def _setColor(self, color):
        warnings.warn(str(type(self)) + " does not implement _setColor(color) method.", NotImplementedWarning)

    def _setStyle(self, style):
        warnings.warn(str(type(self)) + " does not implement _setStyle(style) method.", NotImplementedWarning)

    def _setWidth(self, width):
        warnings.warn(str(type(self)) + " does not implement _setWidth(width) method.", NotImplementedWarning)

    def _setMarker(self, marker):
        warnings.warn(str(type(self)) + " does not implement _setMarker(marker) method.", NotImplementedWarning)

    def _setMarkerSize(self, size):
        warnings.warn(str(type(self)) + " does not implement _setMarkerSize(size) method.", NotImplementedWarning)

    def _setMarkerThick(self, thick):
        warnings.warn(str(type(self)) + " does not implement _setMarkerThick(thick) method.", NotImplementedWarning)

    def _setMarkerFilling(self, type):
        warnings.warn(str(type(self)) + " does not implement _setMarkerFilling(filling) method.", NotImplementedWarning)
