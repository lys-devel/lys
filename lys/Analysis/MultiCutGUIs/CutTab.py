import weakref
from lys.Qt import QtWidgets

from .WaveManager import ChildWavesGUI
from .AxesManager import AxesRangeWidget, FreeLinesWidget
from .AddWaveDialog import AddWaveDialog


class CutTab(QtWidgets.QTabWidget):
    def __init__(self, cui, gui):
        super().__init__()
        self._cui = cui
        self._gui = weakref.ref(gui)
        self.__initlayout__()

    @property
    def gui(self):
        return self._gui()

    def __initlayout__(self):
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QPushButton("Add", clicked=self._add))
        hbox.addWidget(QtWidgets.QPushButton("Typical", clicked=self.typical))

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(ChildWavesGUI(self._cui, self.gui.display))
        vbox.addLayout(hbox)

        make = QtWidgets.QGroupBox("Data")
        make.setLayout(vbox)

        vbox2 = QtWidgets.QVBoxLayout()
        vbox2.addWidget(make)
        vbox2.addWidget(self.gui.interactiveWidget())
        vbox2.addStretch()
        w = QtWidgets.QWidget()
        w.setLayout(vbox2)

        self.addTab(w, "Main")
        self.addTab(AxesRangeWidget(self._cui), "Range")
        self.addTab(FreeLinesWidget(self._cui), "Lines")

    def _add(self):
        d = AddWaveDialog(self, self._cui)
        if d.exec_():
            w = self._cui.addWave(d.getAxes(), filter=d.getFilter(), name=d.getName())
            if d.getDisplayMode() is not None:
                self.gui.display(w, type=d.getDisplayMode())

    def typical(self):
        dim = self._cui.getFilteredWave().ndim
        if dim == 2:
            self._typical2d()
        if dim == 3:
            self._typical3d()
        if dim == 4:
            self._typical4d()
        if dim == 5:
            self._typical5d()

    def _typical2d(self):
        self.gui.display(self._cui.addWave([0, 1]), pos=[0, 0], wid=[4, 4])

    def _typical3d(self):
        c2 = self.gui.display(self._cui.addWave([0, 1]), pos=[0, 0], wid=[3, 4])
        c1 = self.gui.display(self._cui.addWave([2]), pos=[3, 0], wid=[1, 4])
        self.gui.addLine(c1, orientation="vertical")
        self.gui.addRect(c2)

    def _typical4d(self):
        c1 = self.gui.display(self._cui.addWave([0, 1]), pos=[0, 0], wid=[4, 2])
        c2 = self.gui.display(self._cui.addWave([2, 3]), pos=[0, 2], wid=[4, 2])
        self.gui.AddRect(c1)
        self.gui.AddRect(c2)

    def _typical5d(self):
        c1 = self.gui.display(self._cui.addWave([0, 1]), pos=[0, 0], wid=[3, 2])
        c2 = self.gui.display(self._cui.addWave([2, 3]), pos=[0, 2], wid=[3, 2])
        c3 = self.gui.display(self._cui.addWave([4]), pos=[3, 0], wid=[1, 4])
        self.gui.addRect(c1)
        self.gui.addRect(c2)
        self.gui.addLine(c3, orientation="vertical")
