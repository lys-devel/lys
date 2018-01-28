import os,sys
from ExtendAnalysis.ExtendType import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from .Functions import *
from .Fitting import *

class FittingWidget(QWidget):
    def __init__(self,wavelist,canvas=None,path=None):
        super().__init__()
        self.canvas=canvas
        self.__initlayout(wavelist,path)
        self.adjustSize()
        self.updateGeometry()
        self.show()
        self.w_total=Wave()
        self.w_residual=Wave()
        self.w_peaks=[]
        self.id_peaks=[]
    def update(self):
        self.wave=Wave(home()+'/'+self._target.currentText())
        x=self.wave.x
        funcs, guess, bounds=self._tree.getParams()
        n=0
        i=0
        self.w_total.data=np.zeros((x.shape[0]))
        self.w_total.x=x
        for f in funcs:
            val=f.func(x, *guess[n:n+f.nparam()])
            self.w_peaks[i].data=val
            i+=1
            self.w_total.data+=val
            n+=f.nparam()
        self.w_residual.data=self.wave.data-self.w_total.data
        self.w_residual.x=x
        if self.save.isChecked():
            p=home()+'/'+self.path.text()
            mkdir(p)
            self.w_total.Save(p+'/total.npz')
            self.w_residual.Save(p+'/residual.npz')
            i=0
            for f in self.w_peaks:
                f.Save(p+'/peak'+str(i)+'.npz')
                i+=1
            self._tree.saveResult(p)
    def OnPeakAdded(self,int):
        w=Wave()
        self.w_peaks.append(w)
        if self.peaks.isChecked() and self.canvas is not None:
            self.id_peaks.append(self.canvas.Append(w))
        self.update()
    def OnPeakRemoved(self,row):
        if self.peaks.isChecked() and self.canvas is not None:
            self.canvas.Remove(self.id_peaks[row])
            self.id_peaks.remove(self.id_peaks[row])
    def __initlayout(self,wavelist,path):
        vbox1=QVBoxLayout()
        self._target=QComboBox()
        for w in wavelist:
            self._target.addItem(os.path.relpath(w.FileName(),home()))
        self._tree=FittingTree()
        self._tree.updated.connect(self.update)
        self._tree.peakAdded.connect(self.OnPeakAdded)
        self._tree.peakRemoved.connect(self.OnPeakRemoved)
        self._exec=QPushButton('Fit',clicked=self.__execute)
        vbox1.addWidget(self._target)
        hbox2=QHBoxLayout()
        self.save=QCheckBox('Save to')
        self.save.stateChanged.connect(self.__startsave)
        self.load=QPushButton('Load',clicked=self.__load)
        self.path=QLineEdit()
        if path is None:
            self.path.setText(os.path.relpath(pwd()+'/'+w.Name(),home()))
        else:
            self.path.setText(os.path.relpath(path,home()))
        hbox2.addWidget(self.save)
        hbox2.addWidget(self.path)
        hbox2.addWidget(self.load)
        vbox1.addLayout(hbox2)
        if self.canvas is not None:
            hbox1=QHBoxLayout()
            self.tot=QCheckBox('total')
            self.tot.stateChanged.connect(self.__totadd)
            hbox1.addWidget(self.tot)
            self.peaks=QCheckBox('peaks')
            self.peaks.stateChanged.connect(self.__peakadd)
            hbox1.addWidget(self.peaks)
            self.residual=QCheckBox('residual')
            self.residual.stateChanged.connect(self.__resadd)
            hbox1.addWidget(self.residual)
            vbox1.addLayout(hbox1)
        vbox1.addWidget(self._tree)
        vbox1.addWidget(self._exec)
        self.setLayout(vbox1)
    def __totadd(self):
        if self.canvas is not None:
            if self.tot.isChecked():
                self.tot_id=self.canvas.Append(self.w_total)
            else:
                self.canvas.Remove(self.tot_id)
    def __resadd(self):
        if self.canvas is not None:
            if self.residual.isChecked():
                self.res_id=self.canvas.Append(self.w_residual)
            else:
                self.canvas.Remove(self.res_id)
    def __peakadd(self):
        if self.canvas is not None:
            if self.peaks.isChecked():
                for w in self.w_peaks:
                    self.id_peaks.append(self.canvas.Append(w))
            else:
                self.canvas.Remove(self.id_peaks)
                self.id_peaks.clear()
    def __startsave(self):
        if self.save.isChecked():
            self.update()
        else:
            self.w_total.Disconnect()
            self.w_residual.Disconnect()
            for f in self.w_peaks:
                f.Disconnect()
    def __load(self):
        self._tree.loadResult(home()+'/'+self.path.text())
    def __execute(self):
        self.wave=Wave(home()+'/'+self._target.currentText())
        funcs, guess, bounds=self._tree.getParams()
        fit=Fitting()
        for f in funcs:
            fit.addFunction(f)
        res=fit.fit(self.wave.x, self.wave.data, guess=guess, bounds=bounds)
        self._tree.setParams(res[0])

class FittingTree(QTreeView):
    updated=pyqtSignal()
    peakAdded=pyqtSignal(int)
    peakRemoved=pyqtSignal(int)
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._model = QStandardItemModel(0, 2)
        self._model.setHeaderData(0, Qt.Horizontal, 'Name')
        self._model.setHeaderData(1, Qt.Horizontal, 'Value')
        self.setModel(self._model)
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.buildContextMenu )
        self.params=[]
    def addFunction(self):
        dialog=QDialog(self)
        v1=QVBoxLayout()
        combo=QComboBox()
        for f in ListOfFunctions.keys():
            combo.addItem(f)
        v1.addWidget(combo)
        h1=QHBoxLayout()
        ok=QPushButton('O K',clicked=dialog.accept)
        cancel=QPushButton('CALCEL',clicked=dialog.reject)
        h1.addWidget(ok)
        h1.addWidget(cancel)
        v1.addLayout(h1)
        dialog.setLayout(v1)
        result=dialog.exec_()
        if result:
            ftype=combo.currentText()
            self._addParam(ftype)

    class _SingleParam(QObject):
        updated=pyqtSignal()
        def __init__(self,name,parent,tree):
            super().__init__()
            self.child1=QStandardItem(name)
            self.child1.setCheckable(Qt.Checked)
            self.child1.setCheckState(Qt.Checked)
            child2=QStandardItem()
            parent.appendRow([self.child1, child2])
            self.value=QDoubleSpinBox()
            self.value.setDecimals(8)
            self.value.setMinimum(-np.inf)
            self.value.setMaximum(np.inf)
            self.value.valueChanged.connect(self.update)
            tree.setIndexWidget(child2.index(),self.value)
            self.min1=QStandardItem('min')
            self.min1.setCheckable(True)
            min2=QStandardItem()
            self.max1=QStandardItem('max')
            self.max1.setCheckable(True)
            max2=QStandardItem()
            self.child1.appendRow([self.min1, min2])
            self.child1.appendRow([self.max1, max2])
            self.minval=QDoubleSpinBox()
            self.minval.setDecimals(8)
            self.minval.setMinimum(-np.inf)
            self.minval.setMaximum(np.inf)
            self.maxval=QDoubleSpinBox()
            self.maxval.setDecimals(8)
            self.maxval.setMinimum(-np.inf)
            self.maxval.setMaximum(np.inf)
            tree.setIndexWidget(min2.index(),self.minval)
            tree.setIndexWidget(max2.index(),self.maxval)
        def getGuess(self):
            return self.value.value()
        def setGuess(self,value):
            self.value.setValue(value)
        def getBounds(self):
            min=-np.inf
            max=np.inf
            if not self.child1.checkState()==Qt.Checked:
                min=self.getGuess()
                max=self.getGuess()*1.0000000001
            else:
                if self.min1.checkState()==Qt.Checked:
                    min=self.minval.value()
                if self.max1.checkState()==Qt.Checked:
                    max=self.maxval.value()
            return (min,max)
        def update(self):
            self.updated.emit()
    def _addParam(self,ftype):
        dic={}
        parent=QStandardItem(ftype)
        self._model.appendRow(parent)
        dic['Func']=ListOfFunctions[ftype]
        params=dic['Func'].params()
        dic['Params']=[]
        for i in range(len(params)):
            d=self._SingleParam(params[i],parent,self)
            d.updated.connect(self.update)
            dic['Params'].append(d)
        self.params.append(dic)
        self.peakAdded.emit(len(self.params))
    def update(self):
        self.updated.emit()
    def removeFunction(self):
        for i in self.selectedIndexes():
            for j in range(self._model.rowCount()-1,-1,-1):
                if self._model.item(j,0).index()==i:
                    self._remove(j)
    def clear(self):
        for i in range(len(self.params)):
            self._remove(0)
    def _remove(self,i):
        self._model.removeRow(i)
        self.params.remove(self.params[i])
        self.peakRemoved.emit(i)

    def getParams(self):
        res_func=[]
        res_guess=[]
        res_bounds_min=[]
        res_bounds_max=[]
        for p in self.params:
            res_func.append(p['Func'])
            for s in p['Params']:
                res_guess.append(s.getGuess())
                b=s.getBounds()
                res_bounds_min.append(b[0])
                res_bounds_max.append(b[1])
        return res_func, res_guess, (res_bounds_min, res_bounds_max)
    def setParams(self,params):
        i=0
        for p in self.params:
            for s in p['Params']:
                s.setGuess(params[i])
                i+=1
    def buildContextMenu( self, qPoint ):
        menu = QMenu(self)
        menulabels = ['Add Function','Remove Function','Load from current folder']
        actionlist = []
        for label in menulabels:
            actionlist.append( menu.addAction( label ) )
        action = menu.exec_(QCursor.pos())
        if action is None:
            return
        if action.text()=='Add Function':
            self.addFunction()
        if action.text()=='Remove Function':
            self.removeFunction()
        if action.text()=='Load from current folder':
            self.loadResult()
    def saveResult(self,path):
        mkdir(path)
        d=Dict(path+'/FittingResult.dic')
        funcs, guess, bounds=self.getParams()
        d['npeaks']=len(funcs)
        i=0
        n=0
        for f in funcs:
            data=dict()
            data['function']=findFuncByInstance(f)
            data['guess']=guess[n:n+f.nparam()]
            n+=f.nparam()
            d['peak'+str(i)]=data
            i+=1
    def loadResult(self,path):
        if os.path.exists(path+'/FittingResult.dic'):
            self.clear()
            d=Dict(path+'/FittingResult.dic')
            for i in range(d['npeaks']):
                p=d['peak'+str(i)]
                self._addParam(p['function'])
                g=p['guess']
                j=0
                for s in self.params[len(self.params)-1]['Params']:
                    s.setGuess(g[j])
                    j+=1
        else:
            print('Fitting result is not found.')

def FuncSelectDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
