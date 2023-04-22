import sys
import _pickle as cPickle
import dask.array as da

from lys import Wave, DaskWave
from lys.Qt import QtCore, QtWidgets

from . import getFilter


class FilterInterface:
    """
    FilterInterface is a base class of all filters in lys.

    See :doc:`../tutorials/newFilter` for detail

    Example::

        from lys import filters

        # make filter that integrate data along the 0th axis
        f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")

        # apply the filter to data
        result = f.execute(np.ones(3,4))

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
            result = self._execute(wave, *args, **kwargs)
            self._setNote(result)
            return result
        elif isinstance(wave, Wave):
            dw = DaskWave(wave)
            result = self._execute(dw, *args, **kwargs)
            self._setNote(result)
            return result.compute()
        else:
            return self.execute(Wave(wave), *args, **kwargs).data

    def _setNote(self, wave):
        if isinstance(self, Filters):
            return
        if "lysFilters" in wave.note:
            filters = wave.note["lysFilters"]
        else:
            filters = []
        filters.append(self._toDict())
        wave.note["lysFilters"] = filters

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
        return vars(self)

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

    def _toDict(self):
        """
        Export filter as dictionary.

        Returns:
            dict: The exported dictionary.
        """
        d = self.getParameters()
        d["filterName"] = self.__class__.__name__
        return d

    @staticmethod
    def _fromDict(d):
        """
        Load filter from dictionary.

        Args:
            d(dict): The dictionary.
        """
        fname = d["filterName"]
        del d["filterName"]
        filt = getFilter(fname)
        if filt is not None:
            return filt(**d)
        else:
            raise RuntimeError("Could not load " + fname + ". The filter class may be deleted or not loaded. Check plugins and their version.")

    def saveAsFile(self, file):
        """
        Save filter as file.

        Args:
            file(str): filename

        Example::

            from lys import filters
            f = filters.IntegralAllFilter(axes=[0], sumtype="Sum")
            f.saveAsFile("filter.fil")

        """
        f = Filters([self])
        f.saveAsFile(file)


def filterGUI(filterClass):
    """
    Decorator for filter GUI class.

    See :doc:`../tutorials/newFilter` for detail
    """
    def _filterGUI(cls):
        cls._filClass = filterClass
        return cls
    return _filterGUI


class FilterSettingBase(QtWidgets.QWidget):
    """
    Base class for setting widgets of filters.

    See :doc:`../tutorials/newFilter` for detail

    """
    dimensionChanged = QtCore.pyqtSignal()
    """
    Emitted when the dimension of the filter is changed.
    """

    def __init__(self, dimension):
        super().__init__()
        self.dim = dimension

    def GetFilter(self):
        """
        Get a filter instance based on the present state of the widget.

        Returns:
            filter: A filter instance.
        """
        return self._filClass(**self.getParameters())

    @classmethod
    def getFilterClass(cls):
        """
        Return the filter class.

        Returns:
            filterClass: The filter class.
        """
        if hasattr(cls, "_filClass"):
            return cls._filClass

    def getDimension(self):
        """
        Return the dimension of the input data.

        Returns:
            dimension(int): The dimension of the input data.
        """
        return self.dim

    def setParameters(self, **kwargs):
        """
        Set the state of the widget based on the keyword arguments.
        Developers should implement this method to make new filter.


        See :doc:`../tutorials/newFilter` for detail

        """
        raise NotImplementedError("Method setParameters should be implemented.")

    def getParameters(self):
        """
        Get the parameters of the filter based on the current state of the widget.

        See :doc:`../tutorials/newFilter` for detail
        """
        raise NotImplementedError("Method getParameters should be implemented.")


class Filters(FilterInterface):
    """
    The list of filters that can be successively applied.

    filters(list of filter): The filters to be applied.

    """

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

    def isEmpty(self):
        """
        Check if the filter is empty.

        Returns:
            bool: True if the filter is empty.
        """
        return len(self._filters) == 0

    def __str__(self):
        return str([f._toDict() for f in self._filters])

    def insert(self, index, obj):
        """
        Insert a filter before the given index.

        Args:
            index(int): Index before which *obj* is inserted.
            obj(filter): The filter instance to insert.
        """
        self._filters.insert(index, obj)

    def append(self, obj):
        """
        Append the filter to the end. 

        Args:
            obj(filter): The filter instance to append.
        """
        self._filters.append(obj)

    def getFilters(self):
        """
        Get filters.

        Returns:
            list of filters: The list of filters.
        """
        return self._filters

    @staticmethod
    def toString(filter):
        """
        Do not use this method. Use :func:`lys.filters.function.toString`
        """
        if isinstance(filter, Filters):
            return str(filter)
        else:
            return str(Filters([filter]))

    @staticmethod
    def fromString(data):
        """
        Do not use this method. Use :func:`lys.filters.function.fromString`
        """
        if isinstance(data, str):
            data = eval(data)
        if isinstance(data, list):
            res = Filters([FilterInterface._fromDict(f) for f in data])
        else:  # backward compability
            data = data.replace(b"ExtendAnalysis.Analysis.filters", b"lys.filters")
            data = data.replace(b"ExtendAnalysis.Analysis.filter", b"lys.filters.filter")
            res = cPickle.loads(data)
        return res

    @staticmethod
    def fromWave(wave):
        """
        Load filters automatically saved in wave.
        """
        if "lysFilters" in wave.note:
            return Filters.fromString(wave.note["lysFilters"])
        return None

    @staticmethod
    def fromFile(path):
        """
        Do not use this method. Use :func:`lys.filters.function.fromFile`
        """
        with open(path, 'r') as f:
            data = f.read()
        return Filters.fromString(data)

    def saveAsFile(self, path):
        if not path.endswith(".fil"):
            path = path + ".fil"
        with open(path, 'w') as f:
            f.write(str(self))
