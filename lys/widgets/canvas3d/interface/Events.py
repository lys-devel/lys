import weakref
from lys.Qt import QtGui, QtCore

from .CanvasBase import CanvasPart3D

_front = []


def getFrontCanvas3D(exclude=[]):
    if not hasattr(exclude, "__iter__"):
        exclude = [exclude]
    for canvas in reversed(_front):
        c = canvas()
        if c is not None and c not in exclude:
            return c


class CanvasFocusEvent3D(CanvasPart3D):
    focused = QtCore.pyqtSignal(object)
    """
    Emitted when the canvas is focused
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.focused.connect(self._setFrontCanvas)
        self._setFrontCanvas()

    def _setFrontCanvas(self):
        _front.append(weakref.ref(self.canvas()))
        if len(_front) > 1000:
            _front.pop(0)
