from lys import display, edit, MultiCut, glb, Wave
from lys.Qt import QtWidgets, QtCore, QtGui


class _WaveModel(QtCore.QAbstractItemModel):
    def __init__(self, shell):
        super().__init__()
        self._shell = shell
        self._shell.commandExecuted.connect(self.update)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Type')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Shape')

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or not role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
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
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Name"
            if section == 1:
                return "Type"
            if section == 2:
                return "Shape"

    def _getWaves(self):
        return {key: value for key, value in self._shell.dict.items() if isinstance(value, Wave)}

    def update(self):
        size = self.rowCount(parent=QtCore.QModelIndex())
        self.rowsInserted.emit(QtCore.QModelIndex(), 0, size)


class WaveViewer(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.__model = _WaveModel(glb.shell())
        self.setModel(self.__model)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction("Display", self, triggered=self._disp))
        menu.addAction(QtWidgets.QAction("Edit", self, triggered=self._edit))
        menu.addAction(QtWidgets.QAction("MultiCut", self, triggered=self._multicut))
        menu.addAction(QtWidgets.QAction("Delete", self, triggered=self._delete))
        menu.exec_(QtGui.QCursor.pos())

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
