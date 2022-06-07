from lys.Qt import QtCore, QtWidgets, QtGui

from .CanvasBase import CanvasPart, saveCanvas


class CanvasContextMenu(CanvasPart):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.__ag = QtWidgets.QActionGroup(self)
        self._sel = QtWidgets.QAction('Select Range', self, checkable=True, checked=True)
        self._line = QtWidgets.QAction('Draw Line', self, checked=False, checkable=True)
        self._vline = QtWidgets.QAction('Draw Vertical Line', self, checked=False, checkable=True)
        self._hline = QtWidgets.QAction('Draw Horizontal Line', self, checked=False, checkable=True)
        self._rect = QtWidgets.QAction('Draw Rectangle', self, checked=False, checkable=True)
        self._vregion = QtWidgets.QAction('Draw Vertical Region', self, checked=False, checkable=True)
        self._hregion = QtWidgets.QAction('Draw Horizontal Region', self, checked=False, checkable=True)
        self._free = QtWidgets.QAction('Draw Free Region', self, checked=False, checkable=True)
        self._cross = QtWidgets.QAction('Draw Cross', self, checked=False, checkable=True)
        self.__ag.triggered.connect(lambda x: x.setChecked(True))
        canvas.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        canvas.customContextMenuRequested.connect(self._constructContextMenu)

    def _constructContextMenu(self):
        menu = QtWidgets.QMenu()
        menu.addAction(QtWidgets.QAction('Auto scale axes', self, triggered=self.__auto))
        if self.canvas().isRangeSelected():
            m = menu.addMenu('Expand and Shrink')
            m.addAction(QtWidgets.QAction('Expand', self, triggered=lambda: self.__exec('Expand')))
            m.addAction(QtWidgets.QAction('Horizontal Expand', self, triggered=lambda: self.__exec('Horizontal Expand')))
            m.addAction(QtWidgets.QAction('Vertical Expand', self, triggered=lambda: self.__exec('Vertical Expand')))
            m.addAction(QtWidgets.QAction('Shrink', self, triggered=lambda: self.__exec('Shrink')))
            m.addAction(QtWidgets.QAction('Horizontal Shrink', self, triggered=lambda: self.__exec('Horizontal Shrink')))
            m.addAction(QtWidgets.Action('Vertical Shrink', self, triggered=lambda: self.__exec('Vertical Shrink')))

        m = menu.addMenu('Tools')
        m.addAction(self.__ag.addAction(self._sel))
        m.addSeparator()
        m.addAction(self.__ag.addAction(self._line))
        m.addAction(self.__ag.addAction(self._vline))
        m.addAction(self.__ag.addAction(self._hline))
        m.addSeparator()
        m.addAction(self.__ag.addAction(self._rect))
        m.addAction(self.__ag.addAction(self._vregion))
        m.addAction(self.__ag.addAction(self._hregion))
        m.addAction(self.__ag.addAction(self._free))
        m.addSeparator()
        m.addAction(self.__ag.addAction(self._cross))

        menu.addAction(QtWidgets.QAction('Add Text Annotation', self, triggered=self.__addText))

        m = menu.addMenu('Duplicate as')
        m.addAction(QtWidgets.QAction('Matplotlib', self, triggered=lambda: self.__duplicate('matplotlib')))
        m.addAction(QtWidgets.QAction('PyqtGraph', self, triggered=lambda: self.__duplicate('pyqtgraph')))
        menu.exec_(QtGui.QCursor.pos())

    def toolState(self):
        if self._sel.isChecked():
            return "Select"
        elif self._line.isChecked():
            return "Line"
        elif self._vline.isChecked():
            return "VLine"
        elif self._hline.isChecked():
            return "HLine"
        elif self._rect.isChecked():
            return "Rect"
        elif self._vregion.isChecked():
            return "VRegion"
        elif self._hregion.isChecked():
            return "HRegion"
        elif self._free.isChecked():
            return "FreeRegion"
        elif self._cross.isChecked():
            return "Cross"

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

    def __duplicate(self, lib):
        self.canvas().duplicate(lib=lib)
