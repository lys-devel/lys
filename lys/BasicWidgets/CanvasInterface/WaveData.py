from LysQt.QtCore import QObject, pyqtSignal


class WaveData(QObject):
    modified = pyqtSignal(QObject)

    def __init__(self, obj):
        super().__init__()
        self.obj = obj

    def __del__(self):
        self.wave.modified.disconnect(self._emitModified)

    def setMetaData(self, wave, axis, idn, appearance={}, offset=(0, 0, 0, 0), zindex=0, filter=None, filteredWave=None):
        self.wave = wave
        self.wave.modified.connect(self._emitModified)
        self.axis = axis
        self.id = idn
        self.appearance = appearance
        self.offset = offset
        self.zindex = zindex
        self.filter = filter
        if filteredWave is not None:
            self.filteredWave = filteredWave
        else:
            self.filteredWave = wave

    def _emitModified(self):
        self.modified.emit(self)


class LineData(WaveData):
    pass


class ImageData(WaveData):
    pass


class RGBData(WaveData):
    pass


class VectorData(WaveData):
    pass


class ContourData(WaveData):
    pass
