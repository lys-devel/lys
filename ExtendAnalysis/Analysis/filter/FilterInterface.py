import numpy as np
import dask.array as da
from ExtendAnalysis import Wave, DaskWave


class FilterInterface(object):
    def execute(self, wave, **kwargs):
        if isinstance(wave, np.ndarray):
            return self.execute(Wave(wave), **kwargs)
        if isinstance(wave, DaskWave):
            return self._execute(wave, **kwargs)
        if isinstance(wave, Wave):
            dw = DaskWave(wave)
            self._execute(dw, **kwargs)
            res = dw.toWave()
            wave.data = res.data
            wave.axes = res.axes
            return wave
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

    def generalizedFunction(self, wave, func, signature, axes, output_dtypes=None, output_sizes={}):
        if output_dtypes is None:
            output_dtypes = wave.data.dtype
        return da.gufunc(func, signature=signature, output_dtypes=output_dtypes, vectorize=True, allow_rechunk=True, axes=axes, output_sizes=output_sizes)


class EmptyFilter(FilterInterface):
    pass
