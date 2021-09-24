import os
import sys
import copy
import logging
import numpy as np
import scipy.ndimage
import scipy.signal
import _pickle as cPickle
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from . import SettingDict
__home = os.getcwd()
sys.path.append(__home)


def home():
    return __home


def globalSetting():
    return SettingDict(home() + "/.lys/settings/global.dic")


def produce(data, axes, note):
    w = Wave()
    w.data = data
    w.axes = axes
    w.note = note
    return w


class WaveMethods(object):
    def shape(self):
        res = []
        tmp = self.data.shape
        for i in tmp:
            if i is not None:
                res.append(i)
        return tuple(res)

    def axisIsValid(self, dim):
        tmp = self.axes[dim]
        if tmp is None or (tmp == np.array(None)).all():
            return False
        return True

    def posToPoint(self, pos, axis=None):
        if axis is None:
            x0 = self.x[0]
            x1 = self.x[len(self.x) - 1]
            y0 = self.y[0]
            y1 = self.y[len(self.y) - 1]
            dx = (x1 - x0) / (len(self.x) - 1)
            dy = (y1 - y0) / (len(self.y) - 1)
            return (int(round((pos[0] - x0) / dx)), int(round((pos[1] - y0) / dy)))
        else:
            if hasattr(pos, "__iter__"):
                return [self.posToPoint(p, axis) for p in pos]
            ax = self.getAxis(axis)
            x0 = ax[0]
            x1 = ax[len(ax) - 1]
            dx = (x1 - x0) / (len(ax) - 1)
            return int(round((pos - x0) / dx))

    def pointToPos(self, p, axis=None):
        if axis is None:
            x0 = self.x[0]
            x1 = self.x[len(self.x) - 1]
            y0 = self.y[0]
            y1 = self.y[len(self.y) - 1]
            dx = (x1 - x0) / (len(self.x) - 1)
            dy = (y1 - y0) / (len(self.y) - 1)
            return (p[0] * dx + x0, p[1] * dy + y0)
        else:
            if hasattr(p, "__iter__"):
                return [self.pointToPos(pp, axis) for pp in p]
            ax = self.getAxis(axis)
            x0 = ax[0]
            x1 = ax[len(ax) - 1]
            dx = (x1 - x0) / (len(ax) - 1)
            return p * dx + x0

    def getAxis(self, dim):
        val = np.array(self.axes[dim])
        if self.data.ndim <= dim:
            return None
        elif val.ndim == 0:
            return np.arange(self.data.shape[dim])
        else:
            if self.data.shape[dim] == val.shape[0]:
                return val
            else:
                res = np.empty((self.data.shape[dim]))
                for i in range(self.data.shape[dim]):
                    res[i] = np.NaN
                for i in range(min(self.data.shape[dim], val.shape[0])):
                    res[i] = val[i]
                return res

    def addObject(self, name, obj):
        self.note[name] = cPickle.dumps(obj)

    def getObject(self, name):
        return cPickle.loads(self.note[name])

    def addAnalysisLog(self, log):
        if not "AnalysisLog" in self.note:
            self.note["AnalysisLog"] = ""
        self.note["AnalysisLog"] += log

    def getAnalysisLog(self):
        return self.note["AnalysisLog"]


class Wave(QObject, WaveMethods):
    modified = pyqtSignal(object)
    _nameIndex = 0

    def __init__(self, data=None, *args, **kwargs):
        super().__init__()
        self.__name = None
        if type(data) == str:
            data = self._parseFilename(data)
            self._load(data)
        else:
            self._load(None)
            self.setData(data, *args)
        if "name" in kwargs:
            self.SetName(kwargs["name"])

    def _load(self, file):
        if file is None:
            self.axes = [np.array(None)]
            self.data = np.array(None)
            self.note = {}
        else:
            tmp = np.load(file, allow_pickle=True)
            data = tmp['data']
            self.axes = [np.array(None) for i in range(data.ndim)]
            self.data = data
            if 'axes' in tmp:
                self.axes = [axis for axis in tmp['axes']]
            if 'note' in tmp:
                self.note = tmp['note'][()]
            else:
                self.note = {}

    def setData(self, data, *axes):
        if hasattr(data, "__iter__"):
            if len(data) > 0:
                if isinstance(data[0], Wave):
                    self._joinWaves(data, axes)
                    return
        self.data = data
        if len(axes) == self.data.ndim:
            self.axes = list(axes)

    def _joinWaves(self, waves, axes):
        self.data = np.array([w.data for w in waves])
        if len(axes) == 1:
            ax = list(axes)
        else:
            ax = [None]
        self.axes = ax + waves[0].axes

    def __setattr__(self, key, value):  # TODO add note and axes
        if key not in ["x", "y", "z", "data"]:
            super().__setattr__(key, value)
        if key == 'x' and len(self.axes) > 0:
            self.axes[0] = np.array(value)
        elif key == 'y' and len(self.axes) > 1:
            self.axes[1] = np.array(value)
        elif key == 'z' and len(self.axes) > 2:
            self.axes[2] = np.array(value)
        elif key in ['data']:
            if isinstance(value, np.ndarray):
                super().__setattr__(key, value)
            else:
                super().__setattr__(key, np.array(value))
            while(len(self.axes) < self.data.ndim):
                self.axes.append(np.array(None))
            while(len(self.axes) > self.data.ndim):
                self.axes.pop(len(self.axes) - 1)
        self.modified.emit(self)

    def __getattribute__(self, key):
        if key in "xyz":
            index = ['x', 'y', 'z'].index(key)
            return self.getAxis(index)
        else:
            return super().__getattribute__(key)

    def __getitem__(self, key):
        import copy
        if isinstance(key, tuple):
            data = self.data[key]
            axes = []
            for s, ax in zip(key, self.axes):
                if ax is None or (ax == np.array(None)).all():
                    axes.append(None)
                else:
                    axes.append(ax[s])
            w = Wave(data)
            w.axes = axes
            w.note = copy.deepcopy(self.note)
            w.addAnalysisLog("Wave sliced: " + str(key) + "\n")
            return w
        else:
            super().__getitem__(key)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __reduce_ex__(self, proto):
        return produce, (self.data, self.axes, self.note)

    def _parseFilename(self, path):
        if path is None:
            return None
        return (path + ".npz").replace(".npz.npz", ".npz")

    def Duplicate(self):
        w = Wave()
        w.data = copy.copy(self.data)
        w.axes = copy.copy(self.axes)
        w.note = copy.copy(self.note)
        w.SetName(self.Name())
        return w

    def Save(self, file):
        file = os.path.abspath(self._parseFilename(file))
        if file is not None:
            abspath = os.path.abspath(file)
            os.makedirs(os.path.dirname(abspath), exist_ok=True)
            np.savez_compressed(file, data=self.data, axes=self.axes, note=self.note, allow_pickle=True)
            return True

    def SetName(self, name):
        self.__name = name

    def Name(self):
        if self.__name is None:
            self.SetName("wave" + str(Wave._nameIndex))
            Wave._nameIndex += 1
        return self.__name

    def FileName(self):
        print("Wave.FileName is deprecated.")
        return None

    def slice(self, pos1, pos2, axis='x', width=1):
        w = Wave()
        dx = (pos2[0] - pos1[0])
        dy = (pos2[1] - pos1[1])
        index = ['x', 'y', 'xy'].index(axis)
        if index == 2:
            size = int(np.sqrt(dx * dx + dy * dy) + 1)
        else:
            size = abs(pos2[index] - pos1[index]) + 1
        res = np.zeros((size))
        nor = np.sqrt(dx * dx + dy * dy)
        dx, dy = dy / nor, -dx / nor
        for i in range(1 - width, width, 2):
            x, y = np.linspace(pos1[0], pos2[0], size) + dx * (i *
                                                               0.5), np.linspace(pos1[1], pos2[1], size) + dy * (i * 0.5)
            res += scipy.ndimage.map_coordinates(self.data, np.vstack(
                (y, x)), mode="constant", order=3, prefilter=True)
        w.data = res
        if axis == 'x':
            w.x = self.x[pos1[index]:pos2[index] + 1]
        elif axis == 'y':
            w.x = self.y[pos1[index]:pos2[index] + 1]
        else:
            dx = abs(self.x[pos1[0]] - self.x[pos2[0]])
            dy = abs(self.y[pos1[1]] - self.y[pos2[1]])
            d = np.sqrt(dx * dx + dy * dy)
            w.x = np.linspace(0, d, size)
        return w

    @staticmethod
    def SupportedFormats():
        return ["Numpy npz (*.npz)", "Comma-Separated Values (*.csv)", "Text file (*.txt)"]

    def export(self, path, type="Numpy npz (*.npz)"):
        if type == 'Numpy npz (*.npz)':
            np.savez(path + ".npz".replace(".npz.npz", ".npz"),
                     data=self.data, axes=self.axes, note=self.note)
        if type == "Comma-Separated Values (*.csv)":
            np.savetxt(path + ".csv".replace(".csv.csv", ".csv"), self.data, delimiter=',')
        if type == "Text file (*.txt)":
            np.savetxt(path + ".txt".replace(".txt.txt", ".txt"), self.data)

    @staticmethod
    def importFrom(path):
        p, ext = os.path.splitext(path)
        if ext == "npz":
            w = Wave(path)
            return w
        else:
            data = np.loadtxt(path, delimiter=",")
            w = Wave()
            w.data = data
            return w


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
        from . import LoadFile
        AutoSavedWindow._workspace = workspace
        cls.__list = cls._loadWinList()
        AutoSavedWindow._windir = home() + '/.lys/workspace/' + AutoSavedWindow._workspace + '/wins'
        print("Workspace: " + AutoSavedWindow._workspace)
        cls._restore = True
        os.makedirs(AutoSavedWindow._windir, exist_ok=True)
        for path in cls.__list:
            try:
                w = LoadFile.load(path)
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
