import functools
import weakref
import logging
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def saveCanvas(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].saveflg:
            res = func(*args, **kwargs)
        else:
            args[0].saveflg = True
            res = func(*args, **kwargs)
            args[0].Save()
            args[0].draw()
            args[0].saveflg = False
        return res
    return wrapper


def notSaveCanvas(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        saved = args[0].saveflg
        args[0].saveflg = True
        res = func(*args, **kwargs)
        args[0].saveflg = saved
        return res
    return wrapper


class BasicEventCanvasBase(object):
    deleted = pyqtSignal(object)

    def emitCloseEvent(self):
        self.deleted.emit(self)


class SavableCanvasBase(BasicEventCanvasBase):
    def __init__(self, *args, **kwargs):
        self.saveflg = False
        self.savef = None

    def setSaveFunction(self, func):
        self.savef = weakref.WeakMethod(func)

    def Save(self):
        if self.savef is not None:
            self.savef()()

    def EnableSave(self, b):
        self.saveflg = b

    def SaveAsDictionary(self, dictionary, path):
        pass

    def LoadFromDictionary(self, dictionary, path):
        pass

    def saveAppearance(self):
        pass

    def loadAppearance(self):
        pass


class DrawableCanvasBase(SavableCanvasBase):
    afterDraw = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drawflg = None

    def IsDrawEnabled(self):
        return self.drawflg

    def EnableDraw(self, b):
        self.drawflg = b

    def draw(self):
        if self.drawflg is not None:
            if not self.drawflg:
                return
        try:
            self._draw()
            afterDraw.emit()
        except Exception:
            pass

    def _draw(self):
        pass

    def addAfterDrawListener(self, listener):
        print("use afterDraw.connect")
        raise NotImplementedError()
