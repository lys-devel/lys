from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ..filtersGUI import *


class _chunkDialog(QDialog):
    class customSpinBox(QSpinBox):
        def __init__(self, value):
            super().__init__()
            self.setRange(-1, value)
            self.val = value
            self.vallist = self.make_divisors(value)
            self.vallist.insert(0, -1)
            self.setValue(value)

        def stepBy(self, steps):
            pos = self.vallist.index(self.value()) + steps
            if pos < 0:
                pos = 0
            if pos > len(self.vallist):
                pos = (self.vallist) - 1
            self.setValue(self.vallist[pos])

        def make_divisors(self, n):
            divisors = []
            for i in range(1, int(n**0.5) + 1):
                if n % i == 0:
                    divisors.append(i)
                    if i != n // i:
                        divisors.append(n // i)
            divisors.sort()
            return divisors

    def __init__(self, size):
        super().__init__(None)

        self.btn1 = QRadioButton("Auto")
        self.btn2 = QRadioButton("Custom")
        self.btn2.setChecked(True)

        self.ok = QPushButton("O K", clicked=self._ok)
        self.cancel = QPushButton("CANCEL", clicked=self._cancel)
        h1 = QHBoxLayout()
        h1.addWidget(self.ok)
        h1.addWidget(self.cancel)

        self.chunks = [self.customSpinBox(i) for i in size]
        h2 = QHBoxLayout()
        for c in self.chunks:
            h2.addWidget(c)

        layout = QVBoxLayout()
        layout.addWidget(self.btn1)
        layout.addWidget(self.btn2)
        layout.addLayout(h2)
        layout.addLayout(h1)
        self.setLayout(layout)

    def _ok(self):
        self.ok = True
        self.close()

    def _cancel(self):
        self.ok = False
        self.close()

    def getResult(self):
        if self.btn1.isChecked():
            return self.ok, "auto"
        else:
            return self.ok, tuple([c.value() for c in self.chunks])


class PrefilterTab(QWidget):

    filterApplied = pyqtSignal(object)

    def __init__(self, loader):
        super().__init__()
        self.__initlayout__(loader)
        self.wave = None
        self.__outputShape = None
        self.__chunk = "auto"

    def __initlayout__(self, loader):
        self.layout = QVBoxLayout()

        self.filt = FiltersGUI(regionLoader=loader)
        self.layout.addWidget(self.filt)
        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("Rechunk", clicked=self._chunk))
        h1.addWidget(QPushButton("Apply filters", clicked=self._click))
        self.layout.addLayout(h1)

        self.setLayout(self.layout)
        self.adjustSize()

    def setWave(self, wave):
        wave.persist()
        self.wave = wave
        self.filt.setDimension(self.wave.data.ndim)
        self._click()

    def _click(self):
        waves = DaskWave(self.wave, chunks=self.__chunk)
        self.filt.GetFilters().execute(waves)
        if self.__outputShape != waves.data.shape and self.__outputShape is not None:
            ret = QMessageBox.information(
                None, "Caution", "The shape of the processed wave will be changed and the graphs will be disconnected. Do you really want to proceed?", QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.No:
                return
        self.__outputShape = waves.data.shape
        waves.persist()
        self.filterApplied.emit(waves)

    def _chunk(self):
        if self.wave is None:
            return
        d = self._chunkDialog(self.wave.data.shape)
        d.exec_()
        ok, res = d.getResult()
        if ok:
            self.__chunk = res