import functools
import weakref

from lys.Qt import QtCore
from lys.decorators import suppressLysWarnings


def saveCanvas(func):
    """
    When methods of :class:`CanvasBase` or :class:'CanvasPart' that is decorated by *saveCanvas* is called, then *updated* signal of the canvas is emitted. 
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(args[0], CanvasPart):
            canvas = args[0].canvas()
        else:
            canvas = args[0]
        if canvas._saveflg:
            res = func(*args, **kwargs)
        else:
            canvas._saveflg = True
            res = func(*args, **kwargs)
            canvas.updated.emit()
            canvas._saveflg = False
        return res
    return wrapper


def disableSaveCanvas(func):
    """
    When methods of :class:`CanvasBase` or :class:'CanvasPart' that is decorated by *disableSaveCanvas* is called, then *updated* signal of the canvas is *not* emitted in that method.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(args[0], CanvasPart):
            canvas = args[0].canvas()
        else:
            canvas = args[0]
        if canvas._saveflg:
            res = func(*args, **kwargs)
        else:
            canvas._saveflg = True
            res = func(*args, **kwargs)
            canvas._saveflg = False
        return res
    return wrapper


_saveCanvasDummy = saveCanvas


class CanvasBase(object):
    """
    Base class for canvas.

    Canvas is composed of :class:`.Area.CanvasSize`, :class:`.Area.CanvasSize`, :class:`.Axes.CanvasAxis`, :class:`.Axes.CanvasTicks`,
    :class:`.AxisLabel.CanvasAxisLabel`, :class:`.AxisLabel.CanvasTickLabel`, :class:`Data.CanvasData`, and :class:`Annotation.CanvasAnnotation`.

    All of these classes inherits :class:`CanvasPart` and added by :meth:`addCanvasPart`.

    Users can access all public methods of the classes above.
    """
    saveCanvas = QtCore.pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`SaveAsDictionary` is called."""
    loadCanvas = QtCore.pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`LoadFromDictionary` is called."""
    initCanvas = QtCore.pyqtSignal()
    """pyqtSignal that is emitted when the canvas is initialized."""
    updated = QtCore.pyqtSignal()
    """pyqtSignal that is emitted when the canvas is updated."""

    def __init__(self):
        self._saveflg = False
        self.__parts = []

    def addCanvasPart(self, part):
        """
        Add :class:`CanvasPart` as a part of the canvas.

        Args:
            part(CanvasPart): The part to be added.
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

    def finalize(self):
        """
        Finalize the canvas.

        Several graph library (including matplotlib) requires explicit finalization to break circular reference, which causes memory leak.

        Call this method to finalize the canvas, which is usually done by parent widget (such as Graph).
        """
        pass

    def delayUpdate(self):
        """
        This method should be used (as [*with*] block) when the canvas is heavily modified to avoid drawing repeatedly.
        """
        return _CanvasLocker(self)


class _CanvasLocker:
    def __init__(self, canvas):
        self.canvas = canvas

    def __enter__(self):
        self.canvas._saveflg = True

    def __exit__(self, exc_type, exc_value, traceback):
        self.canvas._saveflg = False
        self.canvas.updated.emit()


class CanvasPart(QtCore.QObject):
    """
    The canvas that inherit :class:`CanvasBase` class is composed of multiple *CanvasPart*.
    """

    def __init__(self, canvas):
        super().__init__()
        self._canvas = weakref.ref(canvas)

    def canvas(self):
        """
        Get the canvas that contains the CanvasPart.

        Return:
            CanvasBase: The canvas.
        """
        return self._canvas()
