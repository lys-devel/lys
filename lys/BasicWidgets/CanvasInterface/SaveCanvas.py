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
        if canvas.saveflg:
            res = func(*args, **kwargs)
        else:
            canvas.saveflg = True
            res = func(*args, **kwargs)
            canvas.Save()
            canvas.drawCanvas()
            canvas.updated.emit()
            canvas.saveflg = False
        return res
    return wrapper


def notSaveCanvas(func):
    @ functools.wraps(func)
    def wrapper(*args, **kwargs):
        if isinstance(args[0], CanvasPart):
            canvas = args[0]._canvas
        else:
            canvas = args[0]
        saved = canvas.saveflg
        canvas.saveflg = True
        res = func(*args, **kwargs)
        canvas.saveflg = saved
        return res
    return wrapper


class CanvasPart(QObject):
    def __init__(self, canvas):
        super().__init__()
        self._canvas = weakref.ref(canvas)

    def canvas(self):
        return self._canvas()


class SavableCanvasBase(object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.saveflg = False
        self.savef = None

    def setSaveFunction(self, func):
        self.savef = weakref.WeakMethod(func)

    def Save(self):
        if self.savef is not None:
            self.savef()()


_saveCanvasDummy = saveCanvas


class AbstractCanvasBase(SavableCanvasBase):
    saveCanvas = pyqtSignal(dict)
    loadCanvas = pyqtSignal(dict)
    initCanvas = pyqtSignal()
    updated = pyqtSignal()

    def SaveAsDictionary(self, dictionary):
        self.saveCanvas.emit(dictionary)

    @_saveCanvasDummy
    def LoadFromDictionary(self, dictionary):
        self.loadCanvas.emit(dictionary)

    def drawCanvas(self):
        self._draw()

    def _draw(self):
        pass
