from ExtendAnalysis import *

class MultiCut(AnalysisWindow):
    class _axisWidget(QWidget):
        def __init__(self, n):
            super().__init__()
            self.__initlayout(n)
        def __initlayout(self, n):
            self._check=QCheckBox("Axis "+str(n))
            self._type=QComboBox()
            self._type.addItems(["All", "Point", "Rect", "Circle"])
            layout=QGridLayout()
            layout.addWidget(self._check,0,0)
            layout.addWidget(self._type,0,1)
            self.setLayout(layout)
        def isChecked(self):
            return self._check.isChecked()
    def __init__(self):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
    def __initlayout__(self):
        disp=QPushButton("Display",clicked=self.display)
        pt=QPushButton("Point",clicked=self._point)
        rt=QPushButton("Rect",clicked=self._rect)
        cc=QPushButton("Circle",clicked=self._circle)

        hbtn=QHBoxLayout()
        hbtn.addWidget(pt)
        hbtn.addWidget(rt)
        hbtn.addWidget(cc)
        vbtn=QVBoxLayout()
        vbtn.addWidget(disp)
        vbtn.addLayout(hbtn)

        grp=QGroupBox("Interactive")
        grp.setLayout(vbtn)

        self.__file=QLineEdit()
        btn=QPushButton("Load",clicked=self.load)

        h1=QHBoxLayout()
        h1.addWidget(btn)
        h1.addWidget(self.__file)

        self.layout=QVBoxLayout()
        self.layout.addWidget(grp)
        self.layout.addLayout(h1)

        wid=QWidget()
        wid.setLayout(self.layout)
        self.setWidget(wid)
        self.adjustSize()
    def load(self,file):
        if file == False:
            fname = QFileDialog.getOpenFileName(self, 'Select data file')[0]
        else:
            fname=file
        if os.path.exists(fname):
            self.wave=LoadFile.load(fname)
            self.__file.setText(fname)
            self.__resetLayout()
    def __resetLayout(self):
        for i in range(len(self.wave.shape())):
            wid=self._axisWidget(i)
            self.axes.append(wid)
            self.layout.insertWidget(i,wid)
            self.adjustSize()
    def display(self):
        checked=[]
        for i in range(len(self.wave.shape())):
            if self.axes[i].isChecked():
                checked.append(i)
        if len(checked)==2:
            self._disp2D(checked)
        if len(checked)==1:
            self._disp1D(checked)
    def _disp2D(self,checked):
        j=0
        res=self.wave.data
        for i in range(len(self.wave.shape())):
            if i in checked:
                j+=1
            else:
                res=np.sum(res,axis=j)
        w=Wave()
        w.data=res
        display(w)
    def _point(self):
        pass
    def _rect(self):
        pass
    def _circle(self):
        pass

def create():
    win=MultiCut()
    win.load('/home/smb/data/STEMTest.npz')

addMainMenu(['Analysis','MultiCut'],create)
