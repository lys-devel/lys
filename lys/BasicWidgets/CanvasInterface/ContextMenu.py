from LysQt.QtCore import Qt
from LysQt.QtWidgets import QMenu, QAction, QActionGroup
from LysQt.QtGui import QCursor

from .CanvasBase import CanvasPart, saveCanvas


class CanvasContextMenu(CanvasPart):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.__ag = QActionGroup(self)
        self._sel = QAction('Select Range', self, checkable=True, checked=True)
        self._line = QAction('Draw Line', self, checked=False, checkable=True)
        self._rect = QAction('Draw Rectangle', self, checked=False, checkable=True)
        self.__ag.triggered.connect(lambda x: x.setChecked(True))
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
        m.addAction(self.__ag.addAction(self._sel))
        m.addSeparator()
        m.addAction(self.__ag.addAction(self._line))
        m.addAction(self.__ag.addAction(self._rect))

        menu.addAction(QAction('Add Text', self, triggered=self.__addText))
        menu.exec_(QCursor.pos())

    def toolState(self):
        if self._sel.isChecked():
            return "Select"
        elif self._line.isChecked():
            return "Line"
        elif self._rect.isChecked():
            return "Rect"

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

    def __addText(self):
        self.canvas().addText("text")
        mod = self.canvas().openModifyWindow()
        mod.selectTab("Annot.")
