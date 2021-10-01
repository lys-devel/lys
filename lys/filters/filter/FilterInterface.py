import dask.array as da
from lys import Wave, DaskWave


class FilterInterface(object):
    def execute(self, wave, **kwargs):
        if isinstance(wave, DaskWave):
            return self._execute(wave, **kwargs)
        elif isinstance(wave, Wave):
            dw = DaskWave(wave)
            result = self._execute(dw, **kwargs)
            return result.compute()
        else:
            return self.execute(Wave(wave), **kwargs).data

    def _applyFunc(self, func, data, *args, **kwargs):
        if data.dtype == complex:
            return func(data.real, *args, **kwargs) + 1j * func(data.imag, *args, **kwargs)
        else:
            return func(data, *args, **kwargs)

    def generalizedFunction(self, wave, func, signature, axes, output_dtypes=None, output_sizes={}):
        if output_dtypes is None:
            output_dtypes = wave.data.dtype
        return da.gufunc(func, signature=signature, output_dtypes=output_dtypes, vectorize=True, allow_rechunk=True, axes=axes, output_sizes=output_sizes)

    def _execute(self, wave, **kwargs):
        pass

    def getParameters(self):
        raise NotImplementedError

    def getRelativeDimension(self):
        return 0

    def __str__(self):
        return self.__class__.__name__ + ": " + str(self.getParameters())


class EmptyFilter(FilterInterface):
    pass
