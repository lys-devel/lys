from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class FilterSettingBase(QWidget):
    def __init__(self, parent, dimension=2, loader=None):
        super().__init__(None)
        self.dim = dimension
        self.loader = loader


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
