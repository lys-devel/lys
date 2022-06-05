
from lys import *
from lys.widgets import LysSubWindow
from .MultiCut import *
from .MultiCutGUIs import *


class MultipleGrid(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)

    def __initlayout(self):
        self.layout = QGridLayout()
        w = QWidget()
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


class GridAttachedWindow(LysSubWindow):
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


class MultiCut(GridAttachedWindow):
    def __init__(self, wave=None):
        super().__init__("Multi-dimensional analysis")
        self.__initlayout__()
        self.wave = None
        self.axes = []
        self.ranges = []
        if wave is not None:
            self.load(wave)

    def keyPress(self, e):
        if e.key() == Qt.Key_M:
            self.show()

    def __exportTab(self):
        self._ani = AnimationTab(self._cut.getExecutorList())
        self._data = ExportDataTab()
        self._ani.updated.connect(self._cut.update)
        w = QWidget()
        lay = QVBoxLayout(self)
        lay.addWidget(self._data)
        lay.addWidget(self._ani)
        lay.addStretch()
        w.setLayout(lay)
        return w

    def __initlayout__(self):
        self._pre = PrefilterTab(self._loadRegion)
        self._pre.filterApplied.connect(self._filterApplied)
        self._cut = CutTab(self, self.grid)
        tab = QTabWidget()
        tab.addTab(self._pre, "Prefilter")
        tab.addTab(self._cut, "Cut")
        tab.addTab(self.__exportTab(), "Export")

        self.__file = QLineEdit()
        btn = QPushButton("Load", clicked=self.load)
        self.__useDask = QCheckBox("Dask")
        self.__useDask.setChecked(True)

        h1 = QHBoxLayout()
        h1.addWidget(btn)
        h1.addWidget(self.__file)
        h1.addWidget(self.__useDask)

        layout = QVBoxLayout()
        layout.addWidget(tab)
        layout.addLayout(h1)

        wid = QWidget()
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

    def load(self, file):
        if file is False:
            fname = QFileDialog.getOpenFileName(self, 'Select data file')[0]
        else:
            fname = file
        if isinstance(fname, str):
            self.wave = DaskWave(Wave(fname))
            self.__file.setText(fname)
            self._pre.setWave(self.wave)
        elif isinstance(fname, Wave):
            self.wave = DaskWave(fname)
            self.__file.setText(fname.name)
            self._pre.setWave(self.wave)
        elif isinstance(fname, DaskWave):
            self.wave = fname
            self.__file.setText("from memory")
            self._pre.setWave(self.wave)
        else:
            self.load(Wave(fname))

    def _loadRegion(self, obj):
        g = Graph.active()
        c = g.canvas
        if c is not None:
            r = c.selectedRange()
            p1, p2 = r[0], r[1]
            axes = self._cut.findAxisFromCanvas(c)
            obj.setRegion(axes[0], (p1[0], p2[0]))
            obj.setRegion(axes[1], (p1[1], p2[1]))

    def useDask(self):
        return self.__useDask.isChecked()
