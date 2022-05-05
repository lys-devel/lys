import inspect
import itertools
import numpy as np
from PyQt5.QtWidgets import QAbstractItemView, QVBoxLayout, QWidget, QComboBox, QPushButton, QTreeView, QHBoxLayout, QCheckBox, QMenu, QDialog, QMessageBox
from PyQt5.QtGui import QCursor, QStandardItem, QStandardItemModel
from PyQt5.QtCore import pyqtSignal, Qt, QObject

from lys import Wave
from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference
from .Functions import functions
from .Fitting import fit, sumFunction


class _ResultController(QObject):
    stateChanged = pyqtSignal(bool)

    def __init__(self, canvas, line, info):
        super().__init__()
        self._canvas = canvas
        self._state = False
        self._line = line
        self._info = info
        self._info.updated.connect(self._update)
        self._fitted = None
        self._obj = None

    def _update(self):
        if self._state:
            f = self._info.fitFunction
            if f is None:
                self._remove()
                return False
            p = self._info.fitParameters
            x = self._line.getWave().x
            if self._fitted is None:
                self._fitted = Wave(f(x, *p), x, name=self._line.getWave().name + "_fit")
            else:
                self._fitted.data = f(x, *p)
                self._fitted.x = x
            if self._obj is None:
                self._obj = self._canvas.Append(self._fitted, offset=self._line.getOffset())
        else:
            self._remove()

    def _remove(self):
        if self._obj is not None:
            self._canvas.Remove(self._obj)
            self._obj = None

    def set(self, show):
        self._state = show
        self._update()

    @property
    def state(self):
        return self._state


class _FittingInfo(QObject):
    functionAdded = pyqtSignal(object)
    functionRemoved = pyqtSignal(object)
    updated = pyqtSignal()

    def __init__(self, wave):
        super().__init__()
        self._wave = wave
        self._funcs = []

    @property
    def name(self):
        return self._wave.name

    @property
    def functions(self):
        return self._funcs

    def addFunction(self, name):
        item = _FuncInfo(name)
        item.updated.connect(self.updated)
        self._funcs.append(item)
        self.functionAdded.emit(item)
        self.updated.emit()

    def removeFunction(self, index):
        del self._funcs[index]
        self.functionRemoved.emit(index)
        self.updated.emit()

    def fit(self, parent):
        guess = self.fitParameters
        bounds = np.array(list(itertools.chain(*[fi.range for fi in self._funcs])))
        for g, b in zip(guess, bounds):
            if g < b[0] or g > b[1] or b[0] > b[1]:
                QMessageBox.warning(parent, "Error", "Fit error: all fitting parameters should between minimum and maximum.")
                return
        res, sig = fit(self.fitFunction, self._wave.x, self._wave.data, guess=guess, bounds=bounds.T)
        n = 0
        for fi in self._funcs:
            m = len(fi.parameters)
            fi.setValue(res[n:n + m])
            n = n + m

    @property
    def fitFunction(self):
        if len(self._funcs) == 0:
            return None
        return sumFunction([fi.function for fi in self._funcs])

    @property
    def fitParameters(self):
        return np.array(list(itertools.chain(*[fi.value for fi in self._funcs])))


class _FuncInfo(QObject):
    updated = pyqtSignal()

    def __init__(self, name):
        super().__init__()
        self._name = name
        param = inspect.signature(functions[name]).parameters
        self._params = [_ParamInfo(n) for n in list(param.keys())[1:]]
        for p in self._params:
            p.stateChanged.connect(self.updated)

    def setValue(self, value):
        for p, v in zip(self.parameters, value):
            p.setValue(v)

    @property
    def name(self):
        return self._name

    @property
    def parameters(self):
        return self._params

    @property
    def function(self):
        return functions[self._name]

    @property
    def value(self):
        return [p.value for p in self.parameters]

    @property
    def range(self):
        res = []
        for p in self.parameters:
            if p.enabled:
                b = list(p.range)
                min_enabled, max_enabled = p.minMaxEnabled
                if not min_enabled:
                    b[0] = -np.inf
                if not max_enabled:
                    b[1] = np.inf
                res.append(tuple(b))
            else:
                res.append((p.value, p.value))
        return res


class _ParamInfo(QObject):
    stateChanged = pyqtSignal(object)

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._value = 0
        self._range = [0, 1]
        self._use = True
        self._min, self._max = False, False

    @property
    def name(self):
        return self._name

    def setValue(self, value):
        self._value = value
        self.stateChanged.emit(self)

    @property
    def value(self):
        return self._value

    def setEnabled(self, b):
        self._use = b
        self.stateChanged.emit(self)

    @property
    def enabled(self):
        return self._use

    def setRange(self, min=None, max=None):
        if min is not None:
            self._range[0] = min
        if max is not None:
            self._range[1] = max
        self.stateChanged.emit(self)

    @property
    def range(self):
        return tuple(self._range)

    def setMinMaxEnabled(self, min, max):
        self._min = min
        self._max = max

    @property
    def minMaxEnabled(self):
        return self._min, self._max


class FittingWidget(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._items = [_FittingInfo(line.getWave()) for line in canvas.getLines()]
        self._ctrls = [_ResultController(canvas, line, item) for line, item in zip(canvas.getLines(), self._items)]
        self.__initlayout()
        self.__targetChanged(0, init=True)

    def __initlayout(self):
        self._tree = FittingTree()
        self._target = QComboBox()
        self._target.addItems([item.name for item in self._items])
        self._target.currentIndexChanged.connect(self.__targetChanged)
        self._append = QCheckBox("Append result", stateChanged=self.__append)

        self._exec = QPushButton('Fit', clicked=lambda: self._currentItem.fit(self))
        #self._expo = QPushButton('Append Result', clicked=self.__export)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(self._exec)
        # hbox3.addWidget(self._expo)

        vbox1 = QVBoxLayout()
        vbox1.addWidget(self._target)
        vbox1.addWidget(self._tree)
        vbox1.addWidget(self._append)
        vbox1.addLayout(hbox3)
        self.setLayout(vbox1)
        self.adjustSize()
        self.updateGeometry()
        self.show()

    @avoidCircularReference
    def __targetChanged(self, i, init=False):
        if len(self._items) > 0:
            self._tree.set(self._items[i])
            if not init:
                self._old_ctrl.stateChanged.disconnect(self._append.setChecked)
            self._old_ctrl = self._ctrls[i]
            self._append.setChecked(self._ctrls[i].state)
            self._ctrls[i].stateChanged.connect(self._append.setChecked)

    def __append(self, state):
        self._ctrls[self._target.currentIndex()].set(state)

    @property
    def _currentItem(self):
        return self._items[self._target.currentIndex()]

    def __export(self):
        pass


class FittingTree(QTreeView):
    def __init__(self):
        super().__init__()
        self._obj = None
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._model = QStandardItemModel(0, 2)
        self._model.setHeaderData(0, Qt.Horizontal, 'Name')
        self._model.setHeaderData(1, Qt.Horizontal, 'Value')
        self.setModel(self._model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)
        self._funcs = []

    def set(self, obj):
        if self._obj is not None:
            self._obj.functionAdded.disconnect(self.__addItem)
            self._obj.functionRemoved.disconnect(self._model.removeRow)
        while len(self._funcs) != 0:
            self._model.removeRow(0)
            del self._funcs[0]
        self._obj = obj
        self._obj.functionAdded.connect(self.__addItem)
        self._obj.functionRemoved.connect(self._model.removeRow)
        for f in obj.functions:
            self.__addItem(f)

    def _buildContextMenu(self, qPoint):
        menu = QMenu(self)
        for label in ['Add Function', 'Remove Function', 'Clear']:
            menu.addAction(label)
        action = menu.exec_(QCursor.pos())
        if action is None:
            return
        if action.text() == 'Add Function':
            self.__addFunction()
        if action.text() == 'Remove Function':
            self.__removeFunction()
        if action.text() == 'Clear':
            self.clear()

    def __addFunction(self):
        dialog = _FuncSelectDialog(self)
        result = dialog.exec_()
        if result:
            self._obj.addFunction(dialog.getFunctionName())

    def __addItem(self, funcItem):
        self._funcs.append(_SingleFuncGUI(funcItem, self, self._model))

    def __removeFunction(self):
        for i in self.selectedIndexes():
            for j in range(self._model.rowCount() - 1, -1, -1):
                if self._model.item(j, 0).index() == i:
                    self._obj.removeFunction(j)

    def clear(self):
        while len(self._obj.functions) != 0:
            self._obj.removeFunction(0)


class _FuncSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        self.combo.addItems(functions.keys())

        h1 = QHBoxLayout()
        h1.addWidget(QPushButton('O K', clicked=self.accept))
        h1.addWidget(QPushButton('CALCEL', clicked=self.reject))

        v1 = QVBoxLayout()
        v1.addWidget(self.combo)
        v1.addLayout(h1)
        self.setLayout(v1)

    def getFunctionName(self):
        return self.combo.currentText()


class _SingleFuncGUI(QStandardItem):
    def __init__(self, obj, tree, model):
        super().__init__(obj.name)
        self._obj = obj
        model.appendRow(self)
        self._params = [_SingleParamGUI(p, self, tree) for p in obj.parameters]


class _checkableSpinBoxItem(QObject):
    valueChanged = pyqtSignal(float)
    stateChanged = pyqtSignal(bool)

    def __init__(self, name, tree, parent):
        super().__init__()
        self._item = QStandardItem(name)
        self._item.setCheckable(True)

        self._value = ScientificSpinBox()
        self._value.valueChanged.connect(self.valueChanged)

        item2 = QStandardItem()
        parent.appendRow([self._item, item2])
        tree.setIndexWidget(item2.index(), self._value)

        self._model = tree.model()
        self._model.itemChanged.connect(self._itemChanged)

    def setValue(self, value):
        self._value.setValue(value)

    @property
    def value(self):
        return self._value.value()

    def setChecked(self, state):
        if state:
            self._item.setCheckState(Qt.Checked)
        else:
            self._item.setCheckState(Qt.Unchecked)

    @property
    def checked(self):
        return self.item.checkState() == Qt.Checked

    def _itemChanged(self, item):
        if item == self._item:
            self.stateChanged.emit(item.checkState() == Qt.Checked)

    @property
    def item(self):
        return self._item


class _SingleParamGUI(QObject):
    updated = pyqtSignal()

    def __init__(self, obj, parent, tree):
        super().__init__()
        self._obj = obj
        self.__initlayout(obj, parent, tree)
        obj.stateChanged.connect(self._update)
        self._update(obj)

    def __initlayout(self, obj, parent, tree):
        self._value = _checkableSpinBoxItem(obj.name, tree, parent)
        self._value.valueChanged.connect(self._setValue)
        self._value.stateChanged.connect(self._setState)

        self._min, self._max = _checkableSpinBoxItem('min', tree, self._value.item), _checkableSpinBoxItem('max', tree, self._value.item)
        self._min.valueChanged.connect(self._setRange)
        self._max.valueChanged.connect(self._setRange)
        self._min.stateChanged.connect(self._setMinMaxState)
        self._max.stateChanged.connect(self._setMinMaxState)

    @avoidCircularReference
    def _setValue(self, value):
        self._obj.setValue(value)

    @avoidCircularReference
    def _setState(self, state):
        self._obj.setEnabled(state)

    @avoidCircularReference
    def _setRange(self, *args, **kwargs):
        self._obj.setRange(self._min.value, self._max.value)

    @avoidCircularReference
    def _setMinMaxState(self, state):
        self._obj.setMinMaxEnabled(self._min.checked, self._max.checked)

    @avoidCircularReference
    def _update(self, obj):
        self._value.setValue(obj.value)
        self._value.setChecked(obj.enabled)

        min, max = obj.range
        self._min.setValue(min)
        self._max.setValue(max)

        min, max = obj.minMaxEnabled
        self._min.setChecked(min)
        self._max.setChecked(max)
