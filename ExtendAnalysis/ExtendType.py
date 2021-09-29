import os
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from . import home
from .core import _produceWave

produce = _produceWave
"""only for backward compability. DO NOT DELETE!"""


class SizeAdjustableWindow(QMdiSubWindow):
    def __init__(self):
        super().__init__()
        # Mode #0 : Auto, 1 : heightForWidth, 2 : widthForHeight
        self.__mode = 0
        self.setWidth(0)
        self.setHeight(0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def setWidth(self, val):
        if self.__mode == 2:
            self.__mode = 0
        if val == 0:
            self.setMinimumWidth(35)
            self.setMaximumWidth(100000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)

    def setHeight(self, val):
        if self.__mode == 1:
            self.__mode = 0
        if val == 0:
            self.setMinimumHeight(35)
            self.setMaximumHeight(100000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)


class AttachableWindow(SizeAdjustableWindow):
    resized = pyqtSignal()
    moved = pyqtSignal()
    closed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._parent = None

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def moveEvent(self, event):
        self.moved.emit()
        return super().moveEvent(event)

    def closeEvent(self, event):
        if self._parent is not None:
            self._parent.moved.disconnect(self.attachTo)
            self._parent.resized.disconnect(self.attachTo)
            self._parent.closed.disconnect(self.close)
        self.closed.emit(self)
        return super().closeEvent(event)

    def _attach(self, parent):
        self._parent = parent
        if isinstance(parent, ExtendMdiSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)

    def attachTo(self):
        if self._parent is not None:
            pos = self._parent.pos()
            frm = self._parent.frameGeometry()
            self.move(QPoint(pos.x() + frm.width(), pos.y()))


class ExtendMdiSubWindow(AttachableWindow):
    main = None
    __win = []

    def __init__(self, title=None, floating=False):
        super().__init__()
        if floating:
            ExtendMdiSubWindow.__win.append(self)
            ExtendMdiSubWindow.main.closed.connect(self.close)
        else:
            ExtendMdiSubWindow.main.addSubWindow(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()


class AutoSavedWindow(ExtendMdiSubWindow):
    __list = None
    _isclosed = False
    _restore = False
    _folder = home() + '/.lys/workspace/default/winlist.lst'
    _windir = home() + '/.lys/workspace/default/wins'

    @classmethod
    def _saveWinList(cls):
        with open(cls._folder, 'w') as f:
            f.write(str(cls.__list))

    @classmethod
    def _loadWinList(cls):
        with open(cls._folder, 'r') as f:
            data = eval(f.read())
        return data

    @classmethod
    def _IsUsed(cls, path):
        return path in cls.__list

    @classmethod
    def _AddAutoWindow(cls, win):
        if not win.FileName() in cls.__list:
            cls.__list.append(win.FileName())
        cls._saveWinList()

    @classmethod
    def _RemoveAutoWindow(cls, win):
        if win.FileName() in cls.__list:
            cls.__list.remove(win.FileName())
            if not win.IsConnected():
                os.remove(win.FileName())
        cls._saveWinList()

    @classmethod
    def RestoreAllWindows(cls):
        from . import load
        cls.__list = cls._loadWinList()
        cls._restore = True
        os.makedirs(AutoSavedWindow._windir, exist_ok=True)
        for path in cls.__list:
            try:
                w = load(path)
                if path.find(AutoSavedWindow._windir) > -1:
                    w._Disconnect()
            except:
                pass
        cls._restore = False

    @classmethod
    def StoreAllWindows(cls):
        cls._isclosed = True
        list = cls.main.area.subWindowList(order=QMdiArea.ActivationHistoryOrder)
        for l in reversed(list):
            if isinstance(l, AutoSavedWindow):
                l.close(force=True)
        cls._isclosed = False

    def __new__(cls, file=None, title=None, **kwargs):
        if cls._restore:
            return super().__new__(cls)
        if AutoSavedWindow._IsUsed(file):
            return None
        return super().__new__(cls)

    def __init__(self, file=None, title=None, **kwargs):
        try:
            self.__file
        except Exception:
            self.__closeflg = True
            self.__isTmp = file is None
            if self.__isTmp:
                self.__file = self._NewTmpFilePath()
            else:
                self.__file = os.path.abspath(file)
            if title is not None:
                super().__init__(title)
            else:
                super().__init__(self.Name())
            if os.path.exists(self.__file) and not self.__isTmp:
                self._init(self.__file, **kwargs)
            else:
                self._init(**kwargs)
            AutoSavedWindow._AddAutoWindow(self)

    def _NewTmpFilePath(self):
        os.makedirs(AutoSavedWindow._windir, exist_ok=True)
        for i in range(1000):
            path = AutoSavedWindow._windir + '/' + self._prefix() + str(i).zfill(3) + self._suffix()
            if not AutoSavedWindow._IsUsed(path):
                return path
        print('Too many windows.')

    def FileName(self):
        return self.__file

    def Name(self):
        nam, ext = os.path.splitext(os.path.basename(self.FileName()))
        return nam

    def IsConnected(self):
        return not self.__isTmp

    def _Disconnect(self):
        self.__isTmp = True

    def Save(self, file=None):
        if file is not None:
            AutoSavedWindow._RemoveAutoWindow(self)
            self.__file = os.path.abspath(file)
            os.makedirs(os.path.dirname(self.__file), exist_ok=True)
            self._save(self.__file)
            self.__isTmp = False
            title = os.path.basename(file)
            self.setWindowTitle(title)
            AutoSavedWindow._AddAutoWindow(self)
        else:
            self._save(self.__file)

    def close(self, force=False):
        self.__closeflg = not force
        super().close()

    def closeEvent(self, event):
        if (not self.IsConnected()) and self.__closeflg:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok == QMessageBox.Cancel:
                event.ignore()
                return
        self.Save()
        if not AutoSavedWindow._isClosed:
            AutoSavedWindow._RemoveAutoWindow(self)
        return super().closeEvent(event)
