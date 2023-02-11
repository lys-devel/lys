import io
from lys import Wave, load
from lys.Qt import QtWidgets, QtGui, QtCore

from ..mdi import _AutoSavedWindow
from . TableModifyWindow import TableModifyWindow


class Table(_AutoSavedWindow):
    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.__initlayout(data)
        self._data = data
        self.setWindowTitle(self.__getTitle())
        self.resize(400, 400)
        # self._etable.dataChanged.connect(self.modified)
        # self.modified.emit()

    def __initlayout(self, data):
        self._etable = lysTable(self)
        if data is not None:
            if type(data) == str:
                if data.endswith(".tbl"):
                    self._load(data)
                else:
                    self._etable.setData(data)
            else:
                self._etable.setData(data)
        self._etable.dataChanged.connect(lambda: self.setWindowTitle(self.__getTitle() + "*"))
        self._etable.dataSaved.connect(lambda: self.setWindowTitle(self.__getTitle()))
        self.setWidget(self._etable)
        self.show()

    def __getattr__(self, key):
        if hasattr(self._etable, key):
            return getattr(self._etable, key)
        return super().__getattr__(key)

    def __getTitle(self):
        if isinstance(self._data, str):
            return self._data
        elif isinstance(self._data, Wave):
            return self._data.name

    def _save(self, file):
        d = self._etable.saveAsDictionary()
        with open(file, 'w') as f:
            f.write(str(d))
        print("save", file)

    def _load(self, file):
        print("load", file)
        with open(file, 'r') as f:
            d = eval(f.read())
        self._etable.loadFromDictionary(d)

    def _prefix(self):
        return 'Table'

    def _suffix(self):
        return '.tbl'


class lysTable(QtWidgets.QWidget):
    dataChanged = QtCore.pyqtSignal()
    """
    Emitted when the data is changed.
    """
    dataSaved = QtCore.pyqtSignal()
    """
    Emitted when the data is saved.
    """

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.__initlayout()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._constructContextMenu)

    def __initlayout(self):
        self._model = _ArrayModel(self)
        self._model.dataChanged.connect(self.dataChanged)
        self._table = QtWidgets.QTableView()
        self._table.setModel(self._model)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._table)
        self.setLayout(layout)

    def setData(self, data):
        """
        Set data.

        Args:
            data(str or Wave): The path to a npz file, or an instance of Wave.
        """
        if isinstance(data, Wave):
            self._original = data
            w = data.duplicate()
        elif isinstance(data, str):
            self._original = data
            w = load(data)
        self._data = w.data
        self._axes = [w.getAxis(i).astype(float) for i in range(w.ndim)]
        self._note = w.note
        if w.ndim == 1:
            self._slice = [slice(None)]
        elif w.ndim == 2:
            self._slice = [slice(None), slice(None)]
        elif w.ndim > 2:
            self._slice = [slice(None), slice(None)] + ([0] * (w.ndim - 2))
        self._model.update()

    def saveAsDictionary(self):
        """
        Save the contetnts of the table as dictionary.

        Returns:
            dict: The dictionary.
        """
        d = {}
        if isinstance(self._original, Wave):
            d["type"] = "Wave"
        elif isinstance(self._original, str):
            d["type"] = "File"
            d["File"] = self._original
        w = Wave(self._data, *self._axes, **self._note)
        b = io.BytesIO()
        w.export(b)
        d['Wave'] = b.getvalue()
        d['Slice'] = str(self._slice)
        return d

    def loadFromDictionary(self, d):
        """
        Load the contents of the table from dictionary.

        Args:
            d(dict): The dictionary.
        """
        w = Wave(io.BytesIO(d['Wave']))
        if d["type"] == "Wave":
            self._original = w.duplicate()
        elif d["type"] == "File":
            self._original = d["File"]
        self._data = w.data
        self._axes = w.axes
        self._note = w.note
        self._slice = eval(d["Slice"])
        self._model.update()
        self._table.viewport().update()

    def save(self):
        """
        Save the contents of the table to file or Wave depending on the argument of :meth:`setData`.
        """
        if isinstance(self._original, Wave):
            self._original.data = self._data
            self._original.axes = self._axes
        elif isinstance(self._original, str):
            w = Wave(self._data, *self._axes, **self._note)
            w.export(self._original)
        self.dataSaved.emit()

    def _getSlicedData(self):
        if isinstance(self._slice, int):
            return self._axes[self._slice]
        else:
            return self._data[tuple(self._slice)]

    def _setSlice(self, slc):
        self._slice = slc
        self._model.update()
        self._table.viewport().update()

    def _getSlice(self):
        return self._slice

    def _constructContextMenu(self):
        menu = QtWidgets.QMenu()
        menu.addAction(QtWidgets.QAction('Table settings', self, triggered=self.openModifyWindow, shortcut="Ctrl+T"))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Save changes', self, triggered=self.save, shortcut="Ctrl+S"))
        menu.addAction(QtWidgets.QAction('Export data to file', self, triggered=self.__export, shortcut="Ctrl+Shift+S"))
        menu.exec_(QtGui.QCursor.pos())

    def keyPressEvent(self, e):
        """Reimplementation of keyPressEvent"""
        if e.key() == QtCore.Qt.Key_S:
            if e.modifiers() == QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier:
                self.__export()
            elif e.modifiers() == QtCore.Qt.ControlModifier:
                self.save()
        elif e.key() == QtCore.Qt.Key_T:
            self.openModifyWindow()
        else:
            return super().keyPressEvent(e)

    def openModifyWindow(self):
        parent = self.getParent()
        mod = TableModifyWindow(parent, self)
        mod.setData(self._data)
        return mod

    def __export(self):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            w = Wave(self._data, *self._axes, **self._note)
            w.export(path)

    def getParent(self):
        """
        Get Parent LysSubWindow if it exists.

        Returns:
            LysSubWindow: The parent LysSubWindow. If the canvas is not embedded in LysSubWindow, None is returned.
        """
        parent = self.parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                return parent
            parent = parent.parentWidget()


class _ArrayModel(QtGui.QStandardItemModel):
    dataChanged = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self._parent = parent

    def update(self):
        self._data = self._parent._getSlicedData()
        if len(self._data.shape) == 1:
            self._data = [self._data]
        self.setRowCount(len(self._data[0]))
        self.setColumnCount(len(self._data))

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
