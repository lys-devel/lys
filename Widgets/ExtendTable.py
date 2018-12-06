from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class ExtendTable(QTableView):
    class ArrayModel(QStandardItemModel):
        def __init__(self, array=None,checkable=False):
            super().__init__()
            self.set(array)
            self.__checkable=True
        def data(self,index,role=Qt.DisplayRole):
            if role==Qt.DisplayRole or role==Qt.EditRole:
                if self._data is None:
                    return ""
                elif len(self._data.shape())==1:
                    return str(self._data[index.row()])
                else:
                    return str(self._data[index.row()][index.column()])
            return super().data(index,role)
        def setData(self,index,value,role=Qt.EditRole):
            if role==Qt.EditRole:
                item = index.model().itemFromIndex(index)
                if value.isdigit():
                    if len(self._data.shape())==1:
                        self._data[item.row()]=float(value)
                    else:
                        self._data[item.row()][item.column()]=float(value)
                else:
                    if len(self._data.shape())==1:
                        self._data[item.row()]=value
                    else:
                        self._data[item.row()][item.column()]=value
                self._data.Save()
                return True
            return super().setData(index,value,role)
        def setDataValue(self,value,row,column=0,role=Qt.EditRole):
            if role==Qt.EditRole:
                if str(value).isdigit():
                    if len(self._data.shape())==1:
                        self._data[row]=float(value)
                    else:
                        self._data[row][column]=float(value)
                else:
                    if len(self._data.shape())==1:
                        self._data[row]=value
                    else:
                        self._data[row][column]=value
                self._data.Save()
                return True
            return super().setData(index,value,role)
        def clear(self):
            self._data=None
        def set(self,array):
            if array is None:
                self._data=None
                return
            elif len(array.shape())==1:
                self.setRowCount(array.shape()[0])
                self.setColumnCount(1)
            else:
                self.setRowCount(array.shape()[0])
                self.setColumnCount(array.shape()[1])
            self._data=array
        def flags(self,index):
            if index.column()==0 and self.__checkable:
                item = index.model().itemFromIndex(index)
                item.setCheckable(True)
                return super().flags(index) | Qt.ItemIsUserCheckable
            return super().flags(index)

    def __init__(self,data=None,checkable=True):
        super().__init__()
        if data is None:
            self._model=self.ArrayModel(None, checkable)
        else:
            self._model=self.ArrayModel(data, checkable)
        self.setModel(self._model)
    def clear(self):
        self._model.clear()
    def Append(self,data):
        self._model.set(data)
    def checkState(self,row):
        item=self._model.item(row)
        if item is None:
            return None
        else:
            return item.checkState()
    def selectedRow(self):
        return self.selectionModel().selectedIndexes()[0].row()
    def setData(self,value,row,column):
        self._model.setDataValue(value,row,column)
