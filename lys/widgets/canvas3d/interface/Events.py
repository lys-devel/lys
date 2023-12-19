import time
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


class CanvasMouseEvent3D(CanvasPart3D):
    """
    Basic keyborad event class of Canvas.
    """
    mousePressed = QtCore.pyqtSignal(object)
    """
    Emitted when a mouse is pressed.
    """
    mouseReleased = QtCore.pyqtSignal(object)
    """
    Emitted when a mouse is released.
    """
    mouseMoved = QtCore.pyqtSignal(object)
    """
    Emitted when a mouse is moved.
    """
    clicked = QtCore.pyqtSignal(object)
    """
    Emitted when a mouse is clicked.
    """
    doubleClicked = QtCore.pyqtSignal(object)
    """
    Emitted when a mouse is double-clicked.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.mouseReleased.connect(self._mouseReleased)
        #self.doubleClicked.connect(canvas.openModifyWindow)
        self._clicktime = 0

    def _mouseReleased(self, e):
        self.clicked.emit(e)
        if time.time() - self._clicktime < 0.3:
            self.doubleClicked.emit(e)
        self._clicktime = time.time()


class CanvasKeyboardEvent3D(CanvasPart3D):
    """
    Basic keyborad event class of Canvas.
    """
    keyPressed = QtCore.pyqtSignal(QtGui.QKeyEvent)
    """
    Emitted when a key is pressed.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.keyPressed.connect(self._keyPressed)

    def _keyPressed(self, e):
        if e.key() == QtCore.Qt.Key_A and e.modifiers() == QtCore.Qt.ControlModifier:
            for i in self.canvas().getRGBs() + self.canvas().getImages():
                i.setColorRange()
        if e.key() == QtCore.Qt.Key_C and e.modifiers() == QtCore.Qt.ControlModifier:
            self.canvas().copyToClipboard()
        if e.key() == QtCore.Qt.Key_G and e.modifiers() == QtCore.Qt.ControlModifier:
            self.canvas().openModifyWindow()
        if e.key() == QtCore.Qt.Key_F and e.modifiers() == QtCore.Qt.ControlModifier:
            self.canvas().openFittingWindow()
        if e.key() == QtCore.Qt.Key_D and e.modifiers() == QtCore.Qt.ControlModifier:
            self.canvas().duplicate()