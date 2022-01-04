from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from lys import *
from lys.widgets import ScientificSpinBox


class DataSelectionBox(QTreeView):
    selected = pyqtSignal(list)

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

    def __init__(self, canvas, dim, type):
        super().__init__()
        self.canvas = canvas
        self.__type = type
        self.__initlayout()
        self.flg = False
        self._loadstate()
        canvas.dataChanged.connect(self._loadstate)

    def __initlayout(self):
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)
        self.__model = DataSelectionBox._Model(self.canvas)
        self.setModel(self.__model)
        self.selectionModel().selectionChanged.connect(self._onSelected)

    def _loadstate(self):
        self.flg = True
        list = self.canvas.getWaveData(self.__type)
        self.__model.clear()
        for i, data in enumerate(list):
            item = QStandardItem(data.getWave().name)
            self.__model.setItem(len(list) - 1 - i, 0, item)
            self.__model.setItem(len(list) - 1 - i, 1, QStandardItem(data.axis))
            #self.__model.setItem(len(list) - 1 - i, 2, QStandardItem(str(data.id)))
        self.flg = False

    def _onSelected(self):
        if self.flg:
            return
        self.flg = True
        self.selected.emit(self._selectedData())
        self.flg = False

    def _selectedData(self):
        list = self.canvas.getWaveData(self.__type)
        return [list[i.row()] for i in self.selectedIndexes() if i.column() == 0]

    def sizeHint(self):
        return QSize(150, 100)


class RightClickableSelectionBox(DataSelectionBox):
    def __init__(self, canvas, dim, type, *args, **kwargs):
        super().__init__(canvas, dim, type, *args, **kwargs)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)
        self.canvas = canvas
        self.__dim = dim

    def buildContextMenu(self, qPoint):
        menu = QMenu(self)
        menu.addAction(QAction('Show', self, triggered=lambda: self.__visible(True)))
        menu.addAction(QAction('Hide', self, triggered=lambda: self.__visible(False)))
        menu.addAction(QAction('Remove', self, triggered=self.__remove))
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
        menu.exec_(QCursor.pos())

    def __getWaves(self, type="Wave"):
        res = []
        for d in self._selectedData():
            if type == "Wave":
                res.append(d.getWave())
            else:
                res.append(d.getFilteredWave())
        return res

    def __visible(self, visible):
        for d in self._selectedData():
            d.setVisible(visible)

    def __remove(self):
        for d in self._selectedData():
            self.canvas.Remove(d)

    def __display(self, type, **kwargs):
        from lys import display
        display(*self.__getWaves(type), **kwargs)

    def __append(self, type, **kwargs):
        from lys import Graph
        g = Graph.active(exclude=self.canvas)
        for d in self.__getWaves(type):
            g.Append(d.getWave(), **kwargs)

    def __multicut(self, type):
        from lys import MultiCut
        for d in self.__getWaves(type):
            MultiCut(d)

    def __edit(self, type):
        from lys import Table
        t = Table()
        for d in self.__getWaves(type):
            t.Append(d.getWave())

    def __print(self, type):
        for d in self.__getWaves():
            print(d.getWave())

    def __process(self):
        from lys.filters import FiltersDialog

        class dialog(FiltersDialog):
            def __init__(self, data):
                super().__init__(data.getWave().data.ndim)
                self.applied.connect(data.setFilter)

        data = self.__getWaves()[0]
        d = dialog(data)
        if data.filter is not None:
            d.setFilter(data.filter)
        d.show()

    def __export(self, waveType):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            d = self.__getWaves(waveType)[0]
            d.export(path, type=type)

    def __send(self, waveType):
        from lys import glb
        d = self.__getWaves(waveType)[0]
        w = d.duplicate()
        text, ok = QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            w.name = text
            glb.shell().addObject(w, text)


class OffsetAdjustBox(QWidget):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.__flg = False

    def __initlayout(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.__offsetBox())
        vbox.addWidget(self.__sideBySideBox())
        self.setLayout(vbox)

    def __offsetBox(self):
        self.__spin1 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('x offset'))
        self.__spin2 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('y offset'))
        self.__spin3 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('x muloffset'))
        self.__spin4 = ScientificSpinBox(valueChanged=lambda: self.__dataChanged('y muloffset'))
        gl = QGridLayout()
        gl.addWidget(QLabel('x offset'), 0, 0)
        gl.addWidget(QLabel('y offset'), 0, 1)
        gl.addWidget(QLabel('x muloffset'), 2, 0)
        gl.addWidget(QLabel('y muloffset'), 2, 1)
        gl.addWidget(self.__spin1, 1, 0)
        gl.addWidget(self.__spin3, 3, 0)
        gl.addWidget(self.__spin2, 1, 1)
        gl.addWidget(self.__spin4, 3, 1)
        gr1 = QGroupBox('Offset')
        gr1.setLayout(gl)
        return gr1

    def __sideBySideBox(self):
        self.__spinfrom = ScientificSpinBox()
        self.__spindelta = ScientificSpinBox()
        btn = QPushButton('Set', clicked=self.__sidebyside)
        self.__type = QComboBox()
        self.__type.addItems(['y offset', 'x offset', 'y muloffset', 'x muloffset'])

        g2 = QGridLayout()
        g2.addWidget(QLabel('from'), 0, 0)
        g2.addWidget(self.__spinfrom, 1, 0)
        g2.addWidget(QLabel('delta'), 0, 1)
        g2.addWidget(self.__spindelta, 1, 1)
        g2.addWidget(QLabel('type'), 0, 2)
        g2.addWidget(self.__type, 1, 2)
        g2.addWidget(btn, 2, 1)

        gr2 = QGroupBox('Side by side')
        gr2.setLayout(g2)
        return gr2

    def __sidebyside(self):
        f = self.__spinfrom.value()
        delta = self.__spindelta.value()
        for i, d in enumerate(self._data):
            r = list(d.getOffset())
            if self.__type.currentText() == 'x offset':
                r[0] = f + delta * i
            if self.__type.currentText() == 'y offset':
                r[1] = f + delta * i
            if self.__type.currentText() == 'x muloffset':
                r[2] = f + delta * i
            if self.__type.currentText() == 'y muloffset':
                r[3] = f + delta * i
            d.setOffset(r)

    def __dataChanged(self, type):
        if not self.__flg:
            for d in self._data:
                r = list(d.getOffset())
                if type == 'x offset':
                    r[0] = self.__spin1.value()
                if type == 'y offset':
                    r[1] = self.__spin2.value()
                if type == 'x muloffset':
                    r[2] = self.__spin3.value()
                if type == 'y muloffset':
                    r[3] = self.__spin4.value()
                d.setOffset(r)

    def setData(self, data):
        self._data = data
        self.__flg = True
        if len(data) != 0:
            off = data[0].getOffset()
            self.__spin1.setValue(off[0])
            self.__spin2.setValue(off[1])
            self.__spin3.setValue(off[2])
            self.__spin4.setValue(off[3])
        self.__flg = False
