from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from lys import *
import numpy
import scipy.constants


class ExtendTable(QWidget):
    def __init__(self, wave=None, overwrite=True):
        super().__init__()
        self.row = None
        self.isEdited = False
        self.__initlayout()
        if wave is not None:
            self.Set(wave, overwrite)

    def __initlayout(self):
        self._line = QLineEdit()
        self._line.textChanged.connect(self.edited)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Expr."))
        h1.addWidget(self._line)
        self._etable = _ExtendTableTable()
        self._etable.selected.connect(self.selectionChanged)
        self._etable.changed.connect(self.selectionChanged)
        layout = QVBoxLayout()
        layout.addLayout(h1)
        layout.addWidget(self._etable)
        self.setLayout(layout)

    def Append(self, wave):
        self._etable.Append(wave)

    def checkState(self, index):
        self._etable.checkState(index)

    def clear(self):
        self._etable.clear()

    def Append(self, data, *args, **kwargs):
        self._etable.Append(data, *args, **kwargs)

    def Set(self, data, overwrite=True):
        self.Append(data, pos=(0, 0))
        self.SetSize(np.array(data.data).shape)
        self.SetOverwrite(overwrite)

    def SetOverwrite(self, b):
        self._etable.SetOverwrite(b)

    def SetSize(self, size):
        self._etable.SetSize(size)

    def selectedRow(self):
        return self._etable.selectedRow()

    def setData(self, value, row, column):
        self._etable.setData(value, row, column)

    def addMenu(self, act):
        self._etable.addMenu(act)

    def selectionChanged(self, item, item2):
        if self.isEdited:
            return
        self.row = self._etable.selectedRow()
        self.column = self._etable.selectedColumn()
        self.isEdited = True
        self._line.setText(self._etable.sheet[self.row, self.column])
        self.isEdited = False

    def edited(self):
        if self.isEdited:
            return
        if self.row is not None:
            self.isEdited = True
            self._etable.setRawData(self._line.text(), self.row, self.column)
            self.isEdited = False


class SpreadSheet(object):
    def __init__(self, size=(300, 300)):
        self.waves = []
        self.__initDataSize(size)

    def __initDataSize(self, size):
        self.size = size
        self._data = np.array([[None for i in range(size[0])]
                               for j in range(size[1])])
        self._dict = {"Obj": self._getWave}
        self._dict.update(scipy.constants.__dict__)
        self._dict.update(numpy.__dict__)
        for i in range(size[0]):
            for j in range(size[1]):
                self._dict[self.num2alpha(j + 1) + str(i + 1)] = None

    def alpha2num(self, alpha):
        num = 0
        for index, item in enumerate(list(alpha)):
            num += pow(26, len(alpha) - index - 1) * (ord(item) - ord('A') + 1)
        return num

    def num2alpha(self, num):
        if num <= 26:
            return chr(64 + num)
        elif num % 26 == 0:
            return self.num2alpha(num // 26 - 1) + chr(90)
        else:
            return self.num2alpha(num // 26) + chr(64 + num % 26)

    def setData(self, data, i, j):
        if isinstance(data, str):
            if len(data) != 0:
                if data[0] == "=":
                    try:
                        exec(str(self._data[i][j]) + data, locals(), self._dict)
                        self.saveAutoSaved()
                    except:
                        print("[Table] Error on exec:", str(self._data[i][j]) + data)
                        import inspect
                        print(inspect.stack()[1][3])
                    return
        self._data[i][j] = data

    def evaluateCell(self, i, j):
        expr = self._data[i][j]
        if expr is None or expr == "":
            self._dict[self.num2alpha(j + 1) + str(i + 1)] = None
        else:
            try:
                self._dict[self.num2alpha(
                    j + 1) + str(i + 1)] = eval(expr, locals(), self._dict)
            except NameError:
                self._dict[self.num2alpha(j + 1) + str(i + 1)] = str(expr)
            except Exception as e:
                self._dict[self.num2alpha(j + 1) + str(i + 1)] = str(e)
        return self._dict[self.num2alpha(j + 1) + str(i + 1)]

    def __call__(self, i, j):
        val = self.evaluateCell(i, j)
        if val is None:
            return ""
        else:
            if isinstance(val, float) or isinstance(val, int):
                return '{:.5g}'.format(val)
            else:
                return str(val)

    def __getitem__(self, index):
        data = self._data[index[0]][index[1]]
        if data is None:
            return ""
        else:
            return data

    def Append(self, w):
        self.waves.append(w)
        return len(self.waves) - 1

    def extractWave(self, index, i, j):
        w = self._getWave(index)
        if not hasattr(w.data[0], "__iter__"):
            for k in range(len(w.data)):
                self.setData(
                    "Obj(" + str(index) + ").data[" + str(k) + "]", i + k, j)
        else:
            for k in range(len(w.data)):
                for l in range(len(w.data[0])):
                    self.setData(
                        "Obj(" + str(index) + ").data[" + str(k) + "][" + str(l) + "]", i + l, j + k)

    def Resize(self, size=(300, 300)):
        data_old = np.array(self._data)
        size_old = np.array(self.size)
        self.__initDataSize(size)
        for i in range(min(size[0], size_old[0])):
            for j in range(min(size[1], size_old[1])):
                self._data[j][i] = data_old[j][i]

    def _getWave(self, index):
        return self.waves[index]

    def getDataArray(self):
        return self._data

    def saveAutoSaved(self):
        raise NotImplementedError
        for w in self.waves:
            w.Save()  # this is deprecated


class _ExtendTableTable(QTableView):
    selected = pyqtSignal(QItemSelection, QItemSelection)
    changed = pyqtSignal(QModelIndex, QModelIndex)

    class ArrayModel(QStandardItemModel):
        def __init__(self, checkable=False):
            super().__init__()
            self.clear()
            self.__checkable = checkable
            self.overwrite = False

        def num2alpha(self, num):
            if num <= 26:
                return chr(64 + num)
            elif num % 26 == 0:
                return self.num2alpha(num // 26 - 1) + chr(90)
            else:
                return self.num2alpha(num // 26) + chr(64 + num % 26)

        def data(self, index, role=Qt.DisplayRole):
            if role == Qt.DisplayRole:
                return self.sheet(index.row(), index.column())
            if role == role == Qt.EditRole:
                return self.sheet[index.row(), index.column()]
            return super().data(index, role)

        def setData(self, index, value, role=Qt.EditRole):
            if role == Qt.EditRole:
                item = index.model().itemFromIndex(index)
                res = value
                if self.overwrite and len(res) != 0:
                    if res[0] != "=":
                        res = "=" + res
                self.sheet.setData(res, item.row(), item.column())
                self.dataChanged.emit(index, index)
                return True
            return super().setData(index, value, role)

        def clear(self):
            self.sheet = SpreadSheet()
            self.setRowCount(self.sheet.size[0])
            self.setColumnCount(self.sheet.size[1])
            self.setHorizontalHeaderLabels([self.num2alpha(i + 1) for i in range(300)])

        def resize(self, size):
            self.sheet.Resize(size)
            self.setRowCount(size[1])
            self.setColumnCount(size[0])
            self.setHorizontalHeaderLabels([self.num2alpha(i + 1) for i in range(size[0])])

        def flags(self, index):
            if index.column() == 0 and self.__checkable:
                item = index.model().itemFromIndex(index)
                item.setCheckable(True)
                return super().flags(index) | Qt.ItemIsUserCheckable
            return super().flags(index)

        def SetOverwrite(self, b):
            self.overwrite = b

    def __init__(self, data=None, checkable=False, overwrite=False):
        super().__init__()
        self._model = self.ArrayModel(checkable)
        self.setModel(self._model)
        self.sheet = self._model.sheet
        self.SetOverwrite(overwrite)
        self.__menu = []
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        if data is not None:
            self.Append(data)
        self.selmod = self.selectionModel()
        self.selmod.selectionChanged.connect(self.selected)
        self._model.dataChanged.connect(self.changed)

    def clear(self):
        self._model.clear()
        self.sheet = self._model.sheet

    def Append(self, data, extract=True, pos=None):
        index = self.sheet.Append(data)
        if extract:
            if pos is None:
                self.sheet.extractWave(index, self.selectedRow(), self.selectedColumn())
            else:
                self.sheet.extractWave(index, pos[0], pos[1])

    def checkState(self, row):
        item = self._model.item(row)
        if item is None:
            return None
        else:
            return item.checkState()

    def selectedRow(self):
        indice = self.selectionModel().selectedIndexes()
        if len(indice) == 0:
            return 0
        return self.selectionModel().selectedIndexes()[0].row()

    def selectedColumn(self):
        indice = self.selectionModel().selectedIndexes()
        if len(indice) == 0:
            return 0
        return self.selectionModel().selectedIndexes()[0].column()

    def setData(self, value, row, column):
        self._model.setData(self._model.index(row, column), "=" + str(value))

    def setRawData(self, value, row, column):
        res = str(value)
        self._model.setData(self._model.index(row, column), res)

    def addMenu(self, act):
        self.__menu.append(act)

    def SetSize(self, size):
        self._model.resize(size)

    def SetOverwrite(self, b):
        self._model.SetOverwrite(b)

    def _makeDataFromSelection(self):
        indice = self.selectionModel().selectedIndexes()
        indice = np.array([[item.row(), item.column()] for item in indice])
        indice = sorted(indice, key=lambda x: (x[1], x[0]))
        data = self._createReorderedData(indice)
        data = self._removeNans(np.array(data))
        data = self.reduceDimensions(data)
        return data

    def _createReorderedData(self, indice):
        r = None
        res = []
        tmp = []
        for item in indice:
            if item[1] != r:
                if r is not None:
                    res.append(tmp)
                r = item[1]
                tmp = []
            val = self.sheet(item[0], item[1])
            if val.isdigit():
                val = float(val)
            if val == "":
                val = None
            tmp.append(val)
        res.append(tmp)
        return res

    def reduceDimensions(self, data):
        if data.shape[0] == 1:
            return data[0]
        if data.shape[1] == 1:
            return data[:, 0]
        return data

    def _removeNans(self, data):
        data = data[:, ~np.all(data == None, axis=0)]
        data = data[~np.all(data == None, axis=1), :]
        return data

    def buildContextMenu(self):
        menu = QMenu(self)
        for act in self.__menu:
            menu.addAction(act)
        try:
            data = self._makeDataFromSelection()
        except Exception as e:
            import traceback
            traceback.print_exc()
        else:
            if len(data) != 0:
                if not hasattr(data[0], "__iter__") and data.dtype == float:
                    send = QMenu("1DData")
                    send.addAction(
                        QAction("Export", self, triggered=self._export1D))
                    menu.addMenu(send)
                elif data.dtype == float:
                    if len(data) == 2:
                        send1D = QMenu("1D Wave")
                        menu.addMenu(send1D)
                        send1D.addAction(
                            QAction("Export", self, triggered=self._export1D))
                    send = QMenu("2D Wave")
                    menu.addMenu(send)
                    send.addAction(
                        QAction("Export", self, triggered=self._export2D))
        menu.exec_(QCursor.pos())

    def _export1D(self):
        w = Wave()
        data = self._makeDataFromSelection()
        if len(data) == 2:
            w.data = data[1]
            w.x = data[0]
        filt = ""
        for f in Wave().SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QFileDialog.getSaveFileName(filter=filt)
        w.export(path, type=type)

    def _export2D(self):
        filt = ""
        for f in Wave().SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QFileDialog.getSaveFileName(filter=filt)
        w = Wave()
        w.data = self._makeDataFromSelection()
        w.export(path, type=type)
