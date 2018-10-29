import numpy as np
from matplotlib.figure import Figure, SubplotParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import cm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

#Before import this file, be sure that QGuiApplication instance is initialized.

class ColorSelection(QPushButton):
    colorChanged=pyqtSignal()
    def __init__(self):
        super().__init__()
        self.clicked.connect(self.OnClicked)
        self.__color="black"
    def OnClicked(self):
        res=QColorDialog.getColor(QColor(self.getColor()))
        if res.isValid():
            self.setColor(res.name())
            self.colorChanged.emit()
    def setColor(self,color):
        if isinstance(color,tuple):
            if len(color)==4:
                self.__color="rgba"+str((color[0]*255,color[1]*255,color[2]*255,color[3]))
            if len(color)==3:
                self.__color="rgba"+str((color[0]*255,color[1]*255,color[2]*255,1))
        else:
            self.__color=color
        self.setStyleSheet("background-color:"+self.__color)
    def getColor(self):
        return self.__color

cmaps = [('Perceptually Uniform Sequential', [
            'viridis', 'plasma', 'inferno', 'magma']),
         ('Sequential', [
            'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
            'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
            'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']),
         ('Sequential (2)', [
            'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
            'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
            'hot', 'afmhot', 'gist_heat', 'copper']),
         ('Diverging', [
            'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
            'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']),
         ('Qualitative', [
            'Pastel1', 'Pastel2', 'Paired', 'Accent',
            'Dark2', 'Set1', 'Set2', 'Set3']),
         ('Miscellaneous', [
            'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
            'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'hsv',
            'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'])]
cmapdic={}

def cmap2pixmap(cmap, steps=128):
    sm = cm.ScalarMappable(cmap=cmap)
    sm.norm.vmin = 0.0
    sm.norm.vmax = 1.0
    inds = np.linspace(0, 1, steps)
    rgbas = sm.to_rgba(inds)
    rgbas = [QColor(int(r * 255), int(g * 255),
                    int(b * 255), int(a * 255)).rgba() for r, g, b, a in rgbas]
    im = QImage(steps, 1, QImage.Format_Indexed8)
    im.setColorTable(rgbas)
    for i in range(steps):
        im.setPixel(i, 0, i)
    im = im.scaled(100, 15)
    pm = QPixmap.fromImage(im)
    return pm
def loadCmaps():
    for item in cmaps:
        for i in item[1]:
            cmapdic[i]=cmap2pixmap(i)
loadCmaps()
class ColormapSelection(QWidget):
    colorChanged=pyqtSignal()
    class ColorCombo(QComboBox):
        def __init__(self):
            super().__init__()
            model=QStandardItemModel()
            self.setModel(model)
            self.__list=[]
            n=0
            for item in cmaps:
                for i in item[1]:
                    data=QStandardItem(i)
                    data.setData(cmapdic[i],Qt.DecorationRole)
                    model.setItem(n,data)
                    self.__list.append(i)
                    n+=1
        def setColormap(self,cmap):
            self.setCurrentIndex(self.__list.index(cmap))
    def __init__(self):
        super().__init__()
        self.__combo=ColormapSelection.ColorCombo()
        self.__combo.activated.connect(self.__changed)
        self.__check=QCheckBox("Reverse")
        self.__check.stateChanged.connect(self.__changed)
        self.__log=QCheckBox("Log")
        self.__log.stateChanged.connect(self.__changed)
        layout=QVBoxLayout()

        layout_h=QHBoxLayout()
        layout_h.addWidget(QLabel('Colormaps'))
        layout_h.addWidget(self.__check)
        layout_h.addWidget(self.__log)

        layout.addLayout(layout_h)
        layout.addWidget(self.__combo)
        self.setLayout(layout)
    def __changed(self):
        self.colorChanged.emit()
    def setColormap(self,cmap):
        tmp=cmap.split('_')
        self.__combo.setColormap(tmp[0])
        self.__check.setChecked(not len(tmp)==1)
    def currentColor(self):
        if self.__check.isChecked():
            return self.__combo.currentText()+"_r"
        else:
            return self.__combo.currentText()
    def currentColorMaps(self):
        return cmapdic[self.currentColor()]
    def isLog(self):
        return self.__log.isChecked()
    def setLog(self,value):
        self.__log.setChecked(value)
