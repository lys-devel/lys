from lys import DaskWave, Wave, filters
from lys.Qt import QtCore
from lys.decorators import avoidCircularReference


class MultiCutCUI(QtCore.QObject):
    def __init__(self, wave):
        super().__init__()
        self._wave = _MultiCutWave(wave)
        self._axesRange = _AxesRangeManager(wave.ndim)
        self._freeLine = _FreeLineManager()
        self._children = _ChildWaves(self)
        self._wave.dimensionChanged.connect(self.__reset)

    def __reset(self, wave):
        self._axesRange.reset(wave.ndim)
        self._freeLine.clear()
        self._children.clear()

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
        if "_children" in self.__dict__:
            if hasattr(self._children, key):
                return getattr(self._children, key)
        return super().__getattr__(key)


class _MultiCutWave(QtCore.QObject):
    dimensionChanged = QtCore.pyqtSignal(object)

    def __init__(self, wave):
        super().__init__()
        self._wave = self._filtered = self._load(wave)
        self._wave.persist()
        self._useDask = True

    def _load(self, data):
        if isinstance(data, Wave) or isinstance(data, DaskWave):
            return DaskWave(data)
        else:
            return DaskWave(Wave(data))

    def applyFilter(self, filt):
        dim_old = self._filtered.ndim
        wave = filt.execute(self._wave)
        wave.persist()
        if self._useDask:
            self._filtered = wave
            print("[MultiCut] DaskWave set. shape = ", wave.data.shape, ", dtype = ", wave.data.dtype, ", chunksize = ", wave.data.chunksize)
        else:
            self._filtered = wave.compute()
            print("[MultiCut] Wave set. shape = ", wave.data.shape, ", dtype = ", wave.data.dtype)
        if dim_old != self._filtered.ndim:
            self.dimensionChanged.emit(self._filtered)

    def getRawWave(self):
        return self._wave

    def getFilteredWave(self):
        return self._filtered

    def useDask(self, b):
        self._useDask = b


class _ChildWaves(QtCore.QObject):
    childWavesChanged = QtCore.pyqtSignal()

    def __init__(self, cui):
        super().__init__()
        self._cui = cui
        self._cui.axesRangeChanged.connect(self.__update)
        self._cui.freeLineMoved.connect(self.__update)
        self._sumType = "Mean"
        self._waves = []

    def clear(self):
        self._waves = []

    @property
    def cui(self):
        return self._cui

    def setSumType(self, sumType):
        self._sumType = sumType

    def addWave(self, axes, filter=None, name=None):
        w = self._makeWave(axes)
        if name is not None:
            w.name = name
        item = _ChildWave(w, axes, filter)
        self._waves.append(item)
        self.childWavesChanged.emit()
        return item

    def remove(self, obj):
        self._waves.remove(obj)
        self.childWavesChanged.emit()

    def _makeWave(self, axes):
        wave = self.cui.getFilteredWave()
        ignored = sorted([ax for ax in axes if not isinstance(ax, str)] + self._freeLineAxes(axes))
        ranges = [self.cui.getAxisRange(i) for i in range(wave.ndim)]
        for ax in ignored:
            ranges[ax] = None

        f = [filters.IntegralFilter(ranges, self._sumType)] + self.__getFreeLineFilter(axes, ignored)
        return filters.Filters(f).execute(wave)

    def _freeLineAxes(self, axes):
        res = []
        for ax in axes:
            if isinstance(ax, str):
                res.extend(self._cui.getFreeLine(ax).getAxes())
        return res

    def __getFreeLineFilter(self, axes_orig, ignored):
        axes_final = list(ignored)
        filts = []
        for ax in axes_orig:
            if isinstance(ax, str):
                line = self._cui.getFreeLine(ax)
                axes = list(line.getAxes())
                axes = [axes_final.index(a) for a in axes]
                filts.append(line.getFilter(axes))

                axes_final[axes_final.index(axes[0])] = ax
                axes_final.remove(axes[1])
        if len(filts) != 0:
            filts.append(filters.TransposeFilter([axes_final.index(a) for a in axes_orig]))
        return filts

    def getChildWaves(self):
        return self._waves

    def __update(self, axes):
        for child in self._waves:
            if isinstance(axes, _FreeLine):
                if axes.getName() in child.getAxes():
                    self.__updateSingleWave(child)
            else:
                ax = []
                for a in child.getAxes():
                    if isinstance(a, str):
                        ax.extend(self._freeLineAxes([a]))
                    else:
                        ax.append(a)
                if not set(axes).issubset(ax):
                    self.__updateSingleWave(child)

    def __updateSingleWave(self, child):
        if not child.isEnabled():
            return
        try:
            wav = self._makeWave(child.getAxes())
            child.update(wav)
        except Exception:
            import traceback
            traceback.print_exc()


class _ChildWave(QtCore.QObject):
    def __init__(self, wave, axes, filter=None):
        super().__init__()
        self._orig = wave
        if filter is None:
            self._filt = wave
        else:
            self._filt = filter.execute(wave)
        if isinstance(self._filt, DaskWave):
            self._filt = self._filt.compute()
        self._axes = axes
        self._enabled = True
        self._post = filter

    def getAxes(self):
        return tuple(self._axes)

    def getRawWave(self):
        return self._orig

    def getFilteredWave(self):
        return self._filt

    def setEnabled(self, b):
        self._enabled = b

    def isEnabled(self):
        return self._enabled

    def setPostProcess(self, post):
        self._post = post
        self.update(self._orig)

    def postProcess(self):
        return self._post

    def update(self, wave):
        self._orig = wave
        name = str(self._filt.name)
        post = self.postProcess()
        if post is not None:
            wave = post.execute(wave)
        if isinstance(wave, DaskWave):
            wave = wave.compute()
        self._filt.data = wave.data
        self._filt.axes = wave.axes
        self._filt.note = wave.note
        self._filt.name = name

    def name(self):
        return self._filt.name


class _AxesRangeManager(QtCore.QObject):
    axesRangeChanged = QtCore.pyqtSignal(tuple)
    """
    Emitted after :meth:`setAxisRange` is called.
    """

    def __init__(self, dim):
        super().__init__()
        self.reset(dim)

    def reset(self, dim):
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
    freeLineMoved = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.clear()

    def clear(self):
        self._fregs = []
        self.freeLineChanged.emit()

    def addFreeLine(self, axes, position=[[0, 0], [1, 1]], width=1):
        obj = _FreeLine(axes, position, width)
        obj.lineChanged.connect(lambda: self.freeLineMoved.emit(obj))
        self._fregs.append(obj)
        self.freeLineChanged.emit()
        return obj

    def removeFreeLine(self, obj):
        self._fregs.remove(obj)
        self.freeLineChanged.emit()

    def getFreeLines(self):
        return self._fregs

    def getFreeLine(self, name):
        for line in self._fregs:
            if line.getName() == name:
                return line


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

    def getFilter(self, axes):
        return filters.FreeLineFilter(axes, self._pos, self._width)
