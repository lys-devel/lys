import os
import sys
import traceback
from pathlib import Path


from LysQt.QtWidgets import QMdiArea, QMdiSubWindow, QMessageBox, QSpinBox, QDoubleSpinBox, QCheckBox, QRadioButton, QComboBox, QLineEdit, QListWidget, QTextEdit
from LysQt.QtCore import Qt, pyqtSignal, QPoint
from . import home, load, SettingDict
from .generalWidgets import ScientificSpinBox, ColorSelection, ColormapSelection


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
        self._dicFile = home() + '/.lys/workspace/' + workspace + '/winDict.dic'
        self._windir = home() + '/.lys/workspace/' + workspace + '/wins'

    def update(self):
        dic = {}
        for i, w in enumerate(self._autoWindows()):
            d = {}
            d["FileName"] = w.FileName()
            d["TemporaryFile"] = w.TemporaryFile()
            dic[i] = d
        with open(self._dicFile, 'w') as f:
            f.write(str(dic))

    def _fileNames(self):
        return [w.FileName() for w in self._autoWindows() if w.FileName() is not None]

    def _autoWindows(self):
        return [w for w in self.subWindowList(order=QMdiArea.ActivationHistoryOrder) if isinstance(w, AutoSavedWindow)]

    def addSubWindow(self, window):
        super().addSubWindow(window)
        window.closed.connect(lambda: self.removeSubWindow(window))
        if isinstance(window, AutoSavedWindow):
            if not window.FileName() in self._fileNames():
                window.saved.connect(self.update)
                self.update()

    def removeSubWindow(self, window, store=False):
        if window in self.subWindowList():
            super().removeSubWindow(window)
            if isinstance(window, AutoSavedWindow) and not store:
                if os.path.exists(window.TemporaryFile()):
                    os.remove(window.TemporaryFile())
                self.update()

    @classmethod
    def loadedWindow(cls, path):
        if path is None:
            return None
        for work in cls._main._mdiArea("__all__"):
            for win in work._autoWindows():
                file = win.FileName()
                if win.FileName() is None:
                    continue
                if Path(file) == Path(path).absolute():
                    return win

    def RestoreAllWindows(self):
        # load dict to restore
        os.makedirs(self._windir, exist_ok=True)
        if os.path.exists(self._dicFile):
            with open(self._dicFile, 'r') as f:
                dic = eval(f.read())
        else:
            dic = {}
        # load all windows and disconnect if it is temporary
        i = 0
        while i in dic:
            try:
                w = load(dic[i]["TemporaryFile"], tmpFile=dic[i]["TemporaryFile"])
                w._changeFileName(dic[i]["FileName"])
            except Exception as e:
                print("Load is skipped because of Failure:", e, file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
            i += 1
        self.update()

    def StoreAllWindows(self):
        self.update()
        for win in self._autoWindows():
            self.removeSubWindow(win, store=True)
            win.close(force=True)

    def CloseAllWindows(self):
        for win in self._autoWindows():
            win.close(force=True)

    def tmpFilePath(self, prefix, suffix):
        os.makedirs(self._windir, exist_ok=True)
        used = [w.TemporaryFile() for w in self._autoWindows()]
        for i in range(1000):
            path = self._windir + '/' + prefix + str(i).zfill(3) + suffix
            if path not in used:
                return path
        print('Too many windows.', file=sys.stderr)


class LysSubWindow(QMdiSubWindow):
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
        self._floating = floating
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

    def isFloating(self):
        """Return if the window is out of the mdi window or not"""
        return self._floating


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

    for obj in self.findChildren(QTextEdit):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setPlainText(settings[name])


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

    for obj in self.findChildren(QTextEdit):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.toPlainText()
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

    At the same time, the window is connected to a temporary file in .lys/workspace/. See :meth:`Save` for detail.

    This functionarity is realized by calling :meth:`_save` method, which should be implemented in class that inherit *AutoSavedWindow*

    To gives default file name, the class should also implement :meth:`_prefix` and :meth:`_suffix` methods, in addition to :meth:`save` method.

    """
    saved = pyqtSignal()
    """*saved* signal is emitted when it is saved."""

    def __new__(cls, file=None, warn=True, **kwargs):
        obj = _ExtendMdiArea.loadedWindow(file)
        if obj is not None:
            obj.raise_()
            if obj._mdiArea() == _ExtendMdiArea.current():
                if warn:
                    print(file + " has been loaded in " + obj._mdiArea()._workspace, file=sys.stderr)
                return None
            elif warn:
                msg = QMessageBox(parent=_ExtendMdiArea.current())
                msg.setIcon(QMessageBox.Warning)
                msg.setText(file + " has been loaded in " + obj._mdiArea()._workspace + ". Do you want to move it to current workspace?")
                msg.setWindowTitle("Caution")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                ok = msg.exec_()
                if ok == QMessageBox.Cancel:
                    return None
                else:
                    obj.close(force=True)
                    return super().__new__(cls)
        return super().__new__(cls)

    def __init__(self, file=None, *args, tmpFile=None, **kwargs):
        self.__closeflg = True
        self.__modified = False
        if file is None:
            self.__file = None
        else:
            self.__file = os.path.abspath(file)
        if tmpFile is None:
            self.__tmpFile = _ExtendMdiArea.current().tmpFilePath(self._prefix(), self._suffix())
        else:
            self.__tmpFile = tmpFile
        super().__init__()
        self.setWindowTitle(self.Name())

    def _changeFileName(self, file):
        self.__file = file
        self.setWindowTitle(self.Name())

    def _mdiArea(self):
        parent = self
        while not isinstance(parent, _ExtendMdiArea):
            parent = parent.parent()
        return parent

    def Save(self, file=None, temporary=False):
        """
        Save the content of the window.

        If *file* is given, the content of the window is saved via _save method.

        If *file* is not given, it is saved in the last-saved file if it exists.

        If *temporary* is True, it is saved in the temporary file in .lys/workspace/ automatically.

        Args:
            file(str): the file to be saved.
        """
        if temporary:
            os.makedirs(os.path.dirname(self.__tmpFile), exist_ok=True)
            self._save(self.__tmpFile)
            self.__modified = True
        else:
            if file is not None:
                self.__file = os.path.abspath(file)
                os.makedirs(os.path.dirname(self.__file), exist_ok=True)
            self._save(self.__file)
            self.saved.emit()
            self.__modified = False
        self.setWindowTitle(self.Name())

    def close(self, force=False):
        """Reimplementation of close in QMdiSubWindow"""
        self.__closeflg = not force
        super().close()

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
        if self.__closeflg:
            msg = QMessageBox(parent=_ExtendMdiArea.current())
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Caution")
            if self.__file is None:
                msg.setText("This window is not saved. Do you really want to close it?")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            else:
                msg.setText("Do you want to save the content of this window to " + self.__file + "?")
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            ok = msg.exec_()
            if ok == QMessageBox.Cancel:
                return event.ignore()
            if ok == QMessageBox.Yes:
                self.Save()
        return super().closeEvent(event)

    def FileName(self):
        """Return filename that saves content of the window"""
        return self.__file

    def TemporaryFile(self):
        """Return temporary filename that hold content of the window"""
        return self.__tmpFile

    def Name(self):
        """Return name of the window, which is automatically determined by filename."""
        if self.__file is not None:
            p = Path(self.FileName())
            p = p.relative_to(home())
            name = str(p)
            if self.__modified:
                name += "*"
            return name
        else:
            file = self.TemporaryFile()
            return os.path.basename(file) + " (temporary)"

    def _save(self, file):
        raise NotImplementedError

    def _prefix(self):
        pass

    def _suffix(self):
        pass
