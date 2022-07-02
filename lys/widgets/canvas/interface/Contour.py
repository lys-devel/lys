import warnings
import numpy as np
from lys.errors import NotImplementedWarning

from .CanvasBase import saveCanvas
from .WaveData import WaveData


class ContourData(WaveData):
    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)

    def __setAppearance(self, key, value):
        self._appearance[key] = value

    def __getAppearance(self, key, default=None):
        return self._appearance.get(key, default)

    @saveCanvas
    def setLevel(self, level):
        """
        Set level of the contour.

        Args:
            level(float): The level.
        """
        self._setLevel(level)
        self.__setAppearance('Level', level)

    def getLevel(self):
        """
        Get level of the contour.

        Return:
            float: The level
        """
        return self.__getAppearance('Level')

    @saveCanvas
    def setColor(self, color):
        """
        Set color of the contour line.

        Args:
            color(str): rgb color string such as #ff0000.
        """
        self._setColor(color)
        self.__setAppearance('LineColor', color)

    def getColor(self):
        """
        Get color of the contour line.

        Return:
            str: color string such as #ff0000
        """
        return self.__getAppearance('LineColor')

    @saveCanvas
    def setStyle(self, style):
        """
        Set the style of the line.

        Args:
            style('solid', 'dashed', 'dashdot', 'dotted', 'None'): Style string. 
        """
        self._setStyle(style)
        self.__setAppearance('LineStyle', style)

    def getStyle(self):
        """
        Get the style of the line.

        Return:
            str: Style string.
        """
        return self.__getAppearance('LineStyle')

    @saveCanvas
    def setWidth(self, width):
        """
        Set the width of the line.

        Args:
            width(float): The width of the line.
        """
        self._setWidth(width)
        self.__setAppearance('LineWidth', width)

    def getWidth(self):
        """
        Get the width of the line.

        Return:
            float: The width of the line.
        """
        return self.__getAppearance('LineWidth')

    def _loadAppearance(self, appearance):
        self.setLevel(appearance.get('Level', np.median(self.getFilteredWave().data)))
        self.setColor(appearance.get('LineColor', '#000000'))
        self.setStyle(appearance.get('LineStyle', 'solid'))
        self.setWidth(appearance.get('LineWidth', 2))

    def _setLevel(self, level):
        warnings.warn(str(type(self)) + " does not implement _setLevel(level) method.", NotImplementedWarning)

    def _setColor(self, color):
        warnings.warn(str(type(self)) + " does not implement _setColor(color) method.", NotImplementedWarning)

    def _setStyle(self, style):
        warnings.warn(str(type(self)) + " does not implement _setStyle(style) method.", NotImplementedWarning)

    def _setWidth(self, width):
        warnings.warn(str(type(self)) + " does not implement _setWidth(width) method.", NotImplementedWarning)
