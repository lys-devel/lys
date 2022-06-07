from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import ColorSelection


class _Model(QtGui.QStandardItemModel):
    def __init__(self, canvas, type='text'):
        super().__init__(0, 3)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Line')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Axis')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Zorder')
        self.canvas = canvas
        self.type = type

    def clear(self):
        super().clear()
        self.setColumnCount(3)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Annotation')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Axis')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Zorder')
    """
    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeData(self, indexes):
        mimedata = QMimeData()
        data = []
        for i in indexes:
            if i.column() != 2:
                continue
            t = eval(self.itemFromIndex(i).text())
            data.append(t)
        mimedata.setData('index', str(data).encode('utf-8'))
        mimedata.setText(str(data))
        return mimedata

    def mimeTypes(self):
        return ['index']

    def dropMimeData(self, data, action, row, column, parent):
        f = eval(data.text())
        par = self.itemFromIndex(parent)
        if par is None:
            if row == -1 and column == -1:
                self.canvas.moveAnnotation(f, type=self.type)
            else:
                self.canvas.moveAnnotation(f, self.item(row, 2).text(), type=self.type)
        else:
            self.canvas.moveAnnotation(f, self.item(self.itemFromIndex(parent).row(), 2).text(), type=self.type)
        self.canvas._emitAnnotationChanged()
        return False
    """


class AnnotationSelectionBox(QtWidgets.QTreeView):
    selected = QtCore.pyqtSignal(list)

    def __init__(self, canvas, type='text'):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        self.__initlayout()
        self._loadstate()
        self.canvas.annotationChanged.connect(self._loadstate)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.flg = False

    def __initlayout(self):
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model = _Model(self.canvas, self.__type)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self._onSelected)

    def _loadstate(self):
        self.flg = True
        selected = self._selectedData()
        list = self.canvas.getAnnotations(self.__type)
        self.__model.clear()
        for i, data in enumerate(list):
            self.__model.setItem(i, 0, QtGui.QStandardItem(data.getName()))
            self.__model.setItem(i, 1, QtGui.QStandardItem(data.getAxis()))
            self.__model.setItem(i, 2, QtGui.QStandardItem(str(data.getZOrder())))
            if data in selected:
                index = self.__model.item(i).index()
                self.selectionModel().select(index, QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
        self.flg = False

    def _onSelected(self):
        if self.flg:
            return
        self.flg = True
        self.selected.emit(self._selectedData())
        self.flg = False

    def _selectedData(self):
        list = self.canvas.getAnnotations(self.__type)
        if len(list) != self.__model.rowCount():
            return []
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QtCore.QSize(150, 100)

    def OnAnnotationEdited(self):
        list = self.canvas.getAnnotations(self.__type)
        i = 1
        for item in list:
            self.__model.itemFromIndex(self.__model.index(len(list) - i, 0)).setText(item.name)
            i += 1

    def buildContextMenu(self, qPoint):
        menu = QtWidgets.QMenu(self)
        menulabels = ['show', 'hide', 'remove']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QtGui.QCursor.pos())
        if action is None:
            return

        list = self._selectedData()
        for data in list:
            if action.text() == 'show':
                data.setVisible(True)
            elif action.text() == 'hide':
                data.setVisible(False)
            elif action.text() == 'remove':
                self.canvas.removeAnnotation(data)


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
