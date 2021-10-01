import os
import sys
import shutil
import fnmatch
import itertools
import logging
from pathlib import Path

from LysQt.QtWidgets import QLineEdit, QWidget, QTreeView, QInputDialog
from LysQt.QtWidgets import QFileSystemModel, QHBoxLayout, QVBoxLayout, QLabel, QAbstractItemView, QAction, QMenu, QMessageBox
from LysQt.QtCore import Qt, QDir, QDirIterator, QSortFilterProxyModel, QUrl
from LysQt.QtGui import QCursor

from . import glb, load


class FileSystemView(QWidget):
    """
    *FileSystemView* is a custom widget to see files in lys, which is mainly used in main window.

    Developers can get selected paths by :meth:`selectedPaths` method.
    Context menu for specified type can be registered by :meth:`registerFileMenu` method.

    See :meth:`selectedPaths` and :meth:`registerFileMenu` for detail and examples

    Args:
        path(str): path to see files.
        model(QFileSystemModel): model used in this view
        drop: Accept drag & drop or not

    """

    def __init__(self, path, model=QFileSystemModel(), drop=False):
        super().__init__()
        self._path = path
        self.__initUI(self._path, model, drop)
        self._builder = _contextMenuBuilder()

    def __initUI(self, path, model, drop=False):
        self._Model = _FileSystemModel(path, model, drop)

        self._tree = QTreeView()
        self._tree.setModel(self._Model)
        self._tree.setRootIndex(self._Model.indexFromPath(path))
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._buildContextMenu)

        self._tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QAbstractItemView.InternalMove)
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
        self._builder.build(self.selectedPaths())

    def selectedPaths(self):
        """
        Returns selected paths.

        Return:
            list of str: paths selected

        Example:

            >>> from lys import glb
            >>> view = glb.mainWindow().fileView     # access global fileview in main window.
            >>> view.selectedPaths()
            ["path selected", "path selected2, ..."]
        """
        list = self._tree.selectedIndexes()
        res = []
        for item in list:
            res.append(self._Model.filePath(item))
        if len(res) == 0:
            res.append(self._path)
        return res

    def registerFileMenu(self, ext, menu, add_default=True):
        """register new context menu to filetype specified by *ext*

        Args:
            ext(str): extension of file type, e.g. "txt", "csv", etc...
            menu(QMenu): context menu to be added.
            add_default: if True, default menus such as Cut, Copy is automatically added at the end of menu.

        Example:

            >>> from lys import glb
            >>> view = glb.mainWindow().fileView     # access global fileview in main window.
            >>> menu = QMenu()
            >>> action = QAction("Print", triggered = lambda: print("test"))
            >>> menu.addAction(action)
            >>> view.registerFileMenu(".txt", menu)
        """
        self._builder.register(ext, menu, add_default=add_default)

    def setPath(self, path):
        """
        Set root directory of file system.
        Args:
            path(str): root path
        """
        self._Model.setPath(path)
        self._tree.setRootIndex(self._Model.indexFromPath(path))


class _FileSystemModel(QSortFilterProxyModel):
    """Model class for FileSystemView"""

    def __init__(self, path, model, drop=False):
        super().__init__()
        self._path = path
        self._drop = drop
        self.mod = model
        self.mod.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.mod.setRootPath(self._path)
        self.setSourceModel(self.mod)
        self._exclude = ["*__pycache__", "*dask-worker-space"]
        self._matched = []
        self._filters = []

    def setPath(self, path):
        self._path = path
        self.mod.setRootPath(path)
        self.mod.setNameFilters(["*"])

    def indexFromPath(self, path):
        return self.mapFromSource(self.mod.index(path))

    def SetNameFilter(self, filters):
        filters = [fil for fil in filters.split(" ") if len(fil) != 0]
        self._filters = self.__makeFilterString(filters)
        it = QDirIterator(self._path, self._filters, QDir.Dirs | QDir.Files, QDirIterator.Subdirectories)
        self._matched = []
        while it.hasNext():
            self._matched.append(it.next().replace(self._path + "/", ""))
        self.mod.setNameFilters(["*"])
        self.mod.setRootPath(self._path)

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
        path = self.mod.filePath(index).replace(self._path + "/", "")
        for exc in self._exclude:
            if fnmatch.fnmatch(name, exc):
                return False
        if self.mod.isDir(index):
            return self._matchPath(path)
        return self._matchPath(path, False)

    def _matchPath(self, path, dir=True):
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

    def flags(self, index):
        if self._drop:
            return super().flags(index) | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled
        else:
            return super().flags(index)

    def supportedDropActions(self):
        return Qt.MoveAction

    def canDropMimeData(self, data, action, row, column, parent):
        return True

    def dropMimeData(self, data, action, row, column, parent):
        targetDir = Path(self.mod.filePath(self.mapToSource(parent)))
        if targetDir.is_file():
            targetDir = targetDir.parent
        files = [Path(QUrl(url).toLocalFile()) for url in data.text().splitlines()]
        targets = [Path(str(targetDir.absolute()) + "/" + f.name) for f in files]
        _moveFiles(files, targets)
        return True

    def isDir(self, index):
        return self.mod.isDir(self.mapToSource(index))

    def filePath(self, index):
        return self.mod.filePath(self.mapToSource(index))

    def parent(self, index):
        return self.mapFromSource(self.mod.parent(self.mapToSource(index)))


class _contextMenuBuilder:
    """Builder of context menu in FileSystemView"""

    def __init__(self):
        self._SetDefaultMenu()

    def _SetDefaultMenu(self):
        self._new = QAction('New Directory', triggered=self.__newdir)
        self._load = QAction('Load', triggered=self.__load)
        self._prt = QAction('Print', triggered=self.__print)

        self._delete = QAction('Delete', triggered=self.__del)
        self._rename = QAction('Rename', triggered=self.__rename)

        self._cut = QAction('Cut', triggered=self.__cut)
        self._copy = QAction('Copy', triggered=self.__copy)
        self._paste = QAction('Paste', triggered=self.__paste)

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

    def _test(self, tp):
        return self.__actions[tp]

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
        for p in self._paths:
            nam, ext = os.path.splitext(os.path.basename(p))
            obj = load(p)
            if obj is not None:
                glb.shell().addObject(obj, name=nam)
            else:
                print("Failed to load " + p, file=sys.stderr)

    def __newdir(self):
        text, ok = QInputDialog.getText(None, 'Create directory', 'Directory name:')
        if ok and not len(text) == 0:
            for p in self._paths:
                os.makedirs(p + '/' + text, exist_ok=True)

    def __del(self):
        paths = self._paths
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you really want to delete " + str(len(paths)) + " items?")
        msg.setWindowTitle("Caution")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ok = msg.exec_()
        if ok == QMessageBox.Ok:
            for p in paths:
                if os.path.isfile(p):
                    os.remove(p)
                if os.path.isdir(p):
                    shutil.rmtree(p)

    def __copy(self):
        self._copyType = "copy"
        self._copyPaths = [Path(p) for p in self._paths]

    def __cut(self):
        self._copyType = "cut"
        self._copyPaths = [Path(p) for p in self._paths]

    def __paste(self):
        if hasattr(self, "_copyType"):
            targetDir = Path(self._paths[0])
            targets = [Path(str(targetDir.absolute()) + "/" + path.name) for path in self._copyPaths]
            _moveFiles(self._copyPaths, targets, copy=self._copyType == "copy")

    def __rename(self):
        file = Path(self._paths[0])
        target, ok = QInputDialog.getText(None, "Rename", "Enter new name", text=file.name)
        if ok:
            target = Path(str(file.parent.absolute()) + "/" + target)
            _moveFiles(file, target)

    def __print(self):
        for p in self._paths:
            w = load(p)
            print(w)


def _moveFiles(files, targets, copy=False):
    if isinstance(files, Path):
        return _moveFiles([files], [targets], copy=copy)
    state = None
    pair = []
    for orig, newfile in zip(files, targets):
        if orig == newfile:
            continue
        if newfile.exists():
            if state == "yesall":
                pair.append([orig, newfile])
            elif state == "noall":
                pass
            else:
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setWindowTitle("Caution")
                msgBox.setText(str(newfile.absolute()) + " exists. Do you want to overwrite it?")
                if len(files) == 1:
                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
                else:
                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.YesAll | QMessageBox.NoAll | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Cancel)
                result = msgBox.exec_()
                if result == QMessageBox.Yes:
                    pair.append([orig, newfile])
                elif result == QMessageBox.No:
                    pass
                elif result == QMessageBox.YesAll:
                    state = "yesall"
                    pair.append([orig, newfile])
                elif result == QMessageBox.NoAll:
                    state = "noall"
                elif result == QMessageBox.Cancel:
                    return False
        else:
            pair.append([orig, newfile])
    for orig, newfile in pair:
        if newfile.exists():
            if newfile.is_file():
                os.remove(newfile.absolute())
            else:
                shutil.rmtree(newfile.absolute())
            logging.info(str(newfile.absolute()) + " has been removed.")
        if copy:
            shutil.copyfile(orig.absolute(), newfile.absolute())
            logging.info(str(newfile.absolute()) + " is copied from " + str(orig.absolute()) + ".")
        else:
            orig.rename(newfile)
            logging.info(str(newfile.absolute()) + " is moved from " + str(orig.absolute()) + ".")
