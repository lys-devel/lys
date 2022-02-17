import time

from LysQt.QtGui import QKeyEvent, QMouseEvent
from LysQt.QtCore import pyqtSignal, Qt
from .CanvasBase import CanvasPart, saveCanvas


class CanvasKeyboardEvent(CanvasPart):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.keyPressed.connect(self._keyPressed)

    @saveCanvas
    def _keyPressed(self, e):
        if e.key() == Qt.Key_A:
            for i in self.canvas().getRGBs() + self.canvas().getImages():
                i.setColorRange()


class CanvasMouseEvent(CanvasPart):
    mousePressed = pyqtSignal(object)
    mouseReleased = pyqtSignal(object)
    mouseMoved = pyqtSignal(object)
    clicked = pyqtSignal(object)
    doubleClicked = pyqtSignal(object)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.mousePressed.connect(self._mousePressed)
        self.mouseReleased.connect(self._mouseReleased)
        self.mouseMoved.connect(self._mouseMoved)
        self.__select_rect = False
        self._clicktime = 0

    @saveCanvas
    def _mousePressed(self, e):
        if e.button() == Qt.LeftButton:
            self.__start = self.mapPosition(e, "BottomLeft")
            self.canvas().setSelectedRange([self.__start, self.__start])
            self.__select_rect = True

    @saveCanvas
    def _mouseMoved(self, e):
        if self.__select_rect:
            end = self.mapPosition(e, "BottomLeft")
            self.canvas().setSelectedRange([self.__start, end])

    @saveCanvas
    def _mouseReleased(self, e):
        if self.__select_rect and e.button() == Qt.LeftButton:
            self.__select_rect = False
        self.clicked.emit(e)
        if time.time() - self._clicktime < 0.3:
            self.doubleClicked.emit(e)
        self._clicktime = time.time()

    def mapPosition(self, event, axis):
        pass
