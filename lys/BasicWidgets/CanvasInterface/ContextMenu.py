from LysQt.QtCore import Qt
from LysQt.QtWidgets import QMenu, QAction
from LysQt.QtGui import QCursor

from .CanvasBase import CanvasPart, saveCanvas


class CanvasContextMenu(CanvasPart):
    def __init__(self, canvas):
        super().__init__(canvas)
        canvas.setContextMenuPolicy(Qt.CustomContextMenu)
        canvas.customContextMenuRequested.connect(self._constructContextMenu)

    def _constructContextMenu(self):
        menu = QMenu()
        menu.addAction(QAction('Auto scale axes', self, triggered=self.__auto))
        if self.canvas().isRangeSelected():
            m = menu.addMenu('Expand and Shrink')
            m.addAction(QAction('Expand', self, triggered=lambda: self.__exec('Expand')))
            m.addAction(QAction('Horizontal Expand', self, triggered=lambda: self.__exec('Horizontal Expand')))
            m.addAction(QAction('Vertical Expand', self, triggered=lambda: self.__exec('Vertical Expand')))
            m.addAction(QAction('Shrink', self, triggered=lambda: self.__exec('Shrink')))
            m.addAction(QAction('Horizontal Shrink', self, triggered=lambda: self.__exec('Horizontal Shrink')))
            m.addAction(QAction('Vertical Shrink', self, triggered=lambda: self.__exec('Vertical Shrink')))

        m = menu.addMenu('Tools')
        m.addAction(QAction('Select Range', self))
        m.addAction(QAction('Draw Line', self))
        m.addAction(QAction('Draw Rectangle', self))
        menu.exec_(QCursor.pos())

    @saveCanvas
    def __exec(self, text):
        for axis in self.canvas().axisList():
            self.__ExpandAndShrink(text, axis)
        self.canvas().clearSelectedRange()

    def __ExpandAndShrink(self, mode, axis):
        pos, pos2 = self.canvas().selectedRange()
        size = pos2[0] - pos[0], pos2[1] - pos[1]
        ran = self.canvas().getAxisRange(axis)
        if axis in ['Bottom', 'Top'] and 'Vertical' not in mode:
            i = 0
        elif axis in ['Left', 'Right'] and 'Horizontal' not in mode:
            i = 1
        else:
            return
        minVal, maxVal = min(pos[i], pos[i] + size[i]), max(pos[i], pos[i] + size[i])
        if ran[1] < ran[0]:
            minVal, maxVal = maxVal, minVal
        if 'Shrink' in mode:
            ratio = abs((ran[1] - ran[0]) / size[i])
            minVal = ran[0] - ratio * (minVal - ran[0])
            maxVal = ran[1] + ratio * (ran[1] - maxVal)
        self.canvas().setAxisRange(axis, [minVal, maxVal])

    @saveCanvas
    def __auto(self, *args, **kwargs):
        for axis in self.canvas().axisList():
            self.canvas().setAutoScaleAxis(axis)
        self.canvas().clearSelectedRange()