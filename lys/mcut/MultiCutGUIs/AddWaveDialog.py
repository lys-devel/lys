from lys import filters
from lys.Qt import QtWidgets, QtCore


class _singleAxisWidget(QtWidgets.QFrame):
    def __init__(self, dim, lines, init):
        super().__init__()
        self.__initlayout(dim, lines, init)

    def __initlayout(self, dim, lines, init):
        self._btns = [QtWidgets.QRadioButton(str(d + 1)) for d in range(dim)]
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
        return self.__name.text()

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


class AddWaveDialog(QtWidgets.QDialog):
    _index = 0

    def __init__(self, parent, cui):
        super().__init__(parent)
        self.setWindowTitle("Add new data")
        self._cui = cui
        self.__initlayout()

    def __initlayout(self):
        self._ax = _waveWidget(self._cui.getFilteredWave().ndim, self._cui.getFreeLines(), name="data" + str(AddWaveDialog._index + 1))
        self._canvas = _canvasWidget()
        self._filt = filters.FiltersGUI(min(self._cui.getFilteredWave().ndim, 2))
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

    def getName(self):
        return self._ax.getName()

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
        AddWaveDialog._index += 1
        self.accept()
