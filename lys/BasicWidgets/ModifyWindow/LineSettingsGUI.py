
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ColorWidgets import *

class LineColorAdjustBox(ColorSelection):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.colorChanged.connect(self.__changed)
    def OnClicked(self):
        indexes=self.canvas.getSelectedIndexes(1)
        cols=self.canvas.getDataColor(indexes)
        if len(cols)==0:
            return
        super().OnClicked()
    def __changed(self):
        indexes=self.canvas.getSelectedIndexes(1)
        cols=self.canvas.getDataColor(indexes)
        if len(cols)==0:
            return
        self.canvas.setDataColor(self.getColor(),indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getDataColor(indexes)
        self.setColor(cols[0])
class LineColorSideBySideDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('Select colormap')
        self.__initlayout()

    def __initlayout(self):
        l=QVBoxLayout()
        ok=QPushButton('O K',clicked=self.accept)
        cancel=QPushButton('CANCEL',clicked=self.reject)
        h=QHBoxLayout()
        h.addWidget(ok)
        h.addWidget(cancel)
        self.csel = ColormapSelection()
        l.addWidget(self.csel)
        l.addLayout(h)
        self.setLayout(l)
    def getColor(self):
        return self.csel.currentColor()
class LineStyleAdjustBox(QGroupBox):
    __list=['solid','dashed','dashdot','dotted','None']
    def __init__(self,canvas):
        super().__init__("Line")
        self.canvas=canvas
        canvas.dataSelected.connect(self.OnDataSelected)

        layout=QGridLayout()
        self.__combo=QComboBox()
        self.__combo.addItems(LineStyleAdjustBox.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout.addWidget(QLabel('Type'),0,0)
        layout.addWidget(self.__combo,1,0)
        layout.addWidget(QLabel('Width'),0,1)
        layout.addWidget(self.__spin1,1,1)

        self.setLayout(layout)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setLineStyle(res,indexes)
    def __valueChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        self.canvas.setDataWidth(self.__spin1.value(),indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getLineStyle(indexes)
        res=cols[0]
        self.__combo.setCurrentIndex(LineStyleAdjustBox.__list.index(res))
        wids=self.canvas.getLineWidth(indexes)
        self.__spin1.setValue(wids[0])
class MarkerStyleAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Marker")
        self.canvas=canvas
        self.__list=list(canvas.getMarkerList().values())
        self.__fillist=canvas.getMarkerFillingList()
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()

    def __initlayout(self):
        gl=QGridLayout()

        self.__combo=QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__sizeChange)
        self.__fill=QComboBox()
        self.__fill.addItems(self.__fillist)
        self.__fill.activated.connect(self.__changeFilling)
        self.__spin2=QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__thickChange)

        gl.addWidget(QLabel('Type'),0,0)
        gl.addWidget(self.__combo,1,0)
        gl.addWidget(QLabel('Size'),2,0)
        gl.addWidget(self.__spin1,3,0)
        gl.addWidget(QLabel('Filling'),0,1)
        gl.addWidget(self.__fill,1,1)
        gl.addWidget(QLabel('Thick'),2,1)
        gl.addWidget(self.__spin2,3,1)
        self.setLayout(gl)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setMarker(res,indexes)
    def __changeFilling(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__fill.currentText()
        self.canvas.setMarkerFilling(res,indexes)
    def __sizeChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__spin1.value()
        self.canvas.setMarkerSize(res,indexes)
    def __thickChange(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        res=self.__spin2.value()
        self.canvas.setMarkerThick(res,indexes)
    def OnDataSelected(self):
        indexes=self.canvas.getSelectedIndexes(1)
        if len(indexes)==0:
            return
        cols=self.canvas.getMarker(indexes)
        self.__combo.setCurrentIndex(self.__list.index(cols[0]))
        cols=self.canvas.getMarkerSize(indexes)
        self.__spin1.setValue(cols[0])
        cols=self.canvas.getMarkerThick(indexes)
        self.__spin2.setValue(cols[0])
        cols=self.canvas.getMarkerFilling(indexes)
        self.__fill.setCurrentIndex(self.__fillist.index(cols[0]))
class ApperanceBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout()

        layout_h1=QHBoxLayout()
        layout_h1.addWidget(QLabel('Color'))
        layout_h1.addWidget(LineColorAdjustBox(canvas))
        btn=QPushButton('Side by Side',clicked=self.__sidebyside)
        layout_h1.addWidget(btn)
        layout.addLayout(layout_h1)
        layout.addWidget(LineStyleAdjustBox(canvas))
        layout.addWidget(MarkerStyleAdjustBox(canvas))

        self.setLayout(layout)
    def __sidebyside(self):
        d=LineColorSideBySideDialog()
        res=d.exec_()
        if res==QDialog.Accepted:
            c=d.getColor()
            print(c)
