import inspect
import itertools
import numpy as np
from PyQt5.QtWidgets import QAction, QLineEdit, QAbstractItemView, QVBoxLayout, QWidget, QComboBox, QPushButton, QTreeView, QHBoxLayout, QCheckBox, QMenu, QDialog, QMessageBox, QFileDialog, QLabel, QGridLayout
from PyQt5.QtGui import QCursor, QStandardItem, QStandardItemModel
from PyQt5.QtCore import pyqtSignal, Qt, QObject

from lys import Wave, display
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

    def addFunction(self, func):
        if isinstance(func, dict):
            item = _FuncInfo.loadFromDictionary(func)
        else:
            item = _FuncInfo(func)
        item.updated.connect(self.updated)
        self._funcs.append(item)
        self.functionAdded.emit(item)
        self.updated.emit()

    def removeFunction(self, index):
        del self._funcs[index]
        self.functionRemoved.emit(index)
        self.updated.emit()

    def clear(self):
        while len(self.functions) != 0:
            self.removeFunction(0)

    def fit(self, parent, range, xdata=None):
        guess = self.fitParameters
        bounds = np.array(list(itertools.chain(*[fi.range for fi in self._funcs])))
        for g, b in zip(guess, bounds):
            if g < b[0] or g > b[1] or b[0] > b[1]:
                QMessageBox.warning(parent, "Error", "Fit error: all fitting parameters should between minimum and maximum.")
                return False
        data, x = self.__loadData(range, xdata)
        res, sig = fit(self.fitFunction, x, data, guess=guess, bounds=bounds.T)
        n = 0
        for fi in self._funcs:
            m = len(fi.parameters)
            fi.setValue(res[n:n + m])
            n = n + m
        return True

    def __loadData(self, range, xdata):
        axis = self._wave.x
        range = list(range)
        if range[0] is None:
            range[0] = np.min(axis) - 1
        if range[1] is None:
            range[1] = np.max(axis) + 1
        p = self._wave.posToPoint(range, axis=0)
        if xdata is None:
            x = self._wave.x
        else:
            x = self._wave.note[xdata]
        return self._wave.data[p[0]:p[1]], x[p[0]:p[1]]

    def getParamValue(self, index_f, index_p):
        if len(self.functions) > index_f:
            f = self.functions[index_f]
            if len(f.value) > index_p:
                return f.value[index_p]

    def saveAsDictionary(self):
        return {"function_" + str(i): f.saveAsDictionary() for i, f in enumerate(self.functions)}

    def loadFromDictionary(self, dic):
        i = 0
        while "function_" + str(i) in dic:
            self.addFunction(dic["function_" + str(i)])
            i += 1

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

    def saveAsDictionary(self):
        d = {"param_" + str(i): p.saveAsDictionary() for i, p in enumerate(self.parameters)}
        d["name"] = self._name
        return d

    @classmethod
    def loadFromDictionary(cls, dic):
        obj = cls(dic["name"])
        for i, p in enumerate(obj.parameters):
            p.loadParameters(**dic["param_" + str(i)])
        return obj


class _ParamInfo(QObject):
    stateChanged = pyqtSignal(object)

    def __init__(self, name, value=1, range=(0, 1), enabled=True, minMaxEnabled=(False, False)):
        super().__init__()
        self._name = name
        self._value = value
        self._range = range
        self._use = enabled
        self._min, self._max = minMaxEnabled

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

    def saveAsDictionary(self):
        return {"name": self._name, "value": self.value, "range": self.range, "enabled": self.enabled, "minMaxEnabled": self.minMaxEnabled}

    def loadParameters(self, name, value, range, enabled, minMaxEnabled):
        self._name = name
        self._value = value
        self._range = range
        self._use = enabled
        self._min, self._max = minMaxEnabled


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
        self._tree.plotRequired.connect(self.__plot)
        self._target = QComboBox()
        self._target.addItems([item.name for item in self._items])
        self._target.currentIndexChanged.connect(self.__targetChanged)

        self._xdata = QComboBox()
        self._xdata.addItems(["x axis", "from Wave.note"])
        self._xdata.currentTextChanged.connect(self.__changeXAxis)
        self._keyLabel = QLabel("Key")
        self._keyText = QLineEdit()
        self._keyLabel.hide()
        self._keyText.hide()

        self._min = ScientificSpinBox()
        self._max = ScientificSpinBox()
        self._min.setEnabled(False)
        self._max.setEnabled(False)
        self._useMin = QCheckBox("min", stateChanged=self._min.setEnabled)
        self._useMax = QCheckBox("max", stateChanged=self._max.setEnabled)

        g = QGridLayout()
        g.addWidget(QLabel("Target"), 0, 0)
        g.addWidget(self._target, 0, 1, 1, 2)
        g.addWidget(QLabel("x data"), 1, 0)
        g.addWidget(self._xdata, 1, 1, 1, 2)
        g.addWidget(self._keyLabel, 2, 0)
        g.addWidget(self._keyText, 2, 1, 1, 2)
        g.addWidget(QLabel("Region"), 3, 0)
        g.addWidget(self._useMin, 3, 1)
        g.addWidget(self._useMax, 3, 2)
        g.addWidget(QPushButton("Load from Graph", clicked=self.__loadFromGraph), 4, 0)
        g.addWidget(self._min, 4, 1)
        g.addWidget(self._max, 4, 2)

        self._append = QCheckBox("Append result", stateChanged=self.__append)
        self._all = QCheckBox("Apply to all")

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self._append)
        hbox1.addWidget(self._all)

        self._exec = QPushButton('Fit', clicked=self.__fit)
        hbox3 = QHBoxLayout()
        hbox3.addWidget(self._exec)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(g)
        vbox1.addWidget(self._tree)
        vbox1.addLayout(hbox1)
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

    def __fit(self):
        if self._all.isChecked():
            msg = "This operation will delete all fitting results except displayed and then fit all data in the graph using displayed fitting function. Are your really want to proceed?"
            res = QMessageBox.information(self, "Warning", msg, QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                d = self._currentItem.saveAsDictionary()
                for item in self._items:
                    if item != self._currentItem:
                        item.clear()
                        item.loadFromDictionary(d)
                    res = item.fit(self, self.__loadRange(), self.__loadXAxis())
                    if not res:
                        return
            QMessageBox.information(self, "Information", "All fittings finished.", QMessageBox.Yes)
        else:
            self._currentItem.fit(self, self.__loadRange(), self.__loadXAxis())

    def __loadRange(self):
        r = [0, 0]
        if self._useMin.isChecked():
            r[0] = self._min.value()
        else:
            r[0] = None
        if self._useMax.isChecked():
            r[1] = self._max.value()
        else:
            r[1] = None
        return tuple(r)

    def __loadXAxis(self):
        if self._xdata.currentText() == "x axis":
            return None
        else:
            return self._keyText.text()

    def __append(self, state):
        if self._all.isChecked():
            for c in self._ctrls:
                c.set(state)
        else:
            self._ctrls[self._target.currentIndex()].set(state)

    def __changeXAxis(self, txt):
        self._keyLabel.setVisible(txt == "from Wave.note")
        self._keyText.setVisible(txt == "from Wave.note")

    def __loadFromGraph(self):
        if self.canvas.isRangeSelected():
            r = np.array(self.canvas.selectedRange()).T[0]
            self._min.setValue(min(*r))
            self._max.setValue(max(*r))
            self._useMin.setChecked(True)
            self._useMax.setChecked(True)
        else:
            QMessageBox.information(self, "Warning", "Please select region by dragging in the graph.")

    def __plot(self, f, p):
        res = []
        for item in self._items:
            tmp = item.getParamValue(f, p)
            if tmp is None:
                QMessageBox.information(self, "Warning", "All data should be fitted by the same function to plot parameter.")
                return
            res.append(tmp)
        display(res)

    @property
    def _currentItem(self):
        return self._items[self._target.currentIndex()]


class FittingTree(QTreeView):
    plotRequired = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._obj = None
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._model = QStandardItemModel(0, 2)
        self._model.setHeaderData(0, Qt.Horizontal, 'Name')
        self._model.setHeaderData(1, Qt.Horizontal, 'Value')
        self.setModel(self._model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)
        self._funcs = []
        self.__copied = None
        self.__allCopied = None

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
        isFunc = self.__currentItemIndex() is not None or len(self.selectedIndexes()) == 0
        menu = QMenu(self)
        if not isFunc:
            menu.addAction(QAction('Plot this parameter', self, triggered=self.__plot))
        menu.addAction(QAction('Add Function', self, triggered=self.__addFunction))
        if isFunc:
            menu.addAction(QAction('Remove Function', self, triggered=self.__removeFunction))
        menu.addAction(QAction('Clear', self, triggered=self.__clear))
        menu.addSeparator()
        if isFunc:
            menu.addAction(QAction('Copy Function', self, triggered=self.__copyFunction))
            menu.addAction(QAction('Paste Function', self, triggered=self.__pasteFunction))
        menu.addAction(QAction('Copy All Functions', self, triggered=lambda: self.__copyFunction(all=True)))
        menu.addAction(QAction('Paste All Functions', self, triggered=lambda: self.__pasteFunction(all=True)))
        menu.addSeparator()
        menu.addAction(QAction('Import from File', self, triggered=self.__import))
        menu.addAction(QAction('Export to File', self, triggered=self.__export))
        menu.exec_(QCursor.pos())

    def __currentItemIndex(self):
        for i in self.selectedIndexes():
            for j in range(self._model.rowCount() - 1, -1, -1):
                if self._model.item(j, 0).index() == i:
                    return j

    def __plot(self):
        p = self.selectedIndexes()[0].row()
        f = self.selectedIndexes()[0].parent().row()
        self.plotRequired.emit(f, p)

    def __addFunction(self):
        dialog = _FuncSelectDialog(self)
        result = dialog.exec_()
        if result:
            self._obj.addFunction(dialog.getFunctionName())

    def __addItem(self, funcItem):
        self._funcs.append(_SingleFuncGUI(funcItem, self, self._model))

    def __removeFunction(self):
        self._obj.removeFunction(self.__currentItemIndex())

    def __copyFunction(self, all=False):
        if all:
            self.__allCopied = self._obj.saveAsDictionary()
        else:
            self.__copied = self._obj.functions[self.__currentItemIndex()].saveAsDictionary()

    def __pasteFunction(self, all=False):
        if all:
            if self.__allCopied is None:
                return None
            self.__clear()
            self._obj.loadFromDictionary(self.__allCopied)
        else:
            if self.__copied is None:
                return
            self._obj.addFunction(self.__copied)

    def __export(self):
        path, type = QFileDialog.getSaveFileName(self, "Save fitting results", filter="Dictionary (*.dic);;All files (*.*)")
        if len(path) != 0:
            if not path.endswith(".dic"):
                path = path + ".dic"
            with open(path, "w") as f:
                f.write(str(self._obj.saveAsDictionary()))

    def __import(self):
        fname = QFileDialog.getOpenFileName(self, 'Load fitting', filter="Dictionary (*.dic);;All files (*.*)")
        if fname[0]:
            with open(fname[0], "r") as f:
                d = eval(f.read())
            self._obj.loadFromDictionary(d)

    def __clear(self):
        self._obj.clear()


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
