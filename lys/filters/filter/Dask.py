
from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter

from .FilterInterface import FilterInterface
from .CommonWidgets import QSpinBox, QGridLayout, QLabel


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
        self._chunk = [QSpinBox() for _ in range(dimension)]
        grid = QGridLayout()
        for i in range(dimension):
            grid.addWidget(QLabel("Dim " + str(i + 1)), 0, i)
            grid.addWidget(self._chunk[i], 1, i)
        self.setLayout(grid)

    def getParameters(self):
        return {"chunks": [s.value() for s in self._chunk]}

    def setParameters(self, chunks):
        for c, s in zip(chunks, self._chunk):
            s.setValue(c)


addFilter(RechunkFilter, gui=_RechunkSetting, guiName="Rechunk")