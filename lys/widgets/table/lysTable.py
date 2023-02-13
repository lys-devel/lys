from lys import Wave, display, append, multicut
from lys.Qt import QtWidgets, QtGui, QtCore

from ..mdi import LysSubWindow
from .Data import TableData
from .TableModifyWindow import TableModifyWindow


class lysTable(QtWidgets.QWidget):
    keyPressed = QtCore.pyqtSignal(object)
    """
    Emitted when keyPressEvent is raised.
    """
    saveTable = QtCore.pyqtSignal(dict)
    """
    Emitted when the table is saved by saveAsDictionary method.
    """
    loadTable = QtCore.pyqtSignal(dict)
    """
    Emitted when the table is loaded by loadFromDictionary method.
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.__initlayout()
        self._event = _events(self)

    def __initlayout(self):
        self._data = TableData(self)
        self._model = _ArrayModel(self._data)
        self._table = QtWidgets.QTableView()
        self._table.setModel(self._model)
        self._data.updated.connect(self._table.viewport().update)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._table)
        self.setLayout(layout)

    def __getattr__(self, key):
        if hasattr(self._data, key):
            return getattr(self._data, key)
        return super().__getattr__(key)

    def saveAsDictionary(self):
        """
        Save the contetnts of the table as dictionary.

        Returns:
            dict: The dictionary.
        """
        d = {}
        self.saveTable.emit(d)
        return d

    def loadFromDictionary(self, d):
        """
        Load the contents of the table from dictionary.

        Args:
            d(dict): The dictionary.
        """
        self.loadTable.emit(d)

    def keyPressEvent(self, e):
        """Reimplementation of keyPressEvent"""
        self.keyPressed.emit(e)
        if not e.isAccepted():
            return super().keyPressEvent(e)

    def openModifyWindow(self):
        """Open modify window for this table window."""
        parent = self.__getParent()
        mod = TableModifyWindow(parent, self)
        return mod

    def __getParent(self):
        parent = self.parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                return parent
            parent = parent.parentWidget()


class _events(QtCore.QObject):
    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        parent.keyPressed.connect(self.keyPressed)
        parent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        parent.customContextMenuRequested.connect(self.constructContextMenu)

    def constructContextMenu(self):
        menu = QtWidgets.QMenu()
        menu.addAction(QtWidgets.QAction('Table settings', self._parent, triggered=self._parent.openModifyWindow, shortcut="Ctrl+T"))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Save changes', self._parent, triggered=self._parent.save, shortcut="Ctrl+S"))
        m = menu.addMenu('Full data')
        m.addAction(QtWidgets.QAction('Display', self._parent, triggered=lambda: self.__display()))
        m.addAction(QtWidgets.QAction('Append', self._parent, triggered=lambda: self.__append()))
        m.addAction(QtWidgets.QAction('Multicut', self._parent, triggered=lambda: self.__multicut()))
        m.addAction(QtWidgets.QAction('Export', self._parent, triggered=lambda: self.__export()))
        m.addAction(QtWidgets.QAction('Send to shell', self._parent, triggered=lambda: self.__send()))
        m = menu.addMenu('Sliced data')
        m.addAction(QtWidgets.QAction('Display', self._parent, triggered=lambda: self.__display("slice")))
        m.addAction(QtWidgets.QAction('Append', self._parent, triggered=lambda: self.__append("slice")))
        m.addAction(QtWidgets.QAction('Multicut', self._parent, triggered=lambda: self.__multicut("slice")))
        m.addAction(QtWidgets.QAction('Export', self._parent, triggered=lambda: self.__export("slice")))
        m.addAction(QtWidgets.QAction('Send to shell', self._parent, triggered=lambda: self.__send("slice")))
        menu.exec_(QtGui.QCursor.pos())

    def keyPressed(self, e):
        if e.key() == QtCore.Qt.Key_S and e.modifiers() == QtCore.Qt.ControlModifier:
            self._parent.save()
            e.accept()
        elif e.key() == QtCore.Qt.Key_T:
            self._parent.openModifyWindow()
            e.accept()

    def __getData(self, type="full"):
        if type == "full":
            return self._parent.getData()
        else:
            return self._parent.getSlicedData()

    def __export(self, type="full"):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, _ = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            w = self.__getData(type)
            w.export(path)

    def __display(self, type="full"):
        w = self.__getData(type)
        if w.ndim < 3:
            display(w)
        else:
            QtWidgets.QMessageBox.information(self, "Error", "You cannot display multi-dimensional data.", QtWidgets.QMessageBox.Yes)

    def __append(self, type="full"):
        w = self.__getData(type)
        if w.ndim < 3:
            append(w)
        else:
            QtWidgets.QMessageBox.information(self, "Error", "You cannot append multi-dimensional data.", QtWidgets.QMessageBox.Yes)

    def __multicut(self, type="full"):
        multicut(self.__getData(type))

    def __send(self, type="full"):
        from lys import glb
        w = self.__getData(type)
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            w.name = text
            glb.shell().addObject(w, text)


class _ArrayModel(QtGui.QStandardItemModel):
    dataChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._parent.updated.connect(self.update)
        self.dataChanged.connect(self._parent.dataChanged)


    def update(self):
        self._data = self.__getSlicedData()
        if len(self._data.shape) == 1:
            self._data = [self._data]
        self.setRowCount(len(self._data[0]))
        self.setColumnCount(len(self._data))

    def __getSlicedData(self):
        slc = self._parent.getSlice()
        wave = self._parent.getData()
        if isinstance(slc, int):
            return wave.axes[slc]
        else:
            return wave.data[tuple(slc)]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return "{:.4g}".format(self._data[index.column()][index.row()])
        if role == role == QtCore.Qt.EditRole:
            return str(self._data[index.column()][index.row()])
        return super().data(index, role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            item = index.model().itemFromIndex(index)
            res = eval(value)
            self._data[item.column()][item.row()] = res
            self.dataChanged.emit()
            return True
        return super().setData(index, value, role)
