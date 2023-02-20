
from lys import Wave, DaskWave
from lys.Qt import QtWidgets, QtCore
from lys.widgets import LysSubWindow

from .MultiCut import MultiCutCUI
from .MultiCutGUIs import CutTab, AnimationTab, PrefilterTab, ExportDataTab
from .AxesRange import AxesRangeWidget, FreeLinesWidget
from .CanvasManager import CanvasManager


class MultipleGrid(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)

    def __initlayout(self):
        self.layout = QtWidgets.QGridLayout()
        w = QtWidgets.QWidget()
        w.setLayout(self.layout)
        self.setWidget(w)

    def Append(self, widget, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                wid = self.itemAtPosition(i, j)
                if wid is not None:
                    self.layout.removeWidget(wid)
                    wid.deleteLater()
        self.layout.addWidget(widget, x, y, w, h)

    def setSize(self, size):
        for s in range(size):
            self.layout.setColumnStretch(s, 1)
            self.layout.setRowStretch(s, 1)

    def itemAtPosition(self, i, j):
        item = self.layout.itemAtPosition(i, j)
        if item is not None:
            return item.widget()
        else:
            return None


class _GridAttachedWindow(LysSubWindow):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.grid = MultipleGrid()
        self.closeforce = False
        self.grid.closed.connect(self.forceclose)
        self.attach(self.grid)
        self.attachTo()
        self.adjustSize()
        self.updateGeometry()

    def forceclose(self):
        self.closeforce = True
        self.close()

    def closeEvent(self, event):
        if self.closeforce:
            event.accept()
            return super().closeEvent(event)
        else:
            self.hide()
            event.ignore()
            return


class MultiCut(_GridAttachedWindow):
    def __init__(self, wave=None):
        super().__init__("Multi-dimensional data analysis")
        self._cui = MultiCutCUI(wave)
        self._can = CanvasManager(self._cui)
        self.__initlayout__()
        self.wave = None
        self.axes = []
        self.ranges = []
        if wave is not None:
            self._load(wave)

    def test(self):
        obj = self._cui.addFreeLine([0, 1])
        g = self._can.createCanvas([0, 1], graph=True)
        f = g.addFreeRegionAnnotation()
        self._can.syncAnnotation(f, obj)

    def keyPress(self, e):
        if e.key() == QtCore.Qt.Key_M:
            self.show()

    def __exportTab(self):
        self._ani = AnimationTab(self._cut.getExecutorList())
        self._data = ExportDataTab()
        self._ani.updated.connect(self._cut.update)
        w = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(self._data)
        lay.addWidget(self._ani)
        lay.addStretch()
        w.setLayout(lay)
        return w

    def __initlayout__(self):
        self._pre = PrefilterTab()
        self._pre.filterApplied.connect(self._filterApplied)
        self._pre.applied.connect(self._cui.applyFilter)
        self._cut = CutTab(self, self.grid)
        self._ran = AxesRangeWidget(self._cui)
        self._line = FreeLinesWidget(self._cui)
        self._canl = self._can.widget()
        tab = QtWidgets.QTabWidget()
        tab.addTab(self._pre, "Prefilter")
        tab.addTab(self._cut, "Cut")
        tab.addTab(self.__exportTab(), "Export")
        tab.addTab(self._ran, "Range")
        tab.addTab(self._canl, "Canvas")
        tab.addTab(self._line, "Lines")

        self.__useDask = QtWidgets.QCheckBox("Dask")
        self.__useDask.setChecked(True)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.__useDask)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tab)
        layout.addLayout(h1)

        wid = QtWidgets.QWidget()
        wid.setLayout(layout)
        self.setWidget(wid)
        self.adjustSize()

    def _filterApplied(self, wave):
        if self.useDask():
            w = wave
            print("DaskWave set. shape = ", wave.data.shape, ", dtype = ", wave.data.dtype, ", chunksize = ", wave.data.chunksize)
        else:
            w = wave.compute()
            print("Wave set. shape = ", wave.data.shape, ", dtype = ", wave.data.dtype)
        self._cut._setWave(w)
        self._ani._setWave(w)
        self._data._setWave(w)

    def _load(self, file):
        if file is False:
            fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Select data file')[0]
        else:
            fname = file
        if isinstance(fname, str):
            self.wave = DaskWave(Wave(fname))
            self._pre.setWave(self.wave)
        elif isinstance(fname, Wave):
            self.wave = DaskWave(fname)
            self._pre.setWave(self.wave)
        elif isinstance(fname, DaskWave):
            self.wave = fname
            self._pre.setWave(self.wave)
        else:
            self._load(Wave(fname))

    def useDask(self):
        return self.__useDask.isChecked()
