import os
import weakref
import numpy as np
import dask.array as da

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
    """
    *data* is numpy.ndarray that represents data of :class:`Wave`
    Any type of sequential array will be automatically converted to numpy.ndarray when it is set as *data*.

    All methods implemented in numpy.ndarray can be accessed from :class:`Wave` 

    Example:
        >>> w = Wave([1,2,3])
        >>> w.data = [2,3,4]
        >>> w.data
        [2,3,4]
        >>> type(w.data)
        np.ndarray
        >>> w.shape # equals w.data.shape
        (3,)
    """

    def __set__(self, instance, value):
        instance._data = np.array(value)
        instance.axes._update(instance._data)
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._data


class _WaveAxesDescriptor:
    """
    Axes of :class:`Wave` implemented as :class:`WaveAxes` class.

    *axes* is list of numpy arrays and is used to visualize data.

    axes[0], axes[1], axes[2] can be accessed by :attr:`Wave.x`, :attr:`Wave.y`, and :attr:`Wave.z`

    The initialization can be done from constructor of :class:`Wave`

        >>> w = Wave(np.ones([3,3]), [1,2,3], [4,5,6])
        >>> w.axes
        [[1,2,3],[4,5,6]]

    Then the *axes* can be changed as following.

        >>> w.axes[0] = [7,8,9]
        >>> w.axes
        [[7,8,9],[4,5,6]]

    None can also be set to axis. 

        >>> w.axes[1] = None
        >>> w.axes
        [[7,8,9], None]

    Even if the axis is None, valid axis can be obtained by getAxis.

        >>> w.getAxis(0)
        [7,8,9]
        >>> w.getAxis(1)
        [0,1,2]

    See also:
        :meth:`WaveAxes.getAxis`, :class:`WaveAxes`, :attr:`x`, :attr:`y`, :attr:`z`
    """

    def __set__(self, instance, value):
        # check type
        if not hasattr(value, "__iter__"):
            raise TypeError("Axes should be a list of 1-dimensional array or None")
        for item in value:
            if (not isinstance(item, np.ndarray)) and (not isinstance(item, list)) and (not isinstance(item, tuple)) and item is not None:
                raise TypeError("Axes should be a 1-dimensional sequence or None")
        # set actual instance
        instance._axes = WaveAxes(instance, [np.array(item) for item in value])
        if hasattr(instance, "update"):
            instance.update()

    def __get__(self, instance, objtype=None):
        return instance._axes


class WaveAxes(list):
    """Axes in :class:`Wave` class

    WaveAxes is a list of numpy array that defines axes of the :class:`Wave`.
    Some usufull functions are added to built-in list.

    WaveAxes should be initialized from :class:`Wave` class. Users SHOULD NOT instantiate this class.

    See also:
        :class:`Wave`, :attr:`Wave.axes`
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = weakref.ref(parent)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if hasattr(self._parent(), "update"):
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
        Translate the specified position in axis to the nearest index in data.
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
        Translate the specified indice to the position in data.
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

    @ property
    def x(self):
        """ 
        Shortcut to axes[0]

        Example:
            >>> w = Wave([1,2,3], [1,2,3])
            >>> w.x
            [1,2,3]
            >>> w.x = [3,4,5]
            >>> w.x
            [3,4,5]
            >>> w.axes[0]
            [3,4,5]

        See also:
            :meth:`getAxis`
        """
        return self.getAxis(0)

    @ x.setter
    def x(self, value):
        self[0] = value

    @ property
    def y(self):
        """ Shortcut to axes[1]. See :attr:`x`"""
        return self.getAxis(1)

    @ y.setter
    def y(self, value):
        self[1] = value

    @ property
    def z(self):
        """ Shortcut to axes[2]. See :attr:`x`"""
        return self.getAxis(2)

    @ z.setter
    def z(self, value):
        self[2] = value


class _WaveNoteDescriptor:
    """
    Metadata of :class:`Wave` implemented as :class:`WaveNote` class.

    *note* is python dictionary and is used to save metadata in :class:`Wave`.

    Example:
        >>> w = Wave([1,2,3], note={"key": "item"})
        >>> w.note["key"]
        item
        >>> w.note["key2"] = 1111
        >>> w.note["key2"]
        1111
    """

    def __set__(self, instance, value):
        # check type
        if not isinstance(value, dict):
            raise TypeError("Note should be a dictionary")
        # set actual instance
        instance._note = dict(value)

    def __get__(self, instance, objtype=None):
        return instance._note


def _produceWave(data, axes, note):
    return Wave(data, *axes, *note)


class Wave(QObject):
    """
    Wave class is a central data class in lys, which is composed of :attr:`data`, :attr:`axes`, and :attr:`note`.

    :attr:`data` is a numpy array of any dimension and :attr:`axes` is a list of numpy arrays with size = data.ndim.
    :attr:`note` is a dictionary, which is used to save metadata.

    There are several ways to generate Wave. (See Examples).

    Args:
        data (array_like or str): The data of any dimension, or filename to be loaded
        axes (list of array_like): The axes of data
        note (dict): metadata for Wave.

    Examples:
        Basic initialization

            >>> from lys import Wave
            >>> w = Wave([1,2,3])
            >>> w.data
            [1,2,3]

        Basic initialization with axes and note

            >>> w = Wave(np.ones([2,3]), [1,2], [1,2,3], name="wave1") 
            >>> w.axes          # positional arguments are used for axes
            [[1,2],[1,2,3]]
            >>> w.x             # axes can be accessed from Wave.x, Wave.y etc...
            [1,2]
            >>> w.note          # keyword arguments are saved in note
            {"name": "wave1"}

        Initialize Wave from array of Wave

            >>> w = Wave([1,2,3], [1,2,3])
            >>> w2 = Wave([w,w], [4,5])
            >>> w2.data
            [[1,2,3], [1,2,3]]
            >>> w2.x
            [4,5]
            >>> w2.y
            [1,2,3]

        Save & load numpy npz file

            >>> w = Wave([1,2,3])
            >>> w.export("wave.npz") # save wave to wave.npz
            >>> w2 = Wave("wave.npz")
            >>> w2.data
            [1,2,3]

        Load from various file types by :func:functions.load

            >>> from lys import loadWave
            >>> loadWave("data.png")

    See also:
        :attr:`data`, :attr:`axes`, :attr:`note`
    """
    _nameIndex = 0
    modified = pyqtSignal(object)
    """
    *modified* is a pyqtSignal and is emitted when *Wave* is changed.

    Example:
        >>> w = Wave([1,2,3], name="wave1")
        >>> w.modified.connect(lambda w: print("modified", w.name))
        >>> w.data = [2,3,4]
        modified wave1
    """
    data = _WaveDataDescriptor()
    axes = _WaveAxesDescriptor()
    note = _WaveNoteDescriptor()

    def __init__(self, data=None, *axes, **note):
        super().__init__()
        self.axes = [np.array(None)]
        self.data = np.array(None)
        self.note = note
        if type(data) == str:
            self.__loadData(data)
        else:
            self.__setData(data, *axes)

    def __loadData(self, file):
        """Load data from file"""
        tmp = np.load(file, allow_pickle=True)
        data = tmp['data']
        self.axes = [np.array(None) for i in range(data.ndim)]
        self.data = data
        if 'axes' in tmp:
            self.axes = [axis for axis in tmp['axes']]
        if 'note' in tmp:
            self.note = tmp['note'][()]

    def __setData(self, data, *axes):
        """Set data from *data* and *axes*"""
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
            w = Wave(data, *axes, **self.note)
            return w
        else:
            super().__getitem__(key)

    def __setitem__(self, key, value):
        self.data[key] = value
        self.update()

    def Save(self, file):
        self.export(file)

    def duplicate(self):
        """
        Create duplicated *Wave*

        Return:
            Wave: duplicated wave.

        Example:
            >>> w = Wave([1,2,3])
            >>> w2=w.duplicate()
            >>> w2.data
            [1,2,3]
        """
        return Wave(self.data, *self.axes, **self.note)

    def __reduce_ex__(self, proto):
        return _produceWave, (self.data, list(self.axes), self.note)

    @ staticmethod
    def SupportedFormats():
        """List of supported file formats to export. see :meth:`export`"""
        return ["Numpy npz (*.npz)", "Comma-Separated Values (*.csv)", "Text file (*.txt)"]

    def export(self, path, type="npz"):
        """
        Export *Wave* to file.

        Args:
            path (str): File path to be saved.
            type (str): File extension. See :meth:`SupportedFormats`.

        Exmple:
            >>> w = Wave([1,2,3])
            >>> w.export("wave.npz")
            >>> w2 = Wave.importFrom("wave.npz")
            >>> w2.data
            [1,2,3]

        See also:
            :meth:`importFrom`
        """
        if type in ['Numpy npz (*.npz)', ".npz", "npz"]:
            if not path.endswith(".npz"):
                path = path + ".npz"
            path = os.path.abspath(path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            np.savez_compressed(path, data=self.data, axes=np.array(self.axes, dtype=object), note=self.note, allow_pickle=True)
        if type in ["Comma-Separated Values (*.csv)", ".csv", "csv"]:
            if not path.endswith(".csv"):
                path = path + ".csv"
            np.savetxt(path, self.data, delimiter=',')
        if type in ["Text file (*.txt)", ".txt", "txt"]:
            if not path.endswith(".txt"):
                path = path + ".txt"
            np.savetxt(path, self.data)

    @ staticmethod
    def importFrom(path):
        """
        Import *Wave* from file.

        It is recommended to use :func:`functions.loadWave` to load Wave from various types of files.

        Args:
            path (str): File path to be saved.
            type (str): File extension. See :meth:`SupportedFormats`.

        Exmple:
            >>> w = Wave([1,2,3])
            >>> w.export("wave.npz")
            >>> w2 = Wave.importFrom("wave.npz")
            >>> w2.data
            [1,2,3]

        See also:
            :meth:`export`
        """
        _, ext = os.path.splitext(path)
        if ext == ".npz":
            return Wave(path)
        elif ext == ".csv":
            return Wave(np.loadtxt(path, delimiter=","))
        elif ext == ".txt":
            return Wave(np.loadtxt(path, delimiter=" "))

    def update(self):
        """ 
        Emit *modified* signal

        When *data* is directly changed by indexing, *modified* signal is not emitted.
        Calling *update()* emit *modified* signal manually.

        Example:   
            >>> w = Wave([1,2,3])
            >>> w.modified.connect(lambda: print("modified"))
            >>> w[1] = 0        # modified is emitted through Wave.__setitem__ is called.
            modified
            >>> w.data[1]=0     # modified is NOT emitted through data.__setitem__ is called.
            >>> w.update()
            modified
        """
        self.modified.emit(self)

    def Name(self):
        import inspect
        print("Wave.Name is deprecated. use Wave.name instead")
        print(inspect.stack()[1].filename)
        print(inspect.stack()[1].function)
        return self.name

    @ property
    def name(self):
        """ 
        Shortcut to note["name"]

        Example:
            >>> w = Wave([1,2,3], name="wave1")
            >>> w.note
            {"name": "wave1"}
            >>> w.name
            wave1
            >>> w.name="wave2"
            >>> w.name
            wave2
        """

        if "name" not in self.note:
            self.name = "wave" + str(Wave._nameIndex)
            Wave._nameIndex += 1
        return self.note.get("name")

    @ name.setter
    def name(self, value):
        self.note["name"] = value

    def __str__(self):
        return "Wave object (name = {0}, dtype = {1}, shape = {2})".format(self.name, self.dtype, self.shape)


class DaskWave(QObject):
    axes = _WaveAxesDescriptor()
    note = _WaveNoteDescriptor()

    @classmethod
    def initWorkers(cls, n_workers, threads_per_worker=2):
        try:
            import atexit
            from dask.distributed import Client, LocalCluster
            cluster = LocalCluster(n_workers=n_workers, threads_per_worker=threads_per_worker)
            cls.client = Client(cluster)
            atexit.register(lambda: cls.client.close())
            print("[DaskWave] Local cluster:", cls.client)
        except:
            print("[DaskWave] failed to init dask.distributed")

    def __init__(self, wave, *axes, chunks="auto", **note):
        super().__init__()
        self.data = np.array(None)
        self.axes = [np.array(None)]
        self.note = note
        if isinstance(wave, Wave):
            self.__fromWave(wave, axes, chunks)
        elif isinstance(wave, da.core.Array):
            self.__fromda(wave, axes, chunks, note)
        elif isinstance(wave, DaskWave):
            self.__fromda(wave.data, wave.axes, chunks, wave.note)

    def __fromWave(self, wave, axes, chunks):
        import copy
        if wave.data.dtype == int:
            self.data = da.from_array(wave.data.astype(float), chunks=chunks)
        else:
            self.data = da.from_array(wave.data, chunks=chunks)
        if axes is None:
            self.axes = copy.deepcopy(wave.axes)
        else:
            self.axes = copy.deepcopy(axes)
        self.note = copy.deepcopy(wave.note)

    def __fromda(self, wave, axes, chunks, note):
        import copy
        if chunks == "NoRechunk":
            self.data = wave
        else:
            self.data = wave.rechunk(chunks)
        self.axes = copy.deepcopy(axes)
        self.note = copy.deepcopy(note)

    def __getattr__(self, key):
        if hasattr(self.data, key):
            return self.data.__getattribute__(key)
        if hasattr(self.axes, key):
            return self.axes.__getattribute__(key)
        else:
            return super().__getattr__(key)

    def toWave(self):
        import copy
        w = Wave()
        res = self.data.compute()  # self.client.compute(self.data).result()
        w.data = res
        w.axes = copy.deepcopy(self.axes)
        w.note = copy.deepcopy(self.note)
        return w

    def persist(self):
        self.data = self.data.persist()  # self.client.persist(self.data)

    def sum(self, axis):
        data = self.data.sum(axis)
        axes = []
        for i, ax in enumerate(self.axes):
            if not (i in axis or i == axis):
                axes.append(ax)
        return DaskWave(data, axes=axes)

    def __getitem__(self, key):
        import copy
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if not isinstance(s, int):
                    if ax is None or (ax == np.array(None)).all():
                        axes.append(None)
                    else:
                        axes.append(ax[s])
            d = DaskWave(data, axes=axes, note=copy.deepcopy(self.note))
            return d
        else:
            super().__getitem__(key)

    @staticmethod
    def SupportedFormats():
        return Wave.SupportedFormats()

    def export(self, path, type="Numpy npz (*.npz)"):
        self.toWave().export(path, type)

    def duplicate(self):
        return DaskWave(self, chunks="NoRechunk")
