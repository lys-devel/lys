import time
import weakref
import numpy as np

from LysQt.QtGui import QKeyEvent, QMouseEvent
from LysQt.QtCore import pyqtSignal, Qt, QObject
from .CanvasBase import CanvasPart, saveCanvas


class CanvasKeyboardEvent(CanvasPart):
    """
    Basic keyborad event class of Canvas.
    """
    keyPressed = pyqtSignal(QKeyEvent)
    """
    Emitted when a key is pressed.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.keyPressed.connect(self._keyPressed)

    @saveCanvas
    def _keyPressed(self, e):
        if e.key() == Qt.Key_A and e.modifiers() == Qt.ControlModifier:
            for i in self.canvas().getRGBs() + self.canvas().getImages():
                i.setColorRange()
        if e.key() == Qt.Key_C and e.modifiers() == Qt.ControlModifier:
            self.canvas().copyToClipboard()
        if e.key() == Qt.Key_G and e.modifiers() == Qt.ControlModifier:
            self.canvas().openModifyWindow()
        if e.key() == Qt.Key_F and e.modifiers() == Qt.ControlModifier:
            self.canvas().openFittingWindow()


_front = []


def getFrontCanvas(exclude=[]):
    if not hasattr(exclude, "__iter__"):
        exclude = [exclude]
    for canvas in reversed(_front):
        c = canvas()
        if c is not None and c not in exclude:
            return c


class CanvasFocusEvent(CanvasPart):
    focused = pyqtSignal(object)
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


class CanvasMouseEvent(CanvasPart):
    """
    Basic keyborad event class of Canvas.
    """
    mousePressed = pyqtSignal(object)
    """
    Emitted when a mouse is pressed.
    """
    mouseReleased = pyqtSignal(object)
    """
    Emitted when a mouse is released.
    """
    mouseMoved = pyqtSignal(object)
    """
    Emitted when a mouse is moved.
    """
    clicked = pyqtSignal(object)
    """
    Emitted when a mouse is clicked.
    """
    doubleClicked = pyqtSignal(object)
    """
    Emitted when a mouse is double-clicked.
    """

    def __init__(self, canvas):
        super().__init__(canvas)
        self.mouseReleased.connect(self._mouseReleased)
        self.doubleClicked.connect(canvas.openModifyWindow)
        self._clicktime = 0
        self._select = _RegionSelector(self, canvas)
        self._line = _LineDrawer(self, canvas)
        self._iline = _InfiniteLineDrawer(self, canvas)
        self._rect = _RectDrawer(self, canvas)
        self._region = _RegionDrawer(self, canvas)
        self._fregion = _FreeRegionDrawer(self, canvas)
        self._cross = _CrosshairDrawer(self, canvas)

    def _mouseReleased(self, e):
        self.clicked.emit(e)
        if time.time() - self._clicktime < 0.3:
            self.doubleClicked.emit(e)
        self._clicktime = time.time()

    def mapPosition(self, event, axis):
        """
        Translate the clicked position to the data-coordinates.

        Args:
            event(QEvent): The event that is given as an argument of mouse events such as mousePressed.
            axis('Left' or 'Right' or 'Top' or 'Bottom'): The axis by which the position is translated.
        """
        raise NotImplementedError(str(type(self)) + " does not implement mapPosition(event, axis) method.")


class _RegionSelector(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self.__select_rect = False
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            self.canvas.clearSelectedRange()
            if self.canvas.toolState() == "Select":
                self.__select_rect = True

    def _mouseMoved(self, e):
        if self.__select_rect:
            end = self.canvas.mapPosition(e, "BottomLeft")
            self.canvas.setSelectedRange([self.__start, end])

    def _mouseReleased(self, e):
        if self.__select_rect and e.button() == Qt.LeftButton:
            self.__select_rect = False


class _LineDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._line = None
        self._busy = False
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "Line":
                self._busy = True

    def _mouseMoved(self, e):
        if self._busy:
            end = self.canvas.mapPosition(e, "BottomLeft")
            if self._line is None:
                self._line = self.canvas.addLineAnnotation([self.__start, end])
            else:
                self._line.setPosition([self.__start, end])

    def _mouseReleased(self, e):
        if self._busy and e.button() == Qt.LeftButton:
            self._busy = False
            self._line = None


class _InfiniteLineDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._line = None
        self._index = 0
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "VLine":
                self._index = 0
                self._line = self.canvas.addInfiniteLineAnnotation(self.__start[0], orientation='vertical')
            if self.canvas.toolState() == "HLine":
                self._index = 1
                self._line = self.canvas.addInfiniteLineAnnotation(self.__start[1], orientation='horizontal')

    def _mouseMoved(self, e):
        end = self.canvas.mapPosition(e, "BottomLeft")
        if self._line is not None:
            self._line.setPosition(end[self._index])

    def _mouseReleased(self, e):
        if self._line is not None and e.button() == Qt.LeftButton:
            self._line = None


class _RectDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._rect = None
        self._busy = False
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "Rect":
                self._busy = True

    def _mouseMoved(self, e):
        if self._busy:
            end = self.canvas.mapPosition(e, "BottomLeft")
            if self._rect is None:
                pos = (self.__start[0] + end[0]) / 2, (self.__start[1] + end[1]) / 2
                size = end[0] - self.__start[0], end[1] - self.__start[1]
                self._rect = self.canvas.addRectAnnotation(pos, size)
            else:
                self._rect.setRegion(np.array([self.__start, end]).T)

    def _mouseReleased(self, e):
        if self._busy and e.button() == Qt.LeftButton:
            self._busy = False
            self._rect = None


class _RegionDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._region = None
        self._busy = False
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "VRegion":
                self._busy = True
                self._orientation = 'vertical'
            elif self.canvas.toolState() == "HRegion":
                self._busy = True
                self._orientation = 'horizontal'

    def _mouseMoved(self, e):
        if self._busy:
            end = self.canvas.mapPosition(e, "BottomLeft")
            if self._orientation == 'vertical':
                region = [self.__start[0], end[0]]
            else:
                region = [self.__start[1], end[1]]
            if self._region is None:
                self._region = self.canvas.addRegionAnnotation(region, orientation=self._orientation)
            else:
                self._region.setRegion(region)

    def _mouseReleased(self, e):
        if self._busy and e.button() == Qt.LeftButton:
            self._busy = False
            self._region = None


class _FreeRegionDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._line = None
        self._busy = False
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "FreeRegion":
                self._busy = True

    def _mouseMoved(self, e):
        if self._busy:
            end = self.canvas.mapPosition(e, "BottomLeft")
            if self._line is None:
                self._line = self.canvas.addFreeRegionAnnotation([self.__start, end])
            else:
                self._line.setRegion([self.__start, end])

    def _mouseReleased(self, e):
        if self._busy and e.button() == Qt.LeftButton:
            self._busy = False
            self._line = None


class _CrosshairDrawer(QObject):
    def __init__(self, parent, canvas):
        super().__init__()
        self.canvas = canvas
        self._line = None
        parent.mousePressed.connect(self._mousePressed)
        parent.mouseReleased.connect(self._mouseReleased)
        parent.mouseMoved.connect(self._mouseMoved)

    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.canvas.mapPosition(e, "BottomLeft")
            if self.canvas.toolState() == "Cross":
                self._line = self.canvas.addCrossAnnotation(self.__start)

    def _mouseMoved(self, e):
        end = self.canvas.mapPosition(e, "BottomLeft")
        if self._line is not None:
            self._line.setPosition(end)

    def _mouseReleased(self, e):
        if self._line is not None and e.button() == Qt.LeftButton:
            self._line = None
