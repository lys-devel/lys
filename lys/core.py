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

    Examples::

        from lys import SettingDict

        d = SettingDict("Setting.dic")
        d["setting1"] = "SettingString"

        d2 = SettingDict("Setting.dic")   # setting.dic is loaded
        d2["setting1"] # SettingString
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
        self.__Save()

    def __delitem__(self, key):
        del self.data[key]
        self.__Save()

    def __Save(self, file=None):
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
        print(w.data)     # [1,2,3]

        w.data = [2,3,4]
        print(w.data)     # [2,3,4]
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

    Example::

        from lys import Wave

        w = Wave(np.ones([3,3]), [1,2,3], [4,5,6])
        print(w.axes)        # [array([1, 2, 3]), array([4, 5, 6])]

        w.axes[0] = [7,8,9]
        print(w.axes)        # [array([7, 8, 9]), array([4, 5, 6])]

        print(w.x, w.y)      # [7,8,9], [4,5,6], shortcut to axes[0] and axes[1]

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

        Example::

            from lys import Wave

            w = Wave(np.ones([3,3]), [1,2,3], [3,4,5])

            w.posToPoint((2,4))             # (1,1), position (x,y)=(2,4) corresponds index (1,1)
            w.posToPoint((1,2,3), axis=0)   # (0,1,2), position (x1, x2, x3 = 1,2,3) in the 0th dimension correspoinds index (0,1,2)
            w.posToPoint(2, axis=0)         # 1, position x = 2  correspoinds index 1 in 0th dimension
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

        Example::

            from lys import Wave

            w = Wave(np.ones([3,3]), [1,2,3], [3,4,5])
            w.pointToPos((1,1))             # (2,4), index (1,1) corresponds to position (x,y)=(2,4)
            w.pointToPos((0,1,2), axis=0)   # (1,2,3), index (0,1,2) in the 0th dimension correspoinds position (x1, x2, x3 = 1,2,3)
            w.pointToPos(1, axis=0)         # 2, index 1 in 0th dimensions correspoinds position x = 2
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

    @property
    def x(self):
        """Shortcut to axes[0]"""
        return self.getAxis(0)

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        """Shortcut to axes[1]."""
        return self.getAxis(1)

    @y.setter
    def y(self, value):
        self[1] = value

    @property
    def z(self):
        """Shortcut to axes[2]."""
        return self.getAxis(2)

    @z.setter
    def z(self, value):
        self[2] = value


class _WaveNoteDescriptor:
    """
    Metadata of :class:`Wave` and :class:`DaskWave` implemented as :class:`WaveNote` class.

    All public methods can also be accessed from :class:`Wave` and :class:`DaskWave` through __getattr__.

    *note* is python dictionary and is used to save metadata in :class:`Wave` :class:`DaskWave` class.

    Example::

        from lys import Wave

        w = Wave([1,2,3], key = "item")
        print(w.note["key"])  # item

        w.note["key2"] = 1111
        print(w.note["key2"]) # 1111
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

    @property
    def name(self):
        """
        Shortcut to note["name"], which is frequently used as a name of :class:`Wave` and :class:`DaskWave`.

        Example::

            from lys import Wave

            w = Wave([1,2,3], name="wave1")
            print(w.note)    # {'name': 'wave1'}
            print(w.name)    # 'wave1'

            w.name="wave2"
            print(w.name)    # 'wave2'
        """

        if "name" not in self:
            self["name"] = "wave" + str(WaveNote._nameIndex)
            WaveNote._nameIndex += 1
        return self.get("name")

    @name.setter
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

    Basic initialization without axes and note::

        from lys import Wave

        w = Wave([1,2,3])   # Axes are automatically set.
        print(w.data, w.x)  # [1 2 3] [0. 1. 2.]

    Basic initialization with axes and note::

        from lys import Wave

        w = Wave(np.ones([2,3]), [1,2], [1,2,3], name="wave1")

        print(w.axes)     # [array([1, 2]), array([1, 2, 3])]
        print(w.x)        # [1 2], axes can be accessed from Wave.x, Wave.y etc...
        print(w.note)     # {'name': 'wave1'}, keyword arguments are saved in note

    Initialize Wave from array of Wave::

        from lys import Wave

        w = Wave([1,2,3], [4,5,6])
        w2 = Wave([w,w], [7,8])

        print(w2.data)       # [[1 2 3], [1 2 3]]
        print(w2.x, w2.y)    # [7,8], [4,5,6]

    Save & load numpy npz file::

        from lys import Wave

        w = Wave([1,2,3])
        w.export("wave.npz") # save wave to wave.npz

        w2 = Wave("wave.npz")
        print(w2.data)       # [1 2 3]

    Direct access numpy array methods::

        from lys import Wave

        w = Wave(np.zeros((100,100)))
        print(w.shape)  # (100,100)

    See also:
        :attr:`data`, :attr:`axes`, :attr:`note`
    """
    modified = QtCore.pyqtSignal(object)
    """
    *modified* is a pyqtSignal, which is emitted when *Wave* is changed.

    Example::

        from lys import Wave

        w = Wave([1,2,3], name="wave1")
        w.modified.connect(lambda w: print("modified", w.name))
        w.data = [2,3,4] # modified wave1
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
        self.note["file"] = file
        if isinstance(file, str):
            self.name = os.path.splitext(os.path.basename(file))[0]

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

    @staticmethod
    def SupportedFormats():
        """List of supported file formats to export. see :meth:`export`"""
        return ["Numpy npz (*.npz)", "Comma-Separated Values (*.csv)", "Text file (*.txt)"]

    def export(self, path, type="npz"):
        """
        Export *Wave* to file.

        Args:
            path (str): File path to be saved.
            type (str): File extension. See :meth:`SupportedFormats`.

        Exmple::

            from lys import Wave

            w = Wave([1,2,3])
            w.export("wave.npz")

            w2 = Wave.importFrom("wave.npz")
            print(w2.data) # [1,2,3]

            w3 = Wave("wave.npz") # If the file is .npz, this is also possible.

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

    @staticmethod
    def importFrom(path):
        """
        Import *Wave* from file.

        Args:
            path (str): File path to be saved.
            type (str): File extension. See :meth:`SupportedFormats`.

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
            Wave: Duplicated wave.

        Example::

            from lys import Wave

            w = Wave([1,2,3])
            w2=w.duplicate()
            print(w2.data) # [1,2,3]
        """
        return Wave(self.data, *self.axes, **self.note)

    def update(self):
        """
        Emit *modified* signal

        When *data* is directly changed by indexing, *modified* signal is not emitted.
        Calling *update()* emit *modified* signal manually.

        Example::

            from lys import Wave

            w = Wave([1,2,3])
            w.modified.connect(lambda: print("modified"))

            w.data = [0, 1, 2]        # modified, modified is emitted when Wave.data is changed.
            w.data[1] = 0             # modified is NOT emitted through data.__setitem__ is called.
            w.update()                # modified
        """
        self.modified.emit(self)

    def insert(self, index=np.inf, axis=0, value=None, axisValue=None):
        """
        Insert a value into the data array and the corresponding axis array.

        Args:
            index (int, optional): Index of value to be inserted. If index is not specified, the value is appended.
            axis (int, optional): Axis along which to insert the value. Default is 0.
            value (float, optional): Value to be inserted. Should be a scalar or a compatible array. Default is None.
            axisValue (float, optional): Value to be inserted into the axis array. If None, the index is used.

        Notes:
            If the data array contains integers and value is None, it is converted to floats before insertion.

        Example::

            from lys import Wave

            w = Wave([[1, 2, 3], [4, 5, 6]], [1, 2], [3, 4, 5])
            w.insert(index=1, axis=1, value=7, axisValue=8)
            print(w.data)       # [[1, 7, 2, 3], [4, 7, 5, 6]])
            print(w.axes[0])    # [1, 2]
            print(w.axes[1])    # [3, 8, 4, 5]
        """
        if index is np.inf:
            index = self.data.shape[axis]
        if 'int' in str(self.data.dtype) and value is None:
            self.data = self.data.astype(float)
        axes = self.axes[axis]
        self.data = np.insert(self.data, index, value, axis)
        self.axes[axis] = np.insert(axes, index, axisValue if axisValue is not None else index, 0)

    def delete(self, index=np.inf, axis=0):
        """
        Delete a value from the data array and the corresponding axis array.

        Args:
            index (int, optional): Index of value to be deleted. If index is not specified, the last value is deleted.
            axis (int, optional): Axis along which to delete the value. Default is 0.

        Example::

            from lys import Wave

            w = Wave([[1, 2, 3], [4, 5, 6]], [1, 2], [3, 4, 5])
            w.delete(index=1, axis=1)
            print(w.data)       # [[1, 3], [4, 6]]
            print(w.axes[0])    # [1, 2]
            print(w.axes[1])    # [3, 5]
        """
        if index is np.inf:
            index = self.data.shape[axis] - 1
        axes = self.axes[axis]
        self.data = np.delete(self.data, index, axis)
        self.axes[axis] = np.delete(axes, index, 0)

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
    Particularly, *DaskWave* is extensively used in MultiCut.

    :attr:`data` is a dask array of any dimension. See :class:`Wave` for :attr:`axes` and :attr:`note`.

    Semi-automatic parallel computing is executed when *lys* is launched with parallel computing option (-n).

    See dask manual in https://docs.dask.org/en/latest/ for detailed usage of dask array.

    All public methods in *data*, *axes*, and *note* are accessible from *DaskWave* class through __getattr__.

    *DaskWave* and *Wave* can easily be converted to each other via construtor of *DaskWave* and :meth:`compute` method.

    Args:
        data (Wave or array_like or dask array): The data of any dimension
        axes (list of array_like): The axes of data
        note (dict): metadata for Wave.
        chunks ('auto' or tuple): chunks to be used for dask array.

    Example1::

        from lys import Wave, DaskWave

        w = Wave([1,2,3])       # Initial wave
        dw = DaskWave(w)        # Convert to DaskWave
        dw.data *= 2
        result = dw.compute()   # Parallel computing is executed through dask. Result is Wave.
        print(result,data)      # [2,4,6]

    Example2::

        from lys import Wave, DaskWave

        dw = DaskWave([1,2,3])  # through dask.array.from_array
        dw.compute().data       # [1,2,3]

    Example3::

        from lys import Wave, DaskWave
        import dask.array as da

        arr = da.from_array([1,2,3])   # dask array can be prepared by other mehotds, such as dask.delayed if data is huge
        dw = DaskWave(arr)
        dw.compute().data   #[1,2,3]
    """
    data = _DaskWaveDataDescriptor()
    axes = _WaveAxesDescriptor()
    note = _WaveNoteDescriptor()

    @classmethod
    def initWorkers(cls, n_workers, threads_per_worker=1):
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
        Return calculated Wave.

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

        Example::

            from lys import DaskWave

            w = DaskWave([1,2,3])
            w2=w.duplicate()
            print(w2.compute().data) # [1,2,3]
        """
        return DaskWave(self, chunks="NoRechunk")


class Version:
    def __init__(self, version):
        self._version = str(version)
        self._verNum = tuple(int(i) for i in self._version.split(".") if i.isdigit())

    def __gt__(self, other):
        if (not isinstance(other, Version)):
            other = Version(other)
        maxlen = max(len(self._verNum), len(other._verNum))
        nself = 10**np.arange(maxlen, maxlen - len(self._verNum), -1, dtype=int)
        nother = 10**np.arange(maxlen, maxlen - len(other._verNum), -1, dtype=int)
        return nself.dot(self._verNum) > nother.dot(other._verNum)

    def __lt__(self, other):
        return not (self > other or self == other)

    def __eq__(self, other):
        if (not isinstance(other, Version)):
            other = Version(other)
        return self._verNum == other._verNum

    def __ne__(self, other):
        return not self == other

    def __ge__(self, other):
        return self > other or self == other

    def __le__(self, other):
        return self < other or self == other

    def __str__(self):
        return self._version
