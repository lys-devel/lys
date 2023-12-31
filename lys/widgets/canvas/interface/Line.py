import warnings
import copy
import numpy as np

from lys.errors import NotImplementedWarning

from .CanvasBase import saveCanvas
from .WaveData import WaveData


class _ColorGenerator(object):
    __ncolor = 0

    def nextColor(self):
        list = ["#17becf", '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', "#7f7f7f"]
        self.__ncolor += 1
        return list[self.__ncolor % 9]


class LineData(WaveData):
    """
    Interface to access line data in the canvas.

    Instance of LineData is automatically generated by display or append methods.

    Example::

        from lys import display
        g = display([1,2,3])
        g.getLines()[0].setColor('#ff0000')
    """

    def __setAppearance(self, key, value):
        self._appearance[key] = value

    def __getAppearance(self, key, default=None):
        return self._appearance.get(key, default)

    @saveCanvas
    def setColor(self, color):
        """
        Set color of the line.

        Args:
            color(str): rgb color string such as #ff0000.
        """
        self._setColor(color)
        self.__setAppearance('LineColor', color)

    def getColor(self):
        """
        Get color of the line.

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

    @saveCanvas
    def setMarker(self, marker):
        """
        Set the marker shape.

        Args:
            marker(str): String that indicate the marker shape. List of style strings can be seen from matplotlib.lines.Line2D.markers.values(). 
        """
        self._setMarker(marker)
        self.__setAppearance('Marker', marker)

    def getMarker(self):
        """
        Get the marker shape.

        Return:
            str: String that indicate the marker shape. List of style strings can be seen from matplotlib.lines.Line2D.markers.values(). 
        """
        return self.__getAppearance('Marker')

    @saveCanvas
    def setMarkerSize(self, size):
        """
        Set the size of the marker.

        Args:
            size(float): The size of the marker.
        """
        self._setMarkerSize(size)
        self.__setAppearance('MarkerSize', size)

    def getMarkerSize(self):
        """
        Get the size of the marker.

        Return:
            float: The size of the marker.
        """
        return self.__getAppearance('MarkerSize')

    @saveCanvas
    def setMarkerThick(self, thick):
        """
        Set the thickness of the marker edge.

        Args:
            thick(float): The thickness of the marker edge.
        """
        self._setMarkerThick(thick)
        self.__setAppearance('MarkerThick', thick)

    def getMarkerThick(self):
        """
        Get the thickness of the marker edge.

        Return:
            float: The thickness of the marker edge.
        """
        return self.__getAppearance('MarkerThick')

    @saveCanvas
    def setMarkerFilling(self, type):
        """
        Set the filling of the marker.

        Args:
            type('full', 'left', 'ritght', 'top', 'bottom', or 'none'): Style string. 
        """

        self._setMarkerFilling(type)
        self.__setAppearance('MarkerFilling', type)

    def getMarkerFilling(self):
        """
        Get the filling of the marker.

        Return:
            str: Style string.
        """
        return self.__getAppearance('MarkerFilling')

    @saveCanvas
    def setErrorbar(self, error, direction="y"):
        """
        Set the errorbar.

        If the error is float, the constant errorbar is set.

        If the error is str, the errorbar is loaded from wave.note[error].

        If the error is an array, the array is used as the errorbar.

        Args:
            error(float or str or array): The error.
            direction('x' or 'y'): The direction of the errorbar
        """
        err = self._getErrorbarData(error)
        self._setErrorbar(err, direction)
        if direction == 'x':
            self.__setAppearance("xerror", error)
        elif direction == 'y':
            self.__setAppearance("yerror", error)

    def __checkErrorShape(self, val):
        if isinstance(val, float):
            return True
        elif np.array(val).shape == (len(self.getFilteredWave().data),):
            return True
        elif np.array(val).shape == (2, len(self.getFilteredWave().data)):
            return True
        return False

    def getErrorbar(self, direction="y"):
        """
        Set the errorbar.

        Args:
            direction('x' or 'y'): The direction of the errorbar

        Returns:
            list: The errorbar
        """
        if direction == "x":
            return self.__getAppearance('xerror')
        elif direction == 'y':
            return self.__getAppearance('yerror')

    def _getErrorbarData(self, error):
        err = copy.deepcopy(error)
        if isinstance(err, str):
            err = self.getWave().note.get(err)
        if hasattr(err, "__iter__"):
            err = np.array(err)
        if err is not None:
            if not self.__checkErrorShape(err):
                err = None
        return err

    @saveCanvas
    def setCapSize(self, capsize):
        """
        Set the cap size of the errorbar.

        Args:
            capsize(float): The cap size.
        """
        self._setCapSize(capsize)
        self.__setAppearance("capsize", capsize)

    def getCapSize(self):
        """
        Get the cap size of the errorbar.

        Returns:
            float: The cap size.
        """
        return self.__getAppearance('capsize', 0)

    @saveCanvas
    def setLegendVisible(self, visible):
        """
        Set the visibility of the legend.

        Args:
            visible(bool): The visibility.
        """
        self._setLegendVisible(visible)
        self.__setAppearance("legendVisible", visible)

    def getLegendVisible(self):
        """
        Get the visibility of the legend.

        Returns:
            bool: The visibility.
        """
        return self.__getAppearance('legendVisible', False)

    @saveCanvas
    def setLegendLabel(self, label):
        """
        Set the label of the legend.

        Args:
            label(str): The label.
        """
        self._setLegendLabel(label)
        self.__setAppearance("legendLabel", label)

    def getLegendLabel(self):
        """
        Get the label of the legend.

        Returns:
            str: The label.
        """
        return self.__getAppearance('legendLabel', '')

    def _loadAppearance(self, appearance):
        if 'LineColor' in appearance:
            self.setColor(appearance['LineColor'])
        else:
            if not hasattr(self.canvas(), "_lineColorGenerator"):
                self.canvas()._lineColorGenerator = _ColorGenerator()
            color = self.canvas()._lineColorGenerator.nextColor()
            self.setColor(color)
        self.setStyle(appearance.get('LineStyle', 'solid'))
        self.setWidth(appearance.get('LineWidth', 2))
        self.setMarker(appearance.get('Marker', 'nothing'))
        self.setMarkerSize(appearance.get('MarkerSize', 6))
        self.setMarkerFilling(appearance.get('MarkerFilling', 'full'))
        self.setMarkerThick(appearance.get('MarkerThick', 1))
        self.setErrorbar(appearance.get('xerror'), "x")
        self.setErrorbar(appearance.get('yerror'), "y")
        self.setCapSize(appearance.get('capsize', 0))
        self.setLegendLabel(appearance.get('legendLabel', self.getName()))
        self.setLegendVisible(appearance.get('legendVisible', False))

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

    def _setLegendVisible(self, visible):
        warnings.warn(str(type(self)) + " does not implement _setLegendVisible(visible) method.", NotImplementedWarning)

    def _setLegendLabel(self, label):
        warnings.warn(str(type(self)) + " does not implement _setLegendLabel(label) method.", NotImplementedWarning)
