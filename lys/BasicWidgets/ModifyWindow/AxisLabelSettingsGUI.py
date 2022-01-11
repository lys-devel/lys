from LysQt.QtWidgets import QGroupBox, QCheckBox, QDoubleSpinBox, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QWidget

from .FontGUI import FontSelector


class _AxisLabelAdjustBox(QGroupBox):
    def __init__(self, parent, canvas):
        super().__init__("Axis Label")
        self.__flg = False
        self._parent = parent
        self.canvas = canvas
        self.__initlayout()
        self.update()

    def __getAxes(self):
        if self._parent.isApplyAll():
            return self.canvas.axisList()
        else:
            return [self._parent.getCurrentAxis()]

    def __initlayout(self):
        self.__on = QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        self.__pos = QDoubleSpinBox()
        self.__pos.setRange(-1000, 1000)
        self.__pos.setSingleStep(0.02)
        self.__pos.valueChanged.connect(self.__posChanged)

        lay = QHBoxLayout()
        lay.addWidget(self.__on)
        lay.addWidget(QLabel('Position'))
        lay.addWidget(self.__pos)

        self.__label = QTextEdit()
        self.__label.setMinimumHeight(10)
        self.__label.setMaximumHeight(50)
        self.__label.textChanged.connect(self.__labelChanged)

        layout = QVBoxLayout()
        layout.addLayout(lay)
        layout.addWidget(self.__label)
        self.setLayout(layout)

    def update(self):
        self.__flg = True
        axis = self._parent.getCurrentAxis()
        self.__on.setChecked(self.canvas.getAxisLabelVisible(axis))
        self.__label.setPlainText(self.canvas.getAxisLabel(axis))
        self.__pos.setValue(self.canvas.getAxisLabelCoords(axis))
        self.__flg = False

    def __labelChanged(self):
        if self.__flg:
            return
        axis = self._parent.getCurrentAxis()
        self.canvas.setAxisLabel(axis, self.__label.toPlainText())

    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelVisible(axis, self.__on.isChecked())

    def __posChanged(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setAxisLabelCoords(axis, self.__pos.value())


class _TickLabelAdjustBox(QGroupBox):
    def __init__(self, parent, canvas):
        super().__init__("Tick Label")
        self.__flg = False
        self.canvas = canvas
        self._parent = parent
        self.__initlayout()
        self.update()
        self.canvas.axisChanged.connect(self.update)

    def update(self):
        self.__flg = True
        axis = self._parent.getCurrentAxis()
        self.__on.setChecked(self.canvas.getTickLabelVisible(axis))
        self.__mir.setChecked(self.canvas.getTickLabelVisible(axis, mirror=True))
        self.__mir.setEnabled(True)
        if axis == "Left" and self.canvas.axisIsValid("Right"):
            self.__mir.setEnabled(False)
        if axis == "Bottom" and self.canvas.axisIsValid("Top"):
            self.__mir.setEnabled(False)
        if axis == "Right":
            self.__mir.setEnabled(False)
        if axis == "Top":
            self.__mir.setEnabled(False)
        self.__flg = False

    def __getAxes(self):
        if self._parent.isApplyAll():
            return self.canvas.axisList()
        else:
            return [self._parent.getCurrentAxis()]

    def __initlayout(self):
        self.__on = QCheckBox('Put label')
        self.__on.stateChanged.connect(self.__visible)
        self.__mir = QCheckBox('Mirror')
        self.__mir.stateChanged.connect(self.__visible_mirror)
        layout = QHBoxLayout()
        layout.addWidget(self.__on)
        layout.addWidget(self.__mir)
        self.setLayout(layout)

    def __visible(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setTickLabelVisible(axis, self.__on.isChecked())
        self.update()

    def __visible_mirror(self):
        if self.__flg:
            return
        for axis in self.__getAxes():
            self.canvas.setTickLabelVisible(axis, self.__mir.isChecked(), mirror=True)
        self.update()


class AxisAndTickLabelBox(QWidget):
    def __init__(self, parent, canvas):
        super().__init__()
        self._axis = _AxisLabelAdjustBox(parent, canvas)
        self._tick = _TickLabelAdjustBox(parent, canvas)

        layout = QVBoxLayout(self)
        layout.addWidget(self._axis)
        layout.addWidget(self._tick)
        layout.addStretch()
        self.setLayout(layout)

    def update(self):
        self._axis.update()
        self._tick.update()


class AxisFontBox(QWidget):
    def __init__(self, parent, canvas):
        super().__init__()
        self._parent = parent
        self._canvas = canvas
        self._axis = FontSelector('Axis Font')
        self._axis.fontChanged.connect(self._axisChanged)
        self._tick = FontSelector('Tick Font')
        self._tick.fontChanged.connect(self._tickChanged)

        layout = QVBoxLayout(self)
        layout.addWidget(self._axis)
        layout.addWidget(self._tick)
        layout.addStretch()
        self.setLayout(layout)
        self.update()

    def _axisChanged(self, font):
        if self._parent.isApplyAll():
            axes = self._canvas.axisList()
        else:
            axes = [self._parent.getCurrentAxis()]
        for axis in axes:
            self._canvas.setAxisLabelFont(axis, **font)

    def _tickChanged(self, font):
        if self._parent.isApplyAll():
            axes = self._canvas.axisList()
        else:
            axes = [self._parent.getCurrentAxis()]
        for axis in axes:
            self._canvas.setTickLabelFont(axis, **font)

    def update(self):
        axis = self._parent.getCurrentAxis()
        self._axis.setFont(**self._canvas.getAxisLabelFont(axis))
        self._tick.setFont(**self._canvas.getTickLabelFont(axis))
