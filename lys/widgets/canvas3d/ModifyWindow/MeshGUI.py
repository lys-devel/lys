from lys.Qt import QtWidgets
from lys.widgets import ColorSelection, ColormapSelection
from lys.decorators import avoidCircularReference

class MeshAppearanceBox(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._canvas = canvas
        self.__initLayout(canvas)
        self.__setEnabled(False)

    def __initLayout(self, canvas):
        self._color = _ColorBox(canvas)
        self._edge = _EdgeBox(canvas)
        self._mesh = _MeshBox(canvas)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._color)
        layout.addWidget(self._edge)
        layout.addWidget(self._mesh)
        layout.addStretch()

        self.setLayout(layout)

    def __setEnabled(self, b):
        self._color.setEnabled(b)
        self._edge.setEnabled(b)
        self._mesh.setEnabled(b)

    def setData(self, data):
        if len(data) != 0:
            self.__setEnabled(True)
            self._mesh.setData(data)
            self._edge.setData(data)
            self._color.setData(data)
        else:
            self.__setEnabled(False)


class _MeshBox(QtWidgets.QGroupBox):
    def __init__(self, canvas):
        super().__init__("Mesh")
        self._canvas = canvas
        self.__initLayout()
        self._data = []

    def __initLayout(self):
        self._check = QtWidgets.QCheckBox("Show", toggled=self.__toggle)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._check)
        self.setLayout(layout)

    @avoidCircularReference
    def __toggle(self, *args, **kwargs):
        for d in self._data:
            d.showMeshes(self._check.isChecked())

    @avoidCircularReference
    def setData(self, data):
        self._data = data
        if len(data) != 0:
            self._check.setChecked(data[0].meshesVisible())


class _ColorBox(QtWidgets.QGroupBox):
    def __init__(self, canvas):
        super().__init__("Color")
        self._canvas = canvas
        self.__initLayout()

    def __initLayout(self):
        self._type = QtWidgets.QComboBox()
        self._type.addItems(["scalars", "color"])
        self._type.currentTextChanged.connect(self.__changeType)

        self._color = ColorSelection()
        self._color.setColor("#cccccc")
        self._color.colorChanged.connect(self.__change)
        self._color.hide()
        self._cmap = ColormapSelection(opacity=False, log=False, gamma=False)
        self._cmap.setColormap("viridis")
        self._cmap.colorChanged.connect(self.__change)

        self._label_color = QtWidgets.QLabel("Color")
        self._label_color.hide()
        self._label_cmap = QtWidgets.QLabel("Colormap")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Type"), 0, 0)
        layout.addWidget(self._label_color, 1, 0)
        layout.addWidget(self._label_cmap, 2, 0)
        layout.addWidget(self._type, 0, 1)
        layout.addWidget(self._color, 1, 1)
        layout.addWidget(self._cmap, 2, 1)
        self.setLayout(layout)

    def __changeType(self, type):
        if type=="scalars":
            self._color.hide()
            self._cmap.show()
            self._label_color.hide()
            self._label_cmap.show()
        else:
            self._color.show()
            self._cmap.hide()
            self._label_color.show()
            self._label_cmap.hide()
        self.__change()

    @avoidCircularReference
    def __change(self, *args, **kwargs):
        for d in self._data:
            if self._type.currentText() == "scalars":
                d.setColor(self._cmap.currentColor(), "scalars")
            else:
                d.setColor(self._color.getColor(), "color")            

    @avoidCircularReference
    def setData(self, data):
        self._data = data
        if len(data) != 0:
            type = data[0].getColorType()
            self._type.setCurrentText(type)
            if type == "scalars":
                self._cmap.setColormap(data[0].getColor())
                pass
            else:
                self._color.setColor(data[0].getColor())


class _EdgeBox(QtWidgets.QGroupBox):
    def __init__(self, canvas):
        super().__init__("Edge")
        self._canvas = canvas
        self.__initLayout()
        self._data = []

    def __initLayout(self):
        self._check = QtWidgets.QCheckBox("Show", toggled=self.__toggle)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._check)
        self.setLayout(layout)

    @avoidCircularReference
    def __toggle(self, *args, **kwargs):
        for d in self._data:
            d.showEdges(self._check.isChecked())

    @avoidCircularReference
    def setData(self, data):
        self._data = data
        if len(data) != 0:
            self._check.setChecked(data[0].edgesVisible())