import functools
import weakref

from lys.Qt import QtCore
from lys.errors import suppressLysWarnings


def saveCanvas(func):
    """
    When methods of :class:`CanvasBase` or :class:'CanvasPart' that is decorated by *saveCanvas* is called, then *updated* signal of the canvas is emitted. 
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(args[0], CanvasPart3D):
            canvas = args[0].canvas()
        else:
            canvas = args[0]
        if canvas._saveflg:
            res = func(*args, **kwargs)
        else:
            canvas._saveflg = True
            with canvas.delayUpdate():
                res = func(*args, **kwargs)
                canvas.updated.emit()
            canvas._saveflg = False
        return res
    return wrapper


_saveCanvasDummy = saveCanvas


class CanvasBase3D(object):
    """
    Base class for canvas.

    A 3D canvas is composed of :class:`.Data.CanvasData3D`.
    All of these classes inherits :class:`CanvasPart3D` and added by :meth:`addCanvasPart`.

    Users can access all public methods of the classes above from canvas instance.
    """
    saveCanvas = QtCore.pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`SaveAsDictionary` is called."""
    loadCanvas = QtCore.pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`LoadFromDictionary` is called."""
    initCanvas = QtCore.pyqtSignal()
    """pyqtSignal that is emitted when the canvas is initialized."""
    updated = QtCore.pyqtSignal()
    """pyqtSignal that is emitted when the canvas is updated."""
    finalized = QtCore.pyqtSignal(object)
    """pyqtSignal that is emitted when the canvas is finalized."""

    def __init__(self):
        self._saveflg = False
        self._updateFlg = False
        self.__parts = []

    def addCanvasPart(self, part):
        """
        Add :class:`CanvasPart3D` as a part of the canvas.

        Args:
            part(CanvasPart3D): The part to be added.
        """
        self.__parts.append(part)

    def __getattr__(self, key):
        for part in self.__parts:
            if hasattr(part, key):
                return getattr(part, key)
        return super().__getattr__(key)

    def SaveAsDictionary(self, dictionary=None):
        """
        Save the content of the canvas as dictionary.

        Args:
            dictionary(dict): The content of the canvas is written in *dictionary*.

        Return:
            dict: The dictionary in which the information of the canvas is written
        """
        if dictionary is None:
            dictionary = {}
        self.saveCanvas.emit(dictionary)
        return dictionary

    @suppressLysWarnings
    @_saveCanvasDummy
    def LoadFromDictionary(self, dictionary):
        """
        Load the content of the canvas as dictionary.

        Args:
            dictionary(dict): The content of the canvas is loaded from *dictionary*.
        """
        self.loadCanvas.emit(dictionary)

    def delayUpdate(self):
        """
        This method should be used (as [*with*] block) when the canvas is heavily modified to avoid drawing repeatedly.
        """
        return _CanvasLocker3D(self)


class _CanvasLocker3D:
    def __init__(self, canvas):
        self.canvas = canvas

    def __enter__(self):
        if self.canvas._updateFlg:
            return
        self.canvas._updateFlg = True
        self.canvas.enableRendering(False)

    def __exit__(self, exc_type, exc_value, traceback):
        self.canvas._updateFlg = False
        self.canvas.enableRendering(True)


class CanvasPart3D(QtCore.QObject):
    """
    The canvas that inherit :class:`CanvasBase3D` class is composed of multiple *CanvasPart3D*.
    """

    def __init__(self, canvas):
        super().__init__()
        self._canvas = weakref.ref(canvas)

    def canvas(self):
        """
        Get the canvas that contains the CanvasPart3D.

        Return:
            CanvasBase3D: The canvas.
        """
        return self._canvas()
