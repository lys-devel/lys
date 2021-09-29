import os
import shutil
import fnmatch
import itertools
from ExtendAnalysis import Wave
from ExtendAnalysis.BasicWidgets.GraphWindow import Graph, PreviewWindow, Table
from ExtendAnalysis import load, home
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ExtendFileSystemModel(QSortFilterProxyModel):
    def __init__(self, model=QFileSystemModel()):
        super().__init__()
        self.mod = model
        self.setSourceModel(self.mod)
        self.mod.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self._exclude = []
        self._include = []
        self._matched = []
        self._filters = []
        self._path = ""

    def setRootPath(self, path):
        self._path = path
        self.mod.setRootPath(path)

    def indexFromPath(self, path):
        return self.mapFromSource(self.mod.index(path))

    def AddAcceptedFilter(self, filter):
        self._include.append(filter)

    def AddExcludedFilter(self, filter):
        self._exclude.append(filter)

    def SetNameFilter(self, filters):
        self._filters = self.__makeFilterString(filters)
        it = QDirIterator(self._path, self._filters, QDir.Dirs | QDir.Files, QDirIterator.Subdirectories)
        self._matched = []
        while it.hasNext():
            self._matched.append(it.next().replace(home() + "/", ""))
        self.mod.setNameFilters(["*"])
        self.setRootPath(self._path)

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
            return self.matchPath(path)
        if len(self._include) == 0:
            return self.matchPath(path, False)
        for inc in self._include:
            if fnmatch.fnmatch(name, inc):
                return self.matchPath(path, False)
        return False

    def matchPath(self, path, dir=True):
        if len(self._filters) == 0:
            return True
        if path == self._path:
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


class _FileSystemViewBase(QWidget):
    def __init__(self, view, parent=None, model=ExtendFileSystemModel(), path=''):
        super().__init__()
        self.__view = view
        self.Model = model
        self.__view.setModel(self.Model)
        self.SetPath(path)
        self.__actions = {}

    def SetContextMenuActions(self, dict):
        self.__actions = dict

    def AddContextMenuActions(self, type, actionlist):
        self.__actions[type] = actionlist

    def _buildContextMenu(self, qPoint):
        menu = QMenu(self)
        indexes = self.selectedIndexes()
        tp = self._judgeFileType(indexes)
        if not tp in self.__actions and 'other' in self.__actions:
            tp = 'other'
        if tp in self.__actions:
            for key in self.__actions[tp]:
                if isinstance(key, QAction):
                    menu.addAction(key)
                elif isinstance(key, QMenu):
                    menu.addMenu(key)
            menu.exec_(QCursor.pos())

    def SetPath(self, path):
        self._path = path
        self.Model.setRootPath(path)
        self.__view.setRootIndex(self.Model.indexFromPath(path))

    def currentPath(self):
        return self.Model.filePath(self.tree.currentIndex())

    def selectedPaths(self):
        list = self.selectedIndexes()
        res = []
        for l in list:
            res.append(self.Model.filePath(l))
        return res

    def selectedPath(self):
        ps = self.selectedPaths()
        if len(ps) != 0:
            return ps[0]
        else:
            return None

    def _judgeFileType(self, indexes):
        flg = True
        for i in indexes:
            flg = flg and self.Model.isDir(i)
        if flg:
            return "dir"
        else:
            flg = True
            path, ext = os.path.splitext(self.Model.filePath(indexes[0]))
            for i in indexes:
                path2, ext2 = os.path.splitext(self.Model.filePath(i))
                if not ext == ext2:
                    flg = False
            if flg:
                return ext
            else:
                return "mix"

    def Action_NewDirectory(self):
        return QAction('New Directory', self, triggered=self._Action_NewDirectory)

    def _Action_NewDirectory(self):
        paths = self.selectedPaths()
        text, ok = QInputDialog.getText(self, '---Input Dialog---', 'Directory name:')
        if ok and not len(text) == 0:
            for p in paths:
                os.makedirs(p + '/' + text, exist_ok=True)

    def Action_Delete(self):
        return QAction('Delete', self, triggered=self._Action_Delete)

    def _Action_Delete(self):
        paths = self.selectedPaths()
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

    def Action_Display(self):
        return QAction('Display', self, triggered=self.__display)

    def __display(self):
        g = Graph()
        for p in self.selectedPaths():
            w = Wave(p)
            g.Append(w)

    def Action_MultiCut(self):
        return QAction('MultiCut', self, triggered=self.__multicut)

    def __multicut(self):
        from ExtendAnalysis import MultiCut
        w = Wave(self.selectedPaths()[0])
        MultiCut(w)

    def Action_Append(self):
        return QAction('Append', self, triggered=self.__append)

    def __append(self):
        g = Graph.active()
        if g is None:
            return
        for p in self.selectedPaths():
            w = Wave(p)
            g.Append(w)

    def Action_Preview(self):
        return QAction('Preview', self, triggered=self.__preview)

    def __preview(self):
        list = []
        for p in self.selectedPaths():
            list.append(Wave(p))
        PreviewWindow(list)

    def Action_Edit(self):
        return QAction('Edit', self, triggered=self.__edit)

    def __edit(self):
        t = Table()
        for p in self.selectedPaths():
            w = load(p)
            t.Append(w)

    def Action_Print(self):
        return QAction('Print', self, triggered=self.__print)

    def __print(self):
        for p in self.selectedPaths():
            w = load(p)
            print(w)


class FileSystemView(_FileSystemViewBase):
    def __init__(self, parent=None, model=ExtendFileSystemModel(), path=''):
        self.tree = QTreeView(parent=parent)
        super().__init__(self.tree, parent, model, path)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._buildContextMenu)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setColumnHidden(3, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(1, True)

        self.edit = QLineEdit()
        self.edit.textChanged.connect(self.setFilter)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Filter"))
        h1.addWidget(self.edit)

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addLayout(h1)
        self.setLayout(layout)

    def selectedIndexes(self):
        indexes = self.tree.selectedIndexes()
        if len(indexes) == 0:
            indexes.append(self.Model.indexFromPath(self._path))
        return indexes

    def setFilter(self, txt):
        f = [fil for fil in txt.split(" ") if len(fil) != 0]
        self.Model.SetNameFilter(f)


class FileSystemList(QListView, _FileSystemViewBase):
    def __init__(self, parent=None, model=ExtendFileSystemModel(), path=''):
        QListView.__init__(self, parent=parent)
        _FileSystemViewBase.__init__(self, QListView, parent, model, path)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)

    def selectedIndexes(self):
        indexes = QListView.selectedIndexes(self)
        if len(indexes) == 0:
            indexes.append(self.Model.index(self._path))
        return indexes
