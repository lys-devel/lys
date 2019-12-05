import weakref

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .AxisSettingsGUI import *

class MarginAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Margin (0 means auto)")
        self.canvas=canvas
        self._initlayout(canvas)
    def _valueChanged(self):
        self.canvas.setMargin(self._left.value(),self._right.value(),self._bottom.value(),self._top.value())
    def _initlayout(self,canvas):
        m=canvas.getMargin()
        lv=QVBoxLayout()

        lh1=QHBoxLayout()
        lh1.addWidget(QLabel('Left'))
        self._left=QDoubleSpinBox()
        self._left.setRange(0,1)
        self._left.setSingleStep(0.05)
        self._left.setValue(m[0])
        self._left.valueChanged.connect(self._valueChanged)
        lh1.addWidget(self._left)
        lh1.addWidget(QLabel('Right'))
        self._right=QDoubleSpinBox()
        self._right.setRange(0,1)
        self._right.setSingleStep(0.05)
        self._right.setValue(m[1])
        self._right.valueChanged.connect(self._valueChanged)
        lh1.addWidget(self._right)

        lh2=QHBoxLayout()
        lh2.addWidget(QLabel('Bottom'))
        self._bottom=QDoubleSpinBox()
        self._bottom.setRange(0,1)
        self._bottom.setSingleStep(0.05)
        self._bottom.setValue(m[2])
        self._bottom.valueChanged.connect(self._valueChanged)
        lh2.addWidget(self._bottom)
        lh2.addWidget(QLabel('Top'))
        self._top=QDoubleSpinBox()
        self._top.setRange(0,1)
        self._top.setSingleStep(0.05)
        self._top.setValue(m[3])
        self._top.valueChanged.connect(self._valueChanged)
        lh2.addWidget(self._top)

        lv.addLayout(lh1)
        lv.addLayout(lh2)
        self.setLayout(lv)
class ResizeBox(QGroupBox):
    class _AreaBox(QGroupBox):
        def __init__(self,title,canvas,axis):
            super().__init__(title)
            self._axis=axis
            self.canvas=canvas
            self._initlayout(canvas)
            self.__loadstate()
        def setPartner(self,partner):
            self._partner=weakref.ref(partner)
        def _initlayout(self,canvas):
            layout=QVBoxLayout()

            self.cw=QComboBox()
            self.cw.addItems(['Auto','Absolute','Per Unit','Aspect','Plan'])
            self.cw.activated.connect(self.__ModeChanged)
            layout.addWidget(self.cw)

            tmp=QHBoxLayout()
            self.spin1 = QDoubleSpinBox()
            self.spin1.valueChanged.connect(self.__Changed)
            self.spin1.setDecimals(5)
            self.lab1=QLabel(' * Height')
            tmp.addWidget(self.spin1)
            tmp.addWidget(self.lab1)
            layout.addLayout(tmp)

            tmp=QHBoxLayout()
            self.lab2_1=QLabel('*')
            self.lab2_2=QLabel('Range')
            self.combo2=AxisSelectionWidget(canvas)
            self.combo2.activated.connect(self.__Changed)
            tmp.addWidget(self.lab2_1)
            tmp.addWidget(self.combo2)
            tmp.addWidget(self.lab2_2)
            layout.addLayout(tmp)

            tmp=QHBoxLayout()
            self.lab3_1=QLabel('/')
            self.lab3_2=QLabel('Range')
            self.combo3=AxisSelectionWidget(canvas)
            self.combo3.activated.connect(self.__Changed)
            tmp.addWidget(self.lab3_1)
            tmp.addWidget(self.combo3)
            tmp.addWidget(self.lab3_2)
            layout.addLayout(tmp)

            self.setLayout(layout)
        def __loadstate(self):
            self.__loadflg=True
            lis1=['Auto','Absolute','Per Unit','Aspect','Plan']
            if self._axis==0:
                param=self.canvas.getSizeParams('Width')
            else:
                param=self.canvas.getSizeParams('Height')
            self.cw.setCurrentIndex(lis1.index(param[0]))
            self.spin1.setValue(param[1])
            lis2=self.canvas.axisList()
            try:
                self.combo2.setCurrentIndex(lis2.index(param[2]))
            except:
                self.combo2.setCurrentIndex(lis2.index('Left'))
            try:
                self.combo3.setCurrentIndex(lis2.index(param[3]))
            except:
                self.combo3.setCurrentIndex(lis2.index('Bottom'))
            self._setLook(param[0])
            self.__loadflg=False
        def __ModeChanged(self):
            if self.__loadflg:
                return
            self.__loadflg=True
            type=self.cw.currentText()
            size=self.canvas.getSize()
            if type=='Absolute':
                if self._axis==0:
                    self.spin1.setValue(size[0])
                else:
                    self.spin1.setValue(size[1])
            if type=='Aspect':
                if self._axis==0:
                    self.spin1.setValue(size[0]/size[1])
                else:
                    self.spin1.setValue(size[1]/size[0])
            if type=='Per Unit':
                if self._axis==0:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    ran=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[0]/abs(ran[1]-ran[0]))
                else:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Left'))
                    ran=self.canvas.getAxisRange('Left')
                    self.spin1.setValue(size[1]/abs(ran[1]-ran[0]))
            if type=='Plan':
                if self._axis==0:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    self.combo3.setCurrentIndex(self.canvas.axisList().index('Left'))
                    ran_l=self.canvas.getAxisRange('Left')
                    ran_b=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[0]/size[1]*abs(ran_l[1]-ran_l[0])/abs(ran_b[1]-ran_b[0]))
                else:
                    self.combo2.setCurrentIndex(self.canvas.axisList().index('Left'))
                    self.combo3.setCurrentIndex(self.canvas.axisList().index('Bottom'))
                    ran_l=self.canvas.getAxisRange('Left')
                    ran_b=self.canvas.getAxisRange('Bottom')
                    self.spin1.setValue(size[1]/size[0]*abs(ran_b[1]-ran_b[0])/abs(ran_l[1]-ran_l[0]))
            self.__loadflg=False
            self.__Changed()
        def __Changed(self):
            if self.__loadflg:
                return
            type=self.cw.currentText()
            self._setPartnerComboBox(type)
            self._setLook(type)
            val=self.spin1.value()
            axis1=self.combo2.currentText()
            axis2=self.combo3.currentText()
            if self._axis==0:
                self.canvas.setSizeByArray([type,val,axis1,axis2],'Width')
            else:
                self.canvas.setSizeByArray([type,val,axis1,axis2],'Height')

        def _setPartnerComboBox(self,type):
            part=self._partner()
            val=part.cw.currentIndex()
            part.cw.clear()
            if type in ['Auto','Absolute','Per Unit']:
                part.cw.addItems(['Auto','Absolute','Per Unit','Aspect','Plan'])
            else:
                part.cw.addItems(['Auto','Absolute','Per Unit'])
            part.cw.setCurrentIndex(val)
        def _setLook(self,type):
            if type=='Auto':
                self.spin1.hide()
                self.lab1.setText(' ')
                self._show(2,False)
                self._show(3,False)
            elif type=='Absolute':
                self.spin1.show()
                self.lab1.setText('cm')
                self._show(2,False)
                self._show(3,False)
            elif type=='Per Unit':
                self.spin1.show()
                self.lab1.setText('')
                self._show(2,True)
                self._show(3,False)
            elif type=='Aspect':
                self.spin1.show()
                if self._axis==0:
                    self.lab1.setText('*Height')
                else:
                    self.lab1.setText('*Width')
                self._show(2,False)
                self._show(3,False)
            elif type=='Plan':
                self.spin1.show()
                if self._axis==0:
                    self.lab1.setText('*Height')
                else:
                    self.lab1.setText('*Width')
                self._show(2,True)
                self._show(3,True)
        def _show(self,n,b,text='Range'):
            if n==2:
                if b:
                    self.lab2_1.setText('*')
                    self.lab2_2.setText(text)
                    self.combo2.show()
                else:
                    self.lab2_1.setText(' ')
                    self.lab2_2.setText(' ')
                    self.combo2.hide()
            if n==3:
                if b:
                    self.lab3_1.setText('/')
                    self.lab3_2.setText(text)
                    self.combo3.show()
                else:
                    self.lab3_1.setText(' ')
                    self.lab3_2.setText(' ')
                    self.combo3.hide()

    def __init__(self,canvas):
        super().__init__("Graph Size")
        self.canvas=canvas
        layout_h=QHBoxLayout(self)
        gw=self._AreaBox('Width',canvas,0)
        gh=self._AreaBox('Height',canvas,1)
        gw.setPartner(gh)
        gh.setPartner(gw)
        layout_h.addWidget(gw)
        layout_h.addWidget(gh)
        self.setLayout(layout_h)
