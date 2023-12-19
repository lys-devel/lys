import numpy as np
from lys.Qt import QtWidgets, QtCore, QtGui
from pyvistaqt import QtInteractor

from ..interface import CanvasBase3D, CanvasPart3D, CanvasFocusEvent3D, CanvasMouseEvent3D, CanvasKeyboardEvent3D
from .WaveData import _pyvistaData


class _Plotter(QtInteractor):
    mouseReleased = QtCore.pyqtSignal(object)
    mousePressed = QtCore.pyqtSignal(object)
    mouseMoved = QtCore.pyqtSignal(object)
    focused = QtCore.pyqtSignal(object)
    keyPressed = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def enableRendering(self, b):
        self._render = b

    def render(self):
        if self._render:
            return super().render()

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        self.mousePressed.emit(event)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        self.mouseMoved.emit(event)
        super().mouseReleaseEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focused.emit(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event)

class Canvas3d(CanvasBase3D, QtWidgets.QWidget):
    def __init__(self, parent=None):
        CanvasBase3D.__init__(self)
        QtWidgets.QWidget.__init__(self, parent)
        self.__initlayout()
        self.__initCanvasParts()
        self.plotter.mouseMoved.connect(self.mouseMoved)
        self.plotter.mouseReleased.connect(self.mouseReleased)
        self.plotter.mousePressed.connect(self.mousePressed)
        self.plotter.focused.connect(self.focused)
        self.plotter.keyPressed.connect(self.keyPressed)

    def __initlayout(self):
        self._plotter = _Plotter()
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._plotter.interactor)
        self.setLayout(vlayout)

    def __initCanvasParts(self):
        self.addCanvasPart(_pyvistaData(self))
        self.addCanvasPart(ObjectPicker(self))
        self.addCanvasPart(CanvasFocusEvent3D(self))
        self.addCanvasPart(CanvasMouseEvent3D(self))
        self.addCanvasPart(CanvasKeyboardEvent3D(self))

    @property
    def plotter(self):
        return self._plotter

    def enableRendering(self, b):
        self.plotter.enableRendering(b)


class ObjectPicker(CanvasPart3D):
    objectPicked = QtCore.pyqtSignal(object)
    pickingFinished = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas().plotter.track_click_position(self.__pick)
        self.canvas().dataCleared.connect(self.endPicker)
        self.__type = None

    def startPicker(self, objType):
        self.__type = objType

    def endPicker(self):
        self.__type = None
        self.pickingFinished.emit()

    def __pick(self, *args):
        if self.__type is None:
            return
        picked_pt = np.array(self.canvas().plotter.pick_mouse_position())
        direction = picked_pt - self.canvas().plotter.camera_position[0]
        direction = direction / np.linalg.norm(direction)
        res = self.canvas().rayTrace(picked_pt - 1 * direction, picked_pt + 10000 * direction, type=self.__type)
        self.objectPicked.emit(res)
