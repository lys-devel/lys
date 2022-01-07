import functools
import weakref
from PyQt5.QtCore import QObject, pyqtSignal


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


_saveCanvasDummy = saveCanvas


class CanvasBase(object):
    """
    Base class for canvas.

    Canvas is composed of :class:`.Area.CanvasSize`, :class:`.Area.CanvasSize`, :class:`.Axes.CanvasAxis`, :class:`.Axes.CanvasTicks`,
    :class:`.AxisLabel.CanvasAxisLabel`, :class:`.AxisLabel.CanvasTickLabel`, :class:`Data.CanvasData`, and :class:`Annotation.CanvasAnnotation`.

    All of these classes inherits :class:`CanvasPart` and added by :meth:`addCanvasPart`.
    """
    saveCanvas = pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`SaveAsDictionary` is called."""
    loadCanvas = pyqtSignal(dict)
    """pyqtSignal that is emitted when :meth:`LoadFromDictionary` is called."""
    initCanvas = pyqtSignal()
    """pyqtSignal that is emitted when the canvas is initialized."""
    updated = pyqtSignal()
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

    def SaveAsDictionary(self, dictionary):
        """
        Save the content of the canvas as dictionary.

        Args:
            dictionary(dict): The content of the canvas is written in *dictionary*.
        """
        self.saveCanvas.emit(dictionary)

    @_saveCanvasDummy
    def LoadFromDictionary(self, dictionary):
        """
        Load the content of the canvas as dictionary.

        Args:
            dictionary(dict): The content of the canvas is loaded from *dictionary*.
        """
        self.loadCanvas.emit(dictionary)


class CanvasPart(QObject):
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
