import numpy as np

from lys import Wave, display3D, append3D
from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import LysSubWindow
from lys.filters import FiltersGUI
from lys.errors import suppressLysWarnings
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
        return super().setData(index, value, role)

    def data(self, index, role):
        if not index.isValid() or not role == QtCore.Qt.DisplayRole:
            return
        wave = self.canvas.getWaveData(self.__type)[index.row()]
        if index.column() == 0:
            return wave.getName()

    def flags(self, index):
        if index.column() in [0]:
            return super().flags(index) | QtCore.Qt.ItemIsEditable

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.canvas.getWaveData(self.__type))

    def columnCount(self, parent):
        return 1

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


class _MeshSelectionBoxBase(QtWidgets.QTreeView):
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
        self.selectionModel().selectionChanged.connect(self._selected)

    @suppressLysWarnings
    def _selected(self, *args, **kwargs):
        self.selected.emit(self._selectedData())

    def _selectedData(self):
        list = self.canvas.getWaveData(self.__type)
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QtCore.QSize(150, 100)


class MeshSelectionBox3D(_MeshSelectionBoxBase):
    def __init__(self, canvas, type, *args, **kwargs):
        super().__init__(canvas, type, *args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas = canvas

    def buildContextMenu(self, qPoint):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction('Show', self, triggered=lambda: self.__visible(True)))
        menu.addAction(QtWidgets.QAction('Hide', self, triggered=lambda: self.__visible(False)))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Remove', self, triggered=self.__remove))
        menu.addAction(QtWidgets.QAction('Duplicate', self, triggered=self.__duplicate))
        menu.addSeparator()
        #menu.addAction(QtWidgets.QAction('Process', self, triggered=self.__process))

        raw = menu.addMenu("Raw data")
        raw.addAction(QtWidgets.QAction('Display', self, triggered=lambda: display3D(*self.__getWaves("Wave"))))
        raw.addAction(QtWidgets.QAction('Append', self, triggered=lambda: self.__append("Wave")))
        raw.addAction(QtWidgets.QAction('Print', self, triggered=lambda: self.__print("Wave")))
        #raw.addAction(QtWidgets.QAction('MultiCut', self, triggered=lambda: self.__multicut("Wave")))
        #raw.addAction(QtWidgets.QAction('Edit', self, triggered=lambda: self.__edit("Wave")))
        raw.addAction(QtWidgets.QAction('Export', self, triggered=lambda: self.__export("Wave")))
        raw.addAction(QtWidgets.QAction('Send to shell', self, triggered=lambda: self.__send("Wave")))

        #pr = menu.addMenu("Processed data")
        #pr.addAction(QtWidgets.QAction('Display', self, triggered=lambda: display(*self.__getWaves("ProcessedWave"))))
        #pr.addAction(QtWidgets.QAction('Append', self, triggered=lambda: self.__append("ProcessedWave")))
        #pr.addAction(QtWidgets.QAction('Print', self, triggered=lambda: self.__print("ProcessedWave")))
        #pr.addAction(QtWidgets.QAction('MultiCut', self, triggered=lambda: self.__multicut("ProcessedWave")))
        #pr.addAction(QtWidgets.QAction('Edit', self, triggered=lambda: self.__edit("ProcessedWave")))
        #pr.addAction(QtWidgets.QAction('Export', self, triggered=lambda: self.__export("ProcessedWave")))
        #pr.addAction(QtWidgets.QAction('Send to shell', self, triggered=lambda: self.__send("ProcessedWave")))
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
            self.canvas.remove(d)

    def __append(self, type, **kwargs):
        append3D(*self.__getWaves(type), exclude=self.canvas, **kwargs)

    def __duplicate(self):
        for d in self._selectedData():
            self.canvas.append(d)

    def __multicut(self, type):
        for d in self.__getWaves(type):
            multicut(d)

    def __edit(self, type):
        for d in self.__getWaves(type):
            edit(d)

    def __print(self, type):
        for d in self.__getWaves(type):
            print(d)

    def __process(self):
        data = self._selectedData()
        if len(data) == 1:
            title = "Process for " + data[0].getName()
        else:
            title = "Process for " + str(len(data)) + " waves"
        dlg = FiltersDialog(data[0].getWave().data.ndim, title)
        for d in data:
            dlg.applied.connect(d.setFilter)
        if data[0].getFilter() is not None:
            dlg.setFilter(data[0].getFilter())
        dlg.attach(self.canvas.getParent())
        dlg.attachTo()
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

    def __send(self, waveType):
        from lys import glb
        dat = self._selectedData()[0]
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=dat.getName())
        if ok:
            w = self.__getWaves(waveType)[0].duplicate()
            w.name = text
            glb.shell().addObject(w, text)



class FiltersDialog(LysSubWindow):
    applied = QtCore.pyqtSignal(object)

    def __init__(self, dim, title=None):
        super().__init__()
        if title is not None:
            self.setWindowTitle(title)
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
        filt = self.filters.getFilters()
        if filt.getRelativeDimension() != 0:
            QtWidgets.QMessageBox.information(self, "Information", "You cannot aplly filters that changes dimension of data in Graph process. Use MultiCut instead.", QtWidgets.QMessageBox.Yes)
        else:
            self.ok = True
            self.applied.emit(filt)
            self.close()

    def _cancel(self):
        self.ok = False
        self.close()

    def _apply(self):
        filt = self.filters.getFilters()
        if filt.getRelativeDimension() != 0:
            QtWidgets.QMessageBox.information(self, "Information", "You cannot aplly filters that changes dimension of data in Graph process. Use MultiCut instead.", QtWidgets.QMessageBox.Yes)
        else:
            self.applied.emit(filt)

    def setFilter(self, filt):
        self.filters.setFilters(filt)

