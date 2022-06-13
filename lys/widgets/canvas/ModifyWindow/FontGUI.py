from lys.Qt import QtCore, QtWidgets
from lys.widgets import ColorSelection

from ..interface import FontInfo


class FontSelector(QtWidgets.QGroupBox):
    fontChanged = QtCore.pyqtSignal(dict)

    def __init__(self, name):
        super().__init__(name)
        self.__flg = False
        self.__initlayout()

    def __initlayout(self):
        self.__font = QtWidgets.QComboBox()
        self.__font.addItems(FontInfo.fonts())
        self.__font.activated.connect(self.__fontChanged)
        self.__size = QtWidgets.QDoubleSpinBox()
        self.__size.valueChanged.connect(self.__fontChanged)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__fontChanged)

        lay = QtWidgets.QHBoxLayout()
        lay.addWidget(QtWidgets.QLabel('Size'))
        lay.addWidget(self.__size)
        lay.addWidget(QtWidgets.QLabel('Color'))
        lay.addWidget(self.__color)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.__font)
        layout.addLayout(lay)
        self.setLayout(layout)

    def setFont(self, family, size=10, color="#000000"):
        self.__flg = True
        self.__font.setCurrentText(family)
        self.__size.setValue(size)
        self.__color.setColor(color)
        self.__flg = False

    def getFont(self):
        return {"family": self.__font.currentText(), "size": self.__size.value(), "color": self.__color.getColor()}

    def __fontChanged(self):
        if self.__flg:
            return
        self.fontChanged.emit(self.getFont())


class FontSelectBox(QtWidgets.QGroupBox):
    def __init__(self, canvas, name='Default'):
        super().__init__(name + ' Font')
        self.canvas = canvas
        self.__flg = False
        self.__name = name
        FontInfo.loadFonts()
        self.__initlayout()
        self.__loadstate()
        self.canvas.fontChanged.connect(self.__onFontChanged)

    def __onFontChanged(self, name):
        if name == self.__name or name == 'Default':
            self.__loadstate()

    def __initlayout(self):
        self.__font = QtWidgets.QComboBox()
        font = self.canvas.getCanvasFont(self.__name)
        d = font.family
        for f in FontInfo._fonts:
            self.__font.addItem(f)
        if d not in FontInfo._fonts:
            self.__font.addItem(d)
        self.__font.activated.connect(self.__fontChanged)
        self.__def = QtWidgets.QCheckBox('Use default')
        self.__def.stateChanged.connect(self.__setdefault)
        self.__size = QtWidgets.QDoubleSpinBox()
        self.__size.valueChanged.connect(self.__fontChanged)
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__fontChanged)

        lay = QtWidgets.QHBoxLayout()
        if not self.__name == 'Default':
            lay.addWidget(self.__def)
        lay.addWidget(QtWidgets.QLabel('Size'))
        lay.addWidget(self.__size)
        lay.addWidget(QtWidgets.QLabel('Color'))
        lay.addWidget(self.__color)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.__font)
        layout.addLayout(lay)
        self.setLayout(layout)

    def __loadstate(self):
        self.__flg = True
        font = self.canvas.getCanvasFont(self.__name)
        if font.family in FontInfo._fonts:
            self.__font.setCurrentIndex(FontInfo._fonts.index(font.family))
        self.__size.setValue(font.size)
        self.__color.setColor(font.color)
        self.__def.setChecked(self.canvas.getCanvasFontDefault(self.__name))
        self.__flg = False

    def __fontChanged(self):
        if self.__flg:
            return
        font = FontInfo(self.__font.currentText(), self.__size.value(), self.__color.getColor())
        self.canvas.setCanvasFont(font, self.__name)

    def __setdefault(self):
        if self.__flg:
            return
        val = self.__def.isChecked()
        self.canvas.setCanvasFontDefault(val, self.__name)


class FontSelectWidget(QtWidgets.QGroupBox):
    fontChanged = QtCore.pyqtSignal()

    def __init__(self, canvas, name='Default'):
        super().__init__('Font')
        self.canvas = canvas
        self.__name = name
        FontInfo.loadFonts()
        self.__initlayout()
        self.setFont(self.canvas.getCanvasFont(self.__name))
        self.setFontDefault(True)
        self.canvas.fontChanged.connect(self.__onFontChanged)

    def __onFontChanged(self, name):
        if name == self.__name and self.__def.isChecked():
            self.setFont(self.canvas.getCanvasFont(self.__name))

    def __initlayout(self):
        layout = QtWidgets.QVBoxLayout()
        lay = QtWidgets.QHBoxLayout()
        self.__font = QtWidgets.QComboBox()

        for f in FontInfo._fonts:
            self.__font.addItem(f)
        font = self.canvas.getCanvasFont(self.__name)
        d = font.family
        if d not in FontInfo._fonts:
            self.__font.addItem(d)
        self.__font.activated.connect(self.__Changed)
        layout.addWidget(self.__font)
        self.__def = QtWidgets.QCheckBox('Use default')
        self.__def.stateChanged.connect(self.__Changed)
        lay.addWidget(self.__def)
        lay.addWidget(QtWidgets.QLabel('Size'))
        self.__size = QtWidgets.QDoubleSpinBox()
        self.__size.valueChanged.connect(self.__Changed)
        lay.addWidget(self.__size)
        lay.addWidget(QtWidgets.QLabel('Color'))
        self.__color = ColorSelection()
        self.__color.colorChanged.connect(self.__Changed)
        lay.addWidget(self.__color)
        layout.addLayout(lay)
        self.setLayout(layout)

    def getFont(self):
        if self.__def.isChecked():
            return self.canvas.getCanvasFont(self.__name)
        return FontInfo(self.__font.currentText(), self.__size.value(), self.__color.getColor())

    def setFont(self, font):
        if font.family in FontInfo._fonts:
            self.__font.setCurrentIndex(FontInfo._fonts.index(font.family))
            self.__size.setValue(font.size)
            self.__color.setColor(font.color)

    def setFontDefault(self, b):
        self.__def.setChecked(b)

    def getFontDefault(self):
        return self.__def.isChecked()

    def __Changed(self):
        if self.__def.isChecked():
            self.setFont(self.canvas.getCanvasFont(self.__name))
        self.fontChanged.emit()