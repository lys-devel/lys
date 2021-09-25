import os
import weakref
import copy
import numpy as np
import _pickle as cPickle

from LysQt.QtCore import QObject, pyqtSignal


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
    """Descriptor for WaveData"""

    def __set__(self, instance, value):
        instance._data = np.array(value)
        instance.axes._update(instance._data)
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._data


class _WaveAxesDescriptor:
    """Descriptor for WaveAxes"""

    def __set__(self, instance, value):
        # check type
        if not hasattr(value, "__iter__"):
            raise TypeError("Axes should be a list of 1-dimensional array or None")
        for item in value:
            if (not isinstance(item, np.ndarray)) and (not isinstance(item, list)) and (not isinstance(item, tuple)) and item is not None:
                raise TypeError("Axes should be a 1-dimensional sequence or None")
        # set actual instance
        instance._axes = WaveAxes(instance, [np.array(item) for item in value])
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._axes


class WaveAxes(list):
    """Axes in :class:`Wave` class

    WaveAxes is a list of numpy array that defines axes of the :class:`Wave`.
    Some usufull functions are added to built-in list.

    WaveAxes should be initialized from :class:`Wave` class. Users SHOULD NOT instantiate this class.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = weakref.ref(parent)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._parent().update()

    def getAxis(self, dim):
        """

        Return the axis specified dimension.
        This function can be accessed directly from :class:`Wave` class.

        If the specified axis is invalid, then the default axis is automatically generated and returned.

        Args:
            dim (int): The dimension of the axis.

        Returns:
            numpy.ndarray: The axis of the specified dimension.

        Example:
            >>> w = Wave(np.ones([2,2]), [1,2], None)
            >>> w.getAxis(0)
            [1,2]
            >>> w.axisIsValid(1)
            [0,1] # automatically generated axis
        """
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
        """
        Check if the axis is valid.
        This function can be accessed directly from :class:`Wave` class.

        Args:
            dim (int): The dimension to check the axis is valid.

        Returns:
            bool: The specified axis is valid or not.

        Example:
            >>> w = Wave(np.ones([2,2]), [1,2], None)
            >>> w.axisIsValid(0)
            True
            >>> w.axisIsValid(1)
            False
        """
        ax = self[dim]
        if ax is None or (ax == np.array(None)).all():
            return False
        return True

    def posToPoint(self, pos, axis=None):
        """
        posToPoint translate the specified position in axis to the nearest index in data.
        This function can be accessed directly from :class:`Wave` class.

        if axis is None, then pos should be array of size = data.ndim.
        pos = (x,y,z,...) is translated to indice (n1, n2, n3, ...)

        if axis is not None, then pos is interpreted as position in axis-th dimension.
        When axis = 1, pos = (y1, y2, y3, ...) is translated to indice (n2_1, n2_2, n2_3, ...)

        Args:
            pos (numpy.ndarray or float): The position that is translted to indice.
            axis (None or int): see above description

        Returns:
            tuple or int: The indice corresponding to pos.

        Example:
            >>> w = Wave(np.ones([2,2]), [1,2,3], [3,4,5])
            >>> w.posToPoint((2,4))
            (1,1) # position (x,y)=(2,4) corresponds index (1,1)
            >>> w.posToPoint((1,2,3), axis=0)
            (0,1,2) # position (x1, x2, x3 = 1,2,3) in the 0th dimension correspoinds index (0,1,2)
            >>> w.posToPoint(2, axis=0)
            1 # position x = 2  correspoinds index 1 in 0th dimension
        """
        if axis is None:
            axes = [self.getAxis(d) for d in range(len(self))]
            return tuple(np.abs(ax - val).argmin() for val, ax in zip(pos, axes))
        else:
            if hasattr(pos, "__iter__"):
                return tuple(self.posToPoint(p, axis) for p in pos)
            return np.abs(self.getAxis(axis) - pos).argmin()

    def pointToPos(self, indice, axis=None):
        """
        pointToPos translate the specified indice to the position in data.
        This function can be accessed directly from :class:`Wave` class.

        If axis is None, then indice should be array of size = data.ndim.
        indice = (n1, n2, n3, ...) is translated to indice (x, y, z, ...)

        If axis is not None, then indice is interpreted as indice in axis-th dimension.
        When axis = 1, pos = (n1, n2, n3, ...) is translated to indice (y1, y2, y3, ...)

        Args:
            indice (array of int): The indice that is translted to position.
            axis (None or int): see above description

        Returns:
            tuple or float: The position corresponding to indice.

        Example:
            >>> w = Wave(np.ones([2,2]), [1,2,3], [3,4,5])
            >>> w.pointToPos((1,1))
            (2,4) # index (1,1) corresponds to position (x,y)=(2,4)
            >>> w.posToPoint((0,1,2), axis=0)
            (1,2,3) # index (0,1,2) in the 0th dimension correspoinds position (x1, x2, x3 = 1,2,3)
            >>> w.posToPoint(1, axis=0)
            2 #  index 1 in 0th dimensions correspoinds position x = 2
        """
        if axis is None:
            axes = [self.getAxis(d) for d in range(len(self))]
            return tuple(ax[val] for val, ax in zip(indice, axes))
        else:
            if hasattr(indice, "__iter__"):
                return tuple(self.pointToPos(i, axis) for i in indice)
            ax = self.getAxis(axis)
            return ax[indice]

    def _update(self, data):
        while(len(self) < data.ndim):
            self.append(np.array(None))
        while(len(self) > data.ndim):
            self.pop(len(self) - 1)


class _WaveNoteDescriptor:
    """Descriptor for WaveNote"""

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

    @ staticmethod
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

    @ staticmethod
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

    @ property
    def name(self):
        if "name" not in self.note:
            self.name = "wave" + str(Wave._nameIndex)
            Wave._nameIndex += 1
        return self.note.get("name")

    @ name.setter
    def name(self, value):
        self.note["name"] = value

    @ property
    def x(self):
        return self.getAxis(0)

    @ x.setter
    def x(self, value):
        self.axes[0] = value

    @ property
    def y(self):
        return self.getAxis(1)

    @ y.setter
    def y(self, value):
        self.axes[1] = value

    @ property
    def z(self):
        return self.getAxis(2)

    @ z.setter
    def z(self, value):
        self.axes[2] = value
