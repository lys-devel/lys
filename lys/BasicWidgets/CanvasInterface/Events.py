import time

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
        if e.key() == Qt.Key_A:
            for i in self.canvas().getRGBs() + self.canvas().getImages():
                i.setColorRange()


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
            self.canvas.setSelectedRange([self.__start, self.__start])
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
