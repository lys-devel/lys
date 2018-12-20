from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from .ColorWidgets import *
from .AnnotationGUI import *

class LineAnnotColorAdjustBox(ColorSelection):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        canvas.addAnnotationSelectedListener(self)
        self.colorChanged.connect(self.__changed)
    def OnClicked(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        cols=self.canvas.getAnnotLineColor(indexes)
        if len(cols)==0:
            return
        super().OnClicked()
    def __changed(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        cols=self.canvas.getAnnotLineColor(indexes)
        if len(cols)==0:
            return
        self.canvas.setAnnotLineColor(self.getColor(),indexes)
    def OnAnnotationSelected(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        cols=self.canvas.getAnnotLineColor(indexes)
        self.setColor(cols[0])
class AnnotLineStyleAdjustBox(QGroupBox):
    __list=['solid','dashed','dashdot','dotted','None']
    def __init__(self,canvas):
        super().__init__("Line")
        self.canvas=canvas
        canvas.addAnnotationSelectedListener(self)

        layout=QGridLayout()
        self.__combo=QComboBox()
        self.__combo.addItems(AnnotLineStyleAdjustBox.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout.addWidget(QLabel('Type'),0,0)
        layout.addWidget(self.__combo,1,0)
        layout.addWidget(QLabel('Width'),0,1)
        layout.addWidget(self.__spin1,1,1)

        self.setLayout(layout)

    def __changeStyle(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        res=self.__combo.currentText()
        self.canvas.setAnnotLineStyle(res,indexes)
    def __valueChange(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        self.canvas.setAnnotLineWidth(self.__spin1.value(),indexes)
    def OnAnnotationSelected(self):
        indexes=self.canvas.getSelectedAnnotations('line')
        if len(indexes)==0:
            return
        cols=self.canvas.getAnnotLineStyle(indexes)
        res=cols[0]
        self.__combo.setCurrentIndex(AnnotLineStyleAdjustBox.__list.index(res))
        wids=self.canvas.getAnnotLineWidth(indexes)
        self.__spin1.setValue(wids[0])
class LineAnnotationBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        layout=QVBoxLayout()
        layout.addWidget(AnnotationSelectionBox(canvas,'line'))
        tab=QTabWidget()
        lv1=QVBoxLayout()
        lv1.addWidget(LineAnnotColorAdjustBox(canvas))
        lv1.addWidget(AnnotLineStyleAdjustBox(canvas))
        w=QWidget()
        w.setLayout(lv1)
        tab.addTab(w,'Appearance')
        layout.addWidget(tab)
        self.setLayout(layout)