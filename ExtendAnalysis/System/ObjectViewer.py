
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class _WaveModel(QAbstractItemModel):
    def __init__(self, shell):
        super().__init__()
        self._shell = shell
        self._shell.commandExecuted.connect(self.update)
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self.setHeaderData(1, Qt.Horizontal, 'Type')
        self.setHeaderData(2, Qt.Horizontal, 'Shape')
        self.setHeaderData(3, Qt.Horizontal, 'Path')

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not role == Qt.DisplayRole:
            return QVariant()
        d = self._getWaves()
        if index.column() == 0:
            return list(d.keys())[index.row()]
        if index.column() == 1:
            return str(list(d.values())[index.row()].data.dtype)
        if index.column() == 2:
            return str(list(d.values())[index.row()].data.shape)
        if index.column() == 3:
            list(d.values())[index.row()].FileName()

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self._getWaves())

    def columnCount(self, parent):
        return 4

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column, None)
        return QModelIndex()

    def parent(self, index):
        return QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return "Name"
            if section == 1:
                return "Type"
            if section == 2:
                return "Shape"
            if section == 3:
                return "Path"

    def _getWaves(self):
        from ExtendAnalysis import Wave
        return {key: value for key, value in self._shell.GetDictionary().items() if isinstance(value, Wave)}

    def update(self):
        size = self.rowCount(parent=QModelIndex())
        self.rowsInserted.emit(QModelIndex(), 0, size)


class WaveViewer(QTreeView):
    def __init__(self, shell, parent=None):
        super().__init__(parent)
        self.__model = _WaveModel(shell)
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Display", self, triggered=self._disp))
        menu.addAction(QAction("Edit", self, triggered=self._edit))
        menu.addAction(QAction("MultiCut", self, triggered=self._multicut))
        menu.exec_(QCursor.pos())

    def __getWaves(self):
        index = self.selectionModel().selectedIndexes()
        waves = list(self.__model._getWaves().values())
        return [waves[i.row()] for i in index if i.column() == 0]

    def _disp(self):
        from ExtendAnalysis import Graph
        g = Graph()
        for w in self.__getWaves():
            g.Append(w)

    def _edit(self, type):
        from ExtendAnalysis import Table
        t = Table()
        for w in self.__getWaves():
            t.Append(w)

    def _multicut(self, type):
        from ExtendAnalysis import MultiCut
        MultiCut(self.__getWaves()[0])

    def update(self):
        super().update()
        self.__model.update()
