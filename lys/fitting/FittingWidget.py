import numpy as np

from lys import display
from lys.Qt import QtWidgets, QtGui, QtCore
from lys.widgets import ScientificSpinBox
from lys.decorators import avoidCircularReference

from .Functions import functions
from .FittingCUI import FittingCUI


class _ResultController(QtCore.QObject):
    def __init__(self, canvas, cui, data):
        super().__init__()
        self._canvas = canvas
        self._cui = cui
        self._data = data
        self._state, self._obj, self._fitted = self.__initObj(canvas)
        self._cui.updated.connect(self._update)

    def __initObj(self, canvas):
        for line in canvas.getLines():
            w = line.getWave()
            if "lys_Fitting" in w.note:
                if w.note["lys_Fitting"]["fitted"] is False:
                    if w.note["lys_Fitting"]["id"] == self._cui.id:
                        return True, line, w
        return False, None, None

    def _update(self):
        if self._state:
            f = self._cui.fitFunction
            if f is None:
                self._remove()
                return False
            fitted = self._cui.fittedData()
            if self._fitted is None:
                self._fitted = fitted
            else:
                self._fitted.data = fitted.data
                self._fitted.x = fitted.x
            if self._obj is None:
                self._obj = self._canvas.Append(self._fitted, offset=self._data.getOffset())
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


class FittingWidget(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._items, lines = self.__loadItems()
        self._ctrls = [_ResultController(canvas, item, line) for item, line in zip(self._items, lines)]
        self.__initlayout()
        self.__targetChanged(0)

    def __loadItems(self):
        items, lines = [], []
        for line in self.canvas.getLines():
            wave = line.getWave()
            if "lys_Fitting" in wave.note:
                if wave.note["lys_Fitting"]["fitted"] is False:
                    continue
            items.append(FittingCUI(wave))
            lines.append(line)
        return items, lines

    def __initlayout(self):
        self._tree = FittingTree()
        self._tree.plotRequired.connect(self.__plot)
        self._target = QtWidgets.QComboBox()
        self._target.addItems([item.name for item in self._items])
        self._target.currentIndexChanged.connect(self.__targetChanged)

        hbox2 = QtWidgets.QHBoxLayout()
        hbox2.addWidget(QtWidgets.QLabel("Target"))
        hbox2.addWidget(self._target)

        self._dm = _DataAxisWidget(self.canvas)
        self._dm.axisChanged.connect(self.__axisChanged)

        self._append = QtWidgets.QCheckBox("Append result", stateChanged=self.__append)
        self._all = QtWidgets.QCheckBox("Apply to all")

        hbox1 = QtWidgets.QHBoxLayout()
        hbox1.addWidget(self._append)
        hbox1.addWidget(self._all)

        exec = QtWidgets.QPushButton('Fit', clicked=self.__fit)
        resi = QtWidgets.QPushButton('Residual sum', clicked=self.__resi)
        hbox3 = QtWidgets.QHBoxLayout()
        hbox3.addWidget(exec)
        hbox3.addWidget(resi)

        vbox1 = QtWidgets.QVBoxLayout()
        vbox1.addLayout(hbox2)
        vbox1.addWidget(self._dm)
        vbox1.addWidget(self._tree)
        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox3)
        self.setLayout(vbox1)
        self.adjustSize()
        self.updateGeometry()
        self.show()

    def __axisChanged(self, type, range):
        self._currentItem.setFittingRange(type, range)

    @avoidCircularReference
    def __targetChanged(self, i):
        if len(self._items) > 0:
            self._tree.set(self._items[i])
            self._append.setChecked(self._currentResult.state)
            self._dm.setRange(*self._currentItem.getFittingRange())

    def __resi(self):
        if self._all.isChecked():
            display([item.residualSum() for item in self._items])
        else:
            print("Residual sum:", self._currentItem.residualSum())

    def __fit(self):
        if self._all.isChecked():
            msg = "This operation will delete all fitting results except displayed and then fit all data in the graph using displayed fitting function. Are your really want to proceed?"
            res = QtWidgets.QMessageBox.information(self, "Warning", msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if res == QtWidgets.QMessageBox.Yes:
                d = self._currentItem.saveAsDictionary()
                for item in self._items:
                    if item != self._currentItem:
                        item.loadFromDictionary(d)
                    res, msg = item.fit()
                    if not res:
                        QtWidgets.QMessageBox.warning(self, "Error", msg)
                        return
                QtWidgets.QMessageBox.information(self, "Information", "All fittings finished.", QtWidgets.QMessageBox.Yes)
        else:
            res, msg = self._currentItem.fit()
            if res is False:
                QtWidgets.QMessageBox.warning(self, "Error", msg)

    def __append(self, state):
        if self._all.isChecked():
            for c in self._ctrls:
                c.set(state)
        else:
            self._ctrls[self._target.currentIndex()].set(state)

    def __plot(self, f, p):
        res = []
        for item in self._items:
            tmp = item.getParamValue(f, p)
            if tmp is None:
                QtWidgets.QMessageBox.information(self, "Warning", "All data should be fitted by the same function to plot parameter.")
                return
            res.append(tmp)
        display(res)

    @property
    def _currentItem(self):
        return self._items[self._target.currentIndex()]

    @property
    def _currentResult(self):
        return self._ctrls[self._target.currentIndex()]


class _DataAxisWidget(QtWidgets.QGroupBox):
    axisChanged = QtCore.pyqtSignal(object, tuple)

    def __init__(self, canvas):
        super().__init__("x axis")
        self.__initlayout()
        self.__type = None
        self.__range = (None, None)
        self._canvas = canvas

    def __initlayout(self):
        self._xdata = QtWidgets.QComboBox()
        self._xdata.addItems(["x axis", "from Wave.note"])
        self._xdata.currentTextChanged.connect(self.__changeXAxis)
        self._keyLabel = QtWidgets.QLabel("Key")
        self._keyText = QtWidgets.QLineEdit()
        self._keyText.textChanged.connect(self.__setXAxis)
        self._keyLabel.hide()
        self._keyText.hide()

        self._min = ScientificSpinBox()
        self._max = ScientificSpinBox()
        self._min.valueChanged.connect(self.__loadRange)
        self._max.valueChanged.connect(self.__loadRange)
        self._min.setEnabled(False)
        self._max.setEnabled(False)
        self._useMin = QtWidgets.QCheckBox("min", stateChanged=self._min.setEnabled)
        self._useMax = QtWidgets.QCheckBox("max", stateChanged=self._max.setEnabled)
        self._useMin.stateChanged.connect(self.__loadRange)
        self._useMax.stateChanged.connect(self.__loadRange)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("x data"), 0, 0)
        g.addWidget(self._xdata, 0, 1, 1, 2)
        g.addWidget(self._keyLabel, 1, 0)
        g.addWidget(self._keyText, 1, 1, 1, 2)
        g.addWidget(QtWidgets.QLabel("Region"), 2, 0)
        g.addWidget(self._useMin, 2, 1)
        g.addWidget(self._useMax, 2, 2)
        g.addWidget(QtWidgets.QPushButton("Load from Graph", clicked=self.__loadFromGraph), 3, 0)
        g.addWidget(self._min, 3, 1)
        g.addWidget(self._max, 3, 2)

        self.setLayout(g)

    @avoidCircularReference
    def __loadRange(self, *args, **kwargs):
        r = [0, 0]
        if self._useMin.isChecked():
            r[0] = self._min.value()
        else:
            r[0] = None
        if self._useMax.isChecked():
            r[1] = self._max.value()
        else:
            r[1] = None
        self.__range = tuple(r)
        self.axisChanged.emit(self.__type, self.__range)

    def __changeXAxis(self, txt):
        self._keyLabel.setVisible(txt == "from Wave.note")
        self._keyText.setVisible(txt == "from Wave.note")
        self.__setXAxis()

    @avoidCircularReference
    def __setXAxis(self, *args, **kwargs):
        if self._xdata.currentText() == "x axis":
            self.__type = None
        else:
            self.__type = self._keyText.text()
        self.axisChanged.emit(self.__type, self.__range)

    def __loadFromGraph(self):
        if self._canvas.isRangeSelected():
            r = np.array(self._canvas.selectedRange()).T[0]
            self._min.setValue(min(*r))
            self._max.setValue(max(*r))
            self._useMin.setChecked(True)
            self._useMax.setChecked(True)
            self.__loadRange()
        else:
            QtWidgets.QMessageBox.information(self, "Warning", "Please select region by dragging in the graph.")

    @avoidCircularReference
    def setRange(self, type, range):
        self.__type = type
        self.__range = tuple(range)
        if self.__type is None:
            self._xdata.setCurrentIndex(0)
        else:
            self._xdata.setCurrentIndex(1)
            self._keyText.setText(self.__type)

        if self.__range[0] is None:
            self._useMin.setChecked(False)
        else:
            self._useMin.setChecked(True)
            self._min.setValue(self.__range[0])
        if self.__range[1] is None:
            self._useMax.setChecked(False)
        else:
            self._useMax.setChecked(True)
            self._max.setValue(self.__range[1])


class FittingTree(QtWidgets.QTreeView):
    """The widget for _FittingFunctions"""
    __copied = None
    __allCopied = None
    plotRequired = QtCore.pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self._obj = None
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._model = QtGui.QStandardItemModel(0, 2)
        self._model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        self._model.setHeaderData(1, QtCore.Qt.Horizontal, 'Value')
        self.setModel(self._model)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
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
        isFunc = self.__currentItemIndex() is not None or len(self.selectedIndexes()) == 0
        selected = self.__currentItemIndex() is not None
        menu = QtWidgets.QMenu(self)
        if not isFunc:
            menu.addAction(QtWidgets.QAction('Plot this parameter', self, triggered=self.__plot))
        menu.addAction(QtWidgets.QAction('Add Function', self, triggered=self.__addFunction))
        if isFunc and selected:
            menu.addAction(QtWidgets.QAction('Remove Function', self, triggered=self.__removeFunction))
        menu.addAction(QtWidgets.QAction('Clear', self, triggered=self.__clear))
        menu.addSeparator()
        if isFunc and selected:
            menu.addAction(QtWidgets.QAction('Copy Parameters as list', self, triggered=lambda: self.__copyParams("list")))
            menu.addAction(QtWidgets.QAction('Copy Parameters as dict', self, triggered=lambda: self.__copyParams("dict")))
            menu.addSeparator()
            menu.addAction(QtWidgets.QAction('Copy Function', self, triggered=self.__copyFunction))
            menu.addAction(QtWidgets.QAction('Paste Function', self, triggered=self.__pasteFunction))
        menu.addAction(QtWidgets.QAction('Copy All Functions', self, triggered=lambda: self.__copyFunction(all=True)))
        menu.addAction(QtWidgets.QAction('Paste All Functions', self, triggered=lambda: self.__pasteFunction(all=True)))
        menu.addSeparator()
        menu.addAction(QtWidgets.QAction('Import from File', self, triggered=self.__import))
        menu.addAction(QtWidgets.QAction('Export to File', self, triggered=self.__export))
        menu.exec_(QtGui.QCursor.pos())

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

    def __copyParams(self, type="list"):
        values = self._obj.functions[self.__currentItemIndex()].value
        if type == "list":
            obj = values
        else:
            obj = {n: v for n, v in zip(self._obj.functions[self.__currentItemIndex()].paramNames, values)}
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(str(obj), mode=cb.Clipboard)

    def __copyFunction(self, all=False):
        if all:
            FittingTree.__allCopied = self._obj.saveAsDictionary()
        else:
            FittingTree.__copied = self._obj.functions[self.__currentItemIndex()].saveAsDictionary()

    def __pasteFunction(self, all=False):
        if all:
            if FittingTree.__allCopied is None:
                return None
            self.__clear()
            self._obj.loadFromDictionary(FittingTree.__allCopied)
        else:
            if FittingTree.__copied is None:
                return
            self._obj.addFunction(FittingTree.__copied)

    def __export(self):
        path, type = QtWidgets.QFileDialog.getSaveFileName(self, "Save fitting results", filter="Dictionary (*.dic);;All files (*.*)")
        if len(path) != 0:
            if not path.endswith(".dic"):
                path = path + ".dic"
            with open(path, "w") as f:
                f.write(str(self._obj.saveAsDictionary()))

    def __import(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Load fitting', filter="Dictionary (*.dic);;All files (*.*)")
        if fname[0]:
            with open(fname[0], "r") as f:
                d = eval(f.read())
            self._obj.loadFromDictionary(d)

    def __clear(self):
        self._obj.clear()


class _FuncSelectDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(functions.keys())

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton('O K', clicked=self.accept))
        h1.addWidget(QtWidgets.QPushButton('CALCEL', clicked=self.reject))

        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(self.combo)
        v1.addLayout(h1)
        self.setLayout(v1)

    def getFunctionName(self):
        return self.combo.currentText()


class _SingleFuncGUI(QtGui.QStandardItem):
    def __init__(self, obj, tree, model):
        super().__init__(obj.name)
        self._obj = obj
        model.appendRow(self)
        self._params = [_SingleParamGUI(p, self, tree) for p in obj.parameters]


class _checkableSpinBoxItem(QtCore.QObject):
    valueChanged = QtCore.pyqtSignal(float)
    stateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, name, tree, parent):
        super().__init__()
        self._item = QtGui.QStandardItem(name)
        self._item.setCheckable(True)

        self._value = ScientificSpinBox()
        self._value.valueChanged.connect(self.valueChanged)

        item2 = QtGui.QStandardItem()
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
            self._item.setCheckState(QtCore.Qt.Checked)
        else:
            self._item.setCheckState(QtCore.Qt.Unchecked)

    @property
    def checked(self):
        return self.item.checkState() == QtCore.Qt.Checked

    def _itemChanged(self, item):
        if item == self._item:
            self.stateChanged.emit(item.checkState() == QtCore.Qt.Checked)

    @property
    def item(self):
        return self._item


class _SingleParamGUI(QtCore.QObject):
    updated = QtCore.pyqtSignal()

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
