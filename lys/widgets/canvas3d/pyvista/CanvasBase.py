import numpy as np
from lys.Qt import QtWidgets, QtCore, QtGui
from pyvistaqt import QtInteractor

from ..interface import CanvasBase3D, CanvasPart3D, CanvasFocusEvent3D, CanvasMouseEvent3D, CanvasKeyboardEvent3D, CanvasUtilities3D
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
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.mouseMoved.emit(event)
        super().mouseMoveEvent(event)

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
        self.addCanvasPart(CanvasUtilities3D(self))
        self.addCanvasPart(CanvasFocusEvent3D(self))
        self.addCanvasPart(CanvasMouseEvent3D(self))
        self.addCanvasPart(CanvasKeyboardEvent3D(self))

    @property
    def plotter(self):
        return self._plotter

    def enableRendering(self, b):
        self.plotter.enableRendering(b)

    def closeEvent(self, e):
        self.finalized.emit(e)
        e.accept()

class ObjectPicker(CanvasPart3D):
    objectPicked = QtCore.pyqtSignal(object)
    pickingFinished = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas().plotter.track_click_position(self.__pick, viewport=True)
        self.canvas().dataCleared.connect(self.endPicker)
        self.__type = None

    def startPicker(self, objType):
        self.__type = objType

    def endPicker(self):
        self.__type = None
        self.pickingFinished.emit()

    def __pick(self, pos):
        if self.__type is None:
            return
        start, end = display_to_world_ray(self.canvas().plotter, pos[0], pos[1])
        direction = end - start
        start = self.canvas().plotter.camera_position[0]
        length = np.max(np.abs(self.canvas().plotter.bounds))*100
        res = self.canvas().rayTrace(start, start + length * direction, type=self.__type)
        self.objectPicked.emit(res)

def display_to_world_ray(plotter, x, y):
    ren = plotter.renderer  # vtkRenderer

    def d2w(z):
        ren.SetDisplayPoint(float(x), float(y), float(z))
        ren.DisplayToWorld()                 # display -> world :contentReference[oaicite:2]{index=2}
        wx, wy, wz, w = ren.GetWorldPoint()
        if w == 0:
            return np.array([wx, wy, wz], float)
        return np.array([wx/w, wy/w, wz/w], float)

    start = d2w(0.0)   # near plane
    end   = d2w(1.0)   # far plane
    return start, end