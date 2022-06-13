import warnings

from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import saveCanvas
from .AnnotationData import AnnotationWithLine


class CrossAnnotation(AnnotationWithLine):
    """
    Interface to access cross annotations in canvas.

    *CrossAnnotation* is usually generated by addCrossAnnotation method in canvas.

    Several methods related to the appearance of line is inherited from :class:`.AnnotationData.AnnotationWithLine`

    Args:
        canvas(Canvas): canvas to which the line annotation is added.
        pos(length 2 sequence): The position of the annotation in the form of (x, y).
        axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.

    Example::

        from lys import display
        g = display()
        rect = g.canvas.addCrossAnnotation()
        rect.setLineColor("#ff0000")
    """
    positionChanged = QtCore.pyqtSignal(tuple)
    """PyqtSignal that is emitted when the region is changed."""

    def __init__(self, canvas, pos, axis):
        super().__init__(canvas, "test", axis)
        self._initialize(pos, axis)
        self._pos = pos

    @saveCanvas
    def setPosition(self, pos):
        """
        Set position of the annotation.

        Args:
            pos(length 2 sequence): Theposition of cross in the form of (x, y)
        """
        if tuple(pos) != self._pos:
            self._pos = tuple(pos)
            self._setPosition(pos)
            self.positionChanged.emit(self._pos)

    def getPosition(self):
        """
        Get the position of the annotation.

        Return:
            length 2 sequence: The position of annotation in the form of (x, y)
        """
        return self._pos

    def _initialize(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _initialize(pos, axis) method.", NotImplementedWarning)

    def _setPosition(self, pos):
        warnings.warn(str(type(self)) + " does not implement _setPosition(pos) method.", NotImplementedWarning)