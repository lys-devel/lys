import itertools
import time
from ExtendAnalysis import *
from .filter.FreeLine import *
from scipy import ndimage
import dask
import dask.array as da


class controlledObjects(QObject):
    appended = pyqtSignal(object)
    removed = pyqtSignal(object)

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
        for obj in self._objs:
            self.remove(obj)


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
    updated = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self._enabled = []
        self._graphs = []
        self._sumtype = "Sum"

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

    def setting(self, index):
        self._objs[index].setting()

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
            if not i in axes:
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

    def __applyFreeLines(self, wave, axes_orig, applied):
        for a in axes_orig:
            if a >= 10000:
                fl = self.__findFreeLineExecutor(a)
                axes = list(fl.getAxes())
                for i, ax in enumerate(axes):
                    for ax2 in applied:
                        if ax2 < ax:
                            axes[i] -= 1
                fl.execute(wave, axes)

    def makeWave(self, wave, axes):
        start = time.time()
        slices = [slice(None, None, None)] * wave.data.ndim
        sumlist = []
        for e in self.__exeList(wave):
            if not isinstance(e, FreeLineExecutor):
                e.set(wave, slices, sumlist, ignore=self.__ignoreList(axes))
        sumlist = np.array(sumlist)
        applied = sumlist.tolist()
        for i in range(len(slices)):
            if isinstance(slices[len(slices) - 1 - i], int):
                sumlist[sumlist > len(slices) - 1 - i] -= 1
                applied.append(i)
        tmp = wave[tuple(slices)]
        if len(sumlist) != 0:
            f = self.__getSumFunction(self.__getLib(tmp))
            tmp.data = f(tmp.data, axis=tuple(sumlist.tolist()))
        tmp.axes = [ax for i, ax in enumerate(wave.axes) if not (i in sumlist)]
        res = tmp
        self.__applyFreeLines(res, axes, applied)
        st1 = time.time()
        if isinstance(res, DaskWave):
            res = res.toWave()
        if len(axes) == 2 and axes[0] < 10000:
            if axes[0] > axes[1] or axes[1] >= 10000:
                res.data = res.data.T
                t = res.axes[0]
                res.axes[0] = res.axes[1]
                res.axes[1] = t
        return res

    def __getSumFunction(self, lib):
        if self._sumtype == "Sum":
            return lib.sum
        elif self._sumtype == "Mean":
            return lib.mean
        elif self._sumtype == "Max":
            return lib.max
        elif self._sumtype == "Min":
            return lib.min
        elif self._sumtype == "Median":
            return lib.median

    def __getLib(self, wave):
        if isinstance(wave, DaskWave):
            return da
        else:
            return np


class AllExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axis):
        super().__init__()
        self.axis = axis

    def getAxes(self):
        return (self.axis,)

    def set(self, wave, slices, sumlist, ignore=[]):
        if self.axis in ignore:
            return sl, []
        else:
            slices[self.axis] = slice(None, None, None)
            sumlist.append(self.axis)

    def __str__(self):
        return "All executor for axis = " + str(self.axis)


class DefaultExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axis):
        super().__init__()
        self.axis = axis

    def getAxes(self):
        return (self.axis,)

    def set(self, wave, slices, sumlist, ignore=[]):
        if self.axis in ignore:
            return
        else:
            slices[self.axis] = 0

    def __str__(self):
        return "Default executor for axis = " + str(self.axis)


class RegionExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axes, range=None):
        super().__init__()
        if isinstance(axes, int):
            self.axes = (axes,)
        else:
            self.axes = tuple(axes)
        if range is not None:
            self.setRange(range)

    def getAxes(self):
        return tuple(self.axes)

    def setRange(self, range):
        self.range = []
        if isinstance(range[0], list):
            for r in range:
                self.range.append(r)
        else:
            self.range.append(range)
        self.updated.emit(self.axes)

    def set(self, wave, slices, sumlist, ignore=[]):
        for i, r in zip(self.axes, self.range):
            if not i in ignore:
                p1 = min(wave.posToPoint(r[0], i), wave.posToPoint(r[1], i))
                p2 = max(wave.posToPoint(r[0], i), wave.posToPoint(r[1], i))
                if p1 < 0:
                    p1 = 0
                if p2 < 0:
                    p2 = p1
                if p1 > wave.data.shape[i] - 1:
                    p1 = wave.data.shape[i] - 1
                if p2 > wave.data.shape[i] - 1:
                    p2 = wave.data.shape[i] - 1
                slices[i] = slice(p1, p2 + 1)
                sumlist.append(i)

    def callback(self, region):
        self.setRange(region)

    def Name(self):
        return "Region"

    def __str__(self):
        return "Region executor for axis = " + str(self.axes)


class PointExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axes, pos=None):
        super().__init__()
        if isinstance(axes, int):
            self.axes = (axes,)
        else:
            self.axes = axes
        if pos is not None:
            self.setPosition(pos)
        else:
            if hasattr(axes, "__iter__"):
                self.position = [0 for a in axes]
            else:
                self.position = [0]

    def getAxes(self):
        return tuple(self.axes)

    def setPosition(self, pos):
        if isinstance(pos, float) or isinstance(pos, int):
            self.position = [pos]
        else:
            self.position = pos
        self.updated.emit(tuple(self.axes))

    def set(self, wave, slices, sumlist, ignore=[]):
        for i, p in zip(self.axes, self.position):
            if not i in ignore:
                p = wave.posToPoint(p, i)
                if p < 0:
                    p = 0
                if p > wave.data.shape[i] - 1:
                    p = wave.data.shape[i] - 1
                slices[i] = p

    def callback(self, pos):
        self.setPosition(pos)

    def Name(self):
        return "Point"

    def __str__(self):
        return "Point executor for axis " + str(self.axes)


class FreeLineExecutor(QObject):
    _id = 10000
    updated = pyqtSignal(tuple)

    def __init__(self, axes, pos=None):
        super().__init__()
        self.axes = axes
        self.id = FreeLineExecutor._id
        FreeLineExecutor._id += 1
        self.width = 1
        if pos is not None:
            self.setPosition(pos)

    def getAxes(self):
        return list(self.axes)

    def setPosition(self, pos):
        self.position = pos
        self.updated.emit((self.id,))

    def setting(self):
        val, res = QInputDialog.getInt(None, "Setting for free line", "width")
        if res:
            self.setWidth(val)
        self.updated.emit((self.id,))

    def setWidth(self, w):
        self.width = w

    def execute(self, wave, axes):
        f = FreeLineFilter(axes, self.position, self.width)
        f.execute(wave)
        return

    def callback(self, pos):
        self.setPosition(pos)

    def Name(self):
        return "Line" + str(self.id - 10000) + " (width = " + str(self.width) + ")"

    def ID(self):
        return self.id
