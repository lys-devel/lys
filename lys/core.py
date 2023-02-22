import os
import io
import weakref
import atexit

import numpy as np
import dask.array as da

from lys.Qt import QtCore


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

    All public methods of *data* can also be accessed from :class:`Wave`.

    Any type of sequential array will be automatically converted to numpy.ndarray when it is set as *data*.

    Example::

        from lys import Wave

        w = Wave([1,2,3])
        w.data # [1,2,3]

        w.data = [2,3,4]
        w.data # [2,3,4]
    """

    def __set__(self, instance, value):
        """set data and update axes"""
        instance._data = np.array(value)
        if hasattr(instance, "axes"):
            instance.axes._update(instance._data)
        instance.update()

    def __get__(self, instance, objtype=None):
        return instance._data


class _WaveAxesDescriptor:
    """
    Axes of :class:`Wave` and :class:`DaskWave` implemented as :class:`WaveAxes` class.

    *axes* is list of numpy arrays and is used to visualize data.

    All public methods in *WaveAxes* class can also be accessed from :class:`Wave` and :class:`DaskWave` through __getattr__.

    Example:

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

        Even if the axis is None, automatically-generated axis can be always obtained by *getAxis* method.

            >>> w.getAxis(0)
            [7,8,9]
            >>> w.getAxis(1)
            [0,1,2]

        *x*, *y*, and *z* is shortcut to axes[0], axes[1], and axes[2]

            >>> w = Wave(np.ones([2,3]), [0,1], [2,3,4])
            >>> w.x
            [0,1]
            >>> w.y
            [2,3,4]

    See also:
        :class:`WaveAxes`, :attr:`x`, :attr:`y`, :attr:`z`
    """

    def __set__(self, instance, value):
        # check type
        if not hasattr(value, "__iter__"):
            raise TypeError("Axes should be a list of array or None: Present value = " + str(value))

        # set actual instance
        instance._axes = WaveAxes(instance, value)
        if hasattr(instance, "update"):
            instance.update()

    def __get__(self, instance, objtype=None):
        return instance._axes


class WaveAxes(list):
    """Axes in :class:`Wave` and :class:`DaskWave` class

    *WaveAxes* is a list of numpy array that defines axes of the :class:`Wave` and :class:`DaskWave`.

    All public methods in *WaveAxes* can also be accessed from :class:`Wave` and :class:`DaskWave` through __getattr__.

    Some usufull functions are added to built-in list.

    *WaveAxes* should be initialized from :class:`Wave` and :class:`DaskWave` class. Users SHOULD NOT directly instantiate this class.

    See also:
        :class:`Wave`, :attr:`Wave.axes`, :class:`DaskWave`
    """

    def __init__(self, parent, axes, force=False):
        super().__init__()
        self._parent = weakref.ref(parent)
        for d in range(parent.data.ndim):
            if force:
                self.append(axes[d])
            elif len(axes) > d:
                self.append(self.__createValidAxis(axes[d], d))
            else:
                self.append(self.__createValidAxis(None, d))

    def __setitem__(self, key, value):
        super().__setitem__(key, self.__createValidAxis(value, key))
        if hasattr(self._parent(), "update"):
            self._parent().update()

    def getAxis(self, dim):
        """
        Shortcut to wave.axes[dim]

        Args:
            dim (int): The dimension of the axis.

        Returns:
            numpy.ndarray: The axis of the specified dimension.

        """
        return self[dim]

    def __createValidAxis(self, val, dim):
        val = np.array(val)
        data = self._parent().data
        if val.ndim == 0:
            return np.arange(data.shape[dim]).astype(float)
        else:
            if data.shape[dim] == val.shape[0]:
                return val
            else:
                res = np.arange(data.shape[dim])
                res[:min(data.shape[dim], val.shape[0])] = val[:min(data.shape[dim], val.shape[0])]
                return res

    def posToPoint(self, pos, axis=None):
        """
        Translate the specified position in axis to the nearest indice in data.

        This method can be accessed directly from :class:`Wave` and :class:`DaskWave` class through __getattr__.

        If *axis* is None, then *pos* should be array of size = data.ndim.
        *pos* = (x,y,z,...) is translated to indice (n1, n2, n3, ...)

        if *axis* is not None, then pos is interpreted as position in axis-th dimension.
        When *axis* = 1, *pos* = (y1, y2, y3, ...) is translated to indice (n1, n2, n3, ...)

        Args:
            pos (numpy.ndarray or float): The position that is translted to indice.
            axis (None or int): see above description

        Returns:
            tuple or int: The indice corresponding to pos.

        Example:
            >>> w = Wave(np.ones([3,3]), [1,2,3], [3,4,5])
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
            return int(np.abs(self.getAxis(axis) - pos).argmin())

    def pointToPos(self, indice, axis=None):
        """
        Translate the specified indice to the position in data.

        This method can be accessed directly from :class:`Wave` and :class:`DaskWave` class through __getattr__.

        If *axis* is None, then indice should be array of size = data.ndim.
        *indice* = (n1, n2, n3, ...) is translated to position (x, y, z, ...)

        If *axis* is not None, then *indice* is interpreted as indice in *axis*-th dimension.
        When *axis* = 1, *indice* = (n1, n2, n3, ...) is translated to positions (y1, y2, y3, ...)

        Args:
            indice (array of int): The indice that is translted to position.
            axis (None or int): see above description

        Returns:
            tuple or float: The position corresponding to indice.

        Example:
            >>> w = Wave(np.ones([2,2]), [1,2,3], [3,4,5])
            >>> w.pointToPos((1,1))
            (2,4)       # index (1,1) corresponds to position (x,y)=(2,4)
            >>> w.posToPoint((0,1,2), axis=0)
            (1,2,3)     # index (0,1,2) in the 0th dimension correspoinds position (x1, x2, x3 = 1,2,3)
            >>> w.posToPoint(1, axis=0)
            2           #  index 1 in 0th dimensions correspoinds position x = 2
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
        old_axes = list(self)
        self.clear()
        for d in range(data.ndim):
            if len(old_axes) > d:
                self.append(self.__createValidAxis(old_axes[d], d))
            else:
                self.append(self.__createValidAxis(None, d))

    @ property
    def x(self):
        """
        Shortcut to axes[0]

        Example::

            from lys import Wave
            w = Wave([1,2,3], [1,2,3])
            w.x
            # [1,2,3]
            w.x = [3,4,5]
            w.x
            # [3,4,5]
        """
        return self.getAxis(0)

    @ x.setter
    def x(self, value):
        self[0] = value

    @ property
    def y(self):
        """
        Shortcut to axes[1]. See :attr:`x`
        """
        return self.getAxis(1)

    @ y.setter
    def y(self, value):
        self[1] = value

    @ property
    def z(self):
        """ 
        Shortcut to axes[2]. See :attr:`x`
        """
        return self.getAxis(2)

    @ z.setter
    def z(self, value):
        self[2] = value


class _WaveNoteDescriptor:
    """
    Metadata of :class:`Wave` and :class:`DaskWave` implemented as :class:`WaveNote` class.
    All public methods can also be accessed from :class:`Wave` and :class:`DaskWave` through __getattr__.

    *note* is python dictionary and is used to save metadata in :class:`Wave` :class:`DaskWave` class.

    Example:
        >>> w = Wave([1,2,3], key = "item"})
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
        instance._note = WaveNote(value)

    def __get__(self, instance, objtype=None):
        return instance._note


class WaveNote(dict):
    """Note in :class:`Wave` and :class:`DaskWave` class

    WaveNote is a dictionary to save metadata in :class:`Wave` and :class:`DaskWave` class.
    All public methods can also be accessed from :class:`Wave` and :class:`DaskWave` through __getattr__.
    Some usufull functions are added to built-in dict.

    WaveNote should be initialized from :class:`Wave` and :class:`DaskWave` class. Users SHOULD NOT directly instantiate this class.

    See also:
        :class:`Wave`, :attr:`Wave.note`
    """
    _nameIndex = 0

    @ property
    def name(self):
        """
        Shortcut to note["name"], which is frequently used as a name of :class:`Wave` and :class:`DaskWave`.

        This method can be accessed directly from :class:`Wave` and :class:`DaskWave` class through __getattr__.

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

        if "name" not in self:
            self["name"] = "wave" + str(WaveNote._nameIndex)
            WaveNote._nameIndex += 1
        return self.get("name")

    @ name.setter
    def name(self, value):
        self["name"] = value


def _produceWave(data, axes, note):
    return Wave(data, *axes, **note)


class Wave(QtCore.QObject):
    """
    Wave class is a central data class in lys, which is composed of :attr:`data`, :attr:`axes`, and :attr:`note`.

    :attr:`data` is a numpy array of any dimension and :attr:`axes` is a list of numpy arrays with size = data.ndim.
    :attr:`note` is a dictionary, which is used to save metadata.

    All public methods in *data*, *axes*, and *note* are accessible from *Wave* class through __getattr__.

    There are several ways to generate Wave. (See Examples).

    Args:
        data (array_like or str): The data of any dimension, or filename to be loaded
        axes (list of array_like): The axes of data
        note (dict): metadata for Wave.

    Examples:
        Basic initialization without axses and note

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

            >>> w = Wave([1,2,3], [4,5,6])
            >>> w2 = Wave([w,w], [7,8])
            >>> w2.data
            [[1,2,3], [1,2,3]]
            >>> w2.x
            [7,8]
            >>> w2.y
            [4,5,6]

        Save & load numpy npz file

            >>> w = Wave([1,2,3])
            >>> w.export("wave.npz") # save wave to wave.npz
            >>> w2 = Wave("wave.npz")
            >>> w2.data
            [1,2,3]

        Direct access numpy array methods

            >>> w = Wave(np.zeros((100,100)))
            >>> w.shape
            (100,100)

        Load from various file types by :func:`.functions.load`

            >>> from lys import load
            >>> w = load("data.png")
            >>> display(w)

    See also:
        :attr:`data`, :attr:`axes`, :attr:`note`
    """
    modified = QtCore.pyqtSignal(object)
    """
    *modified* is a pyqtSignal, which is emitted when *Wave* is changed.

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
        if type(data) == str or type(data) == io.BytesIO:
            self.__loadData(data)
        else:
            self.__setData(data, *axes, **note)

    def __loadData(self, file):
        """Load data from file"""
        if isinstance(file, str):
            tmp = np.load(file, allow_pickle=True)
        elif isinstance(file, io.BytesIO):
            tmp = np.load(io.BytesIO(file.getvalue()), allow_pickle=True)
        self.data = tmp['data']
        if 'axes' in tmp:
            axes = []
            for axis in tmp['axes']:
                if axis is None:
                    axes.append(np.array(None))
                elif axis.ndim == 0:
                    axes.append(np.array(None))
                else:
                    axes.append(np.array(axis, dtype=type(axis[0])))
            self.axes = axes
        else:
            self.axes = []
        if 'note' in tmp:
            self.note = tmp['note'][()]

    def __setData(self, data, *axes, **note):
        """Set data from *data*, *axes*, and *note*"""
        if hasattr(data, "__iter__"):
            if len(data) > 0:
                if isinstance(data[0], Wave):
                    self.__joinWaves(data, *axes, **note)
                    return
        self.data = data
        self.axes = axes
        self.note = note

    def __joinWaves(self, waves, *axes, **note):
        self.data = np.array([w.data for w in waves])
        if len(axes) == 1:
            ax = list(axes)
        else:
            ax = [None]
        self.axes = ax + waves[0].axes
        self.note = note

    def __getattr__(self, key):
        if "_data" in self.__dict__:
            if hasattr(self.data, key):
                return getattr(self.data, key)
        if "_axes" in self.__dict__:
            if hasattr(self.axes, key):
                return getattr(self.axes, key)
        if "_note" in self.__dict__:
            if hasattr(self.note, key):
                return getattr(self.note, key)
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        if "_axes" in self.__dict__:
            if hasattr(self.axes, key):
                return setattr(self.axes, key, value)
        if "_note" in self.__dict__:
            if hasattr(self.note, key):
                return setattr(self.note, key, value)
        return super().__setattr__(key, value)

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
            if isinstance(path, str):
                if not path.endswith(".npz"):
                    path = path + ".npz"
                path = os.path.abspath(path)
                os.makedirs(os.path.dirname(path), exist_ok=True)
            np.savez_compressed(path, data=self.data, axes=np.array(self.axes, dtype=object), note=dict(self.note), allow_pickle=False)
        if type in ["Comma-Separated Values (*.csv)", ".csv", "csv"]:
            if isinstance(path, str):
                if not path.endswith(".csv"):
                    path = path + ".csv"
            np.savetxt(path, self.data, delimiter=',')
        if type in ["Text file (*.txt)", ".txt", "txt"]:
            if isinstance(path, str):
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

    def update(self):
        """
        Emit *modified* signal

        When *data* is directly changed by indexing, *modified* signal is not emitted.
        Calling *update()* emit *modified* signal manually.

        Example:
            >>> w = Wave([1,2,3])
            >>> w.modified.connect(lambda: print("modified"))
            >>> w.data = [0, 1, 2]        # modified is emitted when Wave.data is changed.
            modified
            >>> w.data[1]=0               # modified is NOT emitted through data.__setitem__ is called.
            >>> w.update()
            modified
        """
        self.modified.emit(self)

    def __str__(self):
        return "Wave object (name = {0}, dtype = {1}, shape = {2})".format(self.name, self.dtype, self.shape)

    def __getitem__(self, key):
        w = Wave()
        w._data = self.data[key]
        if type(key) != tuple:
            if isinstance(key, slice):
                key = (key,)
            else:
                key = (slice(key),)
        while len(key) < len(w._data.shape):
            key = tuple(list(key) + [slice(None)])
        axes = [ax[sl] for ax, sl in zip(self._axes, key)]
        w._axes = WaveAxes(w, axes, force=True)
        w.note = self._note
        return w

    def __setitem__(self, key, value):
        self._data[key] = value
        self.modified.emit(self)
    # deprecated methods

    def Name(self):
        """deprecated method"""
        import inspect
        print("Wave.Name is deprecated. use Wave.name instead")
        print(inspect.stack()[1].filename)
        print(inspect.stack()[1].function)
        return self.name

    def Save(self, file):
        """deprecated method"""
        import inspect
        print("Wave.Save is deprecated. use Wave.export instead")
        print(inspect.stack()[1].filename)
        print(inspect.stack()[1].function)
        self.export(file)


class _DaskWaveDataDescriptor:
    """
    *data* is dask array that represents data of :class:`DaskWave`

    All public methods of *data* can be accessed from :class:`DaskWave` via __getattr__.
    """

    def __set__(self, instance, value):
        instance._data = value
        if hasattr(instance, "axes"):
            instance.axes._update(instance._data)

    def __get__(self, instance, objtype=None):
        return instance._data


class DaskWave(QtCore.QObject):
    """
    *DaskWave* class is a central data class in lys, which is used for easy parallel computing via dask.

    This class is mainly used for parallel computing of data *with axes and notes*, which enables us to consistent calculation of data and axes.
    Particularly, *DaskWave* is extensively used in *Multicut* package.

    :attr:`data` is a dask array of any dimension. See :class:`Wave` for :attr:`axes` and :attr:`note`.

    Semi-automatic parallel computing is executed is *lys* is launched with parallel computing option.

    See dask manual in https://docs.dask.org/en/latest/ for detailed usage of dask array.

    All public methods in *data*, *axes*, and *note* are accessible from *DaskWave* class through __getattr__.

    *DaskWave* and *Wave* can easily be converted to each other via construtor of *DaskWave* and :meth:`compute` method.

    Args:
        data (Wave or array_like or dask array): The data of any dimension
        axes (list of array_like): The axes of data
        note (dict): metadata for Wave.
        chunks ('auto' or tuple): chunks to be used for dask array.

    Example:

        Basic usage

        >>> from lys import Wave, DaskWave
        >>> w = Wave([1,2,3])       # Initial wave
        >>> dw = DaskWave(w)        # convert to DaskWave
        >>> dw.data *= 2
        >>> result = dw.compute()   # parallel computing is executed through dask
        >>> type(result)
        <class 'lys.core.Wave'>
        >>> result.data
        [2,4,6]

        Initialization from array

        >>> dw = DaskWave([1,2,3])  # through dask.array.from_array
        >>> dw.compute().data
        [1,2,3]

        Initialization from dask array (for large array)

        >>> import dask.array as da
        >>> arr = da.from_array([1,2,3])   # dask array can be prepared by other mehotds, such as dask.delayed if data is huge
        >>> dw = DaskWave(arr)
        >>> dw.compute().data
        [1,2,3]
    """
    data = _DaskWaveDataDescriptor()
    axes = _WaveAxesDescriptor()
    note = _WaveNoteDescriptor()

    @classmethod
    def initWorkers(cls, n_workers, threads_per_worker=2):
        """
        Initializa local cluster. 
        This method is automatically called when lys is launched with parallel computing option.
        DO NOT call this method within lys.

        Args:
            n_workers (int): number of workers to be launched.
            threads_per_worker (int): number of therads for each worker.
        """
        try:
            from dask.distributed import Client, LocalCluster

            def closeClient():
                print("[DaskWave] Closing local cluster...")
                cls.client.close()
                print("[DaskWave] Closing local cluster finished")
            cluster = LocalCluster(n_workers=n_workers, threads_per_worker=threads_per_worker)
            cls.client = Client(cluster)
            atexit.register(closeClient)
            print("[DaskWave] Local cluster launched:", cls.client)
        except Exception:
            print("[DaskWave] failed to initialize local cluster for parallel computing.")

    def __init__(self, data, *axes, chunks="auto", **note):
        super().__init__()
        if isinstance(data, Wave):
            return self.__fromWave(data, chunks)
        elif isinstance(data, da.core.Array):
            return self.__fromda(data, axes, chunks, note)
        elif isinstance(data, DaskWave):
            return self.__fromda(data.data, data.axes, chunks, data.note)
        elif isinstance(data, list) or isinstance(data, tuple):
            if len(data) > 0:
                if isinstance(data[0], DaskWave):
                    return self.__joinWaves(data, *axes, **note)
        self.__fromWave(Wave(data, *axes, **note), chunks)

    def __fromWave(self, wave, chunks):
        """Load from Wave"""
        self.data = da.from_array(wave.data, chunks=chunks)
        self.axes = wave.axes
        self.note = wave.note

    def __fromda(self, wave, axes, chunks, note):
        """Load from da.core.Array"""
        if chunks == "NoRechunk":
            self.data = wave
        else:
            self.data = wave.rechunk(chunks)
        self.axes = axes
        self.note = note

    def __joinWaves(self, waves, *axes, **note):
        self.data = da.stack([w.data for w in waves])
        if len(axes) == 1:
            ax = list(axes)
        else:
            ax = [None]
        self.axes = ax + waves[0].axes
        self.note = note

    def __getattr__(self, key):
        if "_note" in self.__dict__:
            if hasattr(self.note, key):
                return getattr(self.note, key)
        if "_axes" in self.__dict__:
            if hasattr(self.axes, key):
                return getattr(self.axes, key)
        if "_data" in self.__dict__:
            if hasattr(self.data, key):
                return getattr(self.data, key)
        return super().__getattr__(key)

    def __setattr__(self, key, value):
        if "_axes" in self.__dict__:
            if hasattr(self.axes, key):
                return setattr(self.axes, key, value)
        if "_note" in self.__dict__:
            if hasattr(self.note, key):
                return setattr(self.note, key, value)
        return super().__setattr__(key, value)

    def compute(self):
        """
        Return calculated Wave
        Wave.data.compute() is called when this method is called.
        After lazy evaluation is finished, this method returns calculated *Wave*.

        Return:
            Wave: cauculated result
        """
        return Wave(self.data.compute(), *self.axes, **self.note)

    def persist(self):
        """Call data.persist"""
        self.data = self.data.persist()

    def duplicate(self):
        """
        Create duplicated *DaskWave*

        Return:
            DaskWave: duplicated wave.

        Example:
            >>> w = DaskWave([1,2,3])
            >>> w2=w.duplicate()
            >>> w2.compute().data
            [1,2,3]
        """
        return DaskWave(self, chunks="NoRechunk")

    def __getitem__(self, key):
        import inspect
        print("Wave.__getitem__ is deprecated.")
        print(inspect.stack()[1].filename)
        print(inspect.stack()[1].function)
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if not isinstance(s, int):
                    if ax is None or (ax == np.array(None)).all():
                        axes.append(None)
                    else:
                        axes.append(ax[s])
            d = DaskWave(data, *axes, **self.note)
            return d
        else:
            super().__getitem__(key)
