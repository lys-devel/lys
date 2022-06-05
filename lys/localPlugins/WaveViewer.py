
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from lys import display, edit, MultiCut, glb


class _WaveModel(QAbstractItemModel):
    def __init__(self, shell):
        super().__init__()
        self._shell = shell
        self._shell.commandExecuted.connect(self.update)
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self.setHeaderData(1, Qt.Horizontal, 'Type')
        self.setHeaderData(2, Qt.Horizontal, 'Shape')

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

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self._getWaves())

    def columnCount(self, parent):
        return 3

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

    def _getWaves(self):
        from lys import Wave
        return {key: value for key, value in self._shell.dict.items() if isinstance(value, Wave)}

    def update(self):
        size = self.rowCount(parent=QModelIndex())
        self.rowsInserted.emit(QModelIndex(), 0, size)


class WaveViewer(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__model = _WaveModel(glb.shell())
        self.setModel(self.__model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QMenu(self)
        menu.addAction(QAction("Display", self, triggered=self._disp))
        menu.addAction(QAction("Edit", self, triggered=self._edit))
        menu.addAction(QAction("MultiCut", self, triggered=self._multicut))
        menu.addAction(QAction("Delete", self, triggered=self._delete))
        menu.exec_(QCursor.pos())

    def __getWaves(self):
        index = self.selectionModel().selectedIndexes()
        waves = list(self.__model._getWaves().values())
        return [waves[i.row()] for i in index if i.column() == 0]

    def __getWaveNames(self):
        return list(self.__model._getWaves().keys())

    def _disp(self):
        display(*self.__getWaves())

    def _edit(self, type):
        for w in self.__getWaves():
            edit(w)

    def _multicut(self, type):
        MultiCut(self.__getWaves()[0])

    def _delete(self):
        for key in self.__getWaveNames():
            del self.__model._shell.dict[key]

    def update(self):
        super().update()
        self.__model.update()


_instance = WaveViewer()
glb.mainWindow().addTab(_instance, "Waves", "up")
