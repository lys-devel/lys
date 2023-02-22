import io
from lys import Wave, load
from lys.Qt import QtCore


class TableData(QtCore.QObject):
    """
    TableData class handles data in :class:`lys.widgets.table.lysTable.lysTable`.

    Args:
        table(lysTable): The table widget.
    """
    updated = QtCore.pyqtSignal()
    """
    Emitted when data data is updated.
    """
    dataSaved = QtCore.pyqtSignal()
    """
    Emitted after the data is saved.
    """
    dataChanged = QtCore.pyqtSignal()
    """
    Emitted when the data is changed.
    """

    def __init__(self, table):
        super().__init__()
        self._original = None
        self._wave = None
        self._slice = None
        table.saveTable.connect(self.__saveTable)
        table.loadTable.connect(self.__loadTable)
        self.dataChanged.connect(self.__modified)

    def __modified(self):
        self._wave.modified.emit(self._wave)

    def setData(self, data):
        """
        Set data.

        Args:
            data(str or Wave): The path to a npz file, or an instance of Wave.
        """
        if isinstance(data, Wave):
            self._original = data
            w = data.duplicate()
        elif isinstance(data, str):
            self._original = data
            w = load(data)
        self._wave = Wave(w.data, *[w.getAxis(i).astype(float) for i in range(w.ndim)], **w.note)
        self.setSlice()

    def getData(self):
        """
        Returns the edited Wave.

        Returns:
            Wave: The edited Wave.
        """
        return self._wave

    def getSlicedData(self):
        """
        Returns the sliced data.

        Returns:
            Wave: The sliced Wave.
        """
        if isinstance(self._slice, int):
            return Wave(self._wave.axes[self._slice])
        else:
            data = self._wave.data[tuple(self._slice)]
            axes = []
            for i, s in enumerate(self._slice):
                if not isinstance(s, int):
                    axes.append(self._wave.axes[i])
            return Wave(data, *axes, **self._wave.note)

    def setSlice(self, slc=None):
        """
        Set a slice.

        If *slc* is None, the default slice is set.

        If *slc* is integer, :meth:`getSlicedData` returns wave.axes[slc].

        Otherwise, :meth:`getSlicedData` returns wave.data[slc].

        Args:
            slc(tuple of slices or int): The slice to be set.
        """
        if slc is None:
            self._slice = self.__getDefaultSlice()
        else:
            self._slice = slc
        self.updated.emit()

    def __getDefaultSlice(self):
        if self._wave.ndim == 1:
            return [slice(None)]
        elif self._wave.ndim == 2:
            return [slice(None), slice(None)]
        elif self._wave.ndim > 2:
            return [slice(None), slice(None)] + ([0] * (self._wave.ndim - 2))

    def getSlice(self):
        """
        Get slice. See :meth:`setSlice`

        Returns:
            tuple of slices or int: The slice.        
        """
        return self._slice

    def save(self):
        """
        Save the contents of the table to file or Wave depending on the argument of :meth:`setData`.
        """
        if isinstance(self._original, Wave):
            self._original.data = self._wave.data
            self._original.axes = self._wave.axes
        elif isinstance(self._original, str):
            self._wave.export(self._original)
        self.dataSaved.emit()

    def __saveTable(self, d):
        if isinstance(self._original, Wave):
            d["type"] = "Wave"
        elif isinstance(self._original, str):
            d["type"] = "File"
            d["File"] = self._original
        b = io.BytesIO()
        self.getData().export(b)
        d['Wave'] = b.getvalue()
        d['Slice'] = str(self._slice)

    def __loadTable(self, d):
        self._wave = Wave(io.BytesIO(d['Wave']))
        if d["type"] == "Wave":
            self._original = self._wave.duplicate()
        elif d["type"] == "File":
            self._original = d["File"]
        self._slice = eval(d["Slice"])
        self.updated.emit()
