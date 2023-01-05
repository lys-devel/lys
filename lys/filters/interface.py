import sys
import _pickle as cPickle
import dask.array as da

from lys import Wave, DaskWave
from lys.Qt import QtCore, QtWidgets

from . import getFilter


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

    def __add__(self, filt):
        from lys.filters import Filters
        if isinstance(self, Filters):
            f1 = self.getFilters()
        else:
            f1 = [self]
        if isinstance(filt, Filters):
            f2 = filt.getFilters()
        else:
            f2 = [filt]
        return Filters([*f1, *f2])

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
        from lys.filters import Filters
        f = Filters([self])
        f.saveAsFile(file)


def filterGUI(filterClass):
    def _filterGUI(cls):
        cls._filClass = filterClass
        return cls
    return _filterGUI


class FilterSettingBase(QtWidgets.QWidget):
    dimensionChanged = QtCore.pyqtSignal()

    def __init__(self, dimension):
        super().__init__()
        self.dim = dimension

    def GetFilter(self):
        return self._filClass(**self.getParameters())

    @classmethod
    def getFilterClass(cls):
        if hasattr(cls, "_filClass"):
            return cls._filClass

    def getDimension(self):
        return self.dim

    def setParameters(self, **kwargs):
        raise NotImplementedError("Method setParameters should be implemented.")

    def getParameters(self):
        raise NotImplementedError("Method getParameters should be implemented.")


class Filters(FilterInterface):
    def __init__(self, filters):
        self._filters = []
        if isinstance(filters, Filters):
            self._filters.extend(filters._filters)
        for f in filters:
            if isinstance(f, Filters):
                self._filters.extend(f._filters)
            else:
                self._filters.append(f)

    def _execute(self, wave, *args, **kwargs):
        for f in self._filters:
            wave = f.execute(wave, *args, **kwargs)
        return wave

    def getParameters(self):
        return {"filters": self._filters}

    def getRelativeDimension(self):
        return sum([f.getRelativeDimension() for f in self._filters])

    def __str__(self):
        result = []
        for f in self._filters:
            d = f.getParameters()
            d["filterName"] = f.__class__.__name__
            result.append(d)
        return str(result)

    def insert(self, index, obj):
        self._filters.insert(index, obj)

    def append(self, obj):
        self._filters.append(obj)

    def getFilters(self):
        return self._filters

    @staticmethod
    def toString(filter):
        if isinstance(filter, Filters):
            return str(filter)
        else:
            return str(Filters([filter]))

    @staticmethod
    def fromString(data):
        if isinstance(data, str):
            data = eval(data)
        if isinstance(data, list):
            res = Filters._restoreFilter(data)
        else:  # backward compability
            data = data.replace(b"ExtendAnalysis.Analysis.filters", b"lys.filters")
            data = data.replace(b"ExtendAnalysis.Analysis.filter", b"lys.filters.filter")
            res = cPickle.loads(data)
        return res

    @staticmethod
    def _restoreFilter(data):
        # parse from list of parameter dictionary
        result = []
        for f in data:
            fname = f["filterName"]
            del f["filterName"]
            filt = getFilter(fname)
            if filt is not None:
                result.append(filt(**f))
            else:
                print("Could not load " + fname + ". The filter class may be deleted or not loaded. Check plugins and their version.", file=sys.stderr)
                return None
        return Filters(result)

    @staticmethod
    def fromFile(path):
        with open(path, 'r') as f:
            data = f.read()
        return Filters.fromString(data)

    def saveAsFile(self, path):
        if not path.endswith(".fil"):
            path = path + ".fil"
        with open(path, 'w') as f:
            f.write(str(self))
