from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ExtendTable(QTableView):
    class ArrayModel(QStandardItemModel):
        def __init__(self, array):
            super().__init__()
            self.set(array)
        def data(self,index,role=Qt.DisplayRole):
            if role==Qt.DisplayRole or role==Qt.EditRole:
                if self._data is None:
                    return ""
                elif self._data.ndim==1:
                    return str(self._data[index.row()])
                else:
                    return str(self._data[index.row()][index.column()])
            return super().data(index,role)
        def clear(self):
            self._data=None
        def set(self,array):
            if array.ndim==1:
                self.setRowCount(array.shape[0])
                self.setColumnCount(0)
            else:
                self.setRowCount(array.shape[0])
                self.setColumnCount(array.shape[1])
            self._data=array

    def __init__(self,wave):
        super().__init__()
        self._model=self.ArrayModel(wave.data)
        self.setModel(self._model)
        self._model.itemChanged.connect(self.onDataChanged)
        self._wave=wave
    def onDataChanged(self,item):
        if item.text().isdigit():
            if self._wave.data.ndim==1:
                self._wave.data[item.row()]=float(item.text())
            else:
                self._wave.data[item.row()][item.column()]=float(item.text())
    def clear(self):
        self._model.clear()
    def setData(self,wave):
        self._model.set(wave.data)
