from lys import filters, Wave, edit, glb, multicut, append, display
from lys.Qt import QtWidgets, QtCore, QtGui
from lys.widgets import CanvasBase


class _ChildWavesModel(QtCore.QAbstractItemModel):
    def __init__(self, obj):
        super().__init__()
        self.obj = obj
        obj.childWavesChanged.connect(lambda: self.layoutChanged.emit())

    def data(self, index, role):
        item = index.internalPointer()
        if not index.isValid() or item is None:
            return QtCore.QVariant()
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.name()
            elif index.column() == 1:
                axes = tuple(ax + 1 for ax in item.getAxes())
                return str(axes)
            elif index.column() == 2:
                p = item.postProcess()
                if p is None:
                    return "-"
                else:
                    return str(len(p.getFilters())) + " filters"
        elif role == QtCore.Qt.ForegroundRole:
            if item.isEnabled():
                return QtGui.QBrush(QtGui.QColor("black"))
            else:
                return QtGui.QBrush(QtGui.QColor("gray"))

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        return len(self.obj.getChildWaves())

    def columnCount(self, parent):
        return 3

    def index(self, row, column, parent):
        if not parent.isValid():
            if row < len(self.obj.getChildWaves()):
                return self.createIndex(row, column, self.obj.getChildWaves()[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        return QtCore.QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if section == 0:
                return "Name"
            elif section == 1:
                return "Axes"
            else:
                return "Postprocess"


class ChildWavesGUI(QtWidgets.QTreeView):
    def __init__(self, obj, dispfunc, parent=None):
        super().__init__(parent)
        self.obj = obj
        self.__disp = dispfunc
        self.setModel(_ChildWavesModel(obj))
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.buildContextMenu)

    def buildContextMenu(self):
        menu = QtWidgets.QMenu(self)
        connected = QtWidgets.QMenu("Connected")
        copied = QtWidgets.QMenu("Copied")
        menu.addMenu(connected)
        menu.addMenu(copied)

        w = self._getObj()
        types = CanvasBase.dataTypes(w)


        if len(types) == 1 or len(types)==2 and "vector" in types:
            connected.addAction(QtWidgets.QAction("Display in grid", self, triggered=lambda: self.__disp(self._getItem())))
        else:
            g = QtWidgets.QMenu("Display in grid")
            for t in types:
                g.addAction(self.__createAction(t, self.__disp, "copied"))
            connected.addMenu(g)

        if len(types) == 1:
            connected.addAction(QtWidgets.QAction("Display as graph", self, triggered=lambda: self.__disp(self._getItem(), type="graph")))
            connected.addAction(QtWidgets.QAction("Append", self, triggered=lambda: append(self._getObj())))
        else:
            d = QtWidgets.QMenu("Display as graph")
            a = QtWidgets.QMenu("Append")
            for t in types:
                d.addAction(self.__createAction(t, self.__disp, "copied", type="graph"))
                a.addAction(self.__createAction(t, append, "copied"))
            connected.addMenu(d)
            connected.addMenu(a)
        connected.addAction(QtWidgets.QAction("Edit", self, triggered=lambda: edit(self._getObj())))
        connected.addAction(QtWidgets.QAction("Send to shell", self, triggered=self._shell))

        if len(types) == 1:
            copied.addAction(QtWidgets.QAction("Display", self, triggered=lambda: display(self._getObj("copied"))))
            copied.addAction(QtWidgets.QAction("Append", self, triggered=lambda: append(self._getObj("copied"))))
        else:
            dc = QtWidgets.QMenu("Display")
            ac = QtWidgets.QMenu("Append")
            for t in types:
                dc.addAction(self.__createAction(t, display, "copied"))
                ac.addAction(self.__createAction(t, append, "copied"))
            copied.addMenu(dc)
            copied.addMenu(ac)
        copied.addAction(QtWidgets.QAction("MultiCut", self, triggered=lambda: multicut(self._getObj("copied"))))
        copied.addAction(QtWidgets.QAction("Edit", self, triggered=lambda: edit(self._getObj("copied"))))
        copied.addAction(QtWidgets.QAction("Export", self, triggered=lambda: self._export(type="copied")))
        copied.addAction(QtWidgets.QAction("Send to shell", self, triggered=lambda: self._shell(type="copied")))

        menu.addSeparator()
  
        menu.addAction(QtWidgets.QAction("Enable", self, triggered=lambda: self._getItem().setEnabled(True)))
        menu.addAction(QtWidgets.QAction("Disable", self, triggered=lambda: self._getItem().setEnabled(False)))
        menu.addAction(QtWidgets.QAction("Remove", self, triggered=lambda: self.obj.remove(self._getItem())))
        menu.addAction(QtWidgets.QAction("PostProcess", self, triggered=self._post))
        menu.exec_(QtGui.QCursor.pos())

    def __createAction(self, imageType, func, waveType, **kwargs):
        if imageType == "rgb":
            imageType = "RGB"
        if imageType == "contour":
            kwargs["contour"] = True
        elif imageType == "vector":
            kwargs["vector"] = True
        if func == self.__disp:
            return QtWidgets.QAction(imageType, self, triggered=lambda: func(self._getItem(), **kwargs))        
        else:
            return QtWidgets.QAction(imageType, self, triggered=lambda: func(self._getObj(type=waveType), **kwargs))

    def _getItem(self):
        i = self.selectionModel().selectedIndexes()[0].row()
        return self.obj.getChildWaves()[i]

    def _getObj(self, type="Connected"):
        item = self._getItem()
        obj = item.getFilteredWave()
        if type == "copied":
            return obj.duplicate()
        return obj

    def _export(self, type="Connected"):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            self._getObj(type).export(path, type=type)

    def _shell(self, type):
        w = self._getObj(type)
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            glb.shell().addObject(w, text)

    def _post(self):
        item = self._getItem()
        d = _FiltersDialog(item.getRawWave().ndim, self, post=item.postProcess())
        if d.exec_():
            item.setPostProcess(d.result)

    def sizeHint(self):
        return QtCore.QSize(100, 100)


class _FiltersDialog(QtWidgets.QDialog):
    def __init__(self, dim, parent, post=None, title="Postprocess"):
        super().__init__(parent)
        if title is not None:
            self.setWindowTitle(title)
        if post is None:
            self._fdim = 0
        else:
            self._fdim = post.getRelativeDimension()
        self.__initlayout(dim, post)

    def __initlayout(self, dim, post):
        self.filters = filters.FiltersGUI(dim, parent=self)
        if post is not None:
            self.filters.setFilters(post)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QPushButton("O K", clicked=self._ok))
        h1.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filters)
        layout.addLayout(h1)

        self.setLayout(layout)
        self.resize(500, 500)

    def _ok(self):
        self.result = self.filters.getFilters()
        if self.result.getRelativeDimension() != self._fdim:
            QtWidgets.QMessageBox.information(self, "Error", "You cannot change the filter dimension. Create new data instead.", QtWidgets.QMessageBox.Yes)
        else:
            self.accept()
