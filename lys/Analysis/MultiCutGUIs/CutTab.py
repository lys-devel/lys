import numpy as np

from lys import Wave, frontCanvas, filters
from lys.Qt import QtWidgets, QtCore

from .CanvasManager import CanvasManager
from .WaveManager import ChildWavesGUI
from .AxesManager import AxesRangeWidget, FreeLinesWidget


class _axisLayout(QtWidgets.QWidget):
    def __init__(self, dim):
        super().__init__()
        self.__initlayout(dim)
        self._lineids = {}

    def __initlayout(self, dim):
        self._btn1 = [QtWidgets.QRadioButton(str(d)) for d in range(dim)]
        self._btn1.append(QtWidgets.QRadioButton("Line"))

        self._btn2 = [QtWidgets.QRadioButton(str(d)) for d in range(dim)]
        self._btn2.insert(0, QtWidgets.QRadioButton("None"))
        self._btn2.append(QtWidgets.QRadioButton("Line"))

        self.grp1 = QtWidgets.QButtonGroup(self)
        self.grp2 = QtWidgets.QButtonGroup(self)
        for b in self._btn1:
            self.grp1.addButton(b)
        for b in self._btn2:
            self.grp2.addButton(b)

        self._cmb1 = QtWidgets.QComboBox()
        self._cmb2 = QtWidgets.QComboBox()

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("1st Axis"), 0, 0)
        layout.addWidget(QtWidgets.QLabel("2nd Axis"), 1, 0)
        for i, b in enumerate(self._btn1):
            layout.addWidget(b, 0, i + 2)
        layout.addWidget(self._cmb1, 0, len(self._btn1) + 2)
        for i, b in enumerate(self._btn2):
            layout.addWidget(b, 1, i + 1)
        layout.addWidget(self._cmb2, 1, len(self._btn2) + 1)
        self.setLayout(layout)

    def updateLines(self, lines):
        for c in [self._cmb1, self._cmb2]:
            old = c.currentText()
            for i in range(c.count()):
                c.removeItem(0)
            for i, l in enumerate(lines):
                c.addItem(l.getName())
                if l.getName() == old:
                    c.setCurrentIndex(i)

    def getAxes(self):
        ax1 = self._btn1.index(self.grp1.checkedButton())
        ax2 = self._btn2.index(self.grp2.checkedButton()) - 1
        if ax1 == len(self._btn1) - 1:
            ax1 = self._cmb1.currentText()
        if ax2 == len(self._btn2) - 2:
            ax2 = self._cmb2.currentText()
        if ax2 == -1:
            return (ax1,)
        else:
            return (ax1, ax2)


class _singleAxisWidget(QtWidgets.QFrame):
    def __init__(self, dim, lines, init):
        super().__init__()
        self.__initlayout(dim, lines, init)

    def __initlayout(self, dim, lines, init):
        self._btns = [QtWidgets.QRadioButton(str(d)) for d in range(dim)]
        self._btns.append(QtWidgets.QRadioButton("Line"))
        self._btns[init].setChecked(True)
        self._cmb = QtWidgets.QComboBox()
        self._cmb.addItems([line.getName() for line in lines])

        if len(lines) == 0:
            self._btns[dim].setEnabled(False)
            self._cmb.setEnabled(False)

        lay = QtWidgets.QHBoxLayout()
        for b in self._btns:
            lay.addWidget(b)
        lay.addWidget(self._cmb)
        lay.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay)

    def getAxis(self):
        res = -1
        for i, btn in enumerate(self._btns):
            if btn.isChecked():
                res = i
        if res == len(self._btns) - 1:
            res = self._cmb.currentText()
        return res


class _waveWidget(QtWidgets.QGroupBox):
    dimensionChanged = QtCore.pyqtSignal(int)

    def __init__(self, dim, lines, name=None):
        super().__init__("Data")
        self._dim = dim
        self.__initlayout(dim, lines, name)

    def __initlayout(self, dim, lines, name):
        self.__name = QtWidgets.QLineEdit()
        if name is not None:
            self.__name.setText(name)
        self.__labels = [QtWidgets.QLabel("Axis" + str(d + 1)) for d in range(dim)]
        self.__axes = [_singleAxisWidget(dim, lines, d) for d in range(dim)]
        self.__size = QtWidgets.QSpinBox(valueChanged=self._changeSize)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Name"), 0, 0)
        grid.addWidget(self.__name, 0, 1)
        grid.addWidget(QtWidgets.QLabel("Dimension"), 0, 2)
        grid.addWidget(self.__size, 0, 3)
        for d in range(dim):
            grid.addWidget(self.__labels[d], d + 1, 0)
            grid.addWidget(self.__axes[d], d + 1, 1, 1, 3)
        self.setLayout(grid)
        self.__size.setValue(2)
        self.__size.setRange(1, dim)

    def _changeSize(self, value):
        for d in range(self._dim):
            if value > d:
                self.__labels[d].show()
                self.__axes[d].show()
            else:
                self.__labels[d].hide()
                self.__axes[d].hide()
        self.dimensionChanged.emit(value)
        self.adjustSize()

    def getName(self):
        return self.__name

    def getAxes(self):
        return tuple([self.__axes[d].getAxis() for d in range(self.__size.value())])

    def getDimension(self):
        return self.__size.value()


class _canvasWidget(QtWidgets.QGroupBox):
    def __init__(self):
        super().__init__("Display generated data")
        self.setCheckable(True)
        self.__initlayout()

    def __initlayout(self):
        self.__grid = QtWidgets.QRadioButton("In the grid")
        self.__grid.setChecked(True)
        self.__graph = QtWidgets.QRadioButton("As a new graph")

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.__grid)
        h1.addWidget(self.__graph)

        self.setLayout(h1)

    def getDisplayMode(self):
        if self.isChecked():
            if self.__grid.isChecked():
                return "grid"
            else:
                return "graph"


class _gridTableWidget(QtWidgets.QTableWidget):
    def __init__(self, size, parent=None):
        super().__init__(parent)
        self.size = size
        self.setRowCount(size)
        self.setColumnCount(size)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def getGridPos(self):
        rows = [i.row() for i in self.selectionModel().selectedIndexes()]
        columns = [i.column() for i in self.selectionModel().selectedIndexes()]
        if len(rows) * len(columns) == 0:
            return (0, 0), (self.size, self.size)
        return (np.min(rows), np.min(columns)), (np.max(rows) - np.min(rows) + 1, np.max(columns) - np.min(columns) + 1)


class _AddWaveDialog(QtWidgets.QDialog):
    _index = 0

    def __init__(self, parent, cui):
        super().__init__(parent)
        self.setWindowTitle("Add new data")
        self._cui = cui
        self.__initlayout()

    def __initlayout(self):
        self._ax = _waveWidget(self._cui.getFilteredWave().ndim, self._cui.getFreeLines(), name="data" + str(self._index + 1))
        self._canvas = _canvasWidget()
        self._filt = filters.FiltersGUI(2)
        self._ax.dimensionChanged.connect(lambda x: self._canvas.setEnabled(x < 3))
        self._ax.dimensionChanged.connect(self._filt.clear)
        self._ax.dimensionChanged.connect(self._filt.setDimension)

        self.__postButton = QtWidgets.QPushButton("Post-process >>", clicked=self._post)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton("O K", clicked=self._ok))
        h1.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject))
        h1.addWidget(self.__postButton)

        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(self._ax)
        v1.addWidget(self._canvas)
        v1.addStretch()
        v1.addLayout(h1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(v1, 1)
        layout.addWidget(self._filt, 2)
        self._filt.hide()

        self.setLayout(layout)

    def _post(self):
        if self._filt.isVisible():
            self._filt.hide()
            self.__postButton.setText("Post-process >>")
        else:
            self._filt.show()
            self.__postButton.setText("Post-process <<")
        self.adjustSize()

    def getFilter(self):
        filt = self._filt.getFilters()
        if filt.isEmpty():
            return None
        else:
            return filt

    def getAxes(self):
        return self._ax.getAxes()

    def getDisplayMode(self):
        return self._canvas.getDisplayMode()

    def _ok(self):
        # Check dimension of data
        filt = self._filt.getFilters()
        if self._ax.getDimension() + filt.getRelativeDimension() > 2:
            return QtWidgets.QMessageBox.information(self, "Caution", "The data dimension should be 1 or 2 (after post-process).", QtWidgets.QMessageBox.Yes)

        # Check if identical data exists
        ax = self._ax.getAxes()
        same_type = [w for w in self._cui.getChildWaves() if tuple(w.getAxes()) == tuple(ax) and w.postProcess() is None]
        if len(same_type) != 0 and filt.isEmpty():
            msgBox = QtWidgets.QMessageBox(parent=self, text="There is a wave that has the same axes and no post-process. Do you really want to proceed anyway?")
            msgBox.addButton(QtWidgets.QMessageBox.Yes)
            no = msgBox.addButton(QtWidgets.QMessageBox.No)
            msgBox.exec_()
            if msgBox.clickedButton() == no:
                return
        self.accept()


class CutTab(QtWidgets.QTabWidget):
    def __init__(self, cui, grid):
        super().__init__()
        self._cui = cui
        self.grid = grid
        self._can = CanvasManager(cui)

        self.__initlayout__()
        self.__resetLayout(init=True)
        self._cui.dimensionChanged.connect(lambda: self.__resetLayout())

    def __initlayout__(self):
        self.wlist = ChildWavesGUI(self._cui, self.display)
        self._table = _gridTableWidget(4)
        self._usegraph = QtWidgets.QCheckBox("Use Graph")
        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(self._usegraph)
        v1.addWidget(self._table)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.wlist, 2)
        h1.addLayout(v1, 1)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QPushButton("Add", clicked=self._add))
        hbox.addWidget(QtWidgets.QPushButton("Make", clicked=self.make))
        hbox.addWidget(QtWidgets.QPushButton("Display", clicked=self.display))
        hbox.addWidget(QtWidgets.QPushButton("Typical", clicked=self.typical))

        self._make = QtWidgets.QVBoxLayout()
        self._make.addLayout(h1)
        self._make.addLayout(hbox)

        make = QtWidgets.QGroupBox("Data")
        make.setLayout(self._make)

        self._int = self._can.widget()

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(make, 1)
        self.layout.addWidget(self._int, 1)
        self.layout.addStretch()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)

        self.addTab(w, "Main")
        self.addTab(AxesRangeWidget(self._cui), "Range")
        self.addTab(FreeLinesWidget(self._cui), "Lines")

    def __resetLayout(self, init=False):
        if not init:
            self._make.removeWidget(self._ax)
            self._ax.deleteLater()
        self._ax = _axisLayout(self._cui.getFilteredWave().ndim)
        self._make.insertWidget(1, self._ax)
        self._cui.freeLineChanged.connect(lambda: self._ax.updateLines(self._cui.getFreeLines()))
        self.adjustSize()

    def make(self, axes=None, useold=False):
        ax = axes if hasattr(axes, "__iter__") else self._ax.getAxes()
        same_type = [w for w in self._cui.getChildWaves() if tuple(w.getAxes()) == tuple(ax)]
        if len(same_type) != 0:
            msgBox = QtWidgets.QMessageBox(parent=self, text="There is a wave that has the same axes. Do you really want to proceed anyway?")
            msgBox.addButton(QtWidgets.QMessageBox.Yes)
            no = msgBox.addButton(QtWidgets.QMessageBox.No)
            if useold:
                old = msgBox.addButton("Use old one", QtWidgets.QMessageBox.ActionRole)
            msgBox.exec_()
            if msgBox.clickedButton() == no:
                return
            elif msgBox.clickedButton() == old:
                return same_type[0].getFilteredWave()
        return self._cui.addWave(ax)

    def display(self, wave=None, axes=None, pos=None, wid=None):
        ax = axes if hasattr(axes, "__iter__") else self._ax.getAxes()
        w = wave if isinstance(wave, Wave) else self.make(axes, useold=True)
        if w is None:
            return

        if self._usegraph.isChecked():
            c = self._can.createCanvas(ax, graph=True)
        else:
            if pos is None or wid is None:
                pos, wid = self._table.getGridPos()
            if self.grid.itemAtPosition(*pos) is not None:
                msgBox = QtWidgets.QMessageBox(parent=self, text="There is a graph at this position. Do you really want to proceed?")
                msgBox.addButton(QtWidgets.QMessageBox.Yes)
                no = msgBox.addButton(QtWidgets.QMessageBox.No)
                graph = msgBox.addButton("Use Graph", QtWidgets.QMessageBox.ActionRole)
                msgBox.exec_()
                if msgBox.clickedButton() == no:
                    return
                elif msgBox.clickedButton() == graph:
                    self._usegraph.setChecked(True)
                    return self.display(w, axes, pos, wid)
            c = self._can.createCanvas(ax, lib="pyqtgraph")
            self.grid.append(c, pos, wid)
        c.clicked.connect(self._gridClicked)
        c.Append(w)
        return c

    def display2(self, wave, axes, type="grid", pos=None, wid=None):
        if type == "graph":
            c = self._can.createCanvas(axes, graph=True)
        else:
            c = self._can.createCanvas(axes, lib="pyqtgraph")
            self.grid.append(c, pos, wid)
        c.Append(wave)
        return c

    def _add(self):
        d = _AddWaveDialog(self, self._cui)
        if d.exec_():
            w = self._cui.addWave(d.getAxes(), d.getFilter())
            if d.getDisplayMode() is not None:
                self.display2(w, d.getAxes(), type=d.getDisplayMode())

    def _gridClicked(self):
        canvas = frontCanvas()
        b = False
        for i in range(4):
            for j in range(4):
                if self.grid.itemAtPosition(i, j) == canvas:
                    self._table.setCurrentCell(i, j, QtCore.QItemSelectionModel.Select)
                    b = True
                else:
                    self._table.setCurrentCell(i, j, QtCore.QItemSelectionModel.Deselect)
        self._usegraph.setChecked(not b)

    def typical(self):
        dim = self._cui.getFilteredWave().ndim
        if dim == 2:
            self.typical2d()
        if dim == 3:
            self.typical3d()
        if dim == 4:
            self.typical4d()
        if dim == 5:
            self.typical5d()

    def typical2d(self):
        self.display(axes=[0, 1], pos=[0, 0], wid=[4, 4])

    def typical3d(self):
        c1 = self.display(axes=[2], pos=[3, 0], wid=[1, 4])
        c2 = self.display(axes=[0, 1], pos=[0, 0], wid=[3, 4])
        self._can.addLine(c1, orientation="vertical")
        self._can.addRect(c2)

    def typical4d(self):
        c1 = self.display(axes=[0, 1], pos=[0, 0], wid=[4, 2])
        c2 = self.display(axes=[2, 3], pos=[0, 2], wid=[4, 2])
        self._can.AddRect(c1)
        self._can.AddRect(c2)

    def typical5d(self):
        c1 = self.display(axes=[0, 1], pos=[0, 0], wid=[3, 2])
        c2 = self.display(axes=[2, 3], pos=[0, 2], wid=[3, 2])
        c3 = self.display(axes=(4,), pos=[3, 0], wid=[1, 4])
        self._can.addRect(c1)
        self._can.addRect(c2)
        self._can.addLine(c3, orientation="vertical")
