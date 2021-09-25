import os
import weakref
import copy
import numpy as np
import _pickle as cPickle

from PyQt5.QtCore import QObject, pyqtSignal


class SettingDict(dict):
    """Wrapped dict, internally used to automatically save settings

    SettingDict is wrapper of dict that is is automatically saved when __setitem__ and __delitem__ are called.

    If file is not specified, SettingDict behave as normal dict class.

    If file does not exist, the file is automatically created.

    Args:
        file (string): The filename to be loaded and saved

    Examples:
        >>> d = SettingDict() 
        >>> d["setting1"] = "SettingString"
        >>> d.Save("Setting.dic")

        >>> d2 = SettingDict("Setting.dic")   # setting.dic is loaded
        >>> d2["setting1"]
        SettingString

    """

    def __init__(self, file=None):
        self.__file = file
        if file is None:
            return
        if os.path.exists(file):
            with open(file, 'r') as f:
                data = eval(f.read())
            for key, item in data.items():
                self[key] = item

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.Save()

    def __delitem__(self, key):
        del self.data[key]
        self.Save()

    def Save(self, file=None):
        """Save dictionary

        Args:
            file (string): The filename to be saved
        """
        if file is None:
            file = self.__file
        if file is None:
            return
        file = os.path.abspath(file)
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w') as f:
            f.write(str(self))


class _WaveDataDescriptor:
    def __set__(self, instance, value):
        instance._data = np.array(value)
        instance.axes._update(instance._data)
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._data


class _WaveNoteDescriptor:
    def __set__(self, instance, value):
        # check type
        if not isinstance(value, dict):
            raise TypeError("Axes should be a dictionary")
        # set actual instance
        instance._note = WaveNote(value)

    def __get__(self, instance, objtype=None):
        return instance._note


class WaveNote(dict):
    def addObject(self, name, obj):
        self[name] = cPickle.dumps(obj)

    def getObject(self, name):
        return cPickle.loads(self[name])

    def addAnalysisLog(self, log):
        if not "AnalysisLog" in self:
            self["AnalysisLog"] = ""
        self["AnalysisLog"] += log

    def getAnalysisLog(self):
        return self["AnalysisLog"]


class _WaveAxesDescriptor:
    def __set__(self, instance, value):
        # check type
        if not hasattr(value, "__iter__"):
            raise TypeError("Axes should be a list of 1-dimensional array or None")
        # set actual instance
        instance._axes = WaveAxes(instance, [np.array(item) for item in value])
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._axes


class WaveAxes(list):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = weakref.ref(parent)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._parent().update()

    def getAxis(self, dim):
        data = self._parent().data
        val = np.array(self[dim])
        if data.ndim <= dim:
            return None
        elif val.ndim == 0:
            return np.arange(data.shape[dim])
        else:
            if data.shape[dim] == val.shape[0]:
                return val
            else:
                res = np.empty((data.shape[dim]))
                for i in range(data.shape[dim]):
                    res[i] = np.NaN
                for i in range(min(data.shape[dim], val.shape[0])):
                    res[i] = val[i]
                return res

    def axisIsValid(self, dim):
        ax = self[dim]
        if ax is None or (ax == np.array(None)).all():
            return False
        return True

    def posToPoint(self, pos, axis=None):
        data = self._parent().data
        if axis is None:
            x0 = data.x[0]
            x1 = data.x[len(data.x) - 1]
            y0 = data.y[0]
            y1 = data.y[len(data.y) - 1]
            dx = (x1 - x0) / (len(data.x) - 1)
            dy = (y1 - y0) / (len(data.y) - 1)
            return (int(round((pos[0] - x0) / dx)), int(round((pos[1] - y0) / dy)))
        else:
            if hasattr(pos, "__iter__"):
                return [self.posToPoint(p, axis) for p in pos]
            ax = self.getAxis(axis)
            x0 = ax[0]
            x1 = ax[len(ax) - 1]
            dx = (x1 - x0) / (len(ax) - 1)
            return int(round((pos - x0) / dx))

    def pointToPos(self, p, axis=None):
        data = self._parent().data
        if axis is None:
            x0 = data.x[0]
            x1 = data.x[len(data.x) - 1]
            y0 = data.y[0]
            y1 = data.y[len(data.y) - 1]
            dx = (x1 - x0) / (len(data.x) - 1)
            dy = (y1 - y0) / (len(data.y) - 1)
            return (p[0] * dx + x0, p[1] * dy + y0)
        else:
            if hasattr(p, "__iter__"):
                return [self.pointToPos(pp, axis) for pp in p]
            ax = self.getAxis(axis)
            x0 = ax[0]
            x1 = ax[len(ax) - 1]
            dx = (x1 - x0) / (len(ax) - 1)
            return p * dx + x0

    def _update(self, data):
        while(len(self) < data.ndim):
            self.append(np.array(None))
        while(len(self) > data.ndim):
            self.pop(len(self) - 1)


def _produceWave(data, axes, note):
    return Wave(data, *axes, note=note)


class Wave(QObject):
    _nameIndex = 0
    modified = pyqtSignal(object)
    data = _WaveDataDescriptor()
    axes = _WaveAxesDescriptor()
    note = _WaveNoteDescriptor()

    def __init__(self, data=None, *axes, note={}, name=None):
        super().__init__()
        self.axes = [np.array(None)]
        self.data = np.array(None)
        self.note = note
        if type(data) == str:
            self.__loadData(data)
        else:
            self.__setData(data, *axes)
            if name is not None:
                self.name = name

    def __loadData(self, file):
        tmp = np.load(file, allow_pickle=True)
        data = tmp['data']
        self.axes = [np.array(None) for i in range(data.ndim)]
        self.data = data
        if 'axes' in tmp:
            self.axes = [axis for axis in tmp['axes']]
        if 'note' in tmp:
            self.note = tmp['note'][()]

    def __setData(self, data, *axes):
        if hasattr(data, "__iter__"):
            if len(data) > 0:
                if isinstance(data[0], Wave):
                    self.__joinWaves(data, axes)
                    return
        self.data = data
        if len(axes) == self.data.ndim:
            self.axes = list(axes)

    def __joinWaves(self, waves, axes):
        self.data = np.array([w.data for w in waves])
        if len(axes) == 1:
            ax = list(axes)
        else:
            ax = [None]
        self.axes = ax + waves[0].axes

    def __getattr__(self, key):
        if hasattr(self.data, key):
            return self.data.__getattribute__(key)
        if hasattr(self.axes, key):
            return self.axes.__getattribute__(key)
        else:
            return super().__getattr__(key)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if ax is None or (ax == np.array(None)).all():
                    axes.append(None)
                else:
                    axes.append(ax[s])
            w = Wave(data, *axes, note=copy.deepcopy(self.note))
            w.addAnalysisLog("Wave sliced: " + str(key) + "\n")
            return w
        else:
            super().__getitem__(key)

    def __setitem__(self, key, value):
        self.data[key] = value
        self.update()

    def Save(self, file):
        print("Wave.Save is deprecated. use Wave.export instead")
        self.export(file)

    def Duplicate(self):
        return Wave(copy.copy(self.data), *copy.copy(self.axes), note=copy.copy(self.note))

    def __reduce_ex__(self, proto):
        return _produceWave, (self.data, list(self.axes), self.note)

    @staticmethod
    def SupportedFormats():
        return ["Numpy npz (*.npz)", "Comma-Separated Values (*.csv)", "Text file (*.txt)"]

    def export(self, path, type="npz"):
        if type in ['Numpy npz (*.npz)', ".npz", "npz"]:
            path = (path + ".npz").replace(".npz.npz", ".npz")
            path = os.path.abspath(self._parseFilename(path))
            os.makedirs(os.path.dirname(path), exist_ok=True)
            np.savez_compressed(path, data=self.data, axes=self.axes, note=self.note, allow_pickle=True)
        if type in ["Comma-Separated Values (*.csv)", ".csv", "csv"]:
            np.savetxt(path + ".csv".replace(".csv.csv", ".csv"), self.data, delimiter=',')
        if type in ["Text file (*.txt)", ".txt", "txt"]:
            np.savetxt(path + ".txt".replace(".txt.txt", ".txt"), self.data)

    @staticmethod
    def importFrom(path):
        _, ext = os.path.splitext(path)
        if ext == "npz":
            return Wave(path)
        else:
            return Wave(np.loadtxt(path, delimiter=","))

    def update(self):
        self.modified.emit(self)

    def Name(self):
        return self.name

    @property
    def name(self):
        if "name" not in self.note:
            self.name = "wave" + str(Wave._nameIndex)
            Wave._nameIndex += 1
        return self.note.get("name")

    @name.setter
    def name(self, value):
        self.note["name"] = value

    @property
    def x(self):
        return self.getAxis(0)

    @x.setter
    def x(self, value):
        self.axes[0] = value

    @property
    def y(self):
        return self.getAxis(1)

    @y.setter
    def y(self, value):
        self.axes[1] = value

    @property
    def z(self):
        return self.getAxis(2)

    @z.setter
    def z(self, value):
        self.axes[2] = value
