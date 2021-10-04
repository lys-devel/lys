import collections
import numpy as np

from . import Filters

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QComboBox, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, QMenu, QAction, QTabWidget, QPushButton, QInputDialog
from lys.widgets import LysSubWindow
from .FilterIOGUI import FilterExportDialog, FilterImportDialog

filterGroups = collections.OrderedDict()


def filterGUI(filterClass):
    def _filterGUI(cls):
        cls._filClass = filterClass
        return cls
    return _filterGUI


class FilterSettingBase(QWidget):
    def __init__(self, dimension):
        super().__init__()
        self.dim = dimension

    @classmethod
    def _havingFilter(cls, f):
        if not hasattr(cls, "_filClass"):
            raise TypeError("FilterGUI should decorated by @filterGUI.")
        if isinstance(f, cls._filClass):
            return True

    def GetFilter(self):
        return self._filClass(**self.getParameters())

    def parseFromFilter(self, f):
        gui = type(self)(self.dim)
        gui.setParameters(**f.getParameters())
        return gui

    def setParameters(self, **kwargs):
        raise NotImplementedError("Method setParameters should be implemented.")

    def getParameters(self):
        raise NotImplementedError("Method getParameters should be implemented.")


# interface for setting group GUI


class FilterGroupSetting(QWidget):
    filterChanged = pyqtSignal(QWidget)

    def __init__(self, dimension=2, layout=None):
        super().__init__()
        self.dim = dimension
        self._filters = self._filterList()

        self._combo = QComboBox()
        for f in self._filters.keys():
            self._combo.addItem(f, f)
        self._combo.currentTextChanged.connect(self._update)
        vlayout = QVBoxLayout()
        vlayout.addWidget(QLabel('Type'))
        vlayout.addWidget(self._combo)
        self.setLayout(vlayout)
        self._layout = layout
        self._layout.addWidget(self)
        self._childGroup = None
        self._update(self._combo.currentText())

    def _initControlLayout(self):
        return None

    @classmethod
    def _filterList(cls):
        return filterGroups

    def _update(self, text=None):
        if text is None:
            text = self._combo.currentText()
        if text in self._filters:
            self._removeChildGroup()
            if issubclass(self._filters[text], FilterGroupSetting):
                self.filter = self._filters[text](self.dim, layout=self._layout)
                self._addGroup(self.filter)
            else:
                self.filter = self._filters[text](self.dim)
                self.filterChanged.emit(self.filter)

    def _addGroup(self, g):
        self._childGroup = g
        g.filterChanged.connect(self.filterChanged)
        self._layout.addWidget(g)
        g._update()

    def _removeChildGroup(self):
        if self._childGroup is not None:
            self._childGroup._removeChildGroup()
            self._childGroup.filterChanged.disconnect(self.filterChanged)
            self._layout.removeWidget(self._childGroup)
            self._childGroup.deleteLater()
            self._childGroup = None

    @classmethod
    def _havingFilter(cls, f):
        for key, s in cls._filterList().items():
            if s._havingFilter(f) is not None:
                return key

    def parseFromFilter(self, f):
        name = self._havingFilter(f)
        if name is not None:
            self._combo.setCurrentIndex(self._combo.findData(name))
        return self.filter.parseFromFilter(f)

    def setDimension(self, dimension):
        self.dim = dimension


class _PreFilterSetting(QWidget):
    filterAdded = pyqtSignal(QWidget)
    filterDeleted = pyqtSignal(QWidget)
    filterMoved = pyqtSignal(QWidget, str)
    filterInserted = pyqtSignal(QWidget, str)

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__()
        h1 = QHBoxLayout()
        self.root = _RootSetting(dimension, h1)
        self.root.filterChanged.connect(self._filt)
        self._layout = QVBoxLayout()
        self._layout.addLayout(h1)
        self.setLayout(self._layout)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._contextMenu)
        self._child = None

    def _filt(self, widget):
        if self._child is not None:
            self._layout.removeWidget(self._child)
            self._child.deleteLater()
            self._child = None
        self._layout.addWidget(widget)
        self._child = widget
        self.filterAdded.emit(self)

    def GetFilter(self):
        if self._child is not None:
            return self._child.GetFilter()

    def SetFilter(self, filt):
        obj = self.root.parseFromFilter(filt)
        self._filt(obj)

    def clear(self, dimension=2):
        self.root._combo.setCurrentIndex(0)
        self.root.setDimension(dimension)

    def _contextMenu(self, point):
        menu = QMenu(self)
        delete = QAction('Delete', triggered=lambda: self.filterDeleted.emit(self))
        up = QAction('Move to up', triggered=lambda: self.filterMoved.emit(self, "up"))
        down = QAction('Move to down', triggered=lambda: self.filterMoved.emit(self, "down"))
        insup = QAction('Insert filter (up)', triggered=lambda: self.filterInserted.emit(self, "up"))
        insdown = QAction('Insert filter (down)', triggered=lambda: self.filterInserted.emit(self, "down"))
        for item in [up, down, insup, insdown, delete]:
            menu.addAction(item)
        menu.exec_(self.mapToGlobal(point))


class _RootSetting(FilterGroupSetting):
    pass


class FiltersGUI(QWidget):
    def __init__(self, dimension=2, regionLoader=None):
        super().__init__()
        self.loader = regionLoader
        self.dim = dimension
        self.__initLayout()

    def GetFilters(self):
        res = []
        for t in self.__tabs:
            res.extend(t.GetFilters().getFilters())
        return Filters(res)

    def __initLayout(self):
        self._tab = QTabWidget()
        self.__tabs = [_SubFiltersGUI(self.dim, self.loader)]
        self.__preIndex = 0
        self._tab.addTab(self.__tabs[0], "d = " + str(self.dim))
        self._tab.addTab(QWidget(), "+")
        self._tab.currentChanged.connect(self.__addTab)
        self._tab.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self._tab.tabBar().customContextMenuRequested.connect(self._tabContext)

        save = QPushButton("Save", clicked=self._save)
        load = QPushButton("Load", clicked=self._load)
        clear = QPushButton("Clear", clicked=self.clear)
        exp = QPushButton("Export", clicked=self._export)
        imp = QPushButton("Import", clicked=self._import)
        hbox2 = QHBoxLayout()
        hbox2.addWidget(save)
        hbox2.addWidget(load)
        hbox2.addWidget(exp)
        hbox2.addWidget(imp)
        hbox2.addWidget(clear)

        vbox = QVBoxLayout()
        vbox.addWidget(self._tab)
        vbox.addLayout(hbox2)
        self.setLayout(vbox)

    def __addTab(self, index):
        if index != len(self.__tabs):
            self.__preIndex = index
            return
        dim = self.dim + int(np.sum([f.getRelativeDimension() for f in self.GetFilters().getFilters()]))
        self.__insertNewTab(dim)
        self.__preIndex = index
        self._tab.setCurrentIndex(self.__preIndex)

    def __insertNewTab(self, dim):
        w = _SubFiltersGUI(dim, self.loader)
        self.__tabs.append(w)
        self._tab.insertTab(len(self.__tabs) - 1, w, "d = " + str(dim))

    def _tabContext(self, point):
        menu = QMenu(self)
        delete = QAction('Delete tab', triggered=self._delete)
        clear = QAction('Clear tab', triggered=lambda: self.clear(self.__preIndex))
        change = QAction('Change dimension of tab', triggered=self._setDim)
        exp = QAction('Export filter in tab', triggered=lambda: self._export(self.__preIndex))
        imp = QAction('Import filter to tab', triggered=lambda: self._import(self.__preIndex))
        save = QAction('Save filter in tab', triggered=lambda: self._save(self.__preIndex))
        load = QAction('Load filter to tab', triggered=lambda: self._load(self.__preIndex))
        for item in [save, load, exp, imp, change, clear, delete]:
            menu.addAction(item)
        menu.exec_(self.mapToGlobal(point))

    def _setDim(self):
        dim, ok = QInputDialog().getInt(self, "Enter New dimension", "Dimension:")
        if ok:
            self.setDimension(dim, self.__preIndex)

    def setDimension(self, dimension, index=0):
        self.__tabs[index].setDimension(dimension)
        self._tab.setTabText(index, "d = " + str(dimension))
        self.dim = dimension

    def clear(self, index=False):
        if index is False:
            while len(self.__tabs) > 1:
                self.__preIndex = 1
                self._delete()
            self.__tabs[0].clear()
        else:
            self.__tabs[index].clear()

    def _delete(self):
        tab = self.__preIndex
        if tab == 0:
            return
        self._tab.removeTab(tab)
        self.__tabs.pop(tab)
        self.__preIndex = tab - 1
        self._tab.setCurrentIndex(tab - 1)

    def _save(self, index=False):
        self.saveAs(".lys/quickFilter.fil", index)

    def _load(self, index=False):
        self.loadFrom(".lys/quickFilter.fil", index)

    def _export(self, index=-1):
        d = FilterExportDialog(self)
        ok = d.exec_()
        if ok:
            path = d.getExportPath()
            self.saveAs(path, index)

    def _import(self, index=-1):
        d = FilterImportDialog(self)
        ok = d.exec_()
        if ok:
            path = d.getImportPath()
            self.loadFrom(path, index)

    def saveAs(self, file, index=False):
        if index is False:
            filt = self.GetFilters()
        else:
            filt = self.__tabs[index].GetFilters()
        filt.dimension = self.dim
        filt.saveAsFile(file)
        print("Filter is saved to", file)

    def loadFrom(self, file, index=False):
        with open(file, 'r') as f:
            data = eval(f.read())
        self.loadFromString(data, index)

    def loadFromString(self, str, index=False):
        self.loadFilters(Filters.fromString(str), index)

    def loadFilters(self, filt, index=False):
        if index is False:
            self.clear()
            fs = filt.getFilters()
            res, tmp = [], []
            dim = self.dim
            for f in fs:
                tmp.append(f)
                if f.getRelativeDimension() != 0 and f != fs[len(fs) - 1]:
                    dim += f.getRelativeDimension()
                    self.__insertNewTab(dim)
                    res.append(tmp)
                    tmp = []
            res.append(tmp)
            for tab, fil in zip(self.__tabs, res):
                tab.SetFilters(Filters(fil))
        else:
            self.__tabs[index].SetFilters(filt)


class _SubFiltersGUI(QScrollArea):
    def __init__(self, dimension=2, regionLoader=None):
        super().__init__()
        self._flist = []
        self.loader = regionLoader
        self.dim = dimension
        self.__initLayout()

    def setDimension(self, dimension):
        if self.dim != dimension:
            self.dim = dimension
            self.clear()

    def clear(self):
        while(len(self._flist) > 1):
            self._delete(self._flist[0])
        self._flist[0].clear(dimension=self.dim)

    def GetFilters(self):
        res = []
        for f in self._flist:
            filt = f.GetFilter()
            if filt is not None:
                res.append(filt)
        return Filters(res)

    def SetFilters(self, filt):
        self.clear()
        for f in filt.getFilters():
            self._flist[len(self._flist) - 1].SetFilter(f)

    def __initLayout(self):
        self._layout = QVBoxLayout()
        self._layout.addStretch()
        self._addFirst()
        inner = QWidget()
        inner.setLayout(self._layout)
        self.setWidgetResizable(True)
        self.setWidget(inner)

    def __makeNewItem(self):
        item = _PreFilterSetting(self, self.dim, self.loader)
        item.filterAdded.connect(self._add)
        item.filterDeleted.connect(self._delete)
        item.filterMoved.connect(self._move)
        item.filterInserted.connect(self._insert)
        return item

    def _addFirst(self):
        first = self.__makeNewItem()
        self._flist.append(first)
        self._layout.insertWidget(0, first)

    def _add(self, item):
        if self._flist[len(self._flist) - 1] == item:
            newitem = self.__makeNewItem()
            self._layout.insertWidget(self._layout.count() - 1, newitem)
            self._flist.append(newitem)

    def _delete(self, item, force=False):
        if self._layout.indexOf(item) != len(self._flist) - 1 or force:
            self._layout.removeWidget(item)
            item.deleteLater()
            self._flist.remove(item)

    def _move(self, item, direction):
        index = self._layout.indexOf(item)
        if index == 0 and direction == "up":
            return
        if index == len(self._flist) - 2 and direction == "down":
            return
        self._layout.removeWidget(item)
        self._flist.remove(item)
        if direction == "up":
            pos = index - 1
        else:
            pos = index + 1
        self._layout.insertWidget(pos, item)
        self._flist.insert(pos, item)

    def _insert(self, item, direction):
        index = self._layout.indexOf(item)
        if index >= len(self._flist) - 2 and direction == "down":
            return
        if direction == "up":
            pos = index
        else:
            pos = index + 1
        newitem = self.__makeNewItem()
        self._layout.insertWidget(pos, newitem)
        self._flist.insert(pos, newitem)


class FiltersDialog(LysSubWindow):
    applied = pyqtSignal(object)

    def __init__(self, dim):
        super().__init__()
        self.filters = FiltersGUI(dim)

        self.ok = QPushButton("O K", clicked=self._ok)
        self.cancel = QPushButton("CANCEL", clicked=self._cancel)
        self.apply = QPushButton("Apply", clicked=self._apply)
        h1 = QHBoxLayout()
        h1.addWidget(self.ok)
        h1.addWidget(self.cancel)
        h1.addWidget(self.apply)

        layout = QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(h1)
        w = QWidget()
        w.setLayout(layout)
        self.setWidget(w)
        self.resize(500, 500)

    def _ok(self):
        self.ok = True
        self.applied.emit(self.filters.GetFilters())
        self.close()

    def _cancel(self):
        self.ok = False
        self.close()

    def _apply(self):
        self.applied.emit(self.filters.GetFilters())

    def setFilter(self, filt):
        self.filters.loadFilters(filt)


class _DeleteSetting(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)

    @classmethod
    def _havingFilter(cls, f):
        return None

    def getFilter(self):
        return None

    def getRelativeDimension(self):
        return 0


filterGroups[''] = _DeleteSetting
