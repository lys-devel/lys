import os
import sys
import traceback
import math
from pathlib import Path

import numpy as np

from LysQt.QtWidgets import QMdiArea, QMdiSubWindow, QSizePolicy, QMessageBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton, QComboBox, QLineEdit, QListWidget
from LysQt.QtCore import Qt, pyqtSignal, QPoint
from LysQt.QtGui import QValidator
from . import home, load, SettingDict


class _ExtendMdiArea(QMdiArea):
    """
    MdiArea that manage AutoSavedWindows.
    """
    _main = None

    @classmethod
    def current(cls):
        return cls._main._mdiArea()

    def __init__(self, parent, workspace="default"):
        super().__init__()
        _ExtendMdiArea._main = parent
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
        if path is None:
            return None
        for win in self.__list:
            if Path(win.FileName()) == Path(path).absolute():
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


class LysSubWindow(SizeAdjustableWindow):
    """
    LysSubWindow is customized QMdiSubWindow, which implement some usuful methods and signals.

    When a *AutoSavedWindow* is instantiated, it is automatically added to current MdiArea.

    It is recommended to inherit this class when developers implement new sub windows in lys.

    User input on several QWidgets can be saved and restored from file. See :meth:`saveSettings` and :meth:`restoreSettings` for detail.

    LysSubWindow can be attached to different LysSubWindow. See :meth:`attach` for detail. 

    Args:
        floating(bool): Whether the window in in the current mdi area, or floating out side the medi area.
    """
    __win = []

    resized = pyqtSignal()
    """
    *resized* signal is emitted when the window is resized.
    """
    moved = pyqtSignal()
    """
    *moved* signal is emitted when the window is moved.
    """
    closed = pyqtSignal(object)
    """
    *closed* signal is emitted when the window is closed.
    """

    def __init__(self, floating=False):
        from . import glb
        super().__init__()
        self._parent = None
        if floating:
            LysSubWindow.__win.append(self)
            glb.mainWindow().closed.connect(self.close)
        else:
            _ExtendMdiArea.current().addSubWindow(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.updateGeometry()
        self.show()

    def resizeEvent(self, event):
        """Reimplementation of resizeEvent in QMdiSubWindow"""
        self.resized.emit()
        return super().resizeEvent(event)

    def moveEvent(self, event):
        """Reimplementation of moveEvent in QMdiSubWindow"""
        self.moved.emit()
        return super().moveEvent(event)

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
        if self._parent is not None:
            self._parent.moved.disconnect(self.attachTo)
            self._parent.resized.disconnect(self.attachTo)
            self._parent.closed.disconnect(self.close)
        self.closed.emit(self)
        return super().closeEvent(event)

    def attach(self, parent):
        """
        Attach *self* to *parent*

        After it is attached, the window follows the *parent* widget automatically.

        This functionarity is usually used for several setting widgets (such as ModifyWindow of Graph), which should follow the parent (such as Graph) 
        """
        self._parent = parent
        if isinstance(parent, LysSubWindow):
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)

    def attachTo(self):
        """
        Attach *self* to pre-registered parent by :meth:`attach`.

        When the parent window is move programatically by :func:`move`, the window does not follow.

        Developers should call this method to intentionally attach it to parent.
        """
        if self._parent is not None:
            pos = self._parent.pos()
            frm = self._parent.frameGeometry()
            self.move(QPoint(pos.x() + frm.width(), pos.y()))

    def saveSettings(self, file):
        """
        Export all widgets settings from default setting file specified by name.
        User input on various widgets are easily loaded from file by :meth:`restoreSettings`.
        """
        _save(self, file)

    def restoreSettings(self, file):
        """
        Import all widgets settings from default setting file specified by name.
        User input on various widgets are easily exported to file by :meth:`saveSettings`.
        """
        return _restore(self, file)


def _restore(self, file):
    settings = SettingDict(file)

    for obj in self.findChildren(QSpinBox) + self.findChildren(QDoubleSpinBox):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setValue(settings[name])

    for obj in self.findChildren(QCheckBox) + self.findChildren(QRadioButton):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setChecked(settings[name])

    for obj in self.findChildren(QComboBox):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                i = obj.findText(settings[name])
                if i != -1:
                    obj.setCurrentIndex(i)

    for obj in self.findChildren(QLineEdit):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setText(settings[name])

    for obj in self.findChildren(QListWidget):
        name = obj.objectName()
        if _checkName(name):
            obj.clear()
            if name in settings:
                obj.addItems(settings[name])


def _save(self, file):
    settings = SettingDict(file)

    for obj in self.findChildren(QSpinBox) + self.findChildren(QDoubleSpinBox):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.value()

    for obj in self.findChildren(QCheckBox) + self.findChildren(QRadioButton):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.isChecked()

    for obj in self.findChildren(QComboBox):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.currentText()

    for obj in self.findChildren(QLineEdit):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.text()

    for obj in self.findChildren(QListWidget):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = [obj.item(i).text() for i in range(obj.count())]
    return settings


def _checkName(name):
    if name == "":
        return False
    elif name.startswith("qt_"):
        return False
    else:
        return True


class AutoSavedWindow(LysSubWindow):
    """
    This is a base widget class for auto save feature, which is mainly used for Graph class.

    When a *AutoSavedWindow* is instantiated, it is automatically added to current MdiArea.

    At the same time, the window is connected to a temporary file in .lys/workspace/

    When :meth:`Save` is called without *file* argument, data is automatically saved in the temprary file.

    This functionarity is realized by calling :meth:`_save` method, which should be implemented in class that inherit *AutoSavedWindow*

    To gives default file name, the class should also implement :meth:`_prefix` and :meth:`_suffix` methods, in addition to :meth:`save` method.

    Note:
        Functionarity of *AutoSavedWindow* is basically not preffered in usual program.

        However, since users can execute any commands in lys Python Interface, sometimes lys crashes.

        In such case, *AutoSavedWindow* is useful because the edited files (mainly Graph) have been automatically saved in temporary files.

        Even if users kill lys by [kill] command in linux (This is usually caused by infinite loop in program), the edited graphs maintain by this functionarity.
    """
    saved = pyqtSignal()
    """*saved* signal is emitted when it is saved."""

    def __new__(cls, file=None, title=None, **kwargs):
        obj = _ExtendMdiArea.current().loadedWindow(file)
        if obj is not None:
            return obj
        return super().__new__(cls)

    def __init__(self, file=None, **kwargs):
        self.__closeflg = True
        self.__isTmp = file is None
        if self.__isTmp:
            self.__file = _ExtendMdiArea.current().tmpFilePath(self._prefix(), self._suffix())
        else:
            self.__file = os.path.abspath(file)
        super().__init__()
        self.setWindowTitle(self.Name())

    def _IsConnected(self):
        return not self.__isTmp

    def _Disconnect(self):
        self.__isTmp = True

    def Save(self, file=None):
        """
        Save the content of the window.

        If *file* is given, the content of the window is saved via _save method.

        If *file* is not given, it is saved in the last-saved file if it exists.
        If the file has not been saved, it is saved in the temporary file in .lys/workspace/ automatically.

        Args:
            file(str): the file to be saved.
        """
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
        """Reimplementation of close in QMdiSubWindow"""
        self.__closeflg = not force
        super().close()

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
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
        """Return filename that saves content of the window"""
        return self.__file

    def Name(self):
        """Return name of the window, which is automatically determined by filename."""
        return os.path.basename(self.FileName())

    def _save(self, file):
        raise NotImplementedError

    def _prefix(self):
        raise NotImplementedError

    def _suffix(self):
        raise NotImplementedError


class ScientificSpinBox(QDoubleSpinBox):
    """
    Spin box that displays values in sdientific notation, which is frequently used in lys.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRange(-np.inf, np.inf)
        self.setDecimals(128)
        self.setAccelerated(True)

    def textFromValue(self, value):
        """textFromValue"""
        return "{:.6g}".format(value)

    def valueFromText(self, text):
        """Reimplementation of valueFromText"""
        return float(text)

    def validate(self, text, pos):
        """Reimplementation of validate"""
        try:
            float(text)
        except Exception:
            try:
                float(text.replace("e", "").replace("-", ""))
            except Exception:
                return (QValidator.Invalid, text, pos)
            else:
                return (QValidator.Intermediate, text, pos)
        else:
            return (QValidator.Acceptable, text, pos)

    def stepBy(self, steps):
        """stepBy"""
        v = self.value()
        if v == 0:
            n = 1
        else:
            val = np.log10(abs(v))
            p = math.floor(val)
            if math.floor(abs(v) / (10**p)) == 1:  # and np.sign(steps) != np.sign(v):
                p = p - 1
            n = 10 ** p
        self.setValue(v + steps * n)