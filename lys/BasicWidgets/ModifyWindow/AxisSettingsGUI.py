import numpy as np

from LysQt.QtWidgets import QComboBox, QGroupBox, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QCheckBox, QDoubleSpinBox
from .ColorWidgets import ColorSelection
from lys.widgets import ScientificSpinBox


class AxisSelectionWidget(QComboBox):
    def __init__(self, canvas):
        super().__init__()
        canvas.axisChanged.connect(lambda: self.__setItem(canvas))
        self.__setItem(canvas)

    def __setItem(self, canvas):
        self.clear()
        self.addItems(canvas.axisList())


class _AxisRangeAdjustBox(QGroupBox):
    def __init__(self, parent, canvas):
        super().__init__('Axis Range')
        self._parent = parent
        self.canvas = canvas
        self.__initlayout()
        self.update()
        self.canvas.axisRangeChanged.connect(self.update)

    def __initlayout(self):

        self.__combo = QComboBox()
        self.__combo.addItem('Auto')
        self.__combo.addItem('Manual')
        self.__combo.activated.connect(self.__OnModeChanged)

        self.__spin1 = ScientificSpinBox(valueChanged=self.__spinChanged)
        self.__spin2 = ScientificSpinBox(valueChanged=self.__spinChanged)

        layout_h1 = QHBoxLayout()
        layout_h1.addWidget(QLabel('Min'), 1)
        layout_h1.addWidget(self.__spin1, 2)

        layout_h2 = QHBoxLayout()
        layout_h2.addWidget(QLabel('Max'), 1)
        layout_h2.addWidget(self.__spin2, 2)

        rev = QPushButton("Reverse", clicked=self.__reverse)

        layout = QVBoxLayout()
        layout.addWidget(self.__combo)
        layout.addLayout(layout_h1)
        layout.addLayout(layout_h2)
        layout.addWidget(rev)
        self.setLayout(layout)

    def update(self):
        self.__loadflg = True
        axis = self._parent.getCurrentAxis()
        mod = self.canvas.isAutoScaled(axis)
        if mod:
            self.__combo.setCurrentIndex(0)
        else:
            self.__combo.setCurrentIndex(1)
        ran = self.canvas.getAxisRange(axis)
        self.__spin1.setValue(ran[0])
        self.__spin2.setValue(ran[1])
        self.__loadflg = False

    def __OnModeChanged(self):
        if self.__loadflg:
            return
        type = self.__combo.currentText()
        if type == "Auto":
            if self._parent.isApplyAll():
                for axis in self.canvas.axisList():
                    self.canvas.setAutoScaleAxis(axis)
            else:
                axis = self._parent.getCurrentAxis()
                self.canvas.setAutoScaleAxis(axis)
        self.update()

    def __spinChanged(self):
        if self.__loadflg:
            return
        mi = self.__spin1.value()
        ma = self.__spin2.value()
        self.__applyChange(ma, mi)

    def __reverse(self):
        mi = self.__spin1.value()
        ma = self.__spin2.value()
        self.__applyChange(mi, ma)

    def __applyChange(self, ma, mi):
        if self._parent.isApplyAll():
            for ax in self.canvas.axisList():
                self.canvas.setAxisRange(ax, [mi, ma])
        else:
            self.canvas.setAxisRange(self._parent.getCurrentAxis(), [mi, ma])


class _AxisAdjustBox(QGroupBox):
    def __init__(self, parent, canvas):
        super().__init__("Axis Setting")
        self.canvas = canvas
        self._parent = parent
        self.__flg = False
        self.__initlayout()
        self.update()

    def __initlayout(self):

        self.__mirror = QCheckBox("Mirror")
        self.__mirror.stateChanged.connect(self.__mirrorChanged)
        self.__mode = QComboBox()
        self.__mode.addItems(['linear', 'log'])
        self.__mode.activated.connect(self.__chgmod)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)
        self.__spin1 = QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__setThick)

        gl = QGridLayout()
        gl.addWidget(self.__mirror, 0, 0)
        gl.addWidget(QLabel('Mode'), 1, 0)
        gl.addWidget(QLabel('Color'), 2, 0)
        gl.addWidget(QLabel('Thick'), 3, 0)
        gl.addWidget(self.__mode, 1, 1)
        gl.addWidget(self.__color, 2, 1)
        gl.addWidget(self.__spin1, 3, 1)
        self.setLayout(gl)

    def update(self):
        self.__flg = True
        axis = self._parent.getCurrentAxis()
        self.__spin1.setValue(self.canvas.getAxisThick(axis))
        self.__color.setColor(self.canvas.getAxisColor(axis))
        list = ['linear', 'log']
        self.__mode.setCurrentIndex(list.index(self.canvas.getAxisMode(axis)))
        self.__mirror.setChecked(self.canvas.getMirrorAxis(axis))
        self.__flg = False

    def __axis(self):
        if self.__flg:
            return []
        elif self._parent.isApplyAll():
            return self.canvas.axisList()
        else:
            return [self._parent.getCurrentAxis()]

    def __mirrorChanged(self):
        for ax in self.__axis():
            self.canvas.setMirrorAxis(ax, self.__mirror.isChecked())

    def __chgmod(self):
        for ax in self.__axis():
            self.canvas.setAxisMode(ax, self.__mode.currentText())

    def __setThick(self):
        for ax in self.__axis():
            self.canvas.setAxisThick(ax, self.__spin1.value())

    def __changeColor(self):
        for ax in self.__axis():
            self.canvas.setAxisColor(ax, self.__color.getColor())


class _TickAdjustBox(QGroupBox):
    def __init__(self, parent, canvas):
        super().__init__("Tick Setting")
        self.canvas = canvas
        self._parent = parent
        self.__flg = False
        self.__initlayout()
        self.update()

    def __initlayout(self):
        self.__mode = QComboBox()
        self.__mode.addItems(['in', 'out', 'none'])
        self.__mir = QCheckBox('Mirror')
        self.__mir.stateChanged.connect(self.__chon)

        self.__mode.activated.connect(self.__chgmod)
        self.__spin1 = ScientificSpinBox()
        self.__spin1.valueChanged.connect(self.__chnum)
        self.__spin1.setRange(0, np.inf)
        self.__spin2 = QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__chlen)
        self.__spin2.setRange(0, np.inf)
        self.__spin3 = QDoubleSpinBox()
        self.__spin3.valueChanged.connect(self.__chwid)
        self.__spin3.setRange(0, np.inf)

        self.__minor = QCheckBox('Minor')
        self.__minor.stateChanged.connect(self.__minorChanged)
        self.__spin4 = ScientificSpinBox()
        self.__spin4.valueChanged.connect(self.__chnum2)
        self.__spin5 = QDoubleSpinBox()
        self.__spin5.valueChanged.connect(self.__chlen2)
        self.__spin6 = QDoubleSpinBox()
        self.__spin6.valueChanged.connect(self.__chwid2)

        gl = QGridLayout()
        gl.addWidget(QLabel('Location'), 0, 0)
        gl.addWidget(self.__mode, 0, 1)
        gl.addWidget(self.__mir, 0, 2)

        gl.addWidget(QLabel('Major'), 1, 0)
        gl.addWidget(QLabel('Interval'), 2, 0)
        gl.addWidget(self.__spin1, 2, 1)
        gl.addWidget(QLabel('Length'), 3, 0)
        gl.addWidget(self.__spin2, 3, 1)
        gl.addWidget(QLabel('Width'), 4, 0)
        gl.addWidget(self.__spin3, 4, 1)

        gl.addWidget(self.__minor, 1, 2)
        gl.addWidget(QLabel('Interval'), 2, 2)
        gl.addWidget(self.__spin4, 2, 3)
        gl.addWidget(QLabel('Length'), 3, 2)
        gl.addWidget(self.__spin5, 3, 3)
        gl.addWidget(QLabel('Width'), 4, 2)
        gl.addWidget(self.__spin6, 4, 3)
        self.setLayout(gl)

    def __axis(self):
        if self.__flg:
            return []
        elif self._parent.isApplyAll():
            return self.canvas.axisList()
        else:
            return [self._parent.getCurrentAxis()]

    def __chnum(self):
        for ax in self.__axis():
            self.canvas.setTickInterval(ax, self.__spin1.value())

    def __chnum2(self):
        for ax in self.__axis():
            self.canvas.setTickInterval(ax, self.__spin4.value(), which='minor')

    def __chon(self):
        value = self.__mir.isChecked()
        for ax in self.__axis():
            if not self.__mode.currentText() == "none":
                self.canvas.setTickVisible(ax, value, mirror=True, which='major')
                if self.__minor.isChecked():
                    self.canvas.setTickVisible(ax, value, mirror=True, which='minor')

    def __chgmod(self):
        if self.__flg:
            return
        value = self.__mode.currentText()
        if value == "none":
            self.__mir.setChecked(False)
            for ax in self.__axis():
                self.canvas.setTickVisible(ax, False)
                self.canvas.setTickVisible(ax, False, mirror=True)
        else:
            for ax in self.__axis():
                if self.__minor.isChecked():
                    self.canvas.setTickVisible(ax, True)
                else:
                    self.canvas.setTickVisible(ax, True, which='major')
                if self.__mir.isChecked():
                    if self.__minor.isChecked():
                        self.canvas.setTickVisible(ax, True, mirror=True)
                    else:
                        self.canvas.setTickVisible(ax, True, mirror=True, which='major')
                self.canvas.setTickDirection(ax, value)

    def __chlen(self):
        for ax in self.__axis():
            self.canvas.setTickLength(ax, self.__spin2.value())

    def __chlen2(self):
        for ax in self.__axis():
            self.canvas.setTickLength(ax, self.__spin5.value(), which='minor')

    def __chwid(self):
        for ax in self.__axis():
            self.canvas.setTickWidth(ax, self.__spin3.value())

    def __chwid2(self):
        for ax in self.__axis():
            self.canvas.setTickWidth(ax, self.__spin6.value(), which='minor')

    def __minorChanged(self):
        value = self.__minor.isChecked()
        if self.__mode.currentText() == "none":
            value = False
        for ax in self.__axis():
            self.canvas.setTickVisible(ax, value, mirror=False, which='minor')
            if self.__mir.isChecked():
                self.canvas.setTickVisible(ax, value, mirror=True, which='minor')
            else:
                self.canvas.setTickVisible(ax, False, mirror=True, which='minor')

    def update(self):
        axis = self._parent.getCurrentAxis()
        self.__flg = True
        self.__mir.setChecked(self.canvas.getTickVisible(axis, mirror=True))
        self.__minor.setChecked(self.canvas.getTickVisible(axis, which='minor'))
        if self.canvas.getTickVisible(axis):
            self.__mode.setCurrentIndex(['in', 'out', 'none'].index(self.canvas.getTickDirection(axis)))
        else:
            self.__mode.setCurrentIndex(2)
        self.__spin1.setValue(self.canvas.getTickInterval(axis))
        self.__spin2.setValue(self.canvas.getTickLength(axis, 'major'))
        self.__spin3.setValue(self.canvas.getTickWidth(axis, 'major'))
        self.__spin4.setValue(self.canvas.getTickInterval(axis, which='minor'))
        self.__spin5.setValue(self.canvas.getTickLength(axis, 'minor'))
        self.__spin6.setValue(self.canvas.getTickWidth(axis, 'minor'))
        self.__flg = False


class AxisAndTickBox(QWidget):
    def __init__(self, parent, canvas):
        super().__init__()
        self._range = _AxisRangeAdjustBox(parent, canvas)
        self._axis = _AxisAdjustBox(parent, canvas)
        self._tick = _TickAdjustBox(parent, canvas)

        layout_h1 = QHBoxLayout()
        layout_h1.addWidget(self._range)
        layout_h1.addWidget(self._axis)

        layout = QVBoxLayout(self)
        layout.addLayout(layout_h1)
        layout.addWidget(self._tick)
        self.setLayout(layout)

    def update(self):
        self._range.update()
        self._axis.update()
        self._tick.update()
