from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .ColorWidgets import *
from lys.widgets import ScientificSpinBox


class AxisSelectionWidget(QComboBox):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.canvas.axisChanged.connect(self.OnAxisChanged)
        self.canvas.addAxisSelectedListener(self)
        self.flg = False
        self.__setItem()
        self.activated.connect(self._activated)

    def __setItem(self):
        self.addItem('Left')
        if self.canvas.axisIsValid('Right'):
            self.addItem('Right')
        self.addItem('Bottom')
        if self.canvas.axisIsValid('Top'):
            self.addItem('Top')

    def _activated(self):
        self.flg = True
        self.canvas.setSelectedAxis(self.currentText())
        self.flg = False

    def OnAxisChanged(self, axis):
        self.clear()
        self.__setItem()

    def OnAxisSelected(self, axis):
        if self.flg:
            return
        else:
            Items = [self.itemText(i) for i in range(self.count())]
            self.setCurrentIndex(Items.index(axis))


class AxisRangeAdjustBox(QGroupBox):
    def __init__(self, canvas):
        super().__init__('Axis Range')
        self.canvas = canvas
        self.__initlayout()
        self.__loadstate(canvas)
        self.canvas.addAxisSelectedListener(self)
        self.canvas.axisRangeChanged.connect(self.OnAxisRangeChanged)

    def __initlayout(self):
        layout = QVBoxLayout()

        self.__combo = QComboBox()
        self.__combo.addItem('Auto')
        self.__combo.addItem('Manual')
        self.__combo.activated.connect(self.__OnModeChanged)

        self.__spin1 = ScientificSpinBox(valueChanged=self.__spinChanged)
        self.__spin2 = ScientificSpinBox(valueChanged=self.__spinChanged)

        layout_h1 = QHBoxLayout()
        layout_h1.addWidget(QLabel('Min'))
        layout_h1.addWidget(self.__spin1)

        layout_h2 = QHBoxLayout()
        layout_h2.addWidget(QLabel('Max'))
        layout_h2.addWidget(self.__spin2)

        rev = QPushButton("Reverse", clicked=self.__reverse)

        layout.addWidget(self.__combo)
        layout.addLayout(layout_h1)
        layout.addLayout(layout_h2)
        layout.addWidget(rev)
        self.setLayout(layout)

    def __loadstate(self, canvas):
        self.__loadflg = True
        axis = canvas.getSelectedAxis()
        mod = canvas.isAutoScaled(axis)
        if mod:
            self.__combo.setCurrentIndex(0)
        else:
            self.__combo.setCurrentIndex(1)
        self.__spin1.setReadOnly(mod)
        self.__spin2.setReadOnly(mod)
        ran = canvas.getAxisRange(axis)
        self.__spin1.setValue(ran[0])
        self.__spin2.setValue(ran[1])
        self.__loadflg = False

    def OnAxisRangeChanged(self):
        self.__loadstate(self.canvas)

    def OnAxisSelected(self, axis):
        self.__loadstate(self.canvas)

    def __OnModeChanged(self):
        if self.__loadflg:
            return
        type = self.__combo.currentText()
        axis = self.canvas.getSelectedAxis()
        if type == "Auto":
            self.canvas.setAutoScaleAxis(axis)
        else:
            self.canvas.setAxisRange(self.canvas.getAxisRange(axis), axis)
        self.__loadstate(self.canvas)

    def __spinChanged(self):
        if self.__loadflg:
            return
        mi = self.__spin1.value()
        ma = self.__spin2.value()
        self.canvas.setAxisRange([mi, ma], self.canvas.getSelectedAxis())

    def __reverse(self):
        mi = self.__spin1.value()
        ma = self.__spin2.value()
        self.canvas.setAxisRange([ma, mi], self.canvas.getSelectedAxis())


opposite = {'Left': 'right', 'Right': 'left', 'Bottom': 'top', 'Top': 'bottom'}
Opposite = {'Left': 'Right', 'Right': 'Left', 'Bottom': 'Top', 'Top': 'Bottom'}


class AxisAdjustBox(QGroupBox):
    def __init__(self, canvas):
        super().__init__("Axis Setting")
        self.canvas = canvas
        self.__flg = False
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)

    def __initlayout(self):
        gl = QGridLayout()

        self.__all = QCheckBox('All axes')
        self.__all.setChecked(True)
        gl.addWidget(self.__all, 0, 0)

        self.__mirror = QCheckBox("Mirror")
        self.__mirror.stateChanged.connect(self.__mirrorChanged)
        gl.addWidget(self.__mirror, 0, 1)

        gl.addWidget(QLabel('Mode'), 1, 0)
        self.__mode = QComboBox()
        self.__mode.addItems(['linear', 'log'])
        self.__mode.activated.connect(self.__chgmod)
        gl.addWidget(self.__mode, 1, 1)

        gl.addWidget(QLabel('Color'), 2, 0)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)
        gl.addWidget(self.__color, 2, 1)

        gl.addWidget(QLabel('Thick'), 3, 0)
        self.__spin1 = QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__setThick)
        gl.addWidget(self.__spin1, 3, 1)

        self.setLayout(gl)

    def __loadstate(self):
        self.__flg = True
        axis = self.canvas.getSelectedAxis()
        self.__spin1.setValue(self.canvas.getAxisThick(axis))
        self.__color.setColor(self.canvas.getAxisColor(axis))
        list = ['linear', 'log']
        self.__mode.setCurrentIndex(list.index(self.canvas.getAxisMode(axis)))
        if self.canvas.axisIsValid(Opposite[axis]):
            self.__mirror.setEnabled(False)
        else:
            self.__mirror.setEnabled(True)
        self.__mirror.setChecked(self.canvas.getMirrorAxis(axis))
        self.__flg = False

    def OnAxisSelected(self, axis):
        self.__loadstate()

    def __mirrorChanged(self):
        if self.__flg:
            return
        axis = self.canvas.getSelectedAxis()
        value = self.__mirror.isChecked()
        if self.__all.isChecked():
            if not self.canvas.axisIsValid('Right'):
                self.canvas.setMirrorAxis('Left', value)
            if not self.canvas.axisIsValid('Top'):
                self.canvas.setMirrorAxis('Bottom', value)
        else:
            self.canvas.setMirrorAxis(axis, value)

    def __chgmod(self):
        if self.__flg:
            return
        mod = self.__mode.currentText()
        axis = self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisMode('Left', mod)
            self.canvas.setAxisMode('Right', mod)
            self.canvas.setAxisMode('Top', mod)
            self.canvas.setAxisMode('Bottom', mod)
        else:
            self.canvas.setAxisMode(axis, mod)

    def __setThick(self):
        if self.__flg:
            return
        axis = self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisThick('Left', self.__spin1.value())
            self.canvas.setAxisThick('Right', self.__spin1.value())
            self.canvas.setAxisThick('Top', self.__spin1.value())
            self.canvas.setAxisThick('Bottom', self.__spin1.value())
        else:
            self.canvas.setAxisThick(axis, self.__spin1.value())

    def __changeColor(self):
        if self.__flg:
            return
        axis = self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisColor('Left', self.__color.getColor())
            self.canvas.setAxisColor('Right', self.__color.getColor())
            self.canvas.setAxisColor('Top', self.__color.getColor())
            self.canvas.setAxisColor('Bottom', self.__color.getColor())
        else:
            self.canvas.setAxisColor(axis, self.__color.getColor())


class TickAdjustBox(QGroupBox):
    def __init__(self, canvas):
        super().__init__("Tick Setting")
        self.canvas = canvas
        self.__flg = False
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)

    def __initlayout(self):
        layout = QVBoxLayout()

        layout_h = QHBoxLayout()
        self.__all = QCheckBox('All axes')
        self.__all.setChecked(False)
        layout_h.addWidget(self.__all)

        self.__mir = QCheckBox('Mirror')
        self.__mir.stateChanged.connect(self.__chon)
        layout_h.addWidget(self.__mir)

        layout.addLayout(layout_h)

        gl = QGridLayout()

        gl.addWidget(QLabel('Location'), 0, 0)
        self.__mode = QComboBox()
        self.__mode.addItems(['in', 'out', 'none'])
        self.__mode.activated.connect(self.__chgmod)
        gl.addWidget(self.__mode, 0, 1)

        gl.addWidget(QLabel('Interval'), 1, 0)
        self.__spin1 = ScientificSpinBox()
        self.__spin1.valueChanged.connect(self.__chnum)
        self.__spin1.setRange(0, np.inf)
        gl.addWidget(self.__spin1, 1, 1)

        gl.addWidget(QLabel('Length'), 2, 0)
        self.__spin2 = QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__chlen)
        self.__spin2.setRange(0, np.inf)
        gl.addWidget(self.__spin2, 2, 1)

        gl.addWidget(QLabel('Width'), 3, 0)
        self.__spin3 = QDoubleSpinBox()
        self.__spin3.valueChanged.connect(self.__chwid)
        self.__spin3.setRange(0, np.inf)
        gl.addWidget(self.__spin3, 3, 1)

        self.__minor = QCheckBox('Minor')
        self.__minor.stateChanged.connect(self.__minorChanged)
        gl.addWidget(self.__minor, 0, 2)

        gl.addWidget(QLabel('Interval'), 1, 2)
        self.__spin4 = ScientificSpinBox()
        self.__spin4.valueChanged.connect(self.__chnum2)
        gl.addWidget(self.__spin4, 1, 3)

        gl.addWidget(QLabel('Length'), 2, 2)
        self.__spin5 = QDoubleSpinBox()
        self.__spin5.valueChanged.connect(self.__chlen2)
        gl.addWidget(self.__spin5, 2, 3)

        gl.addWidget(QLabel('Width'), 3, 2)
        self.__spin6 = QDoubleSpinBox()
        self.__spin6.valueChanged.connect(self.__chwid2)
        gl.addWidget(self.__spin6, 3, 3)

        layout.addLayout(gl)
        self.setLayout(layout)
        self.__loadstate()

    def __axis(self):
        if self.__all.isChecked():
            res = ['Left', 'Bottom']
            if self.canvas.axisIsValid('Right'):
                res.append('Right')
            if self.canvas.axisIsValid('Top'):
                res.append('Top')
            return res
        else:
            return [self.canvas.getSelectedAxis()]

    def __chnum(self):
        if self.__flg:
            return
        value = self.__spin1.value()
        for ax in self.__axis():
            self.canvas.setAutoLocator(ax, value)

    def __chnum2(self):
        if self.__flg:
            return
        value = self.__spin4.value()
        for ax in self.__axis():
            self.canvas.setAutoLocator(ax, value, which='minor')

    def __chon(self):
        if self.__flg:
            return
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
        if self.__flg:
            return
        value = self.__spin2.value()
        for ax in self.__axis():
            self.canvas.setTickLength(ax, value)

    def __chlen2(self):
        if self.__flg:
            return
        value = self.__spin5.value()
        for ax in self.__axis():
            self.canvas.setTickLength(ax, value, which='minor')

    def __chwid(self):
        if self.__flg:
            return
        axis = self.canvas.getSelectedAxis()
        value = self.__spin3.value()
        for ax in self.__axis():
            self.canvas.setTickWidth(ax, value)

    def __chwid2(self):
        if self.__flg:
            return
        axis = self.canvas.getSelectedAxis()
        value = self.__spin6.value()
        for ax in self.__axis():
            self.canvas.setTickWidth(ax, value, which='minor')

    def __minorChanged(self):
        if self.__flg:
            return
        value = self.__minor.isChecked()
        if self.__mode.currentText() == "none":
            value = False
        for ax in self.__axis():
            self.canvas.setTickVisible(ax, value, mirror=False, which='minor')
            if self.__mir.isChecked():
                self.canvas.setTickVisible(ax, value, mirror=True, which='minor')
            else:
                self.canvas.setTickVisible(ax, False, mirror=True, which='minor')

    def __loadstate(self):
        axis = self.canvas.getSelectedAxis()
        self.__flg = True
        self.__mir.setChecked(self.canvas.getTickVisible(axis, mirror=True))
        self.__minor.setChecked(self.canvas.getTickVisible(axis, which='minor'))
        if self.canvas.getTickVisible(axis):
            self.__mode.setCurrentIndex(['in', 'out', 'none'].index(self.canvas.getTickDirection(axis)))
        else:
            self.__mode.setCurrentIndex(2)
        self.__spin1.setValue(self.canvas.getAutoLocator(axis))
        self.__spin2.setValue(self.canvas.getTickLength(axis, 'major'))
        self.__spin3.setValue(self.canvas.getTickWidth(axis, 'major'))
        self.__spin4.setValue(self.canvas.getAutoLocator(axis, which='minor'))
        self.__spin5.setValue(self.canvas.getTickLength(axis, 'minor'))
        self.__spin6.setValue(self.canvas.getTickWidth(axis, 'minor'))
        self.__flg = False

    def OnAxisSelected(self, axis):
        self.__loadstate()


class AxisAndTickBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        layout = QVBoxLayout(self)
        layout_h1 = QHBoxLayout()
        layout_h1.addWidget(AxisRangeAdjustBox(canvas))
        layout_h1.addWidget(AxisAdjustBox(canvas))
        layout.addLayout(layout_h1)
        layout.addWidget(TickAdjustBox(canvas))
        self.setLayout(layout)
