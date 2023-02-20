from lys import DaskWave, filters
from lys.Qt import QtWidgets, QtCore


class PrefilterTab(QtWidgets.QWidget):
    filterApplied = QtCore.pyqtSignal(object)
    applied = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.__initlayout__()
        self.wave = None
        self.__outputShape = None

    def __initlayout__(self):
        self.filt = filters.FiltersGUI()
        apply = QtWidgets.QPushButton("Apply filters", clicked=self._click)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filt)
        layout.addWidget(apply)
        self.setLayout(layout)
        self.adjustSize()

    def setWave(self, wave):
        wave.persist()
        self.wave = wave
        self.filt.setDimension(self.wave.data.ndim)
        self._click()

    def _click(self):
        waves = DaskWave(self.wave, chunks="auto")
        waves = self.filt.GetFilters().execute(waves)
        if self.__outputShape != waves.data.ndim and self.__outputShape is not None:
            ret = QtWidgets.QMessageBox.information(self, "Caution", "The dimension of the processed wave will be changed and the graphs will be disconnected. Do you really want to proceed?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.No:
                return
        self.__outputShape = waves.data.ndim
        waves.persist()
        self.applied.emit(self.filt.GetFilters())
        self.filterApplied.emit(waves)
