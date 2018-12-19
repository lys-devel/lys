from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import numpy as np

class DataSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self,canvas):
            super().__init__(0,3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
            self.canvas=canvas
        def clear(self):
            super().clear()
            self.setColumnCount(3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
        def supportedDropActions(self):
            return Qt.MoveAction
        def mimeData(self, indexes):
            mimedata = QMimeData()
            data=[]
            for i in indexes:
                if i.column() !=2:
                    continue
                t=eval(self.itemFromIndex(i).text())
                data.append(t)
            mimedata.setData('index',str(data).encode('utf-8'))
            mimedata.setText(str(data))
            return mimedata
        def mimeTypes(self):
            return ['index']
        def dropMimeData(self, data, action, row, column, parent):
            f=eval(data.text())
            par=self.itemFromIndex(parent)
            if par is None:
                if row==-1 and column==-1:
                    self.canvas.moveItem(f)
                else:
                    self.canvas.moveItem(f,self.item(row,2).text())
            else:
                self.canvas.moveItem(f,self.item(self.itemFromIndex(parent).row(),2).text())
            return False
    def __init__(self,canvas,dim):
        super().__init__()
        self.canvas=canvas
        self.__dim=dim
        self.__initlayout()
        self.flg=False
        self._loadstate()
        canvas.addDataChangeListener(self)
        canvas.addDataSelectionListener(self)
    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model=DataSelectionBox._Model(self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)
    def OnDataSelected(self):
        if self.flg:
            return
        indexes=self.canvas.getSelectedIndexes(self.__dim)
        list=self.canvas.getWaveData(self.__dim)
        selm=self.selectionModel()
        for i in range(len(list)):
            index0=self.__model.index(len(list)-i-1,0)
            index1=self.__model.index(len(list)-i-1,1)
            index2=self.__model.index(len(list)-i-1,2)
            id=float(self.__model.itemFromIndex(index2).text())
            if id in indexes:
                selm.select(index0,QItemSelectionModel.Select)
                selm.select(index1,QItemSelectionModel.Select)
                selm.select(index2,QItemSelectionModel.Select)
            else:
                selm.select(index0,QItemSelectionModel.Deselect)
                selm.select(index1,QItemSelectionModel.Deselect)
                selm.select(index2,QItemSelectionModel.Deselect)

    def _loadstate(self):
        list=self.canvas.getWaveData(self.__dim)
        self.__model.clear()
        i=1
        for l in list:
            self.__model.setItem(len(list)-i,0,QStandardItem(l.wave.Name()))
            self.__model.setItem(len(list)-i,1,QStandardItem(self.canvas.axesName(l.axis)))
            self.__model.setItem(len(list)-i,2,QStandardItem(str(l.id)))
            i+=1
        self.OnDataSelected()
    def OnSelected(self):
        self.flg=True
        indexes=self.selectedIndexes()
        ids=[]
        for i in indexes:
            if i.column()==2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedIndexes(self.__dim,ids)
        self.flg=False
    def OnDataChanged(self):
        self._loadstate()
    def sizeHint(self):
        return QSize(150,100)
class DataShowButton(QPushButton):
    def __init__(self,canvas,dim,flg):
        if flg:
            super().__init__('Show')
        else:
            super().__init__('Hide')
        self.__flg=flg
        self.canvas=canvas
        self.clicked.connect(self.__clicked)
        self.__dim=dim
    def __clicked(self):
        list=self.canvas.getSelectedIndexes(self.__dim)
        if self.__flg:
            self.canvas.showData(self.__dim,list)
        else:
            self.canvas.hideData(self.__dim,list)
class RightClickableSelectionBox(DataSelectionBox):
    def __init__(self,canvas,dim):
        super().__init__(canvas,dim)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas=canvas
        self.__dim=dim
    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['Show', 'Hide', 'Remove', 'Display', 'Edit', 'Print']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        list=self.canvas.getSelectedIndexes(self.__dim)
        if action==None:
            return
        elif action.text() == 'Show':
            self.canvas.showData(self.__dim,list)
        elif action.text() == 'Hide':
            self.canvas.hideData(self.__dim,list)
        elif action.text() == 'Edit':
            from ExtendAnalysis.GraphWindow import Table
            t=Table()
            data=self.canvas.getDataFromIndexes(self.__dim,list)
            for d in data:
                t.Append(d.wave)
        elif action.text() == 'Display':
            from ExtendAnalysis.GraphWindow import Graph
            g=Graph()
            data=self.canvas.getDataFromIndexes(self.__dim,list)
            for d in data:
                g.Append(d.wave)
        elif action.text() == 'Remove':
            self.canvas.Remove(list)
        elif action.text() == 'Print':
            data=self.canvas.getDataFromIndexes(self.__dim,list)
            for d in data:
                print(d.wave.FileName())
class OffsetAdjustBox(QWidget):
    def __init__(self,canvas,dim):
        super().__init__()
        self.canvas=canvas
        canvas.addDataSelectionListener(self)
        self.__initlayout()
        self.__flg=False
        self.__dim=dim
    def __initlayout(self):
        vbox=QVBoxLayout()
        gr1=QGroupBox('Offset')
        gl=QGridLayout()
        self.__spin1=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin1.setDecimals(6)
        self.__spin2=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin2.setDecimals(6)
        self.__spin3=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin3.setDecimals(6)
        self.__spin4=QDoubleSpinBox(valueChanged=self.__dataChanged)
        self.__spin4.setDecimals(6)
        gl.addWidget(QLabel('x offset'),0,0)
        gl.addWidget(self.__spin1,1,0)
        gl.addWidget(QLabel('x muloffset'),2,0)
        gl.addWidget(self.__spin3,3,0)
        gl.addWidget(QLabel('y offset'),0,1)
        gl.addWidget(self.__spin2,1,1)
        gl.addWidget(QLabel('y muloffset'),2,1)
        gl.addWidget(self.__spin4,3,1)
        gr1.setLayout(gl)
        vbox.addWidget(gr1)

        gr2=QGroupBox('Side by side')
        g2=QGridLayout()
        self.__spinfrom=QDoubleSpinBox()
        self.__spinfrom.setRange(-np.inf,np.inf)
        self.__spindelta=QDoubleSpinBox()
        self.__spindelta.setRange(-np.inf,np.inf)
        g2.addWidget(QLabel('from'),0,0)
        g2.addWidget(self.__spinfrom,1,0)
        g2.addWidget(QLabel('delta'),0,1)
        g2.addWidget(self.__spindelta,1,1)

        btn=QPushButton('Set',clicked=self.__sidebyside)
        self.__type=QComboBox()
        self.__type.addItem('y offset')
        self.__type.addItem('x offset')
        self.__type.addItem('y muloffset')
        self.__type.addItem('x muloffset')
        g2.addWidget(QLabel('type'),0,2)
        g2.addWidget(self.__type,1,2)
        g2.addWidget(btn,2,1)
        gr2.setLayout(g2)
        vbox.addWidget(gr2)

        self.setLayout(vbox)
    def __sidebyside(self):
        indexes=self.canvas.getSelectedIndexes(self.__dim)
        f=self.__spinfrom.value()
        d=self.__spindelta.value()
        for i in range(len(indexes)):
            r=list(self.canvas.getOffset(indexes[i])[0])
            if self.__type.currentText()=='x offset':
                r[0]=f+d*i
            if self.__type.currentText()=='y offset':
                r[1]=f+d*i
            if self.__type.currentText()=='x muloffset':
                r[2]=f+d*i
            if self.__type.currentText()=='y muloffset':
                r[3]=f+d*i
            self.canvas.setOffset(r,indexes[i])
    def __dataChanged(self):
        if not self.__flg:
            indexes=self.canvas.getSelectedIndexes(self.__dim)
            self.canvas.setOffset((self.__spin1.value(),self.__spin2.value(),self.__spin3.value(),self.__spin4.value()),indexes)
    def OnDataSelected(self):
        self.__loadstate()
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedIndexes(self.__dim)
        if len(indexes)==0:
            return
        data=self.canvas.getOffset(indexes)[0]
        self.__spin1.setValue(data[0])
        self.__spin1.setRange(-np.inf,np.inf)
        self.__spin2.setValue(data[1])
        self.__spin2.setRange(-np.inf,np.inf)
        self.__spin3.setValue(data[2])
        self.__spin3.setRange(-np.inf,np.inf)
        self.__spin4.setValue(data[3])
        self.__spin4.setRange(-np.inf,np.inf)
        self.__flg=False
