import dask.array as da
from lys import Wave, DaskWave


class FilterInterface:
    """
    FilterInterface is a base class of all filters in lys.

    All filters can be applid by :meth:`execute` method.

    Example:

        Apply filter to Wave

        >>> from lys import Wave, filters
        >>> w = Wave(np.ones(3,4), [2,3,4], [5,6,7,8])
        >>> f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
        >>> result = f.execute(w)

    """

    def execute(self, wave, *args, **kwargs):
        """
        Execute filter to *wave*

        Args:
            wave(Wave or DaskWave): Wave that the filter is applied
            *args(any): additional parameters
            *kwargs(any): additional keyward parameters

        """
        if isinstance(wave, DaskWave):
            return self._execute(wave, *args, **kwargs)
        elif isinstance(wave, Wave):
            dw = DaskWave(wave)
            result = self._execute(dw, *args, **kwargs)
            return result.compute()
        else:
            return self.execute(Wave(wave), *args, **kwargs).data

    def _applyFunc(self, func, data, *args, **kwargs):
        if data.dtype == complex:
            return func(data.real, *args, **kwargs) + 1j * func(data.imag, *args, **kwargs)
        else:
            return func(data, *args, **kwargs)

    def _generalizedFunction(self, wave, func, signature, axes, output_dtypes=None, output_sizes={}):
        if output_dtypes is None:
            output_dtypes = wave.data.dtype
        return da.gufunc(func, signature=signature, output_dtypes=output_dtypes, vectorize=True, allow_rechunk=True, axes=axes, output_sizes=output_sizes)

    def _execute(self, wave, *axes, **kwargs):
        pass

    def getParameters(self):
        """Returns parameters used for this filter as dict"""
        raise NotImplementedError

    def getRelativeDimension(self):
        """Returns change of dimension for this filter"""
        return 0

    def __str__(self):
        return self.__class__.__name__ + ": " + str(self.getParameters())

    def saveAsFile(self, file):
        """
        Save filter as file.

        Saved filters can be read from file by :meth:`.filters.filters.loadFrom`

        Args:
            file(str): filename

        Example:
            >>> from lys import filters
            >>> f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
            >>> f.saveAsFile("filter.fil")

        """
        from .filters import Filters
        f = Filters([self])
        f.saveAsFile(file)


class EmptyFilter(FilterInterface):
    def __init__(self):
        pass

    def _execute(self, wave, *args, **kwargs):
        return wave

    def getParameters(self):
        return {}
