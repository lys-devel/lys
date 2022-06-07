from lys import Wave, glb
from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import ScientificSpinBox


class _Model(QtGui.QStandardItemModel):
    def __init__(self, canvas):
        super().__init__(0, 3)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Line')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Axis')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Zorder')
        self.canvas = canvas

    def clear(self):
        super().clear()
        self.setColumnCount(3)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Line')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Axis')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Zorder')

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def mimeData(self, indexes):
        mimedata = QtCore.QMimeData()
        data = []
        for i in indexes:
            if i.column() != 2:
                continue
            t = eval(self.itemFromIndex(i).text())
            data.append(t)
        mimedata.setData('index', str(data).encode('utf-8'))
        mimedata.setText(str(data))
        return mimedata

    def mimeTypes(self):
        return ['index']

    def dropMimeData(self, data, action, row, column, parent):
        f = eval(data.text())
        par = self.itemFromIndex(parent)
        if par is None:
            if row == -1 and column == -1:
                self.canvas.moveItem(f)
            else:
                self.canvas.moveItem(f, self.item(row, 2).text())
        else:
            self.canvas.moveItem(f, self.item(self.itemFromIndex(parent).row(), 2).text())
        return False


class _DataSelectionBoxBase(QtWidgets.QTreeView):
    selected = QtCore.pyqtSignal(list)

    def __init__(self, canvas, dim, type):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        self.__initlayout()
        self.flg = False
        self._loadstate()
        canvas.dataChanged.connect(self._loadstate)

    def __initlayout(self):
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model = _Model(self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self._onSelected)

    def _loadstate(self):
        self.flg = True
        selected = self._selectedData()
        list = self.canvas.getWaveData(self.__type)
        self.__model.clear()
        for i, data in enumerate(list):
            self.__model.setItem(i, 0, QtGui.QStandardItem(data.getWave().name))
            self.__model.setItem(i, 1, QtGui.QStandardItem(data.getAxis()))
            self.__model.setItem(i, 2, QtGui.QStandardItem(str(data.getZOrder())))
            if data in selected:
                index = self.__model.item(i).index()
                self.selectionModel().select(index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
        self.flg = False

    def _onSelected(self):
        if self.flg:
            return
        self.flg = True
        self.selected.emit(self._selectedData())
        self.flg = False

    def _selectedData(self):
        list = self.canvas.getWaveData(self.__type)
        if len(list) != self.__model.rowCount():
            return []
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QtCore.QSize(150, 100)


class DataSelectionBox(_DataSelectionBoxBase):
    def __init__(self, canvas, dim, type, *args, **kwargs):
        super().__init__(canvas, dim, type, *args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas = canvas
        self.__dim = dim

    def buildContextMenu(self, qPoint):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction('Show', self, triggered=lambda: self.__visible(True)))
        menu.addAction(QtWidgets.QAction('Hide', self, triggered=lambda: self.__visible(False)))
        menu.addAction(QtWidgets.QAction('Remove', self, triggered=self.__remove))
        menu.addAction(QtWidgets.QAction('Duplicate', self, triggered=self.__duplicate))
        menu.addAction(QtWidgets.QAction('Process', self, triggered=self.__process))

        raw = menu.addMenu("Raw data")
        raw.addAction(QtWidgets.QAction('Display', self, triggered=lambda: self.__display("Wave")))
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
        pr.addAction(QtWidgets.QAction('Display', self, triggered=lambda: self.__display("ProcessedWave")))
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

    def __display(self, type, **kwargs):
        from lys import display
        display(*self.__getWaves(type), **kwargs)

    def __append(self, type, **kwargs):
        from lys import append
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
        from lys.filters import FiltersDialog
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
        from lys import display
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
        d = self.__getWaves(waveType)[0]
        w = d.duplicate()
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            w.name = text
            glb.shell().addObject(w, text)


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
        self.__flg = False

    def __initlayout(self):
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.__offsetBox())
        vbox.addWidget(self.__sideBySideBox())
        self.setLayout(vbox)

    def __offsetBox(self):
        self.__spin1 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('x offset'))
        self.__spin2 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('y offset'))
        self.__spin3 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('x muloffset'))
        self.__spin4 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('y muloffset'))
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
        btn = QtWidgets.QPushButton('Set', clicked=self.__sidebyside)
        self.__type = QtWidgets.QComboBox()
        self.__type.addItems(['y offset', 'x offset', 'y muloffset', 'x muloffset'])

        g2 = QtWidgets.QGridLayout()
        g2.addWidget(QtWidgets.QLabel('from'), 0, 0)
        g2.addWidget(self.__spinfrom, 1, 0)
        g2.addWidget(QtWidgets.QLabel('delta'), 0, 1)
        g2.addWidget(self.__spindelta, 1, 1)
        g2.addWidget(QtWidgets.QLabel('type'), 0, 2)
        g2.addWidget(self.__type, 1, 2)
        g2.addWidget(btn, 2, 1)

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

    def __dataChanged(self, type):
        if not self.__flg:
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

    def setData(self, data):
        self._data = data
        self.__flg = True
        if len(data) != 0:
            off = data[0].getOffset()
            self.__spin1.setValue(off[0])
            self.__spin2.setValue(off[1])
            self.__spin3.setValue(off[2])
            self.__spin4.setValue(off[3])
        self.__flg = False
