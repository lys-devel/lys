import collections
from .filters import *
import _pickle as cPickle

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ExtendAnalysis import *

filterGroups = collections.OrderedDict()


class FilterSettingBase(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)
        self.dim = dimension
        self.loader = loader


# interface for setting group GUI
class FilterGroupSetting(QWidget):
    filterChanged = pyqtSignal(QWidget)

    def __init__(self, parent, dimension=2, loader=None, layout=None):
        super().__init__()
        self.dim = dimension
        self.loader = loader
        self._filters = self._filterList()

        self._layout = layout
        self._combo = QComboBox()
        for f in self._filters.keys():
            self._combo.addItem(f, f)
        self._combo.currentTextChanged.connect(self._update)
        vlayout = QVBoxLayout()
        vlayout.addWidget(QLabel('Type'))
        vlayout.addWidget(self._combo)
        self.setLayout(vlayout)
        self._layout.addWidget(self)
        self._childGroup = None
        self._update(self._combo.currentText())

    @classmethod
    def _filterList(cls):
        return filterGroups

    def _update(self, text=None):
        if text is None:
            text = self._combo.currentText()
        if text in self._filters:
            self._removeChildGroup()
            if issubclass(self._filters[text], FilterGroupSetting):
                self.filter = self._filters[text](None, self.dim, loader=self.loader, layout=self._layout)
                self._addGroup(self.filter)
            else:
                self.filter = self._filters[text](None, self.dim, loader=self.loader)
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

    def __init__(self, parent, dimension=2, loader=None):
        super().__init__()
        h1 = QHBoxLayout()
        self.root = _RootSetting(self, dimension, loader, h1)
        self.root.filterChanged.connect(self._filt)
        self._layout = QVBoxLayout()
        self._layout.addLayout(h1)
        self.setLayout(self._layout)
        self._child = None

    def _filt(self, widget):
        if self._child is not None:
            self._layout.removeWidget(self._child)
            self._child.deleteLater()
            self._child = None
        if isinstance(widget, _DeleteSetting):
            self.filterDeleted.emit(self)
        else:
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


class _RootSetting(FilterGroupSetting):
    filterAdded = pyqtSignal(QWidget)
    filterDeleted = pyqtSignal(QWidget)
    @classmethod
    def _filterList(cls):
        return filterGroups


class FiltersGUI(QWidget):
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

    def __initLayout(self):
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        self._layout = QVBoxLayout()
        self._layout.addStretch()
        self._addFirst()
        inner = QWidget()
        inner.setLayout(self._layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        hbox.addWidget(scroll, 3)

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

        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

    def _addFirst(self):
        first = _PreFilterSetting(self, self.dim, self.loader)
        first.filterAdded.connect(self._add)
        first.filterDeleted.connect(self._delete)
        self._flist.append(first)
        self._layout.insertWidget(0, first)

    def _add(self, item):
        if self._flist[len(self._flist) - 1] == item:
            newitem = _PreFilterSetting(self, self.dim, self.loader)
            newitem.filterAdded.connect(self._add)
            newitem.filterDeleted.connect(self._delete)
            self._layout.insertWidget(self._layout.count() - 1, newitem)
            self._flist.append(newitem)

    def _delete(self, item, force=False):
        if len(self._flist) > 1 or force:
            self._layout.removeWidget(item)
            item.deleteLater()
            self._flist.remove(item)

    def _save(self):
        self.saveAs(".lys/quickFilter.fil")

    def _load(self):
        self.loadFrom(".lys/quickFilter.fil")

    def _export(self):
        fname = QFileDialog.getSaveFileName(self, 'Save Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
        if fname[0]:
            self.saveAs((fname[0] + ".fil").replace(".fil.fil", ".fil"))

    def _import(self):
        fname = QFileDialog.getOpenFileName(self, 'Open Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
        if fname[0]:
            self.loadFrom(fname[0])

    def saveAs(self, file):
        filt = self.GetFilters()
        s = String(file)
        s.data = str(filt)

    def loadFrom(self, file):
        s = String(file)
        self.loadFromString(s.data)

    def loadFromString(self, str):
        self.loadFilters(Filters.fromString(str))

    def loadFilters(self, filt):
        self.clear()
        for f in filt.getFilters():
            self._flist[len(self._flist) - 1].SetFilter(f)


class FiltersDialog(ExtendMdiSubWindow):
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


filterGroups[''] = _DeleteSetting
