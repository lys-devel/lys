import os
import logging
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from . import SettingDict
from . import home
from .core import _produceWave

produce = _produceWave
"""only for backward compability"""


def globalSetting():
    return SettingDict(home() + "/.lys/settings/global.dic")


class ExtendMdiSubWindowBase(QMdiSubWindow):
    pass


class SizeAdjustableWindow(ExtendMdiSubWindowBase):
    def __init__(self):
        super().__init__()
        # Mode #0 : Auto, 1 : heightForWidth, 2 : widthForHeight
        self.__mode = 0
        self.__aspect = 0
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

    def _attach(self, parent):
        self._parent = parent
        if isinstance(parent, ExtendMdiSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)

    def closeEvent(self, event):
        if self._parent is not None:
            self._parent.moved.disconnect(self.attachTo)
            self._parent.resized.disconnect(self.attachTo)
            self._parent.closed.disconnect(self.close)
        self.closed.emit(self)
        return super().closeEvent(event)

    def attachTo(self):
        if self._parent is not None:
            pos = self._parent.pos()
            frm = self._parent.frameGeometry()
            self.move(QPoint(pos.x() + frm.width(), pos.y()))


class ExtendMdiSubWindow(AttachableWindow):
    mdimain = None
    __wins = []

    def __init__(self, title=None, floating=False):
        logging.debug('[ExtendMdiSubWindow] __init__')
        super().__init__()
        self.__floating = floating
        ExtendMdiSubWindow._AddWindow(self, floating)
        self.setAttribute(Qt.WA_DeleteOnClose)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()

    @classmethod
    def CloseAllWindows(cls):
        for g in cls.__wins:
            g.close()

    @classmethod
    def _AddWindow(cls, win, floating):
        cls.__wins.append(win)
        if cls.mdimain is not None and not floating:
            cls.mdimain.addSubWindow(win)

    @classmethod
    def _RemoveWindow(cls, win, floating):
        cls.__wins.remove(win)
        if not floating:
            cls.mdimain.removeSubWindow(win)

    @classmethod
    def _Contains(cls, win):
        return win in cls.__wins

    @classmethod
    def AllWindows(cls):
        return cls.__wins

    def closeEvent(self, event):
        ExtendMdiSubWindow._RemoveWindow(self, self.__floating)
        super().closeEvent(event)

    def isFloating(self):
        return self.__floating


class AutoSavedWindow(ExtendMdiSubWindow):
    __list = None
    _isclosed = False
    _restore = False
    folder_prefix = home() + '/.lys/workspace/'

    @classmethod
    def _saveWinList(cls):
        file = home() + '/.lys/workspace/' + AutoSavedWindow._workspace + '/winlist.lst'
        with open(file, 'w') as f:
            f.write(str(cls.__list))

    @classmethod
    def _loadWinList(cls):
        file = home() + '/.lys/workspace/' + AutoSavedWindow._workspace + '/winlist.lst'
        with open(file, 'r') as f:
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
    def SwitchTo(cls, workspace='default'):
        if workspace == "":
            workspace = "default"
        cls.StoreAllWindows()
        cls.RestoreAllWindows(workspace)

    @classmethod
    def RestoreAllWindows(cls, workspace='default'):
        from . import load
        AutoSavedWindow._workspace = workspace
        cls.__list = cls._loadWinList()
        AutoSavedWindow._windir = home() + '/.lys/workspace/' + AutoSavedWindow._workspace + '/wins'
        print("Workspace: " + AutoSavedWindow._workspace)
        cls._restore = True
        os.makedirs(AutoSavedWindow._windir, exist_ok=True)
        for path in cls.__list:
            try:
                w = load(path)
                if path.find(AutoSavedWindow._windir) > -1:
                    w.Disconnect()
            except:
                pass
        cls._restore = False

    @classmethod
    def StoreAllWindows(cls):
        cls._isclosed = True
        list = cls.mdimain.subWindowList(order=QMdiArea.ActivationHistoryOrder)
        for l in reversed(list):
            if isinstance(l, AutoSavedWindow):
                l.close(force=True)
        cls._isclosed = False

    @classmethod
    def _IsClosed(cls):
        return cls._isclosed

    def _onRestore(cls):
        return cls._restore

    def NewTmpFilePath(self):
        os.makedirs(AutoSavedWindow._windir, exist_ok=True)
        for i in range(1000):
            path = AutoSavedWindow._windir + '/' + self._prefix() + str(i).zfill(3) + \
                self._suffix()
            if not AutoSavedWindow._IsUsed(path):
                return path
        print('Too many windows.')

    def __new__(cls, file=None, title=None, **kwargs):
        logging.debug('[AutoSavedWindow] __new__ called.')
        if cls._restore:
            return super().__new__(cls)
        if AutoSavedWindow._IsUsed(file):
            logging.debug('[AutoSavedWindow] found loaded window.', file)
            return None
        return super().__new__(cls)

    def __init__(self, file=None, title=None, **kwargs):
        logging.debug('[AutoSavedWindow] __init__ called.')
        try:
            self.__file
        except Exception:
            logging.debug('[AutoSavedWindow] new window will be created.')
            self.__closeflg = True
            if file is None:
                logging.debug(
                    '[AutoSavedWindow] file is None. New temporary window is created.')
                self.__isTmp = True
                self.__file = self.NewTmpFilePath()
            else:
                logging.debug('[AutoSavedWindow] file is ' + file + '.')
                self.__isTmp = False
                self.__file = file
            if title is not None:
                super().__init__(title)
            else:
                super().__init__(self.Name())
            if file is not None:
                self.__file = os.path.abspath(file)
            if os.path.exists(self.__file) and not self.__isTmp:
                self._init(self.__file, **kwargs)
            else:
                self._init(**kwargs)
            AutoSavedWindow._AddAutoWindow(self)

    def setLoadFile(self, file):
        self.__loadFile = os.path.abspath(file)

    def FileName(self):
        return self.__file

    def Name(self):
        nam, ext = os.path.splitext(os.path.basename(self.FileName()))
        return nam

    def IsConnected(self):
        return not self.__isTmp

    def Disconnect(self):
        self.__isTmp = True

    def Save(self, file=None):
        logging.debug('[AutoSavedWindow] Saved')
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
        if force:
            self.__closeflg = False
        else:
            self.__closeflg = True
        super().close()

    def closeEvent(self, event):
        if (not AutoSavedWindow._IsClosed()) and (not self.IsConnected()) and self.__closeflg:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok == QMessageBox.Cancel:
                event.ignore()
                return
        self.Save()
        if not AutoSavedWindow._IsClosed():
            AutoSavedWindow._RemoveAutoWindow(self)
        return super().closeEvent(event)
