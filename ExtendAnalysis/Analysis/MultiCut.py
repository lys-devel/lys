from ExtendAnalysis import *

class MultiCut(AnalysisWindow):
    class _axisWidget(QWidget):
        valueChanged=pyqtSignal(object,object)
        def __init__(self, n):
            super().__init__()
            self.__initlayout(n)
        def __initlayout(self, n):
            self._check=QCheckBox("Axis "+str(n))
            self._type=QComboBox()
            self._type.addItems(["All", "Point", "Rect", "Circle"])

            h1=QHBoxLayout()
            h1.addWidget(self._check)
            h1.addWidget(self._type)

            h2=QHBoxLayout()
            self.v1=QSpinBox()
            self.v2=QSpinBox()
            self.v1.setRange(0,10000000)
            self.v2.setRange(0,10000000)
            h2.addWidget(self.v1)
            h2.addWidget(self.v2)
            self.layout=QVBoxLayout()
            self.layout.addLayout(h1)
            self.layout.addLayout(h2)
            self.setLayout(self.layout)
        def isChecked(self):
            return self._check.isChecked()
        def setRect(self,index):
            self.index=index
            self._type.setCurrentText("Rect")
        def callback(self,roi):
            index=self.index
            val=self,roi.pos()+roi.size()
            self.v1.setValue(roi.pos()[index])
            self.v2.setValue(roi.pos()[index]+roi.size()[index])
            self.valueChanged.emit(self,(self.v1.value(),self.v2.value()))
    def __init__(self):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave=None
        self.axes=[]
        self.ranges=[]
        self.__graphs=[]
        self.__graphAxis=[]
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
            wid.valueChanged.connect(self.callback)
            self.axes.append(wid)
            self.ranges.append([None])
            self.layout.insertWidget(i,wid)
            self.adjustSize()
    def display(self):
        checked=[]
        for i in range(len(self.wave.shape())):
            if self.axes[i].isChecked():
                checked.append(i)
        if len(checked)==2:
            g=self._disp2D(checked)
        elif len(checked)==1:
            self._disp1D(checked)
        else:
            return
        self.__graphs.append(g)
        self.__graphAxis.append(checked)
        g.closed.connect(self.__graphClosed)
    def __graphClosed(self,graph):
        i=self.__graphs.index(graph)
        self.__graphs.pop(i)
        self.__graphAxis.pop(i)
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
        return display(w)
    def _point(self):
        pass
    def _rect(self):
        g=Graph.active()
        i=self.__graphs.index(g)
        ax=self.__graphAxis[i]
        id=g.canvas.addRect([0,0],[1,1])
        k=0
        for n in ax:
            self.axes[n].setRect(k)
            k+=1
            g.canvas.addCallback(id,self.axes[n].callback)
    def _circle(self):
        pass
    def callback(self,axis,r):
        index=self.axes.index(axis)
        self.ranges[index]=r
        self.update(index)
    def update(self,index):
        for g, axs in zip(self.__graphs,self.__graphAxis):
            if not index in axs:
                w=g.canvas.getWaveData()[0].wave
                w.data=self._int2D(axs)
    def _int2D(self,checked):
        import time
        start=time.time()
        j=0
        sl=[slice(None)]*len(self.wave.shape())
        for i in range(len(self.wave.shape())):
            if not i in checked:
                sl[i]=slice(*self.ranges[i])
        res=self.wave.data[tuple(sl)]
        for i in range(len(self.wave.shape())):
            if i in checked:
                j+=1
            else:
                res=np.sum(res,axis=j)
        print(time.time()-start)
        return res

def create():
    win=MultiCut()
    win.load('/home/smb/data/STEMTest.npz')

addMainMenu(['Analysis','MultiCut'],create)
