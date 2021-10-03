import numpy as np
from lys import DaskWave
from .FilterInterface import FilterInterface


class SelectIndexFilter(FilterInterface):
    """
    Indexing of data.

    For example, when *axis* = 1 and index=4, data[:,4] is returned.

    For more complex indexing, use `class``SliceFilter`.

    Args:
        index(int): index to be evaluated.
        axis(int): axis to be evaluated.
    """

    def __init__(self, index, axis=0):
        self._axis = axis
        self._index = index

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl = [slice(None)] * wave.data.ndim
        sl[self._axis] = self._index
        wave.data = wave.data[tuple(sl)]
        wave.axes = axes
        return wave

    def getParameters(self):
        return {"axis": self._axis, "index": self._index}

    def getRelativeDimension(self):
        return -1


class SliceFilter(FilterInterface):
    """
    Slicing waves.

    Args:
        slices(sequence of slice object): slices to be applied.

    Example:

        Apply slice::

            w = Wave([[1, 2, 3], [4, 5, 6]], [7, 8], [9, 10, 11], name="wave")
            f = filters.SliceFilter([slice(None), slice(1, 3)])
            result = f.execute(w)
            print(result.data, result.x, result.y)
            # [[2, 3], [5, 6]], [7, 8], [10, 11]

    """

    def __init__(self, slices):
        self._sl = []
        for s in slices:
            if s is None:
                self._sl.append(slice(None))
            elif isinstance(s, slice):
                self._sl.append(s)
            elif isinstance(s, int):
                self._sl.append(slice(s, s, 1))
            elif isinstance(s, list) or isinstance(s, tuple):
                self._sl.append(slice(*s))

    def _execute(self, wave, **kwargs):
        slices = self._sl
        axes = []
        for i, s in enumerate(slices):
            if not self._isChangeDim(s):
                if wave.axisIsValid(i):
                    axes.append(wave.axes[i][s])
                else:
                    axes.append(None)
        for i, s in enumerate(slices):
            if self._isChangeDim(s):
                slices[i] = s.start
        return DaskWave(wave.data[tuple(slices)], *axes, **wave.note)

    def _isChangeDim(self, slice):
        if slice.start is None:
            return False
        if slice.start == slice.stop:
            return True
        return False

    def getParameters(self):
        return {"slices": self._sl}

    def getRelativeDimension(self):
        return -np.sum([1 for s in self._sl if s.start == s.stop])


class IndexMathFilter(FilterInterface):
    """
    Calculate wave[*index1*] op wave[*index2*] (op = +-*/).

    Args:
        axis(int): axis to be calculated
        type('+' or '-' or '*' or '/'): operator type
        index1(int): index1 along *axis*
        index2(int): index2 along *axis*

    """

    def __init__(self, axis, type, index1, index2):
        self._type = type
        self._axis = axis
        self._index1 = index1
        self._index2 = index2

    def _execute(self, wave, **kwargs):
        axes = list(wave.axes)
        axes.pop(self._axis)
        sl1 = [slice(None)] * wave.data.ndim
        sl1[self._axis] = self._index1
        sl2 = [slice(None)] * wave.data.ndim
        sl2[self._axis] = self._index2
        if self._type == "+":
            data = wave.data[tuple(sl1)] + wave.data[tuple(sl2)]
        if self._type == "-":
            data = wave.data[tuple(sl1)] - wave.data[tuple(sl2)]
        if self._type == "*":
            data = wave.data[tuple(sl1)] * wave.data[tuple(sl2)]
        if self._type == "/":
            data = wave.data[tuple(sl1)] / wave.data[tuple(sl2)]
        wave.axes = axes
        return DaskWave(data, *axes, **wave.note)

    def getParameters(self):
        return {"axis": self._axis, "type": self._type, "index1": self._index1, "index2": self._index2}

    def getRelativeDimension(self):
        return -1


class TransposeFilter(FilterInterface):
    """
    Tranpose data by np.transpose

    Args:
        axes(sequence of int): order of axes.

    Example:

        Tranpose data:
            w = Wave([[1, 2, 3], [4, 5, 6]])
            f = filters.TransposeFilter(axes=[1, 0])
            result = f.execute(w)
            print(result.data)
            # [[1, 4], [2, 5], [3, 6]]
    """

    def __init__(self, axes):
        self._axes = axes

    def _execute(self, wave, **kwargs):
        data = wave.data.transpose(self._axes)
        axes = [wave.axes[i] for i in self._axes]
        return DaskWave(data, *axes, **wave.note)

    def getParameters(self):
        return {"axes": self._axes}
