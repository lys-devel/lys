import numpy as np

from lys import DaskWave
from lys.Qt import QtCore
from lys.decorators import avoidCircularReference
from lys.filters import Filters, SliceFilter, EmptyFilter, IntegralAllFilter, TransposeFilter

from .MultiCutExecutors import FreeLineExecutor, DefaultExecutor


class controlledObjects(QtCore.QObject):
    appended = QtCore.pyqtSignal(object)
    removed = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._objs = []
        self._axis = []

    def append(self, obj, axes):
        self._objs.append(obj)
        self._axis.append(axes)
        self.appended.emit(obj)

    def remove(self, obj):
        if obj in self._objs:
            i = self._objs.index(obj)
            self._objs.pop(i)
            self._axis.pop(i)
            self.removed.emit(obj)
            return i
        return None

    def removeAt(self, index):
        self.remove(self._objs[index])

    def getAxes(self, obj):
        i = self._objs.index(obj)
        return self._axis[i]

    def getObjectsAndAxes(self):
        return zip(self._objs, self._axis)

    def __len__(self):
        return len(self._objs)

    def __getitem__(self, index):
        return [self._objs[index], self._axis[index]]

    def clear(self):
        while len(self._objs) != 0:
            self.remove(self._objs[0])


class SwitchableObjects(controlledObjects):

    def __init__(self):
        super().__init__()
        self._enabled = []

    def enableAt(self, index):
        self.enable(self._objs[index])

    def disableAt(self, index):
        self.disable(self._objs[index])

    def enable(self, obj):
        i = self._objs.index(obj)
        self._enabled[i] = True

    def disable(self, obj):
        i = self._objs.index(obj)
        self._enabled[i] = False

    def append(self, obj, axes):
        super().append(obj, axes)
        self._enabled.append(True)

    def remove(self, obj):
        super().remove(obj)
        if obj in self._objs:
            i = self._objs.index(obj)
            self._enabled.pop(i)

    def isEnabled(self, i):
        if isinstance(i, int):
            return self._enabled[i]
        else:
            return self.isEnabled(self._objs.index(i))


class ExecutorList(controlledObjects):
    updated = QtCore.pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self._enabled = []
        self._graphs = []
        self._sumtype = "Mean"

    def setSumType(self, sumtype):
        self._sumtype = sumtype

    def graphRemoved(self, graph):
        for i, g in enumerate(self._graphs):
            if g == graph:
                self.removeAt(i)

    def append(self, obj, graph=None):
        super().append(obj, obj.getAxes())
        self._enabled.append(False)
        self._graphs.append(graph)
        obj.updated.connect(self.updated.emit)
        self.enable(obj)

    def remove(self, obj):
        obj.updated.disconnect()
        i = super().remove(obj)
        if i is not None:
            self._enabled.pop(i)
            self._graphs.pop(i)
        self.updated.emit(tuple(obj.getAxes()))
        return i

    def enableAt(self, index):
        self.enable(self._objs[index])

    def enable(self, obj):
        i = self._objs.index(obj)
        self._enabled[i] = True
        if isinstance(obj, FreeLineExecutor):
            return
        for o in self._objs:
            if not o == obj:
                for ax1 in obj.getAxes():
                    for ax2 in o.getAxes():
                        if ax1 == ax2 and not isinstance(o, FreeLineExecutor):
                            self.disable(o)
        self.updated.emit(obj.getAxes())

    def setting(self, index, parentWidget=None):
        self._objs[index].setting(parentWidget)

    def disable(self, obj):
        i = self._objs.index(obj)
        self._enabled[i] = False
        self.updated.emit(obj.getAxes())

    def disableAt(self, index):
        self.disable(self._objs[index])

    def getFreeLines(self):
        res = []
        for o in self._objs:
            if isinstance(o, FreeLineExecutor):
                res.append(o)
        return res

    def isEnabled(self, i):
        return self._enabled[i]

    def saveEnabledState(self):
        import copy
        self._saveEnabled = copy.deepcopy(self._enabled)

    def restoreEnabledState(self):
        for i, b in enumerate(self._saveEnabled):
            if b:
                self.enableAt(i)
            else:
                self.disableAt(i)

    def __exeList(self, wave):
        axes = []
        res = []
        for i, e in enumerate(self._objs):
            if self.isEnabled(i):
                if not isinstance(e, FreeLineExecutor):
                    axes.extend(e.getAxes())
                    res.append(e)
        for i in range(wave.data.ndim):
            if i not in axes:
                res.append(DefaultExecutor(i))
        return res

    def __findFreeLineExecutor(self, id):
        for fl in self.getFreeLines():
            if fl.ID() == id:
                return fl

    def __ignoreList(self, axes):
        ignore = []
        for ax in axes:
            if ax < 10000:
                ignore.append(ax)
            else:
                ignore.extend(self.__findFreeLineExecutor(ax).getAxes())
        return ignore

    def __getFreeLineFilter(self, axes_orig, applied):
        for a in axes_orig:
            if a >= 10000:
                fl = self.__findFreeLineExecutor(a)
                axes = list(fl.getAxes())
                for i, ax in enumerate(axes):
                    for ax2 in applied:
                        if ax2 < ax:
                            axes[i] -= 1
                return fl.getFilter(axes)
        return EmptyFilter()

    def makeWave(self, wave_orig, axes):
        wave = wave_orig.duplicate()
        slices = [slice(None, None, None)] * wave.data.ndim
        sumlist = []
        for e in self.__exeList(wave):
            if not isinstance(e, FreeLineExecutor):
                e.set(wave, slices, sumlist, ignore=self.__ignoreList(axes))
        sumlist = np.array(sumlist)
        applied = sumlist.tolist()  # summed or integer sliced axes
        for i in reversed(range(len(slices))):
            if isinstance(slices[i], int):
                sumlist[sumlist > i] -= 1
                applied.append(i)
        f1 = SliceFilter(slices)
        f2 = IntegralAllFilter(sumlist.tolist(), self._sumtype)
        f3 = self.__getFreeLineFilter(axes, applied)
        f4 = self.__getTransposeFilter(axes)
        f = Filters([f1, f2, f3, f4])
        res = f.execute(wave)
        if isinstance(res, DaskWave):
            res = res.compute()
        return res

    def __getTransposeFilter(self, axes):
        if len(axes) == 2 and axes[0] < 10000:
            if axes[0] > axes[1] or axes[1] >= 10000:
                return TransposeFilter([1, 0])
        return EmptyFilter()


class MultiCutCUI(QtCore.QObject):
    def __init__(self, wave):
        super().__init__()
        self._wave = _MultiCutWave(wave)
        self._wave.filterApplied.connect(self.__filterApplied)
        self.__filterApplied(wave)

    def __filterApplied(self, wave):
        self._axesRange = _AxesRangeManager(wave.ndim)
        self._freeLine = _FreeLineManager()

    def __getattr__(self, key):
        if "_axesRange" in self.__dict__:
            if hasattr(self._axesRange, key):
                return getattr(self._axesRange, key)
        if "_wave" in self.__dict__:
            if hasattr(self._wave, key):
                return getattr(self._wave, key)
        if "_freeLine" in self.__dict__:
            if hasattr(self._freeLine, key):
                return getattr(self._freeLine, key)
        return super().__getattr__(key)


class _MultiCutWave(QtCore.QObject):
    filterApplied = QtCore.pyqtSignal(object)

    def __init__(self, wave):
        super().__init__()
        self._wave = self._filtered = DaskWave(wave, chunks="auto")
        self._useDask = True

    def applyFilter(self, filt):
        wave = filt.execute(self._wave)
        wave.persist()
        if self._useDask:
            self._filtered = wave
        else:
            self._filtered = wave.compute()
        self.filterApplied.emit(self._filtered)

    def getFilteredWave(self):
        return self._filtered


class _AxesRangeManager(QtCore.QObject):
    axesRangeChanged = QtCore.pyqtSignal(tuple)
    """
    Emitted after :meth:`setAxisRange` is called.
    """

    def __init__(self, dim):
        super().__init__()
        self._ranges = [0] * dim

    @avoidCircularReference
    def setAxisRange(self, axis, range):
        """
        Set the integrated range for MultiCut.

        Args:
            axis(int): The axis of which integrated range is set.
            range(float or length 2 sequence): The integrated range. If *range* is a float, only a point is used for integration. 
        """
        if hasattr(axis, "__iter__"):
            for ax, r in zip(axis, range):
                self._ranges[ax] = r
            self.axesRangeChanged.emit(tuple(axis))
        else:
            self._ranges[axis] = range
            self.axesRangeChanged.emit((axis,))

    def getAxisRange(self, axis):
        """
        Get the integrated range for MultiCut.

        Args:
            axis(int): The axis.

        Returns:    
            float or length 2 sequence: See :meth:`setAxisRange`.
        """
        return self._ranges[axis]

    def getAxisRangeType(self, axis):
        """
        Get the axis range type for the specified axis.

        Returns:
            'point' or 'range': The axis range type.
        """
        r = self.getAxisRange(axis)
        if hasattr(r, "__iter__"):
            return 'range'
        else:
            return 'point'


class _FreeLineManager(QtCore.QObject):
    freeLineChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._fregs = []

    def addFreeLine(self, axes, position=[[0, 0], [1, 1]], width=1):
        obj = _FreeLine(axes, position, width)
        self._fregs.append(obj)
        self.freeLineChanged.emit()
        return obj

    def removeFreeLine(self, obj):
        self._fregs.remove(obj)
        self.freeLineChanged.emit()

    def getFreeLines(self):
        return self._fregs


class _FreeLine(QtCore.QObject):
    _index = 0

    lineChanged = QtCore.pyqtSignal()

    def __init__(self, axes, position=[[0, 0], [1, 1]], width=1):
        super().__init__()
        _FreeLine._index += 1
        self._name = "Line" + str(_FreeLine._index)
        self._axes = axes
        self._pos = position
        self._width = width

    def getName(self):
        return self._name

    def getAxes(self):
        return self._axes

    def setPosition(self, pos):
        self._pos = pos
        self.lineChanged.emit()

    def getPosition(self):
        return self._pos

    def setWidth(self, width):
        self._width = width
        self.lineChanged.emit()

    def getWidth(self):
        return self._width
