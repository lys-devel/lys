import io
from lys import Wave, load, display, append, multicut
from lys.Qt import QtWidgets, QtGui, QtCore

from ..mdi import LysSubWindow
from . TableModifyWindow import TableModifyWindow


class lysTable(QtWidgets.QWidget):
    dataChanged = QtCore.pyqtSignal()
    """
    Emitted when the data is changed.
    """
    dataSaved = QtCore.pyqtSignal()
    """
    Emitted when the data is saved.
    """
    keyPressed = QtCore.pyqtSignal(object)
    """Emitted when keyPressEvent is raised."""

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.__initlayout()
        self._event = _events(self)

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
        self._slice = self.__getDefaultSlice()
        self._model.update()

    def __getDefaultSlice(self):
        if self._data.ndim == 1:
            return [slice(None)]
        elif self._data.ndim == 2:
            return [slice(None), slice(None)]
        elif self._data.ndim > 2:
            return [slice(None), slice(None)] + ([0] * (self._data.ndim - 2))

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
        b = io.BytesIO()
        self.getData().export(b)
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
            w = self.getData()
            w.export(self._original)
        self.dataSaved.emit()

    def getData(self):
        """
        Returns the edited Wave.

        Returns:
            Wave: The edited Wave.
        """
        return Wave(self._data, *self._axes, **self._note)

    def getSlicedData(self):
        """
        Returns the sliced data.

        Returns:
            Wave: The sliced Wave.
        """
        if isinstance(self._slice, int):
            return Wave(self._axes[self._slice])
        else:
            data = self._data[tuple(self._slice)]
            axes = []
            for i, s in enumerate(self._slice):
                if not isinstance(s, int):
                    axes.append(self._axes[i])
            return Wave(data, *axes, **self._note)

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

    def keyPressEvent(self, e):
        """Reimplementation of keyPressEvent"""
        self.keyPressed.emit(e)
        if not e.isAccepted():
            return super().keyPressEvent(e)

    def openModifyWindow(self):
        """Open modify window for this table."""
        parent = self.__getParent()
        mod = TableModifyWindow(parent, self)
        mod.setData(self._data)
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
