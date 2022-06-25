import numpy as np

from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import ColorSelection


class _Model(QtCore.QAbstractItemModel):
    def __init__(self, canvas, type):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        canvas.annotationChanged.connect(lambda: self.layoutChanged.emit())

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            wave = self.canvas.getAnnotations(self.__type)[index.row()]
            if index.column() == 0:
                name = str(value)
                if len(name) != 0:
                    wave.setName(name)
            if index.column() == 2:
                z = int(value)
                wave.setZOrder(z)
        return super().setData(index, value, role)

    def data(self, index, role):
        if not index.isValid() or not role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        annot = self.canvas.getAnnotations(self.__type)[index.row()]
        if index.column() == 0:
            return annot.getName()
        elif index.column() == 1:
            return annot.getAxis()
        elif index.column() == 2:
            return annot.getZOrder()

    def flags(self, index):
        if index.column() in [0, 2]:
            return super().flags(index) | QtCore.Qt.ItemIsEditable
        else:
            return super().flags(index)

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.canvas.getAnnotations(self.__type))

    def columnCount(self, parent):
        return 3

    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row, column)
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        header = ["Name", "Axis", "Zorder"]
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return header[section]


class AnnotationSelectionBox(QtWidgets.QTreeView):
    selected = QtCore.pyqtSignal(list)

    def __init__(self, canvas, type='text'):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        self.__initlayout()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)

    def __initlayout(self):
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.__model = _Model(self.canvas, self.__type)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(lambda: self.selected.emit(self._selectedData()))

    def _selectedData(self):
        list = self.canvas.getAnnotations(self.__type)
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QtCore.QSize(150, 100)

    def OnAnnotationEdited(self):
        list = self.canvas.getAnnotations(self.__type)
        i = 1
        for item in list:
            self.__model.itemFromIndex(self.__model.index(len(list) - i, 0)).setText(item.name)
            i += 1

    def _buildContextMenu(self, qPoint):
        list = self._selectedData()
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction('Show', self, triggered=lambda: [data.setVisible(True) for data in list]))
        menu.addAction(QtWidgets.QAction('Hide', self, triggered=lambda: [data.setVisible(False) for data in list]))
        menu.addAction(QtWidgets.QAction('Remove', self, triggered=lambda: [self.canvas.removeAnnotation(data) for data in list]))
        menu.addAction(QtWidgets.QAction('Z order', self, triggered=self.__zorder))
        menu.exec_(QtGui.QCursor.pos())

    def __zorder(self):
        data = self._selectedData()
        d = _ZOrderDialog(np.max([item.getZOrder() for item in data]))
        if d.exec_():
            fr, step = d.getParams()
            for i, item in enumerate(data):
                item.setZOrder(fr + step * i)


class _ZOrderDialog(QtWidgets.QDialog):
    def __init__(self, init, parent=None):
        super().__init__(parent)
        self._from = QtWidgets.QSpinBox()
        self._from.setRange(0, 1000000)
        self._from.setValue(init)
        self._delta = QtWidgets.QSpinBox()
        self._delta.setRange(0, 1000000)
        self._delta.setValue(1)

        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("From"), 0, 0)
        g.addWidget(self._from, 1, 0)
        g.addWidget(QtWidgets.QLabel("Delta"), 0, 1)
        g.addWidget(self._delta, 1, 1)

        g.addWidget(QtWidgets.QPushButton("O K", clicked=self.accept), 2, 0)
        g.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject), 2, 1)

        self.setLayout(g)

    def getParams(self):
        return self._from.value(), self._delta.value()


class LineColorAdjustBox(ColorSelection):
    def __init__(self, canvas, type="line"):
        super().__init__()
        self.type = type
        self.canvas = canvas
        self.colorChanged.connect(self.__changed)

    def __changed(self):
        for d in self.data:
            d.setLineColor(self.getColor())

    def _loadstate(self):
        if len(self.data) != 0:
            self.setColor(self.data[0].getLineColor())

    def setData(self, data):
        self.data = data
        self._loadstate()


class LineStyleAdjustBox(QtWidgets.QGroupBox):
    __list = ['solid', 'dashed', 'dashdot', 'dotted', 'None']

    def __init__(self, canvas, type="line"):
        super().__init__("Line")
        self.type = type
        self.canvas = canvas

        self.__combo = QtWidgets.QComboBox()
        self.__combo.addItems(self.__list)
        self.__combo.activated.connect(self.__changeStyle)
        self.__spin1 = QtWidgets.QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__valueChange)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Type'), 0, 0)
        layout.addWidget(self.__combo, 1, 0)
        layout.addWidget(QtWidgets.QLabel('Width'), 0, 1)
        layout.addWidget(self.__spin1, 1, 1)

        self.setLayout(layout)

    def __changeStyle(self):
        res = self.__combo.currentText()
        for d in self.data:
            d.setLineStyle(res)

    def __valueChange(self):
        val = self.__spin1.value()
        for d in self.data:
            d.setLineWidth(val)

    def _loadstate(self):
        if len(self.data) != 0:
            d = self.data[0]
            self.__combo.setCurrentText(d.getLineStyle())
            self.__spin1.setValue(d.getLineWidth())

    def setData(self, data):
        self.data = data
        self._loadstate()
