from LysQt.QtCore import QObject, pyqtSignal
from .SaveCanvas import CanvasPart


class WaveData(CanvasPart):
    modified = pyqtSignal(QObject)

    def __init__(self, canvas, obj):
        super().__init__(canvas)
        self.obj = obj
        self.appearance = {}

    def __del__(self):
        self.wave.modified.disconnect(self._emitModified)

    def setMetaData(self, wave, axis, idn, appearance={}, offset=(0, 0, 0, 0), zindex=0, filter=None, filteredWave=None):
        self.wave = wave
        self.wave.modified.connect(self._emitModified)
        self.axis = axis
        self.id = idn
        self.appearance.update(appearance)
        self.offset = offset
        self.zindex = zindex
        self.filter = filter
        if filteredWave is not None:
            self.filteredWave = filteredWave
        else:
            self.filteredWave = wave

    def _emitModified(self):
        self.modified.emit(self)

    def saveAppearance(self):
        """
        Save appearance from dictionary.

        Users can save/load appearance of data by save/loadAppearance methods.

        Return:
            dict: dictionary that include all appearance information.
        """
        return dict(self.appearance)

    def loadAppearance(self, appearance):
        """
        Load appearance from dictionary.

        Users can save/load appearance of data by save/loadAppearance methods.

        Args:
            appearance(dict): dictionary that include all appearance information, which is usually generated by :meth:`saveAppearance` method.
        """
        self._loadAppearance(appearance)

    def _loadAppearance(self, appearance):
        pass
