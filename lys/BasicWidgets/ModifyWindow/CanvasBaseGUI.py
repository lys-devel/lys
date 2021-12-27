from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import numpy as np
from lys import *
from lys.widgets import ScientificSpinBox


class DataSelectionBox(QTreeView):
    class _Model(QStandardItemModel):
        def __init__(self, canvas):
            super().__init__(0, 3)
            self.setHeaderData(0, Qt.Horizontal, 'Line')
            self.setHeaderData(1, Qt.Horizontal, 'Axis')
            self.setHeaderData(2, Qt.Horizontal, 'Zorder')
            self.canvas = canvas

        def clear(self):
            super().clear()
            self.setColumnCount(3)
            self.setHeaderData(0, Qt.Horizontal, 'Line')
            self.setHeaderData(1, Qt.Horizontal, 'Axis')
            self.setHeaderData(2, Qt.Horizontal, 'Zorder')

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
                    self.canvas.moveItem(f)
                else:
                    self.canvas.moveItem(f, self.item(row, 2).text())
            else:
                self.canvas.moveItem(f, self.item(self.itemFromIndex(parent).row(), 2).text())
            return False

    def __init__(self, canvas, dim, contour=False, vector=False):
        super().__init__()
        self.canvas = canvas
        self.__dim = dim
        self._contour = contour
        self._vector = vector
        self.__initlayout()
        self.flg = False
        self._loadstate()
        canvas.dataChanged.connect(self.OnDataChanged)
        canvas.dataSelected.connect(self.OnDataSelected)

    def __initlayout(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model = DataSelectionBox._Model(self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self.OnSelected)

    def OnDataSelected(self):
        indexes = self.canvas.getSelectedIndexes(self.__dim)
        list = self.canvas.getWaveData(self.__dim)
        selm = self.selectionModel()
        for i in range(len(list)):
            index0 = self.__model.index(len(list) - i - 1, 0)
            index1 = self.__model.index(len(list) - i - 1, 1)
            index2 = self.__model.index(len(list) - i - 1, 2)
            id = float(self.__model.itemFromIndex(index2).text())
            if id in indexes:
                selm.select(index0, QItemSelectionModel.Select)
                selm.select(index1, QItemSelectionModel.Select)
                selm.select(index2, QItemSelectionModel.Select)
            else:
                selm.select(index0, QItemSelectionModel.Deselect)
                selm.select(index1, QItemSelectionModel.Deselect)
                selm.select(index2, QItemSelectionModel.Deselect)

    def _loadstate(self):
        self.flg = True
        list = self.canvas.getWaveData(self.__dim, contour=self._contour, vector=self._vector)
        self.__model.clear()
        i = 1
        for l in list:
            self.__model.setItem(len(list) - i, 0, QStandardItem(l.wave.name))
            self.__model.setItem(len(list) - i, 1, QStandardItem(l.axis))
            self.__model.setItem(len(list) - i, 2, QStandardItem(str(l.id)))
            i += 1
        self.OnDataSelected()
        self.flg = False

    def OnSelected(self):
        if self.flg:
            return
        self.flg = True
        indexes = self.selectedIndexes()
        ids = []
        for i in indexes:
            if i.column() == 2:
                ids.append(int(self.__model.itemFromIndex(i).text()))
        self.canvas.setSelectedIndexes(self.__dim, ids)
        self.flg = False

    def OnDataChanged(self):
        self._loadstate()

    def sizeHint(self):
        return QSize(150, 100)


class DataShowButton(QPushButton):
    def __init__(self, canvas, dim, flg):
        if flg:
            super().__init__('Show')
        else:
            super().__init__('Hide')
        self.__flg = flg
        self.canvas = canvas
        self.clicked.connect(self.__clicked)
        self.__dim = dim

    def __clicked(self):
        list = self.canvas.getSelectedIndexes(self.__dim)
        if self.__flg:
            self.canvas.showData(self.__dim, list)
        else:
            self.canvas.hideData(self.__dim, list)


class RightClickableSelectionBox(DataSelectionBox):
    def __init__(self, canvas, dim, *args, **kwargs):
        super().__init__(canvas, dim, *args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas = canvas
        self.__dim = dim

    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        list = self.canvas.getSelectedIndexes(self.__dim)
        menu.addAction(QAction('Show', self, triggered=lambda: self.canvas.showData(self.__dim, list)))
        menu.addAction(QAction('Hide', self, triggered=lambda: self.canvas.hideData(self.__dim, list)))
        menu.addAction(QAction('Remove', self, triggered=lambda: self.canvas.Remove(list)))
        menu.addAction(QAction('Print', self, triggered=self.__print))
        menu.addAction(QAction('Process', self, triggered=self.__process))

        raw = menu.addMenu("Raw data")
        raw.addAction(QAction('Display', self, triggered=lambda: self.__display("Wave")))
        raw.addAction(QAction('Append', self, triggered=lambda: self.__append("Wave")))
        raw.addAction(QAction('MultiCut', self, triggered=lambda: self.__multicut("Wave")))
        if self.__dim == 3 or self.__dim == "rgb":
            raw.addAction(QAction('Append as Vector', self, triggered=lambda: self.__append("Wave", vector=True)))
        raw.addAction(QAction('Edit', self, triggered=lambda: self.__edit("Wave")))
        raw.addAction(QAction('Export', self, triggered=lambda: self.__export("Wave")))
        raw.addAction(QAction('Send to shell', self, triggered=lambda: self.__send("Wave")))

        pr = menu.addMenu("Processed data")
        pr.addAction(QAction('Display', self, triggered=lambda: self.__display("ProcessedWave")))
        pr.addAction(QAction('Append', self, triggered=lambda: self.__append("ProcessedWave")))
        pr.addAction(QAction('MultiCut', self, triggered=lambda: self.__multicut("ProcessedWave")))
        if self.__dim == 3 or self.__dim == "rgb":
            pr.addAction(QAction('Append as Vector', self, triggered=lambda: self.__append("ProcessedWave", vector=True)))
        pr.addAction(QAction('Edit', self, triggered=lambda: self.__edit("ProcessedWave")))
        pr.addAction(QAction('Export', self, triggered=lambda: self.__export("ProcessedWave")))
        pr.addAction(QAction('Send to shell', self, triggered=lambda: self.__send("ProcessedWave")))

        action = menu.exec_(QCursor.pos())

    def __display(self, type, vector=False):
        from lys import Graph
        g = Graph()
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))
        for d in data:
            if type == "Wave":
                g.Append(d.wave, vector=vector)
            else:
                g.Append(d.filteredWave, vector=vector)

    def __append(self, type, vector=False):
        from lys import Graph
        g = Graph.active(exclude=self.canvas)
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))
        for d in data:
            if type == "Wave":
                g.Append(d.wave, vector=vector)
            else:
                g.Append(d.filteredWave, vector=vector)

    def __getWaves(self, type):
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))
        res = []
        for d in data:
            if type == "Wave":
                res.append(d.wave)
            else:
                res.append(d.filteredWave)
        return res

    def __multicut(self, type):
        from lys import MultiCut
        for d in self.__getWaves(type):
            MultiCut(d)

    def __edit(self, type):
        from lys import Table
        t = Table()
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))
        for d in data:
            if type == "Wave":
                t.Append(d.wave)
            else:
                t.Append(d.filteredWave)

    def __print(self):
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))
        for d in data:
            print(d.wave)

    def __process(self):
        from lys.filters import FiltersDialog

        class dialog(FiltersDialog):
            def __init__(self, data):
                super().__init__(data.wave.data.ndim)
                self.data = data
                self.applied.connect(self.__set)

            def __set(self, f):
                self.data.filter = f
                self.data.wave.modified.emit(self.data.wave)
        data = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))[0]
        d = dialog(data)
        if data.filter is not None:
            d.setFilter(data.filter)
        d.show()

    def __export(self, waveType):
        filt = ""
        list = self.canvas.getSelectedIndexes(self.__dim)
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            d = self.canvas.getDataFromIndexes(self.__dim, list)[0]
            if waveType == "Wave":
                d.wave.export(path, type=type)
            else:
                d.filteredWave.export(path, type=type)

    def __send(self, waveType):
        from lys import glb
        d = self.canvas.getDataFromIndexes(self.__dim, self.canvas.getSelectedIndexes(self.__dim))[0]
        if waveType == "Wave":
            w = d.wave.duplicate()
        else:
            w = d.filteredWave.duplicate()
        text, ok = QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            w.name = text
            glb.shell().addObject(w, text)


class OffsetAdjustBox(QWidget):
    def __init__(self, canvas, dim):
        super().__init__()
        self.canvas = canvas
        canvas.dataSelected.connect(self.OnDataSelected)
        self.__initlayout()
        self.__flg = False
        self.__dim = dim

    def __initlayout(self):
        vbox = QVBoxLayout()
        gr1 = QGroupBox('Offset')
        gl = QGridLayout()
        self.__spin1 = ScientificSpinBox(valueChanged=self.__dataChanged)
        self.__spin2 = ScientificSpinBox(valueChanged=self.__dataChanged)
        self.__spin3 = ScientificSpinBox(valueChanged=self.__dataChanged)
        self.__spin4 = ScientificSpinBox(valueChanged=self.__dataChanged)
        gl.addWidget(QLabel('x offset'), 0, 0)
        gl.addWidget(self.__spin1, 1, 0)
        gl.addWidget(QLabel('x muloffset'), 2, 0)
        gl.addWidget(self.__spin3, 3, 0)
        gl.addWidget(QLabel('y offset'), 0, 1)
        gl.addWidget(self.__spin2, 1, 1)
        gl.addWidget(QLabel('y muloffset'), 2, 1)
        gl.addWidget(self.__spin4, 3, 1)
        gr1.setLayout(gl)
        vbox.addWidget(gr1)

        gr2 = QGroupBox('Side by side')
        g2 = QGridLayout()
        self.__spinfrom = QDoubleSpinBox()
        self.__spinfrom.setRange(-np.inf, np.inf)
        self.__spindelta = QDoubleSpinBox()
        self.__spindelta.setRange(-np.inf, np.inf)
        g2.addWidget(QLabel('from'), 0, 0)
        g2.addWidget(self.__spinfrom, 1, 0)
        g2.addWidget(QLabel('delta'), 0, 1)
        g2.addWidget(self.__spindelta, 1, 1)

        btn = QPushButton('Set', clicked=self.__sidebyside)
        self.__type = QComboBox()
        self.__type.addItem('y offset')
        self.__type.addItem('x offset')
        self.__type.addItem('y muloffset')
        self.__type.addItem('x muloffset')
        g2.addWidget(QLabel('type'), 0, 2)
        g2.addWidget(self.__type, 1, 2)
        g2.addWidget(btn, 2, 1)
        gr2.setLayout(g2)
        vbox.addWidget(gr2)

        self.setLayout(vbox)

    def __sidebyside(self):
        indexes = self.canvas.getSelectedIndexes(self.__dim)
        f = self.__spinfrom.value()
        d = self.__spindelta.value()
        for i in range(len(indexes)):
            r = list(self.canvas.getOffset(indexes[i])[0])
            if self.__type.currentText() == 'x offset':
                r[0] = f + d * i
            if self.__type.currentText() == 'y offset':
                r[1] = f + d * i
            if self.__type.currentText() == 'x muloffset':
                r[2] = f + d * i
            if self.__type.currentText() == 'y muloffset':
                r[3] = f + d * i
            self.canvas.setOffset(r, indexes[i])

    def __dataChanged(self):
        if not self.__flg:
            indexes = self.canvas.getSelectedIndexes(self.__dim)
            self.__flg = True
            self.canvas.setOffset((self.__spin1.value(), self.__spin2.value(), self.__spin3.value(), self.__spin4.value()), indexes)
            self.__flg = False

    def OnDataSelected(self):
        self.__loadstate()

    def __loadstate(self):
        if self.__flg:
            return
        self.__flg = True
        indexes = self.canvas.getSelectedIndexes(self.__dim)
        if len(indexes) == 0:
            self.__flg = False
            return
        data = self.canvas.getOffset(indexes)[0]
        self.__spin1.setValue(data[0])
        self.__spin2.setValue(data[1])
        self.__spin3.setValue(data[2])
        self.__spin4.setValue(data[3])
        self.__flg = False
