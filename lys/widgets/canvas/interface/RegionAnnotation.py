import warnings

from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import saveCanvas
from .AnnotationData import AnnotationWithLine


class RegionAnnotation(AnnotationWithLine):
    """
    Interface to access region annotations in canvas.

    *RegionAnnotation* is usually generated by addRegionAnnotation method in canvas.

    Several methods related to the appearance of line is inherited from :class:`.AnnotationData.AnnotationWithLine`

    Args:
        canvas(Canvas): canvas to which the line annotation is added.
        region(length 2 sequence): The region of the annotation in the form of (x1, x2).
        axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the line annotation is added.

    Example::

        from lys import display
        g = display()
        rect = g.canvas.addRegionAnnotation()
        rect.setLineColor("#ff0000")
    """
    regionChanged = QtCore.pyqtSignal(tuple)
    """PyqtSignal that is emitted when the region is changed."""

    def __init__(self, canvas, region, orientation, axis):
        super().__init__(canvas, "region", axis)
        self._initialize(region, orientation, axis)
        self._region = region
        self._orientation = orientation

    @saveCanvas
    def setRegion(self, region):
        """
        Set region of the annotation.

        Args:
            region(length 2 sequence): The region of rectangle in the form of (x1, x2)
        """
        r = (min(*region), max(*region))
        if r != self._region:
            self._region = r
            self._setRegion(r)
            self.regionChanged.emit(self.getRegion())

    def getRegion(self):
        """
        Get the region of the annotation.

        Return:
            length 2 sequence: The region of annotation in the form of (x1, x2)
        """
        return self._region

    def getOrientation(self):
        """
        Get the orientation of the annotation.

        Return:
            str: The orientation of annotation ('vertical' or 'horizontal')
        """
        return self._orientation

    def _initialize(self, region, orientation, axis):
        warnings.warn(str(type(self)) + " does not implement _initialize(region, orientation, axis) method.", NotImplementedWarning)

    def _setRegion(self, region):
        warnings.warn(str(type(self)) + " does not implement _setRegion(region) method.", NotImplementedWarning)


class FreeRegionAnnotation(AnnotationWithLine):
    """
    Interface to access free region annotations in canvas.

    *FreeRegionAnnotation* is usually generated by addFreeRegionAnnotation method in canvas.

    Several methods related to the appearance of line is inherited from :class:`.AnnotationData.AnnotationWithLine`

    Args:
        canvas(Canvas): canvas to which the line annotation is added.
        region(2*2 sequence): The position of the region in the form of [(x0, y0), (x1 ,y1)]
        width(float): The width of the region.
        axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.

    Example::

        from lys import display
        g = display()
        rect = g.canvas.addFreeRegionAnnotation()
        rect.setLineColor("#ff0000")
    """
    regionChanged = QtCore.pyqtSignal(list)
    """PyqtSignal that is emitted when the region is changed."""
    widthChanged = QtCore.pyqtSignal(float)
    """PyqtSignal that is emitted when the region width is changed."""

    def __init__(self, canvas, region, width, axis):
        super().__init__(canvas, "fregion", axis)
        self._initialize(region, width, axis)
        self._region = region
        self._width = width

    @saveCanvas
    def setRegion(self, region):
        """
        Set region of the annotation.

        Args:
            region(2*2 sequence): The position of the region in the form of [(x0, y0), (x1 ,y1)]
        """
        r = [tuple(region[0]), tuple(region[1])]
        if r != self._region:
            self._region = r
            self._setRegion(r)
            self.regionChanged.emit(self.getRegion())

    def getRegion(self):
        """
        Get the region of the annotation.

        Return:
            2*2 sequence: The position of the region in the form of [(x0, y0), (x1 ,y1)]
        """
        return self._region

    @saveCanvas
    def setWidth(self, width):
        """
        Set width of the annotation.

        Args:
            width(float): The width of annotation.
        """
        if width != self._width:
            self._width = width
            self._setWidth(width)
            self.widthChanged.emit(self.getWidth())

    def getWidth(self):
        """
        Get the width of the annotation.

        Return:
            float: The width of annotation.
        """
        return self._width

    def _initialize(self, region, width, axis):
        warnings.warn(str(type(self)) + " does not implement _initialize(region, width, axis) method.", NotImplementedWarning)

    def _setRegion(self, region):
        warnings.warn(str(type(self)) + " does not implement _setRegion(region) method.", NotImplementedWarning)

    def _setWidth(self, width):
        warnings.warn(str(type(self)) + " does not implement _setWidth(width) method.", NotImplementedWarning)
