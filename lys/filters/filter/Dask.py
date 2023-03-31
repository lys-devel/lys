
from lys import DaskWave
from lys.Qt import QtWidgets
from lys.filters import FilterInterface, FilterSettingBase, filterGUI, addFilter


class RechunkFilter(FilterInterface):
    """
    Rechunk dask array

    Users should proper chunk size for efficient parallel calculation for dask array.

    RechunkFilter enables users to rechunk dask array manually.

    See dask manual (https://docs.dask.org/en/latest/array-chunks.html) for detail.

    Args:
        chunks('auto' or tuple of int): chunk size.
    """

    def __init__(self, chunks="auto"):
        self._chunks = chunks

    def _execute(self, wave, *args, **kwargs):
        return DaskWave(wave, chunks=self._chunks)

    def getParameters(self):
        return {"chunks": self._chunks}


@filterGUI(RechunkFilter)
class _RechunkSetting(FilterSettingBase):
    def __init__(self, dimension=2):
        super().__init__(dimension)

        self._chunk = [QtWidgets.QSpinBox() for _ in range(dimension)]
        grid = QtWidgets.QGridLayout()
        for i in range(dimension):
            grid.addWidget(QtWidgets.QLabel("Dim " + str(i + 1)), 0, i)
            self._chunk[i].setRange(1, 100000000)
            grid.addWidget(self._chunk[i], 1, i)

        self._auto = QtWidgets.QRadioButton("Auto", toggled=self._toggled)
        self._custom = QtWidgets.QRadioButton("Custom", toggled=self._toggled)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self._auto)
        h1.addWidget(self._custom)

        self._auto.setChecked(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h1)
        layout.addLayout(grid)
        self.setLayout(layout)

    def _toggled(self):
        for spin in self._chunk:
            spin.setEnabled(not self._auto.isChecked())

    def getParameters(self):
        if self._auto.isChecked():
            return {"chunks": "auto"}
        else:
            return {"chunks": [s.value() for s in self._chunk]}

    def setParameters(self, chunks):
        if chunks == "auto":
            self._auto.setChecked(True)
        else:
            self._custom.setChecked(True)
            for c, s in zip(chunks, self._chunk):
                s.setValue(c)


addFilter(RechunkFilter, gui=_RechunkSetting, guiName="Rechunk", guiGroup="Dask")
