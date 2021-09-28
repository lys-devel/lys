import os
import sys
import traceback
import rlcompleter
import shutil
import fnmatch
import itertools


from LysQt.QtWidgets import QMainWindow, QMdiArea, QSplitter, QLineEdit, QWidget, QTreeView
from LysQt.QtWidgets import QFileSystemModel, QHBoxLayout, QVBoxLayout, QLabel, QAbstractItemView, QAction, QMenu, QMessageBox
from LysQt.QtCore import Qt, pyqtSignal, QEvent, QDir, QDirIterator, QSortFilterProxyModel
from LysQt.QtGui import QCursor

from . import plugin, load, home

from .CommandWindow import *


class MainWindow(QMainWindow):
    closed = pyqtSignal(object)
    _instance = None

    def __init__(self):
        super().__init__()
        MainWindow._instance = self
        self.__initUI()
        self.__initMenu()
        ExtendMdiSubWindow.mdimain = self.area
        AutoSavedWindow.RestoreAllWindows()

    def __initUI(self):
        self.setWindowTitle('lys')
        self.area = QMdiArea()
        self._side = self.__sideBar()

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self.area)
        sp.addWidget(self._side)
        self.setCentralWidget(sp)
        self.show()

    def __sideBar(self):
        self._fileView = FileSystemView()
        self._setting = SettingWidget()

        self._tab_up = QTabWidget()
        self._tab_up.addTab(_CommandLogWidget(self), "Command")

        self._tab = QTabWidget()
        self._tab.addTab(self._fileView, "File")
        #self._tab.addTab(WorkspaceWidget(self), "Workspace")
        self._tab.addTab(self._setting, "Settings")
        self._tab.addTab(TaskWidget(), "Tasks")

        layout_h = QSplitter(Qt.Vertical)
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(_CommandLineEdit(plugin.shell()))
        layout_h.addWidget(self._tab)

        lay = QHBoxLayout()
        lay.addWidget(layout_h)
        w = QWidget()
        w.setLayout(lay)
        return w

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Window")

        act = win.addAction("Close all graphs")
        act.triggered.connect(Graph.closeAllGraphs)
        act.setShortcut("Ctrl+K")

        act = win.addAction("Show/Hide Sidebar")
        act.triggered.connect(lambda: self._side.setVisible(not self._side.isVisible()))
        act.setShortcut("Ctrl+J")
        return

    def closeEvent(self, event):
        if not self.__saveData():
            event.ignore()
            return
        self.closed.emit(event)
        if not event.isAccepted():
            return
        ExtendMdiSubWindow.CloseAllWindows()

    def __saveData(self):
        AutoSavedWindow.StoreAllWindows()
        return True

    def addTab(self, widget, name, position):
        if position == "up":
            self._tab_up.addTab(widget, name)
        if position == "down":
            self._tab.addTab(widget, name)

    @property
    def fileView(self):
        return self._fileView


class _CommandLogWidget(QTextEdit):
    """Simple command log widget"""
    class _Logger(object):
        def __init__(self, editor, out, color):
            self.editor = editor
            self.out = out
            self.color = color

        def write(self, message):
            self.editor.updated.emit(message, self.color)
            if self.out:
                self.out.write(message)

        def flush(self):
            pass
    __logFile = ".lys/commandlog.log"
    updated = pyqtSignal(str, QColor)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.__load()
        sys.stdout = self._Logger(self, sys.stdout, self.textColor())
        sys.stderr = self._Logger(self, sys.stderr, QColor(255, 0, 0))
        self.updated.connect(self._update)

    def __load(self):
        if os.path.exists(self.__logFile):
            with open(self.__logFile, 'r') as f:
                self.__clog = f.read()
        else:
            self.__clog = ""
        self.setPlainText(self.__clog)

    def _save(self):
        data = self.toPlainText()
        if len(data) > 300000:
            data = data[-300000:]
        with open(self.__logFile, 'w') as f:
            f.write(data)

    def _update(self, message, color):
        self.moveCursor(QTextCursor.End)
        self.setTextColor(color)
        self.insertPlainText(message)
        self.moveCursor(QTextCursor.StartOfLine)
        self._save()


class _CommandLineEdit(QLineEdit):
    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self.returnPressed.connect(self.__SendCommand)
        self.__logn = 0
        self.completer = rlcompleter.Completer(self.shell.dict)

    def __findBlock(self):
        text = self.text()
        end = self.cursorPosition()
        for i in range(1, end + 1):
            if text[end - i] in [",", "(", " ", "=", "["]:
                return end - i + 1, end
        return 0, end

    def _resetComplete(self):
        self.__tabn = -1

    def _complete(self):
        if len(self.text()) == 0:
            return True
        if self.__tabn == -1:
            self._printComplete()
            self.__tabn += 1
            return True
        if self.__tabn == 0:
            s, e = self.__findBlock()
            self.__prefix = self.text()[:s]
            self.__suffix = self.text()[e:]
            self.__txt = self.text()[s:e]
        try:
            tmp = self.completer.complete(self.__txt, self.__tabn)
            if tmp is None and not self.__tabn == 0:
                tmp = self.completer.complete(self.__txt, 0)
                self.__tabn = 0
            if tmp is not None:
                self.setText(self.__prefix + tmp + self.__suffix)
                self.setCursorPosition(len(self.__prefix + tmp))
                self.__tabn += 1
        except Exception:
            print("fail to complete:", self.__txt, self.__tabn)
        return True

    def _printComplete(self):
        if len(self.text()) == 0:
            return
        s, e = self.__findBlock()
        self.__txt = self.text()[s:e]
        res = ""
        for i in range(100):
            tmp = self.completer.complete(self.__txt, i)
            if tmp is None:
                break
            res += tmp.replace("(", "") + ", "
        if i == 99:
            res += "etc..."
        if res != "":
            print(res)

    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                return self._complete()
            else:
                self._resetComplete()

            if event.key() == Qt.Key_Up:
                log = self.shell.commandLog
                if len(log) == 0:
                    return True
                if not len(log) - 2 == self.__logn:
                    self.__logn += 1
                self.setText(log[len(log) - self.__logn])
                return True

            if event.key() == Qt.Key_Down:
                log = self.shell.commandLog
                if not self.__logn == 0:
                    self.__logn -= 1
                if self.__logn == 0:
                    self.setText("")
                else:
                    self.setText(log[max(0, len(log) - self.__logn)])
                return True

        return QLineEdit.event(self, event)

    def __SendCommand(self):
        txt = self.text()
        self.clear()
        self.__logn = 0
        print(">", txt)
        try:
            res = self.shell.eval(txt, save=True)
            if res is not None:
                print(res)
            return
        except Exception:
            pass
        try:
            self.shell.exec(txt)
            return
        except Exception:
            err = traceback.format_exc()
            try:
                res = self.shell._do(txt)
            except Exception:
                sys.stderr.write('Invalid command.\n')
                print(err)


class _FileSystemModel(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.mod = QFileSystemModel()
        self.mod.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.mod.setRootPath(home())
        self.setSourceModel(self.mod)
        self._exclude = ["*__pycache__", "*dask-worker-space"]
        self._matched = []
        self._filters = []

    def indexFromPath(self, path):
        return self.mapFromSource(self.mod.index(path))

    def SetNameFilter(self, filters):
        filters = [fil for fil in filters.split(" ") if len(fil) != 0]
        self._filters = self.__makeFilterString(filters)
        it = QDirIterator(home(), self._filters, QDir.Dirs | QDir.Files, QDirIterator.Subdirectories)
        self._matched = []
        while it.hasNext():
            self._matched.append(it.next().replace(home() + "/", ""))
        self.mod.setNameFilters(["*"])
        self.mod.setRootPath(home())

    def __makeFilterString(self, filters):
        result = []
        for fs in itertools.permutations(filters):
            res = "*"
            for f in fs:
                res += f + "*"
            result.append(res)
        return result

    def filterAcceptsRow(self, row, parent):
        index = self.mod.index(row, 0, parent)
        name = self.mod.data(index, Qt.DisplayRole)
        path = self.mod.filePath(index).replace(home() + "/", "")
        for exc in self._exclude:
            if fnmatch.fnmatch(name, exc):
                return False
        if self.mod.isDir(index):
            return self._matchPath(path)
        return self._matchPath(path, False)

    def _matchPath(self, path, dir=True):
        if len(self._filters) == 0:
            return True
        if path == home():
            return True
        for m in self._matched:
            if m == path:
                return True
            if dir:
                if m.startswith(path + "/") or m == path:
                    return True
            else:
                if m == path:
                    return True
        return False

    def isDir(self, index):
        return self.mod.isDir(self.mapToSource(index))

    def filePath(self, index):
        return self.mod.filePath(self.mapToSource(index))

    def parent(self, index):
        return self.mapFromSource(self.mod.parent(self.mapToSource(index)))


class FileSystemView(QWidget):
    def __init__(self):
        super().__init__()
        self.__initUI(home())
        self._builder = _contextMenuBuilder()

    def __initUI(self, path=home()):
        self._Model = _FileSystemModel()

        self._tree = QTreeView()
        self._tree.setModel(self._Model)
        self._tree.setRootIndex(self._Model.indexFromPath(path))
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._buildContextMenu)
        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.setColumnHidden(3, True)
        self._tree.setColumnHidden(2, True)
        self._tree.setColumnHidden(1, True)

        edit = QLineEdit()
        edit.textChanged.connect(self._Model.SetNameFilter)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Filter"))
        h1.addWidget(edit)

        layout = QVBoxLayout()
        layout.addWidget(self._tree)
        layout.addLayout(h1)
        self.setLayout(layout)

    def _buildContextMenu(self, qPoint):
        indexes = self._tree.selectedIndexes()
        if len(indexes) == 0:
            indexes.append(self._Model.indexFromPath(home()))
        self._builder.build(self.selectedPaths())

    def selectedPaths(self):
        list = self._tree.selectedIndexes()
        res = []
        for item in list:
            res.append(self._Model.filePath(item))
        return res

    def registerFileMenu(self, ext, menu, add_default=True):
        self._builder.register(ext, menu, add_default=add_default)


class _contextMenuBuilder:
    def __init__(self):
        self._SetDefaultMenu()

    def _SetDefaultMenu(self):
        self._new = QAction('New Directory', triggered=self._Action_NewDirectory)
        self._load = QAction('Load', triggered=self.__load)
        self._prt = QAction('Print', triggered=self.__print)

        self._delete = QAction('Delete', triggered=self._Action_Delete)
        self._rename = QAction('Rename', triggered=self.__print)

        self._cut = QAction('Cut', triggered=self.__print)
        self._copy = QAction('Copy', triggered=self.__print)
        self._paste = QAction('Paste', triggered=self.__print)

        menu = {}
        menu["dir_single"] = self._makeMenu([self._new, self._load, self._prt, "sep", self._cut, self._copy, self._paste, "sep", self._rename, self._delete])
        menu["dir_multi"] = self._makeMenu([self._load, self._prt, "sep", self._cut, self._copy, "sep", self._delete])

        menu["mix_single"] = self._makeMenu([self._load, self._prt, "sep", self._cut, self._copy, "sep", self._rename, self._delete])
        menu["mix_multi"] = self._makeMenu([self._load, self._prt, "sep", self._cut, self._copy, "sep", self._delete])

        self.__actions = menu

    def register(self, ext, menu, add_default):
        menu_s = self._duplicateMenu(menu)
        menu_m = self._duplicateMenu(menu)
        if add_default:
            menu_s.addSeparator()
            menu_s.addAction(self._load)
            menu_s.addAction(self._prt)
            menu_s.addSeparator()
            menu_s.addAction(self._cut)
            menu_s.addAction(self._copy)
            menu_s.addSeparator()
            menu_s.addAction(self._rename)
            menu_s.addAction(self._delete)

            menu_m.addSeparator()
            menu_m.addAction(self._load)
            menu_m.addAction(self._prt)
            menu_m.addSeparator()
            menu_m.addAction(self._cut)
            menu_m.addAction(self._copy)
            menu_m.addSeparator()
            menu_m.addAction(self._delete)
        self.__actions[ext + "_single"] = menu_s
        self.__actions[ext + "_multi"] = menu_m

    def _duplicateMenu(self, origin):
        result = QMenu()
        for m in origin.actions():
            if isinstance(m, QMenu):
                result.addMenu(self._duplicateMenu(m))
            else:
                result.addAction(m)
        return result

    def _makeMenu(self, list):
        result = QMenu()
        for item in list:
            if item == "sep":
                result.addSeparator()
            else:
                result.addAction(item)
        return result

    def build(self, paths):
        self._paths = paths
        tp = self._judgeFileType(self._paths)
        self.__actions[tp].exec_(QCursor.pos())

    def _judgeFileType(self, paths):
        if all([os.path.isdir(p) for p in paths]):
            res = "dir"
        else:
            ext = os.path.splitext(paths[0])[1]
            if all([ext == os.path.splitext(p)[1] for p in paths]):
                if ext + "_single" not in self.__actions:
                    res = "mix"
                else:
                    res = ext
            else:
                res = "mix"
        # check if there is multiple files
        if len(paths) == 1:
            res += "_single"
        else:
            res += "_multi"
        return res

    def __load(self):
        for p in self.selectedPaths():
            nam, ext = os.path.splitext(os.path.basename(p))
            plugin.shell().addObject(load(p), name=nam)

    def _Action_NewDirectory(self):
        paths = self.selectedPaths()
        text, ok = QInputDialog.getText(self, '---Input Dialog---', 'Directory name:')
        if ok and not len(text) == 0:
            for p in paths:
                os.makedirs(p + '/' + text, exist_ok=True)

    def _Action_Delete(self):
        paths = self._paths
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you really want to delete " + str(len(paths)) + " items?")
        msg.setWindowTitle("Caution")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ok = msg.exec_()
        if ok == QMessageBox.Ok:
            for p in self.selectedPaths():
                if os.path.isfile(p):
                    os.remove(p)
                if os.path.isdir(p):
                    shutil.rmtree(p)

    def __print(self):
        for p in self.selectedPaths():
            w = load(p)
            print(w)


def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)
