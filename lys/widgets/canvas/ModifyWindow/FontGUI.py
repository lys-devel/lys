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

    def setFont(self, fname, size=10, color="#000000"):
        self.__flg = True
        self.__font.setCurrentText(fname)
        self.__size.setValue(size)
        self.__color.setColor(color)
        self.__flg = False

    def getFont(self):
        return {"fname": self.__font.currentText(), "size": self.__size.value(), "color": self.__color.getColor()}

    def __fontChanged(self):
        if self.__flg:
            return
        self.fontChanged.emit(self.getFont())
