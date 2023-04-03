import os
import sys
import traceback
import shutil
from pathlib import Path

from lys import home, load, lysPath
from lys.Qt import QtCore, QtWidgets, QtGui
from lys.decorators import avoidCircularReference


class _MdiAreaBase(QtWidgets.QMdiArea):
    """MDI window that handle LysSubWindow"""
    _main = None
    updated = QtCore.pyqtSignal()
    """Emitted when the contents of the workspace is sotred in file."""

    @classmethod
    def current(cls):
        return cls._main._mdiArea()

    def __init__(self, parent, workspace="default"):
        super().__init__()
        _ExtendMdiArea._main = parent
        self._workspace = workspace
        self._name = workspace
        self._dicFile = home() + '/.lys/workspace/' + workspace + '/winDict.dic'
        self.updated.connect(self._update)

    def setName(self, name):
        self._name = name
        self.updated.emit()

    def getName(self):
        return self._name

    def addSubWindow(self, window):
        super().addSubWindow(window)
        window.closed.connect(lambda: self.removeSubWindow(window))

    def removeSubWindow(self, window):
        if window in self.subWindowList():
            super().removeSubWindow(window)

    def storeWorkspace(self):
        self.updated.emit()
        self.updated.disconnect(self._update)

    def restoreWorkspace(self):
        # load dict to restore
        os.makedirs(self._windir, exist_ok=True)
        if os.path.exists(self._dicFile):
            with open(self._dicFile, 'r') as f:
                dic = eval(f.read())
        else:
            dic = {}
        self._restore(dic)
        self.updated.emit()

    def _restore(self, dic):
        self._name = dic.get("Name", self._workspace)

    def _update(self):
        dic = self._saveAsDict()
        with open(self._dicFile, 'w') as f:
            f.write(str(dic))

    def _saveAsDict(self):
        return {"Name": self._name}


class _MdiAreaTemp(_MdiAreaBase):
    """MdiArea that manage AutoSavedWindows."""

    def __init__(self, parent, workspace="default"):
        super().__init__(parent, workspace)
        self._windir = home() + '/.lys/workspace/' + workspace + '/wins'

    def _autoWindows(self):
        return [w for w in self.subWindowList(order=QtWidgets.QMdiArea.ActivationHistoryOrder) if isinstance(w, _AutoSavedWindow)]

    def _saveAsDict(self):
        dic = super()._saveAsDict()
        for i, w in enumerate(self._autoWindows()):
            dic[i] = self._windowDict(w)
        return dic

    def _restore(self, dic):
        super()._restore(dic)
        i = 0
        while i in dic:
            try:
                self._restoreWindow(dic[i])
            except Exception as e:
                print("Load is skipped because of Failure (The file is temporary saved in ./backup):", e, file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
                os.makedirs("backup", exist_ok=True)
                shutil.copy2(dic[i]["TemporaryFile"], "backup/")
            i += 1

    def _windowDict(self, w):
        return {"TemporaryFile": lysPath(w.TemporaryFile())}

    def _restoreWindow(self, d):
        return load(d["TemporaryFile"], tmpFile=d["TemporaryFile"])

    def removeSubWindow(self, window):
        super().removeSubWindow(window)
        if isinstance(window, _AutoSavedWindow):
            self.updated.emit()

    def tmpFilePath(self, prefix, suffix):
        os.makedirs(self._windir, exist_ok=True)
        used = [w.TemporaryFile() for w in self._autoWindows()]
        for i in range(1000):
            path = self._windir + '/' + prefix + str(i).zfill(3) + suffix
            if path not in used:
                return path
        print('Too many windows.', file=sys.stderr)

    def closeAllWindows(self):
        for win in self._autoWindows():
            win.close(force=True)

    def storeWorkspace(self):
        super().storeWorkspace()
        for win in self._autoWindows():
            win.close(force=True, store=True)


class _ExtendMdiArea(_MdiAreaTemp):
    """
    MdiArea that manage AutoSavedWindows.
    """

    def _conservableWindows(self):
        return [w for w in self.subWindowList(order=QtWidgets.QMdiArea.ActivationHistoryOrder) if isinstance(w, _ConservableWindow)]

    def addSubWindow(self, window):
        super().addSubWindow(window)
        if isinstance(window, _ConservableWindow):
            if window.FileName() not in [w.FileName() for w in self._conservableWindows() if w.FileName() is not None]:
                window.fileChanged.connect(self.updated)
                self.updated.emit()

    def _windowDict(self, w):
        d = super()._windowDict(w)
        if isinstance(w, _ConservableWindow):
            if w.FileName() is None:
                file = None
            else:
                file = lysPath(w.FileName())
            d["FileName"] = file
        return d

    def _restoreWindow(self, d):
        w = super()._restoreWindow(d)
        if isinstance(w, _ConservableWindow):
            w._changeFileName(d["FileName"])
            w.fileChanged.connect(self.updated)


class _TitleProxyStyle(QtWidgets.QProxyStyle):
    def drawComplexControl(self, control, option, painter, widget=None):
        if control == QtWidgets.QStyle.CC_TitleBar:
            if hasattr(widget, "titleColor"):
                color = widget.titleColor
                if color.isValid():
                    option.palette.setBrush(QtGui.QPalette.Highlight, QtGui.QColor(color))
                    bg = QtGui.QColor(color)
                    bg.setAlpha(128)
                    option.palette.setBrush(QtGui.QPalette.Window, QtGui.QColor(bg))
                    pixmap = QtGui.QPixmap(512, 512)
                    pixmap.fill(QtGui.QColor("transparent"))
                    option.icon = QtGui.QIcon(pixmap)
        return super().drawComplexControl(control, option, painter, widget)


class LysSubWindow(QtWidgets.QMdiSubWindow):
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

    resized = QtCore.pyqtSignal()
    """
    *resized* signal is emitted when the window is resized.
    """
    resizeFinished = QtCore.pyqtSignal()
    """
    *resizedFinished* signal is emitted when the resize of the window is finished.
    """
    moved = QtCore.pyqtSignal()
    """
    *moved* signal is emitted when the window is moved.
    """
    moveFinished = QtCore.pyqtSignal()
    """
    *moveFinished* signal is emitted when the move of the window is finished.
    """
    focused = QtCore.pyqtSignal()
    """
    *focused* signal is emitted when the window is focused.
    """
    closed = QtCore.pyqtSignal(object)
    """
    *closed* signal is emitted when the window is closed.
    """
    saved = QtCore.pyqtSignal(dict)
    """
    *saved* signal is emitted when the saveSettings method is called.
    User settings can be stored in dictionary.
    """
    loaded = QtCore.pyqtSignal(dict)
    """
    *loaded* signal is emitted when the loadSettings method is called.
    User settings can be restored from dictionary.
    """

    def __init__(self, floating=False):
        from lys import glb
        super().__init__()
        self._parent = None
        self._floating = floating
        self._titleColor = QtGui.QColor()
        self.setStyle(_TitleProxyStyle())
        self.installEventFilter(self)
        self._resizeTimer = QtCore.QTimer(self)
        self._resizeTimer.timeout.connect(self.resizeFinished)
        self._resizeTimer.setSingleShot(True)
        self._moveTimer = QtCore.QTimer(self)
        self._moveTimer.timeout.connect(self.resizeFinished)
        self._moveTimer.setSingleShot(True)
        if floating:
            LysSubWindow.__win.append(self)
            glb.mainWindow().closed.connect(self.close)
        else:
            _ExtendMdiArea.current().addSubWindow(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.updateGeometry()
        self.show()

    @property
    def titleColor(self):
        return self._titleColor

    def setTitleColor(self, color):
        """
        Set the title color of the mdi window.
        Args:
            color(QColor): The title color.
        """
        self._titleColor = color
        self.update()

    def eventFilter(self, object, event):
        if event.type() == QtCore.QEvent.FocusIn:
            self.focused.emit()
        return super().eventFilter(object, event)

    def resizeEvent(self, event):
        """Reimplementation of resizeEvent in QMdiSubWindow"""
        self.resized.emit()
        if self._resizeTimer.isActive():
            self._resizeTimer.stop()
        self._resizeTimer.start(300)
        return super().resizeEvent(event)

    def moveEvent(self, event):
        """Reimplementation of moveEvent in QMdiSubWindow"""
        self.moved.emit()
        if self._moveTimer.isActive():
            self._moveTimer.stop()
        self._moveTimer.start(300)
        return super().moveEvent(event)

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
        if self._parent is not None:
            self._parent.focused.disconnect(self._setFocus)
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
            self.focused.connect(self._setFocus)
            self._parent.focused.connect(self._setFocus)
            self._parent.moved.connect(self.attachTo)
            self._parent.resized.connect(self.attachTo)
            self._parent.closed.connect(self.close)

    @avoidCircularReference
    def _setFocus(self):
        _ExtendMdiArea.current().setActiveSubWindow(self)
        _ExtendMdiArea.current().setActiveSubWindow(self._parent)

    def attachTo(self):
        """
        Attach *self* to pre-registered parent by :meth:`attach`.

        When the parent window is move programatically by :func:`move`, the window does not follow.

        Developers should call this method to intentionally attach it to parent.
        """
        if self._parent is not None:
            pos = self._parent.pos()
            frm = self._parent.frameGeometry()
            self.move(QtCore.QPoint(pos.x() + frm.width(), pos.y()))

    def saveSettings(self, file):
        """
        Export all widgets settings from default setting file specified by name.
        User input on various widgets are easily loaded from file by :meth:`restoreSettings`.
        """
        data = _save(self)
        self.saved.emit(data)
        file = os.path.abspath(file)
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, 'w') as f:
            f.write(str(data))

    def restoreSettings(self, file):
        """
        Import all widgets settings from default setting file specified by name.
        User input on various widgets are easily exported to file by :meth:`saveSettings`.
        """
        if os.path.exists(file):
            with open(file, 'r') as f:
                data = eval(f.read())
            _restore(self, data)
            self.loaded.emit(data)

    def setSettingFile(self, file):
        """
        Enable automatic setting storing by saveSettings.
        restoreSettings will be called when this functions is called.
        """
        from lys import glb
        glb.mainWindow().closed.connect(lambda: self.saveSettings(file))
        self.closed.connect(lambda: self.saveSettings(file))
        self.restoreSettings(file)

    def isFloating(self):
        """Return if the window is out of the mdi window or not"""
        return self._floating


def _restore(self, settings):
    for obj in self.findChildren(QtWidgets.QSpinBox) + self.findChildren(QtWidgets.QDoubleSpinBox):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setValue(settings[name])

    for obj in self.findChildren(QtWidgets.QCheckBox) + self.findChildren(QtWidgets.QRadioButton):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setChecked(settings[name])

    for obj in self.findChildren(QtWidgets.QComboBox):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                i = obj.findText(settings[name])
                if i != -1:
                    obj.setCurrentIndex(i)

    for obj in self.findChildren(QtWidgets.QLineEdit):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setText(settings[name])

    for obj in self.findChildren(QtWidgets.QListWidget):
        name = obj.objectName()
        if _checkName(name):
            obj.clear()
            if name in settings:
                obj.addItems(settings[name])

    for obj in self.findChildren(QtWidgets.QTextEdit):
        name = obj.objectName()
        if _checkName(name):
            if name in settings:
                obj.setPlainText(settings[name])


def _save(self):
    settings = dict()

    for obj in self.findChildren(QtWidgets.QSpinBox) + self.findChildren(QtWidgets.QDoubleSpinBox):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.value()

    for obj in self.findChildren(QtWidgets.QCheckBox) + self.findChildren(QtWidgets.QRadioButton):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.isChecked()

    for obj in self.findChildren(QtWidgets.QComboBox):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.currentText()

    for obj in self.findChildren(QtWidgets.QLineEdit):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = obj.text()

    for obj in self.findChildren(QtWidgets.QListWidget):
        name = obj.objectName()
        if _checkName(name):
            settings[name] = [obj.item(i).text() for i in range(obj.count())]

    for obj in self.findChildren(QtWidgets.QTextEdit):
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


class _AutoSavedWindow(LysSubWindow):
    modified = QtCore.pyqtSignal()
    """*modified* signal is emitted when the content of the window is changed."""

    def __init__(self, *args, tmpFile=None, **kwargs):
        if tmpFile is None:
            self.__tmpFile = _ExtendMdiArea.current().tmpFilePath(self._prefix(), self._suffix())
        else:
            self.__tmpFile = tmpFile
        super().__init__(*args, **kwargs)
        self.modified.connect(self.__save)
        self.closed.connect(self.__delete)

    def close(self, store=False, **kwargs):
        if store:
            self.closed.disconnect(self.__delete)
        super().close()

    def __delete(self):
        if os.path.exists(self.TemporaryFile()):
            os.remove(self.TemporaryFile())

    def __save(self):
        os.makedirs(os.path.dirname(self.__tmpFile), exist_ok=True)
        self._save(self.__tmpFile)

    def TemporaryFile(self):
        """Return temporary filename that hold content of the window"""
        return os.path.abspath(self.__tmpFile)

    def Name(self):
        """Return name of the window, which is automatically determined."""
        return os.path.basename(self.TemporaryFile()).replace(self._suffix(), "") + " (not saved)"

    def _prefix(self):
        pass

    def _suffix(self):
        pass


class _ConservableWindow(_AutoSavedWindow):
    fileChanged = QtCore.pyqtSignal()
    """*fileChanged* signal is emitted when it is saved."""

    def __init__(self, file=None, *args, **kwargs):
        if file is None:
            self.__file = None
        else:
            self.__file = os.path.abspath(file)
        super().__init__(*args, **kwargs)
        self.__closeflg = True
        self.__modified = False
        self.setWindowTitle(self.Name())
        self.modified.connect(self.__onModified)

    def __onModified(self):
        self.__modified = True
        self.setWindowTitle(self.Name())

    def _changeFileName(self, file, mkdir=False):
        if file is None:
            self.__file = None
        else:
            self.__file = os.path.abspath(file)
            if mkdir:
                os.makedirs(os.path.dirname(self.__file), exist_ok=True)
        self.setWindowTitle(self.Name())

    def Save(self, file=None):
        """
        Save the content of the window.

        Args:
            file(str): The file to be saved. If *file* is None, the window is saved in the last-saved file.
        """
        if file is not None:
            self._changeFileName(file, mkdir=True)
            self.fileChanged.emit()
        self._save(self.__file)
        self.__modified = False
        self.setWindowTitle(self.Name())

    def close(self, force=False, **kwargs):
        """Reimplementation of close in QMdiSubWindow"""
        self.__closeflg = not force
        super().close(**kwargs)

    def closeEvent(self, event):
        """Reimplementation of closeEvent in QMdiSubWindow"""
        if self.__closeflg:
            msg = QtWidgets.QMessageBox(parent=_ExtendMdiArea.current())
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Caution")
            if self.__file is None:
                msg.setText("This window is not saved. Do you really want to close it?")
                msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            elif self.__modified:
                msg.setText("Do you want to save the content of this window to " + self.__file + "?")
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
            else:
                return super().closeEvent(event)
            ok = msg.exec_()
            if ok == QtWidgets.QMessageBox.Cancel:
                return event.ignore()
            if ok == QtWidgets.QMessageBox.Yes:
                self.Save()
        return super().closeEvent(event)

    def FileName(self):
        """Return filename that saves content of the window"""
        return self.__file

    def Name(self):
        """Return name of the window, which is automatically determined by filename."""
        if self.__file is not None:
            p = Path(self.FileName())
            if Path.cwd() in p.parents:
                p = p.relative_to(home())
            else:
                p = p.resolve()
            name = str(p)
            if self.__modified:
                name += "*"
            return name
        else:
            return super().Name()

    def _save(self, file):
        raise NotImplementedError
