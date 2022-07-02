import numpy as np
from matplotlib import cm
from matplotlib.lines import Line2D

from lys.Qt import QtCore, QtWidgets
from lys.widgets import ColormapSelection, ColorSelection


class _LineColorSideBySideDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Select colormap')
        self.__initlayout()

    def __initlayout(self):
        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QPushButton('O K', clicked=self.accept))
        h.addWidget(QtWidgets.QPushButton('CANCEL', clicked=self.reject))

        self.csel = ColormapSelection(opacity=False, log=False, reverse=True, gamma=False)

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self.csel)
        lay.addLayout(h)
        self.setLayout(lay)

    def getColor(self):
        return self.csel.currentColor()


class _LineStyleAdjustBox(QtWidgets.QGroupBox):
    __list = ['solid', 'dashed', 'dashdot', 'dotted', 'None']
    widthChanged = QtCore.pyqtSignal(float)
    styleChanged = QtCore.pyqtSignal(str)

    def __init__(self, canvas):
        super().__init__("Line")
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        self.__combo = QtWidgets.QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(lambda: self.styleChanged.emit(self.__combo.currentText()))

        self.__spin1 = QtWidgets.QDoubleSpinBox()
        self.__spin1.valueChanged.connect(lambda: self.widthChanged.emit(self.__spin1.value()))

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Type'), 0, 0)
        layout.addWidget(self.__combo, 1, 0)
        layout.addWidget(QtWidgets.QLabel('Width'), 0, 1)
        layout.addWidget(self.__spin1, 1, 1)
        self.setLayout(layout)

    def setWidth(self, width):
        self.__spin1.setValue(width)

    def setStyle(self, style):
        self.__combo.setCurrentText(style)

    def setEnabled(self, b):
        self.__combo.setEnabled(b)
        self.__spin1.setEnabled(b)


class _MarkerStyleAdjustBox(QtWidgets.QGroupBox):
    markerChanged = QtCore.pyqtSignal(str)
    markerFillingChanged = QtCore.pyqtSignal(str)
    markerSizeChanged = QtCore.pyqtSignal(float)
    markerThickChanged = QtCore.pyqtSignal(float)

    def __init__(self, canvas):
        super().__init__("Marker")
        self.canvas = canvas
        self.__list = list(Line2D.markers.values())
        self.__fillist = Line2D.fillStyles
        self.__initlayout()

    def __initlayout(self):
        gl = QtWidgets.QGridLayout()

        self.__combo = QtWidgets.QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(lambda: self.markerChanged.emit(self.__combo.currentText()))

        self.__spin1 = QtWidgets.QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.markerSizeChanged.emit)

        self.__fill = QtWidgets.QComboBox()
        self.__fill.addItems(self.__fillist)
        self.__fill.activated.connect(lambda: self.markerFillingChanged.emit(self.__fill.currentText()))

        self.__spin2 = QtWidgets.QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.markerThickChanged.emit)

        gl.addWidget(QtWidgets.QLabel('Type'), 0, 0)
        gl.addWidget(self.__combo, 1, 0)
        gl.addWidget(QtWidgets.QLabel('Size'), 2, 0)
        gl.addWidget(self.__spin1, 3, 0)
        gl.addWidget(QtWidgets.QLabel('Filling'), 0, 1)
        gl.addWidget(self.__fill, 1, 1)
        gl.addWidget(QtWidgets.QLabel('Thick'), 2, 1)
        gl.addWidget(self.__spin2, 3, 1)
        self.setLayout(gl)

    def setMarker(self, marker):
        self.__combo.setCurrentText(marker)

    def setMarkerFilling(self, filling):
        self.__fill.setCurrentText(filling)

    def setMarkerSize(self, size):
        self.__spin1.setValue(size)

    def setMarkerThick(self, thick):
        self.__spin2.setValue(thick)

    def setEnabled(self, b):
        self.__combo.setEnabled(b)
        self.__spin1.setEnabled(b)
        self.__fill.setEnabled(b)
        self.__spin2.setEnabled(b)


class AppearanceBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._lines = []

        self._color = ColorSelection()
        self._color.colorChanged.connect(lambda c: [line.setColor(c) for line in self._lines])
        self._side = QtWidgets.QPushButton('Side by Side', clicked=self.__sidebyside)

        self._style = _LineStyleAdjustBox(canvas)
        self._style.widthChanged.connect(lambda w: [line.setWidth(w) for line in self._lines])
        self._style.styleChanged.connect(lambda s: [line.setStyle(s) for line in self._lines])

        self._marker = _MarkerStyleAdjustBox(canvas)
        self._marker.markerChanged.connect(lambda val: [line.setMarker(val) for line in self._lines])
        self._marker.markerSizeChanged.connect(lambda val: [line.setMarkerSize(val) for line in self._lines])
        self._marker.markerFillingChanged.connect(lambda val: [line.setMarkerFilling(val) for line in self._lines])
        self._marker.markerThickChanged.connect(lambda val: [line.setMarkerThick(val) for line in self._lines])

        layout_h1 = QtWidgets.QHBoxLayout()
        layout_h1.addWidget(QtWidgets.QLabel('Color'))
        layout_h1.addWidget(self._color)
        layout_h1.addWidget(self._side)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_h1)
        layout.addWidget(self._style)
        layout.addWidget(self._marker)

        self.setLayout(layout)
        self.__setEnabled(False)

    def __sidebyside(self):
        d = _LineColorSideBySideDialog()
        res = d.exec_()
        if res == QtWidgets.QDialog.Accepted:
            c = d.getColor()
            if c == "" or c == "_r":
                return
            sm = cm.ScalarMappable(cmap=c)
            rgbas = sm.to_rgba(np.linspace(0, 1, len(self._lines)), bytes=True)
            rgbas = [('#{0:02x}{1:02x}{2:02x}').format(r, g, b) for r, g, b, a in rgbas]
            for line, color in zip(self._lines, rgbas):
                line.setColor(color)

    def setLines(self, lines):
        self._lines = lines
        if len(lines) != 0:
            self.__setEnabled(True)
            self._color.setColor(lines[0].getColor())
            self._style.setWidth(lines[0].getWidth())
            self._style.setStyle(lines[0].getStyle())
            self._marker.setMarker(lines[0].getMarker())
            self._marker.setMarkerSize(lines[0].getMarkerSize())
            self._marker.setMarkerFilling(lines[0].getMarkerFilling())
            self._marker.setMarkerThick(lines[0].getMarkerThick())
        else:
            self.__setEnabled(False)

    def __setEnabled(self, b):
        self._color.setEnabled(b)
        self._side.setEnabled(b)
        self._style.setEnabled(b)
        self._marker.setEnabled(b)
