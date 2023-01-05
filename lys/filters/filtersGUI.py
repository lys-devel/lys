import numpy as np

from lys import filters
from lys.Qt import QtCore, QtWidgets
from lys.widgets import LysSubWindow

from .FilterManager import _filterGroups


def filterGUI(filterClass):
    def _filterGUI(cls):
        cls._filClass = filterClass
        return cls
    return _filterGUI


class FilterSettingBase(QtWidgets.QWidget):
    dimensionChanged = QtCore.pyqtSignal()

    def __init__(self, dimension):
        super().__init__()
        self.dim = dimension

    def GetFilter(self):
        return self._filClass(**self.getParameters())

    @classmethod
    def getFilterClass(cls):
        if hasattr(cls, "_filClass"):
            return cls._filClass

    def getDimension(self):
        return self.dim

    def setParameters(self, **kwargs):
        raise NotImplementedError("Method setParameters should be implemented.")

    def getParameters(self):
        raise NotImplementedError("Method getParameters should be implemented.")


class FiltersGUI(QtWidgets.QTreeWidget):
    def __init__(self, dimension=2, parent=None):
        super().__init__(parent=parent)
        self.dim = dimension
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context)
        self.setHeaderLabel("Filters: Right click to edit")

    def setDimension(self, dimension):
        self.dim = dimension
        self._update()

    def _context(self, point):
        menu = QtWidgets.QMenu(self)
        menus = []
        menus.append(QtWidgets.QAction('Add a filter', triggered=lambda: self.__add()))
        if self.__currentIndex() != -1:
            menus.append(QtWidgets.QAction('Insert a filter above', triggered=lambda: self.__add(self.__currentIndex())))
            menus.append(QtWidgets.QAction('Insert a filter below', triggered=lambda: self.__add(self.__currentIndex() + 1)))
            menus.append("sep")
            menus.append(QtWidgets.QAction('Move up', triggered=lambda: self.__move(self.__currentIndex(), "up")))
            menus.append(QtWidgets.QAction('Move down', triggered=lambda: self.__move(self.__currentIndex(), "down")))
        menus.append("sep")
        if self.topLevelItemCount() != 0:
            menus.append(QtWidgets.QAction('Copy filters', triggered=self.__copy))
        menus.append(QtWidgets.QAction('Paste filters', triggered=self.__paste))
        menus.append("sep")
        if self.topLevelItemCount() != 0:
            menus.append(QtWidgets.QAction('Export to file', triggered=self.__export))
        menus.append(QtWidgets.QAction('Import from file', triggered=self.__import))
        menus.append("sep")
        if self.__currentIndex() != -1:
            menus.append(QtWidgets.QAction('Delete', triggered=self.__delete))
        if self.topLevelItemCount() != 0:
            menus.append(QtWidgets.QAction('Clear', triggered=self.clear))

        # add actions and separators
        for item in menus:
            if item == "sep":
                menu.addSeparator()
            else:
                menu.addAction(item)
        menu.exec_(self.mapToGlobal(point))

    def __currentIndex(self):
        item = self.currentItem()
        if item is None:
            return -1
        if item.parent() is not None:
            item = item.parent()
        return self.indexOfTopLevelItem(item)

    def __add(self, index=-1):
        d = _FilterSelectionDialog(self)
        ok = d.exec_()
        if ok:
            self.__addItem(d.getFilterClass(), index=index)
            self._update()

    def __addItem(self, filter, index=-1, params=None):
        w = filters.getFilterGui(filter)(self.__getDimension(index))
        if params is not None:
            w.setParameters(**params)
        w.dimensionChanged.connect(self._update)
        item = QtWidgets.QTreeWidgetItem([filters.getFilterGuiName(filter)])
        child = QtWidgets.QTreeWidgetItem([""])
        item.addChild(child)
        self.setItemWidget(child, 0, w)
        if index == -1:
            self.addTopLevelItem(item)
        else:
            self.insertTopLevelItem(index, item)

    def __getDimension(self, index=-1):
        dims = [f.getRelativeDimension() for f in self.GetFilters().getFilters()]
        if index == -1:
            return self.dim + int(np.sum(dims))
        else:
            return self.dim + int(np.sum(dims[:index]))

    def __delete(self):
        for item in self.selectedItems():
            if item.parent() is not None:
                item = item.parent()
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))
        self._update()

    def __move(self, index, type="up"):
        parent = self.topLevelItem(index)
        wid = self.itemWidget(parent.child(0), 0)
        self.takeTopLevelItem(index)
        if type == "up":
            self.__addItem(wid._filClass, index - 1, wid.getParameters())
        else:
            self.__addItem(wid._filClass, index - 1, wid.getParameters())

    def clear(self):
        while self.topLevelItemCount() != 0:
            self.takeTopLevelItem(0)

    def _update(self):
        dim = int(self.dim)
        for i in range(self.topLevelItemCount()):
            parent = self.topLevelItem(i)
            child = parent.child(0)
            w = self.itemWidget(child, 0)
            if dim != w.getDimension():
                wid = filters.getFilterGui(parent.text(0))(dim)
                wid.setParameters(**w.getParameters())
                self.removeItemWidget(child, 0)
                self.setItemWidget(child, 0, wid)
                wid.dimensionChanged.connect(self._update)
            dim += w.GetFilter().getRelativeDimension()

    def GetFilters(self):
        res = []
        for i in range(self.topLevelItemCount()):
            w = self.itemWidget(self.topLevelItem(i).child(0), 0)
            res.append(w.GetFilter())
        return filters.Filters(res)

    def setFilters(self, filt):
        self.clear()
        for f in filt.getFilters():
            self.__addItem(f, params=f.getParameters())
        self._update()

    def __copy(self):
        filt = self.GetFilters()
        filt.dimension = self.dim
        filt.saveAsFile(".lys/quickFilter.fil")

    def __paste(self):
        filt = filters.fromFile(".lys/quickFilter.fil")
        self.setFilters(filt)

    def __export(self):
        path, type = QtWidgets.QFileDialog.getSaveFileName(self, "Save Filters", filter="Filter (*.fil);;All files (*.*)")
        if len(path) != 0:
            if not path.endswith(".fil"):
                path = path + ".fil"
            filt = self.GetFilters()
            filt.dimension = self.dim
            filt.saveAsFile(path)

    def __import(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Filters', filter="Filter (*.fil);;All files (*.*)")
        if fname[0]:
            filt = filters.fromFile(fname[0])
            self.setFilters(filt)


class _FilterSelectionDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select filter")
        self.__initlayout()
        self.show()

    def __initlayout(self):
        self.sel = _FilterSelectionWidget(self)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton("O K", clicked=self.__ok))
        h1.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject))

        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(self.sel)
        v1.addLayout(h1)
        self.setLayout(v1)

    def __ok(self):
        self._filter = self.sel.getFilterClass()
        if self._filter is None:
            msgBox = QtWidgets.QMessageBox(parent=self)
            msgBox.setText("Please select filter.")
            msgBox.addButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec_()
        else:
            self.accept()

    def getFilterClass(self):
        return self._filter


class _FilterSelectionWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.__initItems()
        self.setHeaderLabel("List of Filters")

    def __initItems(self):
        for key, value in _filterGroups.items():
            if key == "":
                continue
            item = QtWidgets.QTreeWidgetItem([key])
            if isinstance(value, dict):
                for key2 in value.keys():
                    item2 = QtWidgets.QTreeWidgetItem([key2])
                    item.addChild(item2)
            self.addTopLevelItem(item)

    def getFilterClass(self):
        item = self.currentItem()
        if item.childCount() != 0:
            return None
        if item.parent() is not None:
            return _filterGroups[item.parent().text(0)][item.text(0)]._filClass
        else:
            return _filterGroups[item.text(0)]._filClass


class FiltersDialog(LysSubWindow):
    applied = QtCore.pyqtSignal(object)

    def __init__(self, dim):
        super().__init__()
        self.filters = FiltersGUI(dim, parent=self)

        self.ok = QtWidgets.QPushButton("O K", clicked=self._ok)
        self.cancel = QtWidgets.QPushButton("CANCEL", clicked=self._cancel)
        self.apply = QtWidgets.QPushButton("Apply", clicked=self._apply)
        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self.ok)
        h1.addWidget(self.cancel)
        h1.addWidget(self.apply)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(h1)
        w = QtWidgets.QWidget()
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
        self.filters.setFilters(filt)
