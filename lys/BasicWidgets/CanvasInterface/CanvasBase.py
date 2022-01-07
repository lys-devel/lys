import functools
import weakref
from PyQt5.QtCore import QObject, pyqtSignal


def saveCanvas(func):
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
    saveCanvas = pyqtSignal(dict)
    loadCanvas = pyqtSignal(dict)
    initCanvas = pyqtSignal()
    updated = pyqtSignal()

    def __init__(self):
        self._saveflg = False
        self.__parts = []

    def addCanvasPart(self, part):
        self.__parts.append(part)

    def __getattr__(self, key):
        for part in self.__parts:
            if hasattr(part, key):
                return getattr(part, key)
        return super().__getattr__(key)

    def SaveAsDictionary(self, dictionary):
        self.saveCanvas.emit(dictionary)

    @_saveCanvasDummy
    def LoadFromDictionary(self, dictionary):
        self.loadCanvas.emit(dictionary)


class CanvasPart(QObject):
    def __init__(self, canvas):
        super().__init__()
        self._canvas = weakref.ref(canvas)

    def canvas(self):
        return self._canvas()
