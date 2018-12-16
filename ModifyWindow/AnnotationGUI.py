from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .FontGUI import *

class AnnotationSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self,canvas,type='text'):
            super().__init__(0,3)
            self.setHeaderData(0,Qt.Horizontal,'Line')
            self.setHeaderData(1,Qt.Horizontal,'Axis')
            self.setHeaderData(2,Qt.Horizontal,'Zorder')
            self.canvas=canvas
            self.type=type
        def clear(self):
            super().clear()
            self.setColumnCount(3)
            self.setHeaderData(0,Qt.Horizontal,'Annotation')
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
                    self.canvas.moveAnnotation(f,type=self.type)
                else:
                    self.canvas.moveAnnotation(f,self.item(row,2).text(),type=self.type)
            else:
                self.canvas.moveAnnotation(f,self.item(self.itemFromIndex(parent).row(),2).text(),type=self.type)
            self.canvas._emitAnnotationChanged()
            return False
    def __init__(self,canvas,type='text'):
        super().__init__()
        self.canvas=canvas
        self.__type=type
        self.__initlayout()
        self._loadstate()
        self.canvas.addAnnotationChangeListener(self,type)
        self.canvas.addAnnotationEditedListener(self,type)
        self.canvas.addAnnotationSelectedListener(self,type)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.flg=False
    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model=AnnotationSelectionBox._Model(self.canvas,self.__type)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)
    def OnAnnotationSelected(self):
        if self.flg:
            return
        self.flg=True
        indexes=self.canvas.getSelectedAnnotations(self.__type)
        list=self.canvas.getAnnotations(self.__type)
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
        self.flg=False
    def _loadstate(self):
        list=self.canvas.getAnnotations(self.__type)
        self.__model.clear()
        i=1
        for l in list:
            self.__model.setItem(len(list)-i,0,QStandardItem(l.name))
            self.__model.setItem(len(list)-i,1,QStandardItem(self.canvas.axesName(l.obj.axes)))
            self.__model.setItem(len(list)-i,2,QStandardItem(str(l.id)))
            i+=1

    def OnSelected(self):
        if self.flg:
            return
        self.flg=True
        indexes=self.selectedIndexes()
        ids=[]
        for i in indexes:
            if i.column()==2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedAnnotations(ids,self.__type)
        self.flg=False
    def OnAnnotationChanged(self):
        self._loadstate()
    def OnAnnotationEdited(self):
        list=self.canvas.getAnnotations(self.__type)
        i=1
        for l in list:
            self.__model.itemFromIndex(self.__model.index(len(list)-i,0)).setText(l.name)
            i+=1
    def sizeHint(self):
        return QSize(150,100)
    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menulabels = ['Show', 'Hide', 'Add', 'Remove']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        list=self.canvas.getSelectedAnnotations(self.__type)
        if action==None:
            return
        elif action.text() == 'Show':
            self.canvas.showAnnotation(list,self.__type)
        elif action.text() == 'Hide':
            self.canvas.hideAnnotation(list,self.__type)
        elif action.text() == 'Remove':
            self.canvas.removeAnnotation(list,self.__type)
        elif action.text() == 'Add':
            self.canvas.addText("")
class AnnotationEditBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.__flg=False
        self.__initlayout()
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        l=QVBoxLayout()
        self.__font=FontSelectWidget(self.canvas)
        self.__font.fontChanged.connect(self.__fontChanged)
        l.addWidget(self.__font)
        self.__txt=QTextEdit()
        self.__txt.textChanged.connect(self.__txtChanged)
        self.__txt.setMinimumHeight(10)
        self.__txt.setMaximumHeight(50)
        l.addWidget(self.__txt)
        self.setLayout(l)
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedAnnotations()
        if not len(indexes)==0:
            tmp=self.canvas.getAnnotationText(indexes)[0]
            self.__txt.setText(tmp)
            tmp=self.canvas.getAnnotationFontDefault(indexes)[0]
            self.__font.setFontDefault(tmp)
            tmp=self.canvas.getAnnotationFont(indexes)[0]
            self.__font.setFont(tmp)
        self.__flg=False
    def __txtChanged(self):
        if self.__flg:
            return
        txt=self.__txt.toPlainText()
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotationText(indexes,txt)
    def __fontChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        if self.__font.getFontDefault():
            self.canvas.setAnnotationFont(indexes,font='Text',default=True)
        else:
            self.canvas.setAnnotationFont(indexes,self.__font.getFont())
    def OnAnnotationSelected(self):
        self.__loadstate()
class AnnotationMoveBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.__initlayout()
        self.canvas=canvas
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        l=QVBoxLayout()
        self.__mode=QComboBox()
        self.__mode.addItems(['Absolute','Relative'])
        self.__mode.activated.connect(self.__chgMod)
        l.addWidget(self.__mode)
        gl=QGridLayout()
        self.__x=QDoubleSpinBox()
        self.__y=QDoubleSpinBox()
        self.__x.setRange(-float('inf'),float('inf'))
        self.__y.setRange(-float('inf'),float('inf'))
        self.__x.setDecimals(5)
        self.__y.setDecimals(5)
        self.__x.valueChanged.connect(self.__changePos)
        self.__y.valueChanged.connect(self.__changePos)
        gl.addWidget(QLabel('x'),0,0)
        gl.addWidget(QLabel('y'),0,1)
        gl.addWidget(self.__x,1,0)
        gl.addWidget(self.__y,1,1)
        l.addLayout(gl)
        self.setLayout(l)
    def OnAnnotationSelected(self):
        self.__loadstate()
    def __loadstate(self):
        list=self.canvas.getSelectedAnnotations()
        if len(list)==0:
            return
        tmp=self.canvas.getAnnotPositionMode(list)[0]
        self.__mode.setCurrentIndex(['Absolute','Relative'].index(tmp))
        tmp=self.canvas.getAnnotPosition(list)[0]
        self.__x.setValue(tmp[0])
        self.__y.setValue(tmp[1])
    def __chgMod(self):
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotPositionMode(indexes,self.__mode.currentText())
        self.__loadstate()
    def __changePos(self):
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotPosition(indexes,(self.__x.value(),self.__y.value()))
class AnnotationBoxAdjustBox(QWidget):
    list=['none','square','circle','round','round4','larrow','rarrow','darrow','roundtooth','sawtooth']
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.__initlayout()
        self.__flg=False
        self.canvas.addAnnotationSelectedListener(self)
    def __initlayout(self):
        gl=QGridLayout()
        gl.addWidget(QLabel('Mode'),0,0)
        self.__mode=QComboBox()
        self.__mode.addItems(self.list)
        self.__mode.activated.connect(self.__modeChanged)
        gl.addWidget(self.__mode,0,1)

        gl.addWidget(QLabel('Face Color'),1,0)
        self.__fc=ColorSelection()
        self.__fc.colorChanged.connect(self.__fcChanged)
        gl.addWidget(self.__fc,1,1)

        gl.addWidget(QLabel('Edge Color'),2,0)
        self.__ec=ColorSelection()
        self.__ec.colorChanged.connect(self.__ecChanged)
        gl.addWidget(self.__ec,2,1)

        self.setLayout(gl)
    def OnAnnotationSelected(self):
        self.__loadstate()
    def __loadstate(self):
        self.__flg=True
        indexes=self.canvas.getSelectedAnnotations()
        if not len(indexes)==0:
            tmp=self.canvas.getAnnotBoxStyle(indexes)[0]
            self.__mode.setCurrentIndex(self.list.index(tmp))
            tmp=self.canvas.getAnnotBoxColor(indexes)[0]
            self.__fc.setColor(tmp)
            tmp=self.canvas.getAnnotBoxEdgeColor(indexes)[0]
            self.__ec.setColor(tmp)
        self.__flg=False
    def __modeChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxStyle(indexes,self.__mode.currentText())
        self.__loadstate()
    def __fcChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxColor(indexes,self.__fc.getColor())
    def __ecChanged(self):
        if self.__flg:
            return
        indexes=self.canvas.getSelectedAnnotations()
        self.canvas.setAnnotBoxEdgeColor(indexes,self.__ec.getColor())
class AnnotationBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        layout=QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas))
        tab=QTabWidget()
        tab.addTab(AnnotationEditBox(canvas),'Text')
        tab.addTab(AnnotationMoveBox(canvas),'Position')
        tab.addTab(AnnotationBoxAdjustBox(canvas),'Box')
        layout.addWidget(tab)
        self.setLayout(layout)
