import warnings
from lys import filters
from lys.Qt import QtCore
from lys.errors import NotImplementedWarning

from .CanvasBase import CanvasPart3D, saveCanvas


class WaveData3D(CanvasPart3D):
    """
    Interface to access wave data in the canvas.
    """
    modified = QtCore.pyqtSignal()
    """This pyqtSignal is emimtted when the data is changed."""

    def __init__(self, canvas, wave):
        super().__init__(canvas)
        self._wave = wave
        self._wave.modified.connect(self._update)
        self._appearance = {}
        self._offset = (0, 0, 0, 0)
        self._filter = None
        self._filteredWave = wave

    @saveCanvas
    def _update(self, *args, **kwargs):
        self._filteredWave = self._calcFilteredWave(self._wave, self._offset, self._filter)
        self._updateData()
        self.modified.emit()

    def _calcFilteredWave(self, w, offset, filter):
        if filter is None:
            filt = filters.Filters([filters.OffsetFilter(offset)])
            filt = filters.Filters([])
        else:
            filt = filter
        w = filt.execute(w)
        return w

    def getWave(self):
        """
        Get the wave.

        Return:
            Wave: The wave.
        """
        return self._wave

    def getFilteredWave(self):
        """
        Get the wave to which offset and filter have been applied.

        Return:
            Wave: The filtered wave.
        """
        return self._filteredWave

    def getName(self):
        """
        Get the name of the wave data.

        Return:
            str: The name.
        """
        return self._appearance.get('DataName', self.getWave().name)

    def setName(self, name):
        """
        Set the name of the data.

        Args:
            name(str): The name of the data.
        """
        self._appearance['DataName'] = name

    @saveCanvas
    def setVisible(self, visible):
        """
        Set the visibility of the data.

        Args:
            visible(bool): The visibility of the data.
        """
        self._setVisible(visible)
        self._appearance['Visible'] = visible

    def getVisible(self):
        """
        Get the visibility of the data.

        Return:
            bool: The visibility of the data.
        """
        return self._appearance.get('Visible', True)

    @saveCanvas
    def setOffset(self, offset):
        """
        Set the offset to the data.

        The data is offset as x'=x*x1+x0 and y'=y*y1+y0.

        Args:
            offset(tuple of length 4 float): The offset in the form of (x0, y0, x1, y1).
        """
        self._offset = offset
        self._update()

    def getOffset(self):
        """
        Get the offset to the data.

        See :meth:`setOffset` for detail.

        Return:
            tuple of length 4 float: The offset in the form of (x0, y0, x1, y1).
        """
        return tuple(self._offset)

    @saveCanvas
    def setFilter(self, filter=None):
        """
        Apply filter to the data.

        Args:
            filter(filterr): The filter. See :class:`lys.filters.filter.FilterInterface.FilterInterface`
        """
        self._filter = filter
        self._update()

    def getFilter(self):
        return self._filter

    def saveAppearance(self):
        """
        Save appearance from dictionary.

        Users can save/load appearance of data by save/loadAppearance methods.

        Return:
            dict: dictionary that include all appearance information.
        """
        return dict(self._appearance)

    @saveCanvas
    def loadAppearance(self, appearance):
        """
        Load appearance from dictionary.

        Users can save/load appearance of data by save/loadAppearance methods.

        Args:
            appearance(dict): dictionary that include all appearance information, which is usually generated by :meth:`saveAppearance` method.
        """
        self.setVisible(appearance.get('Visible', True))
        self.setName(appearance.get('DataName', self.getWave().name))
        self._loadAppearance(appearance)

    def _setVisible(self, visible):
        warnings.warn(str(type(self)) + " does not implement _setVisible(visible) method.", NotImplementedWarning)

    def _updateData(self):
        raise NotImplementedError(str(type(self)) + " does not implement _updateData() method.")

    def _loadAppearance(self, appearance):
        raise NotImplementedError(str(type(self)) + " does not implement _loadAppearance(appearance) method.")


class MeshData3D(WaveData3D):
    @saveCanvas
    def setColor(self, color=None, type="scalars"):
        self.__setAppearance("colorType", type)
        self.__setAppearance("color", color)
        self._setColor(color, type)

    def showEdges(self, b):
        """
        Show edges of the mesh.

        Args:
            b(bool): Whether the edges of the mesh are shown.
        """
        self.__setAppearance("showEdges", b)
        self._showEdges(b)

    def __setAppearance(self, key, value):
        self._appearance[key] = value

    def __getAppearance(self, key, default=None):
        return self._appearance.get(key, default)

    def _loadAppearance(self, appearance):
        pass

    def _setColor(self, color, type):
        warnings.warn(str(type(self)) + " does not implement _setColor(color, type) method.", NotImplementedWarning)

    def _showEdges(self, b):
        warnings.warn(str(type(self)) + " does not implement _showEdges(b) method.", NotImplementedWarning)
