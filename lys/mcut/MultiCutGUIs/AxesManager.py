import numpy as np

from lys.Qt import QtWidgets, QtCore, QtGui
from lys.widgets import ScientificSpinBox, RangeSlider
from lys.decorators import avoidCircularReference


class _AxisRangeWidget(QtWidgets.QGroupBox):
    def __init__(self, cui, index):
        super().__init__("Axis " + str(index + 1))
        self._cui = cui
        self._index = index
        self.__initlayout()
        self.__setEvent()
        self.__update()
        self._cui.axesRangeChanged.connect(self.__update)
        self._cui.filterApplied.connect(self.__filterApplied)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)

    def __initlayout(self):
        self._point = QtWidgets.QRadioButton("Point")
        self._range = QtWidgets.QRadioButton("Range")

        self._value = ScientificSpinBox()
        self._value1 = ScientificSpinBox()
        self._value2 = ScientificSpinBox()

        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._rslider = RangeSlider(QtCore.Qt.Horizontal)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._point, 0, 0)
        layout.addWidget(self._value, 0, 1)
        layout.addWidget(self._range, 1, 0)
        layout.addWidget(self._value1, 1, 1)
        layout.addWidget(self._value2, 1, 2)

        v = QtWidgets.QVBoxLayout()
        v.addLayout(layout)
        v.addWidget(self._slider)
        v.addWidget(self._rslider)
        self.setLayout(v)

    def __setEvent(self):
        self._point.toggled.connect(self.__changeMode)
        self._range.toggled.connect(self.__changeMode)

        self._value.valueChanged.connect(self.__value)
        self._value1.valueChanged.connect(self.__range)
        self._value2.valueChanged.connect(self.__range)

        self._slider.valueChanged.connect(self.__slider)
        self._rslider.sliderMoved.connect(self.__rslider)

    def __filterApplied(self):
        self.__update()

    @ avoidCircularReference
    def __update(self, axes=None):
        if axes is not None:
            if self._index not in axes:
                return
        self._axis = ax = np.array(sorted(self._cui.getFilteredWave().getAxis(self._index)))
        self._value.setRange(min(ax), max(ax))
        self._value1.setRange(min(ax), max(ax))
        self._value2.setRange(min(ax), max(ax))
        self._slider.setRange(0, len(self._axis) - 1)
        self._rslider.setMinimum(0)
        self._rslider.setMaximum(len(self._axis) - 1)
        r = self._cui.getAxisRange(self._index)
        if hasattr(r, "__iter__"):
            self._range.setChecked(True)
            self._value1.setValue(min(r))
            self._value2.setValue(max(r))
            self._value1.setValue(min(r))
            self._rslider.setLow(self.__valToIndex(min(r)))
            self._rslider.setHigh(self.__valToIndex(max(r)))
        else:
            self._point.setChecked(True)
            self._value.setValue(r)
            self._slider.setValue(self.__valToIndex(r))

    def __changeMode(self):
        b = self._range.isChecked()
        self._value.setEnabled(not b)
        self._value1.setEnabled(b)
        self._value2.setEnabled(b)
        if b:
            self._slider.hide()
            self._rslider.show()
            self._value1.setValue(self._value.value())
            self._value2.setValue(self._value.value())
            index = self.__valToIndex(self._value.value())
            self._rslider.setLow(index)
            self._rslider.setHigh(index)
        else:
            self._slider.show()
            self._rslider.hide()
            self._value.setValue((self._value1.value() + self._value2.value()) / 2)
            index = self.__valToIndex((self._value1.value() + self._value2.value()) / 2)
            self._slider.setValue(index)

    def __valToIndex(self, value):
        return np.argmin(abs(self._axis - value))

    @ avoidCircularReference
    def __slider(self, value):
        self._value.setValue(self._axis[value])
        self._cui.setAxisRange(self._index, self._axis[value])

    @ avoidCircularReference
    def __value(self, value):
        self._slider.setValue(self.__valToIndex(value))
        self._cui.setAxisRange(self._index, value)

    @ avoidCircularReference
    def __rslider(self, value1, value2):
        self._value1.setValue(self._axis[self._rslider.low()])
        self._value2.setValue(self._axis[self._rslider.high()])
        self._value1.setMaximum(self._value2.value())
        self._value2.setMinimum(self._value1.value())
        self._cui.setAxisRange(self._index, [self._axis[self._rslider.low()], self._axis[self._rslider.high()]])

    @ avoidCircularReference
    def __range(self, *args, **kwargs):
        self._value1.setMaximum(self._value2.value())
        self._value2.setMinimum(self._value1.value())
        self._rslider.setHigh(self.__valToIndex(max(self._value1.value(), self._value2.value())))
        self._rslider.setLow(self.__valToIndex(min(self._value1.value(), self._value2.value())))
        self._cui.setAxisRange(self._index, [self._value1.value(), self._value2.value()])

    def _buildContextMenu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction("Copy", self, triggered=self._copy))
        menu.addAction(QtWidgets.QAction("Paste", self, triggered=self._paste))
        menu.exec_(QtGui.QCursor.pos())

    def _copy(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        if self._point.isChecked():
            cb.setText(str(self._value.value()), mode=cb.Clipboard)
        else:
            cb.setText(str((self._value1.value(), self._value2.value())), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = eval(cb.text(mode=cb.Clipboard))
        if hasattr(v, "__iter__"):
            if len(v) == 2:
                self._range.setChecked(True)
                self._value1.setValue(v[0])
                self._value2.setValue(v[1])
                self._value1.setValue(v[0])
        else:
            self._point.setChecked(True)
            self._value.setValue(v)


class AxesRangeWidget(QtWidgets.QScrollArea):
    def __init__(self, cui):
        super().__init__()
        self._cui = cui
        self.setWidgetResizable(True)
        self.__initlayout()
        cui.dimensionChanged.connect(self.__update)

    def __initlayout(self):
        self._axes = [_AxisRangeWidget(self._cui, i) for i in range(self._cui.getFilteredWave().ndim)]
        self._layout = QtWidgets.QVBoxLayout()
        for ax in self._axes:
            self._layout.addWidget(ax)
        self._layout.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(self._layout)
        self.setWidget(w)

    def __update(self):
        for ax in self._axes:
            self._layout.removeWidget(ax)
            ax.deleteLater()
        self._axes = [_AxisRangeWidget(self._cui, i) for i in range(self._cui.getFilteredWave().ndim)]
        for i, ax in enumerate(self._axes):
            self._layout.insertWidget(i, ax)

    def sizeHint(self):
        return QtCore.QSize(100, 100)


class _FreeLineWidget(QtWidgets.QGroupBox):
    def __init__(self, cui, obj):
        super().__init__(obj.getName() + ": " + str(obj.getAxes()) + " axes")
        self._cui = cui
        self._obj = obj
        self.__initlayout()
        self._update()
        self._obj.lineChanged.connect(self._update)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)

    def __initlayout(self):
        self._val1 = [ScientificSpinBox(valueChanged=self._updateValues) for i in range(2)]
        self._val2 = [ScientificSpinBox(valueChanged=self._updateValues) for i in range(2)]
        self.width = ScientificSpinBox(valueChanged=self._updateValues)

        lay = QtWidgets.QGridLayout()
        for n in range(2):
            lay.addWidget(QtWidgets.QLabel("Point " + str(n)), n, 0)
            lay.addWidget(self._val1[n], 0, n + 1)
            lay.addWidget(self._val2[n], 1, n + 1)
        lay.addWidget(QtWidgets.QLabel("Width"), n + 1, 0)
        lay.addWidget(self.width, n + 1, 1)
        self.setLayout(lay)

    @avoidCircularReference
    def _update(self, *args, **kwargs):
        for v, val in zip(self._val1, self._obj.getPosition()[0]):
            v.setValue(val)
        for v, val in zip(self._val2, self._obj.getPosition()[1]):
            v.setValue(val)
        self.width.setValue(self._obj.getWidth())

    @avoidCircularReference
    def _updateValues(self, *args, **kwargs):
        self._obj.setPosition([[self._val1[0].value(), self._val1[1].value()], [self._val2[0].value(), self._val2[1].value()]])
        self._obj.setWidth(self.width.value())

    def _buildContextMenu(self):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction("Copy", self, triggered=self._copy))
        menu.addAction(QtWidgets.QAction("Paste", self, triggered=self._paste))
        menu.exec_(QtGui.QCursor.pos())

    def _copy(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(str([self._obj.getPosition(), self._obj.getWidth()]), mode=cb.Clipboard)

    def _paste(self):
        cb = QtWidgets.QApplication.clipboard()
        v = eval(cb.text(mode=cb.Clipboard))
        self._obj.setPosition(v[0])
        self._obj.setWidth(v[1])


class FreeLinesWidget(QtWidgets.QScrollArea):
    def __init__(self, cui):
        super().__init__()
        self._cui = cui
        self.setWidgetResizable(True)
        self.__initlayout()
        self._cui.freeLineChanged.connect(self.__update)

    def __initlayout(self):
        self._axes = [_FreeLineWidget(self._cui, obj) for obj in self._cui.getFreeLines()]
        self._layout = QtWidgets.QVBoxLayout()
        for ax in self._axes:
            self._layout.addWidget(ax)
        self._layout.addStretch()

        w = QtWidgets.QWidget()
        w.setLayout(self._layout)
        self.setWidget(w)

    def __update(self):
        for ax in self._axes:
            self._layout.removeWidget(ax)
            ax.deleteLater()
        self._axes = [_FreeLineWidget(self._cui, obj) for obj in self._cui.getFreeLines()]
        for i, ax in enumerate(self._axes):
            self._layout.insertWidget(i, ax)

    def sizeHint(self):
        return QtCore.QSize(100, 100)
