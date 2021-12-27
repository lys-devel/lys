class WaveData(object):
    def __init__(self, obj):
        self.obj = obj

    def setMetaData(self, wave, axis, idn, appearance={}, offset=(0, 0, 0, 0), zindex=0, contour=False, filter=None, vector=False, filteredWave=None):
        self.wave = wave
        self.axis = axis
        #self.axes = axes
        self.id = idn
        self.appearance = appearance
        self.offset = offset
        self.zindex = zindex
        self.contour = contour
        self.vector = vector
        self.filter = filter
        if filteredWave is not None:
            self.filteredWave = filteredWave
        else:
            self.filteredWave = wave


class LineData(WaveData):
    pass
