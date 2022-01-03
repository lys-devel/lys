import warnings
from lys.errors import NotImplementedWarning

from .SaveCanvas import saveCanvas
from .WaveData import WaveData


class ContourData(WaveData):
    def __init__(self, canvas, obj):
        super().__init__(canvas, obj)
        # self.appearanceSet.connect(self._loadAppearance)
