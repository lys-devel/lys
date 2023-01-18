import numpy as np

from lys import Wave, glb, display, append
from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import ScientificSpinBox, LysSubWindow
from lys.filters import FiltersGUI
from lys.decorators import avoidCircularReference


class _Model(QtCore.QAbstractItemModel):
    def __init__(self, canvas, type):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        canvas.dataChanged.connect(lambda: self.layoutChanged.emit())

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            wave = self.canvas.getWaveData(self.__type)[index.row()]
            if index.column() == 0:
                name = str(value)
                if len(name) != 0:
                    wave.setName(name)
            if index.column() == 2:
                z = int(value)
                wave.setZOrder(z)
        return super().setData(index, value, role)

    def data(self, index, role):
        if not index.isValid() or not role == QtCore.Qt.DisplayRole:
            return
        wave = self.canvas.getWaveData(self.__type)[index.row()]
        if index.column() == 0:
            return wave.getName()
        elif index.column() == 1:
            return wave.getAxis()
        elif index.column() == 2:
            return str(wave.getZOrder())

    def flags(self, index):
        if index.column() in [0, 2]:
            return super().flags(index) | QtCore.Qt.ItemIsEditable
        else:
            return super().flags(index)

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.canvas.getWaveData(self.__type))

    def columnCount(self, parent):
        return 3

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column)
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        header = ["Name", "Axis", "Z order"]
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return header[section]


class _DataSelectionBoxBase(QtWidgets.QTreeView):
    selected = QtCore.pyqtSignal(list)

    def __init__(self, canvas, type):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        self.__initlayout()

    def __initlayout(self):
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.__model = _Model(self.canvas, self.__type)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(lambda: self.selected.emit(self._selectedData()))

    def _selectedData(self):
        list = self.canvas.getWaveData(self.__type)
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QtCore.QSize(150, 100)


class DataSelectionBox(_DataSelectionBoxBase):
    def __init__(self, canvas, dim, type, *args, **kwargs):
        super().__init__(canvas, type, *args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas = canvas
        self.__dim = dim

    def buildContextMenu(self, qPoint):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction('Show', self, triggered=lambda: self.__visible(True)))
        menu.addAction(QtWidgets.QAction('Hide', self, triggered=lambda: self.__visible(False)))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Remove', self, triggered=self.__remove))
        menu.addAction(QtWidgets.QAction('Duplicate', self, triggered=self.__duplicate))
        menu.addAction(QtWidgets.QAction('Z order', self, triggered=self.__zorder))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Process', self, triggered=self.__process))

        raw = menu.addMenu("Raw data")
        raw.addAction(QtWidgets.QAction('Display', self, triggered=lambda: display(*self.__getWaves("Wave"))))
        raw.addAction(QtWidgets.QAction('Append', self, triggered=lambda: self.__append("Wave")))
        raw.addAction(QtWidgets.QAction('Print', self, triggered=lambda: self.__print("Wave")))
        raw.addAction(QtWidgets.QAction('MultiCut', self, triggered=lambda: self.__multicut("Wave")))
        if self.__dim == 3 or self.__dim == "rgb":
            raw.addAction(QtWidgets.QAction('Append as Vector', self, triggered=lambda: self.__append("Wave", vector=True)))
        raw.addAction(QtWidgets.QAction('Edit', self, triggered=lambda: self.__edit("Wave")))
        raw.addAction(QtWidgets.QAction('Export', self, triggered=lambda: self.__export("Wave")))
        if self.__dim == 2:
            raw.addAction(QtWidgets.QAction('Convert to 1D waves', self, triggered=lambda: self.__to1d("Wave")))
        raw.addAction(QtWidgets.QAction('Send to shell', self, triggered=lambda: self.__send("Wave")))

        pr = menu.addMenu("Processed data")
        pr.addAction(QtWidgets.QAction('Display', self, triggered=lambda: display(*self.__getWaves("ProcessedWave"))))
        pr.addAction(QtWidgets.QAction('Append', self, triggered=lambda: self.__append("ProcessedWave")))
        pr.addAction(QtWidgets.QAction('Print', self, triggered=lambda: self.__print("ProcessedWave")))
        pr.addAction(QtWidgets.QAction('MultiCut', self, triggered=lambda: self.__multicut("ProcessedWave")))
        if self.__dim == 3 or self.__dim == "rgb":
            pr.addAction(QtWidgets.QAction('Append as Vector', self, triggered=lambda: self.__append("ProcessedWave", vector=True)))
        pr.addAction(QtWidgets.QAction('Edit', self, triggered=lambda: self.__edit("ProcessedWave")))
        pr.addAction(QtWidgets.QAction('Export', self, triggered=lambda: self.__export("ProcessedWave")))
        if self.__dim == 2:
            pr.addAction(QtWidgets.QAction('Convert to 1D waves', self, triggered=lambda: self.__to1d("ProcessedWave")))
        pr.addAction(QtWidgets.QAction('Send to shell', self, triggered=lambda: self.__send("ProcessedWave")))
        menu.exec_(QtGui.QCursor.pos())

    def __getWaves(self, type="Wave"):
        res = []
        for d in self._selectedData():
            if type == "Wave":
                res.append(d.getWave())
            else:
                res.append(d.getFilteredWave())
        return res

    def __visible(self, visible):
        for d in self._selectedData():
            d.setVisible(visible)

    def __remove(self):
        for d in self._selectedData():
            self.canvas.Remove(d)

    def __append(self, type, **kwargs):
        append(*self.__getWaves(type), exclude=self.canvas, **kwargs)

    def __duplicate(self):
        for d in self._selectedData():
            self.canvas.Append(d)

    def __multicut(self, type):
        from lys import MultiCut
        for d in self.__getWaves(type):
            MultiCut(d)

    def __edit(self, type):
        from lys import Table
        t = Table()
        for d in self.__getWaves(type):
            t.Append(d)

    def __print(self, type):
        for d in self.__getWaves(type):
            print(d)

    def __process(self):
        data = self._selectedData()
        dlg = FiltersDialog(data[0].getWave().data.ndim)
        for d in data:
            dlg.applied.connect(d.setFilter)
        if data[0].getFilter() is not None:
            dlg.setFilter(data[0].getFilter())
        dlg.show()

    def __export(self, waveType):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            d = self.__getWaves(waveType)[0]
            d.export(path, type=type)

    def __to1d(self, waveType):
        d = self.__getWaves(waveType)[0]
        w = d.duplicate()
        dialog = _SliceDialog(w, self)
        result = dialog.exec_()
        if result:
            axis, n = dialog.getParams()
            result = []
            for i in range(n):
                if axis == "y":
                    index = int(w.data.shape[0] / n * i)
                    result.append(Wave(w.data[index, :], w.y))
                else:
                    index = int(w.data.shape[1] / n * i)
                    result.append(Wave(w.data[:, index], w.x))
        display(*result)

    def __send(self, waveType):
        dat = self._selectedData()[0]
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=dat.getName())
        if ok:
            w = self.__getWaves(waveType)[0].duplicate()
            w.name = text
            glb.shell().addObject(w, text)

    def __zorder(self):
        data = self._selectedData()
        d = _ZOrderDialog(np.min([item.getZOrder() for item in data]))
        if d.exec_():
            fr, step = d.getParams()
            for i, item in enumerate(data):
                item.setZOrder(fr + step * i)


class FiltersDialog(LysSubWindow):
    applied = QtCore.pyqtSignal(object)

    def __init__(self, dim):
        super().__init__()
        self.filters = FiltersGUI(dim, parent=self)

        self.ok = QtWidgets.QPushButton("O K", clicked=self._ok)
        self.cancel = QtWidgets.QPushButton("CANCEL", clicked=self._cancel)
        self.apply = QtWidgets.QPushButton("Apply", clicked=self._apply)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.ok)
        h1.addWidget(self.cancel)
        h1.addWidget(self.apply)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(h1)
        w = QtWidgets.QWidget()
        w.setLayout(layout)
        self.setWidget(w)
        self.resize(500, 500)

    def _ok(self):
        self.ok = True
        self.applied.emit(self.filters.GetFilters())
        self.close()

    def _cancel(self):
        self.ok = False
        self.close()

    def _apply(self):
        self.applied.emit(self.filters.GetFilters())

    def setFilter(self, filt):
        self.filters.setFilters(filt)


class _ZOrderDialog(QtWidgets.QDialog):
    def __init__(self, init, parent=None):
        super().__init__(parent)
        self._from = QtWidgets.QSpinBox()
        self._from.setRange(0, 1000000)
        self._from.setValue(init)
        self._delta = QtWidgets.QSpinBox()
        self._delta.setRange(0, 1000000)
        self._delta.setValue(1)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("From"), 0, 0)
        g.addWidget(self._from, 1, 0)
        g.addWidget(QtWidgets.QLabel("Delta"), 0, 1)
        g.addWidget(self._delta, 1, 1)

        g.addWidget(QtWidgets.QPushButton("O K", clicked=self.accept), 2, 0)
        g.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject), 2, 1)

        self.setLayout(g)

    def getParams(self):
        return self._from.value(), self._delta.value()


class _SliceDialog(QtWidgets.QDialog):
    def __init__(self, wave, parent=None):
        super().__init__(parent)
        self.wave = wave
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(["x", "y"])
        self.combo.currentTextChanged.connect(self._update)

        self.slice = QtWidgets.QSpinBox()
        self.slice.setRange(0, 10000)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Cut along"), 0, 0)
        g.addWidget(self.combo, 0, 1)
        g.addWidget(QtWidgets.QLabel("Num. of slices"), 1, 0)
        g.addWidget(self.slice, 1, 1)
        g.addWidget(QtWidgets.QPushButton('O K', clicked=self.accept), 2, 0)
        g.addWidget(QtWidgets.QPushButton('CALCEL', clicked=self.reject), 2, 1)

        self.setLayout(g)
        self._update("x")

    def _update(self, txt):
        if txt == "x":
            self.slice.setValue(self.wave.data.shape[1])
        else:
            self.slice.setValue(self.wave.data.shape[0])

    def getParams(self):
        return self.combo.currentText(), self.slice.value()


class OffsetAdjustBox(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.__initlayout()

    def __initlayout(self):
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.__offsetBox())
        vbox.addWidget(self.__sideBySideBox())
        self.setLayout(vbox)
        self.__setEnabled(False)

    def __offsetBox(self):
        self.__spin1 = ScientificSpinBox()
        self.__spin2 = ScientificSpinBox()
        self.__spin3 = ScientificSpinBox()
        self.__spin4 = ScientificSpinBox()
        self.__spin1.valueChanged.connect(lambda: self.__dataChanged('x offset'))
        self.__spin2.valueChanged.connect(lambda: self.__dataChanged('y offset'))
        self.__spin3.valueChanged.connect(lambda: self.__dataChanged('x muloffset'))
        self.__spin4.valueChanged.connect(lambda: self.__dataChanged('y muloffset'))
        gl = QtWidgets.QGridLayout()
        gl.addWidget(QtWidgets.QLabel('x offset'), 0, 0)
        gl.addWidget(QtWidgets.QLabel('y offset'), 0, 1)
        gl.addWidget(QtWidgets.QLabel('x muloffset'), 2, 0)
        gl.addWidget(QtWidgets.QLabel('y muloffset'), 2, 1)
        gl.addWidget(self.__spin1, 1, 0)
        gl.addWidget(self.__spin3, 3, 0)
        gl.addWidget(self.__spin2, 1, 1)
        gl.addWidget(self.__spin4, 3, 1)
        gr1 = QtWidgets.QGroupBox('Offset')
        gr1.setLayout(gl)
        return gr1

    def __sideBySideBox(self):
        self.__spinfrom = ScientificSpinBox()
        self.__spindelta = ScientificSpinBox()
        self.__set = QtWidgets.QPushButton('Set', clicked=self.__sidebyside)
        self.__type = QtWidgets.QComboBox()
        self.__type.addItems(['y offset', 'x offset', 'y muloffset', 'x muloffset'])

        g2 = QtWidgets.QGridLayout()
        g2.addWidget(QtWidgets.QLabel('from'), 0, 0)
        g2.addWidget(self.__spinfrom, 1, 0)
        g2.addWidget(QtWidgets.QLabel('delta'), 0, 1)
        g2.addWidget(self.__spindelta, 1, 1)
        g2.addWidget(QtWidgets.QLabel('type'), 0, 2)
        g2.addWidget(self.__type, 1, 2)
        g2.addWidget(self.__set, 2, 1)

        gr2 = QtWidgets.QGroupBox('Side by side')
        gr2.setLayout(g2)
        return gr2

    def __sidebyside(self):
        f = self.__spinfrom.value()
        delta = self.__spindelta.value()
        for i, d in enumerate(self._data):
            r = list(d.getOffset())
            if self.__type.currentText() == 'x offset':
                r[0] = f + delta * i
            if self.__type.currentText() == 'y offset':
                r[1] = f + delta * i
            if self.__type.currentText() == 'x muloffset':
                r[2] = f + delta * i
            if self.__type.currentText() == 'y muloffset':
                r[3] = f + delta * i
            d.setOffset(r)

    @avoidCircularReference
    def __dataChanged(self, type):
        for d in self._data:
            r = list(d.getOffset())
            if type == 'x offset':
                r[0] = self.__spin1.value()
            if type == 'y offset':
                r[1] = self.__spin2.value()
            if type == 'x muloffset':
                r[2] = self.__spin3.value()
            if type == 'y muloffset':
                r[3] = self.__spin4.value()
            d.setOffset(r)

    def __setEnabled(self, b):
        self.__spin1.setEnabled(b)
        self.__spin2.setEnabled(b)
        self.__spin3.setEnabled(b)
        self.__spin4.setEnabled(b)
        self.__spinfrom.setEnabled(b)
        self.__spindelta.setEnabled(b)
        self.__type.setEnabled(b)
        self.__set.setEnabled(b)

    @avoidCircularReference
    def setData(self, data):
        self._data = data
        if len(data) != 0:
            self.__setEnabled(True)
            off = data[0].getOffset()
            self.__spin1.setValue(off[0])
            self.__spin2.setValue(off[1])
            self.__spin3.setValue(off[2])
            self.__spin4.setValue(off[3])
        else:
            self.__setEnabled(False)
