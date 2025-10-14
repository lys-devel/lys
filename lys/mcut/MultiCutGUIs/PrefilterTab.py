from lys import filters
from lys.Qt import QtWidgets, QtCore


class PrefilterTab(QtWidgets.QWidget):
    filterApplied = QtCore.pyqtSignal(object)

    def __init__(self, cui):
        super().__init__()
        self._cui = cui
        self.__initlayout__()
        self._filt.setDimension(cui.getRawWave().ndim)
        self._dim = 0
        self.filterApplied.connect(self._cui.applyFilter)
        self._cui.rawDataChanged.connect(self.__label)

    def __initlayout__(self):
        self._label = QtWidgets.QLabel()
        self._filt = filters.FiltersGUI()
        self.__label()
        apply = QtWidgets.QPushButton("Apply filters", clicked=self._update)

        self.__useDask = QtWidgets.QCheckBox("Use dask for postprocess (recommended)", toggled=self._cui.useDask)
        self.__useDask.setChecked(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._label)
        layout.addWidget(self._filt)
        layout.addWidget(self.__useDask)
        layout.addWidget(apply)
        self.setLayout(layout)
        self.adjustSize()

    def __label(self):
        w = self._cui.getRawWave()
        txt = "shape: {0}, dtype: {1}, chunk: {2}".format(w.shape, w.dtype, w.chunksize)
        self._label.setText(txt)
        self._filt.setDimension(w.ndim)

    def _update(self):
        dim = self._filt.getFilters().getRelativeDimension()
        if self._dim != dim:
            ret = QtWidgets.QMessageBox.information(self, "Caution", "The dimension of the processed wave will be changed and the graphs will be disconnected. Do you really want to proceed?", QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if ret == QtWidgets.QMessageBox.No:
                return
        self._dim = dim
        self.filterApplied.emit(self._filt.getFilters())
