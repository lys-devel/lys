import weakref
from lys.Qt import QtWidgets

from .WaveManager import ChildWavesGUI
from .AxesManager import AxesRangeWidget, FreeLinesWidget
from .PrefilterTab import PrefilterTab
from .AnimationTab import AnimationTab
from .ExportDataTab import ExportDataTab
from .AddWaveDialog import AddWaveDialog
from .Template import TemplateDialog


class MultiCutTabs(QtWidgets.QTabWidget):
    def __init__(self, cui, gui):
        super().__init__()
        self.__initlayout__(cui, gui)

    def __initlayout__(self, cui, gui):
        self.addTab(MainWidget(cui, gui), "Main")
        self.addTab(PrefilterTab(cui), "Filter")
        self.addTab(AxesRangeWidget(cui), "Range")
        self.addTab(FreeLinesWidget(cui), "Lines")
        self.addTab(self.__exportTab(cui), "Export")

    def __exportTab(self, cui):
        self._ani = AnimationTab(cui)
        self._ani.updated.connect(self.update)
        self._data = ExportDataTab(cui)

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self._data)
        lay.addWidget(self._ani)
        lay.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(lay)
        return w


class MainWidget(QtWidgets.QWidget):
    def __init__(self, cui, gui, parent=None):
        super().__init__(parent)
        self._cui = cui
        self._cui.filterApplied.connect(self.__update)
        self._cui.dimensionChanged.connect(self.__update)
        self._gui = weakref.ref(gui)
        self.__initlayout()
        self.__update()

    @property
    def gui(self):
        return self._gui()

    def __initlayout(self):
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QPushButton("Add", clicked=self._add))
        hbox.addWidget(QtWidgets.QPushButton("Template", clicked=self._template))

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(ChildWavesGUI(self._cui, self.gui.display))
        vbox.addLayout(hbox)

        self._make = QtWidgets.QGroupBox("Data")
        self._make.setLayout(vbox)

        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.addWidget(self._make)
        vbox2.addWidget(self.gui.interactiveWidget())
        vbox2.addStretch()
        self.setLayout(vbox2)

    def __update(self):
        w = self._cui.getFilteredWave()
        txt = "Data shape: {0}, dtype: {1}".format(w.shape, w.dtype)
        self._make.setTitle(txt)

    def _add(self):
        d = AddWaveDialog(self, self._cui)
        if d.exec_():
            w = self._cui.addWave(d.getAxes(), filter=d.getFilter(), name=d.getName())
            if d.getDisplayMode() is not None:
                self.gui.display(w, type=d.getDisplayMode())

    def _template(self):
        d = TemplateDialog(self, self._cui.getFilteredWave().ndim, self.gui)
        d.exec_()
