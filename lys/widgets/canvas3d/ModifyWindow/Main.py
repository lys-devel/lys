from lys.Qt import QtCore, QtWidgets
from .DataGUI import MeshSelectionBox3D, FilterEditWidget


class ModifyWidget3D(QtWidgets.QTabWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initLayout(canvas)
        self.__setEnabled(canvas)
        self.show()

    def __initLayout(self, canvas):
        self.tabBar().setStyleSheet("QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;} ")
        self.addTab(_VolumeTab(canvas), "Volume")
        self.addTab(_SurfaceTab(canvas), "Surface")
        self.addTab(_LineTab(canvas), "Line")
        self.addTab(_PointTab(canvas), "Point")

    def __setEnabled(self, canvas):
        self.setTabEnabled(0, len(canvas.getVolume()) != 0)
        self.setTabEnabled(1, len(canvas.getSurface()) != 0)
        self.setTabEnabled(2, len(canvas.getLine()) != 0)
        self.setTabEnabled(3, len(canvas.getPoint()) != 0)


class _VolumeTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._sel = MeshSelectionBox3D(canvas, "volume")
        self._filt = FilterEditWidget()

        self._sel.selected.connect(self._filt.setData)

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(self._filt, "Filter")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._sel)
        layout.addWidget(self._tab)
        self.setLayout(layout)


class _SurfaceTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._sel = MeshSelectionBox3D(canvas, "surface")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._sel)
        self.setLayout(layout)


class _LineTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._sel = MeshSelectionBox3D(canvas, "line")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._sel)
        self.setLayout(layout)


class _PointTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self._sel = MeshSelectionBox3D(canvas, "point")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._sel)
        self.setLayout(layout)