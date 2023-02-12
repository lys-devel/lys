from lys import Wave, lysPath
from lys.Qt import QtWidgets

from ..mdi import _AutoSavedWindow
from . import lysTable


class Table(_AutoSavedWindow):
    _modified = False

    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.__initlayout(data)
        self.__initEvents()
        self.resizeFinished.connect(self.modified)
        self.moveFinished.connect(self.modified)
        self.modified.emit()

    def __initlayout(self, data):
        self.resize(400, 400)
        self._etable = lysTable(self)
        self._etable.saveTable.connect(self._savePosition)
        self._etable.loadTable.connect(self._loadPosition)
        if data is not None:
            if type(data) == str:
                if data.endswith(".tbl"):
                    self._load(data)
                    self._data = self._etable._original
                else:
                    self._etable.setData(data)
                    self._data = data
            else:
                self._etable.setData(data)
                self._data = data
        self.setWidget(self._etable)
        self.show()

    def __initEvents(self):
        def setMod(b):
            self._modified = b

        self.setWindowTitle(self.Name())
        self._etable.dataChanged.connect(lambda: setMod(True))
        self._etable.dataChanged.connect(lambda: self.setWindowTitle(self.Name() + "*"))
        self._etable.dataChanged.connect(self.modified)
        self._etable.dataSaved.connect(lambda: setMod(False))
        self._etable.dataSaved.connect(lambda: self.setWindowTitle(self.Name()))
        self._etable.dataSaved.connect(self.modified)

    def __getattr__(self, key):
        if hasattr(self._etable, key):
            return getattr(self._etable, key)
        return super().__getattr__(key)

    def Name(self):
        if isinstance(self._data, str):
            return lysPath(self._data)
        elif isinstance(self._data, Wave):
            return self._data.name

    def _save(self, file):
        d = self._etable.saveAsDictionary()
        with open(file, 'w') as f:
            f.write(str(d))

    def _savePosition(self, d):
        d['Table'] = {'Position': [self.pos().x(), self.pos().y()], 'Size': [self.size().width(), self.size().height()]}

    def _load(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        self._etable.loadFromDictionary(d)

    def _loadPosition(self, d):
        if 'Table' in d:
            self.move(*d['Table']['Position'])
            self.resize(*d['Table']['Size'])
        else:
            self.resize(400, 400)

    def _prefix(self):
        return 'Table'

    def _suffix(self):
        return '.tbl'

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
        if self._modified:
            msg = QtWidgets.QMessageBox(parent=self)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Caution")
            msg.setText("The change in thit Table is not saved. Do you want to save the content of this window?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
            ok = msg.exec_()
            if ok == QtWidgets.QMessageBox.Cancel:
                return event.ignore()
            if ok == QtWidgets.QMessageBox.Yes:
                self.save()
        return super().closeEvent(event)
