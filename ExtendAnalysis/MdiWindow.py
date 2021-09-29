import os
import sys
import traceback

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from . import home, load


class LysMdiArea(QMdiArea):
    _main = None

    @classmethod
    def current(cls):
        return cls._main._mdiArea()

    def __init__(self, parent, workspace="default"):
        super().__init__()
        LysMdiArea._main = parent
        self._workspace = workspace
        self.__list = []
        self._folder = home() + '/.lys/workspace/' + workspace + '/winlist.lst'
        self._windir = home() + '/.lys/workspace/' + workspace + '/wins'

    def _fileNames(self):
        return [w.FileName() for w in self.__list]

    def _saveWinList(self):
        with open(self._folder, 'w') as f:
            f.write(str(self._fileNames()))

    def _AddAutoWindow(self, win):
        if not win.FileName() in self._fileNames():
            self.__list.append(win)
            win.saved.connect(self._saveWinList)
            win.closed.connect(lambda: self._RemoveAutoWindow(win))
        self._saveWinList()

    def _RemoveAutoWindow(self, win):
        if win in self.__list:
            self.__list.remove(win)
            if not win._IsConnected() and os.path.exists(win.FileName()):
                os.remove(win.FileName())
            self._saveWinList()

    def CloseAllWindows(self):
        for win in self.__list:
            self.__list.remove(win)
            win.close(force=True)
            self._saveWinList()

    def addSubWindow(self, window):
        super().addSubWindow(window)
        window.closed.connect(lambda: self.removeSubWindow(window))
        if isinstance(window, AutoSavedWindow):
            self._AddAutoWindow(window)

    def loadedWindow(self, path):
        for win in self.__list:
            if win.FileName() == path:
                return win

    def RestoreAllWindows(self):
        # load windos paths to restore
        os.makedirs(self._windir, exist_ok=True)
        if os.path.exists(self._folder):
            with open(self._folder, 'r') as f:
                names = eval(f.read())
        else:
            names = []
        # load all windows and disconnect if it is temporary
        self.__list = []
        for path in names:
            try:
                w = load(path)
                if path.find(self._windir) > -1:
                    w._Disconnect()
            except Exception as e:
                print("Load is skipped because of Failure:", e, file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)

    def StoreAllWindows(self):
        wins = list(self.__list)
        self.__list.clear()
        for win in reversed(wins):
            win.close(force=True)

    def tmpFilePath(self, prefix, suffix):
        os.makedirs(self._windir, exist_ok=True)
        for i in range(1000):
            path = self._windir + '/' + prefix + str(i).zfill(3) + suffix
            if self.loadedWindow(path) is None:
                return path
        print('Too many windows.', file=sys.stderr)


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


class ExtendMdiSubWindow(SizeAdjustableWindow):
    __win = []

    resized = pyqtSignal()
    moved = pyqtSignal()
    closed = pyqtSignal(object)

    def __init__(self, title=None, floating=False):
        from . import plugin
        super().__init__()
        self._parent = None
        if floating:
            ExtendMdiSubWindow.__win.append(self)
            plugin.mainWindow().closed.connect(self.close)
        else:
            LysMdiArea.current().addSubWindow(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        if title is not None:
            self.setWindowTitle(title)
        self.updateGeometry()
        self.show()

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


class AutoSavedWindow(ExtendMdiSubWindow):
    saved = pyqtSignal()

    def __new__(cls, file=None, title=None, **kwargs):
        obj = LysMdiArea.current().loadedWindow(file)
        if obj is not None:
            return obj
        return super().__new__(cls)

    def __init__(self, file=None, title=None, **kwargs):
        self.__closeflg = True
        self.__isTmp = file is None
        if self.__isTmp:
            self.__file = LysMdiArea.current().tmpFilePath(self._prefix(), self._suffix())
        else:
            self.__file = os.path.abspath(file)
        if title is not None:
            super().__init__(title)
        else:
            super().__init__(self.Name())

    def _IsConnected(self):
        return not self.__isTmp

    def _Disconnect(self):
        self.__isTmp = True

    def Save(self, file=None):
        if file is not None:
            self.__file = os.path.abspath(file)
            os.makedirs(os.path.dirname(self.__file), exist_ok=True)
            self._save(self.__file)
            self.__isTmp = False
            title = os.path.basename(file)
            self.setWindowTitle(title)
        else:
            self._save(self.__file)
        self.saved.emit()

    def close(self, force=False):
        self.__closeflg = not force
        super().close()

    def closeEvent(self, event):
        if self.__isTmp and self.__closeflg:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("This window is not saved. Do you really want to close it?")
            msg.setWindowTitle("Caution")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok == QMessageBox.Cancel:
                event.ignore()
                return
        return super().closeEvent(event)

    def FileName(self):
        return self.__file

    def Name(self):
        nam, ext = os.path.splitext(os.path.basename(self.FileName()))
        return nam

    def _save(self, file):
        raise NotImplementedError

    def _prefix(self):
        raise NotImplementedError

    def _suffix(self):
        raise NotImplementedError
