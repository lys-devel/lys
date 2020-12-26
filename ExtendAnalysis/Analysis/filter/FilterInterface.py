import numpy as np
from ExtendAnalysis import Wave, DaskWave


class FilterInterface(object):
    def execute(self, wave, **kwargs):
        if isinstance(wave, np.ndarray):
            self.execute(Wave(wave), **kwargs)
        if isinstance(wave, Wave) or isinstance(wave, DaskWave):
            self._execute(wave, **kwargs)
        if hasattr(wave, "__iter__"):
            for w in wave:
                self.execute(w, **kwargs)

    def _applyFunc(self, func, data, *args, **kwargs):
        if data.dtype == complex:
            return func(data.real, *args, **kwargs) + 1j * func(data.imag, *args, **kwargs)
        else:
            return func(data, *args, **kwargs)

    def _execute(self, wave, **kwargs):
        pass

    def getRelativeDimension(self):
        return 0
