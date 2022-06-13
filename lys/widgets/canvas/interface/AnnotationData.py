import warnings
from lys.errors import NotImplementedWarning

from .CanvasBase import CanvasPart, saveCanvas


class AnnotationData(CanvasPart):
    def __init__(self, canvas, name, axis):
        super().__init__(canvas)
        self._name = name
        self._appearance = {}
        self._axis = axis

    def getName(self):
        """
        Get the name of the annotation.

        Return:
            str: The name of annotation
        """
        return self._name

    def getAxis(self):
        """
        Get axis to which the annotation is added.

        Return:
            str: The axis ('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight')
        """
        return self._axis

    @saveCanvas
    def setVisible(self, visible):
        """
        Set the visibility of the annotaion.

        Args:
            visible(bool): When it is True, the annotation is shown.
        """
        self._setVisible(visible)
        self._appearance['Visible'] = visible

    def getVisible(self):
        """
        Get the visibility of the annotaion.

        Return:
            bool: When it is True, the annotation is shown.
        """

        return self._appearance['Visible']

    @saveCanvas
    def setZOrder(self, z):
        """
        Set the z order of the annotaion.

        Args:
            z(int): The z order of the annotation.
        """
        self._setZOrder(z)
        self._appearance['ZOrder'] = z

    def getZOrder(self):
        """
        Get the z order of the annotaion.

        Return:
            int: The z order of the annotation.
        """
        return self._appearance['ZOrder']

    @saveCanvas
    def loadAppearance(self, appearance):
        """
        Load appearnce from dictionary.

        Args:
            appearance(dict): The dictionary that include appearance information, which is usually generated by :meth:`saveAppearance` method.
        """
        self.setVisible(appearance.get('Visible', True))
        self._loadAppearance(appearance)

    def saveAppearance(self):
        """
        Save appearnce as dictionary.

        Return:
            dict: The dictionary that include appearance information, which is usually used by :meth:`loadAppearance` method.
        """
        return dict(self._appearance)

    def _setVisible(self, visible):
        warnings.warn(str(type(self)) + " does not implement _setVisible(visible) method.", NotImplementedWarning)

    def _setZOrder(self, z):
        warnings.warn(str(type(self)) + " does not implement _setZOrder(z) method.", NotImplementedWarning)

    def _loadAppearance(self, appearance):
        warnings.warn(str(type(self)) + " does not implement _loadAppearance(appearance) method.", NotImplementedWarning)


class AnnotationWithLine(AnnotationData):
    @saveCanvas
    def setLineColor(self, color):
        """
        Set the color of the line.

        Args:
            color(str): The color string such as '#ff0000'
        """
        self._setLineColor(color)
        self._appearance['LineColor'] = color

    def getLineColor(self):
        """
        Get the color of the line.

        Return:
            str: The color string such as '#ff0000'
        """
        return self._appearance['LineColor']

    @ saveCanvas
    def setLineStyle(self, style):
        """
        Set the style of the line.

        Args:
            style('solid', 'dashed', 'dashdot', 'dotted', or 'none'): The line style.
        """
        self._setLineStyle(style)
        self._appearance['LineStyle'] = style

    def getLineStyle(self):
        """
        Get the style of the line.

        Return:
            str: The line style ('solid', 'dashed', 'dashdot', 'dotted', or 'none').
        """
        return self._appearance['LineStyle']

    @ saveCanvas
    def setLineWidth(self, width):
        """
        Set the width of the line.

        Args:
            width(int): The width of the line.
        """
        self._setLineWidth(width)
        self._appearance['LineWidth'] = width

    def getLineWidth(self):
        """
        Get the width of the line.

        Return:
            int: The width of the line.
        """
        return self._appearance['LineWidth']

    def _loadAppearance(self, appearance):
        self.setLineColor(appearance.get('LineColor', '#000000'))
        self.setLineWidth(appearance.get('LineWidth', 1))
        self.setLineStyle(appearance.get('LineStyle', 'solid'))

    def _setLineColor(self, color):
        warnings.warn(str(type(self)) + " does not implement _setColor(color) method.", NotImplementedWarning)

    def _setLineWidth(self, width):
        warnings.warn(str(type(self)) + " does not implement _setWidth(width) method.", NotImplementedWarning)

    def _setLineStyle(self, color):
        warnings.warn(str(type(self)) + " does not implement _setStyle(style) method.", NotImplementedWarning)