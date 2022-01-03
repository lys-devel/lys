import warnings
from lys.errors import NotImplementedWarning

from .SaveCanvas import saveCanvas
from .WaveData import WaveData


class ContourData(WaveData):
    def __init__(self, canvas, wave, axis):
        super().__init__(canvas, wave, axis)
        # self.appearanceSet.connect(self._loadAppearance)
