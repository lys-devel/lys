import os

from lys import lysPath
from lys.Qt import QtWidgets
from lys.widgets import AxisSelectionLayout, FileSystemView
from lys.decorators import avoidCircularReference


class TemplateDialog(QtWidgets.QDialog):
    def __init__(self, parent, dim, gui):
        super().__init__(parent)
        self._gui = gui
        self._dim = dim
        self.setWindowTitle("Template Manager")
        dir = self.__initTemplates(dim)
        self.__initlayout(dim, dir)
        self.setTemplate(lysPath(".lys/templates/" + str(dim) + "D/" + "Default"))

    def __initTemplates(self, dim):
        dir = lysPath(".lys/templates/" + str(dim) + "D")
        if not os.path.exists(dir):
            os.makedirs(dir, exist_ok=True)
        default = lysPath(".lys/templates/" + str(dim) + "D/" + "Default")
        if not os.path.exists(default):
            d = self.__loadDefault(dim)
            with open(default, "w") as f:
                f.write(str(d))
        return dir

    def __loadDefault(self, dim):
        if dim < 6:
            with open(os.path.dirname(__file__) + "/DefaultTemplate.dic", "r") as f:
                d = eval(f.read())
            return d[str(dim) + "D"]
        return None

    def __initlayout(self, dim, dir):
        self._view = FileSystemView(dir)
        self.__initTreeMenu()
        self._view.selectionChanged.connect(self.__selected)
        self._axes = _AxesMap(dim)
        self._check = _Checks("Load")

        self._label = QtWidgets.QLabel("")
        v1 = QtWidgets.QVBoxLayout()
        v1.addWidget(self._label)
        inf = QtWidgets.QGroupBox("Information")
        inf.setLayout(v1)

        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QPushButton("O K", clicked=self._ok))
        h.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(inf)
        layout.addLayout(self._check)
        layout.addWidget(self._axes)
        layout.addLayout(h)

        lh = QtWidgets.QHBoxLayout()
        lh.addWidget(self._view)
        lh.addLayout(layout)

        self.setLayout(lh)
        self.adjustSize()

    def setTemplate(self, path):
        with open(path, "r") as f:
            d = eval(f.read())
        self._template = d
        if self._template is None:
            self._check.enableChecks({})
            self._label.setText("Invalid template. Default template is only valid for d <= 5.")
        else:
            self._check.enableChecks(d.get("TemplateChecks", {}))
            txt = "Name: " + lysPath(path).replace(".lys/templates/" + str(self._dim) + "D/", "")
            self._label.setText(txt)

    def __selected(self):
        path = self._view.selectedPath()
        if os.path.isfile(path):
            self.setTemplate(path)

    def __initTreeMenu(self):
        dmenu = QtWidgets.QMenu(self)
        self._dmenus = []
        self._dmenus.append(QtWidgets.QAction("Save present state", triggered=self.__save))
        self._dmenus.append(QtWidgets.QAction("Import from file", triggered=self.__import))
        for m in self._dmenus:
            dmenu.addAction(m)
        self._view.registerFileMenu("dir", dmenu, hide_load=True, hide_print=True)

        menu = QtWidgets.QMenu(self)
        self._menus = []
        self._menus.append(QtWidgets.QAction("Export to file", triggered=self.__export))
        for m in self._menus:
            menu.addAction(m)
        self._view.registerFileMenu("mix", menu, hide_load=True, hide_print=True)

    def __save(self):
        path = self._view.selectedPath() + "/"
        d = _AddDialog(self, path)
        if d.exec_():
            name = d.getName()
            dic = self._gui.saveAsDictionary(**d.getChecks())
            dic["TemplateChecks"] = d.getChecks()
            with open(path + name, "w") as f:
                f.write(str(dic))

    def __export(self):
        file = self._view.selectedPath()
        if not os.path.isfile(file):
            QtWidgets.QMessageBox.information(self, "Caution", "You have to select template file.")
            return
        path, type = QtWidgets.QFileDialog.getSaveFileName(self, "Save Template", filter="Template (*.tpl);;All files (*.*)")
        if len(path) != 0:
            if not path.endswith('.tpl'):
                path += '.tpl'
            with open(file, "r") as f:
                contents = f.read()
            with open(path, "w") as f:
                f.write(contents)

    def __import(self):
        path, type = QtWidgets.QFileDialog.getOpenFileName(self, "Open Template", filter="Template (*.tpl);;All files (*.*)")
        if len(path) != 0:
            with open(path, "r") as f:
                contents = f.read()
            file = self._view.selectedPath() + "/" + os.path.basename(path)
            if os.path.exists(file):
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("The file " + os.path.basename(path) + " exists. Do your want to overwrite it?")
                msg.setWindowTitle("Warning")
                msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                ok = msg.exec_()
                if ok == QtWidgets.QMessageBox.No:
                    return
            with open(file, "w") as f:
                f.write(contents)

    def _ok(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("Applying template will delete all settings on present MultiCut windows. Are your really want to proceed?")
        msg.setWindowTitle("Warning")
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        ok = msg.exec_()
        if ok == QtWidgets.QMessageBox.No:
            return
        axesMap = self._axes.getAxesMap()
        self._gui.loadFromDictionary(self._template, axesMap=axesMap, **self._check.getChecks())
        self.accept()


class _AddDialog(QtWidgets.QDialog):
    def __init__(self, parent, directory):
        super().__init__(parent)
        self._dir = directory
        self.setWindowTitle("Save present state")
        self.__initlayout()

    def __initlayout(self):
        self._name = QtWidgets.QLineEdit()
        self._name.setText(self.__defaultName())
        self._check = _Checks("Save")

        h = QtWidgets.QHBoxLayout()
        h.addWidget(QtWidgets.QLabel("Name"))
        h.addWidget(self._name)

        btn = QtWidgets.QHBoxLayout()
        btn.addWidget(QtWidgets.QPushButton("O K", clicked=self.__ok))
        btn.addWidget(QtWidgets.QPushButton("CANCEL", clicked=self.reject))

        v = QtWidgets.QVBoxLayout()
        v.addLayout(h)
        v.addLayout(self._check)
        v.addLayout(btn)

        self.setLayout(v)
        self.adjustSize()

    def __exists(self, file):
        return os.path.exists(self._dir + file)

    def __defaultName(self):
        i = 1
        while self.__exists("template" + str(i)):
            i += 1
        return "template" + str(i)

    def __ok(self):
        self._file = self._name.text()
        if self.__exists(self._file):
            msg = QtWidgets.QMessageBox(self)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("The file " + self._file + " exists. Do your want to overwrite it?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            ok = msg.exec_()
            if ok == QtWidgets.QMessageBox.No:
                return
        self.accept()

    def getName(self):
        return self._file

    def getChecks(self):
        return self._check.getChecks()


class _Checks(QtWidgets.QHBoxLayout):
    def __init__(self, name):
        super().__init__()
        self.__initlayout(name)

    def __initlayout(self, name):
        self._grid = QtWidgets.QCheckBox("Graphs on grid")
        self._grid.setChecked(True)
        self._graph = QtWidgets.QCheckBox("Independent graphs")
        self._annot = QtWidgets.QCheckBox("Interactive annotations")
        self._annot.setChecked(True)

        vg = QtWidgets.QVBoxLayout()
        vg.addWidget(self._grid)
        vg.addWidget(self._graph)
        vg.addWidget(self._annot)

        self._guiGroup = QtWidgets.QGroupBox(name + " graphs")
        self._guiGroup.setLayout(vg)

        self._range = QtWidgets.QCheckBox("Integrated regions")
        self._lines = QtWidgets.QCheckBox("Free line regions")
        vc = QtWidgets.QVBoxLayout()
        vc.addWidget(self._range)
        vc.addWidget(self._lines)

        self._cuiGroup = QtWidgets.QGroupBox(name + " parameters")
        self._cuiGroup.setLayout(vc)

        self.addWidget(self._cuiGroup)
        self.addWidget(self._guiGroup)

    def getChecks(self):
        return {
            "useGrid": self._grid.isChecked(),
            "useGraph": self._graph.isChecked(),
            "useAnnot": self._annot.isChecked(),
            "useRange": self._range.isChecked(),
            "useLine": self._lines.isChecked()
        }

    def enableChecks(self, d):
        self._grid.setEnabled(d.get("useGrid", True))
        self._grid.setChecked(d.get("useGrid", True))
        self._graph.setEnabled(d.get("useGraph", True))
        self._graph.setChecked(d.get("useGraph", True))
        self._annot.setEnabled(d.get("useAnnot", True))
        self._annot.setChecked(d.get("useAnnot", True))
        self._range.setEnabled(d.get("useRange", True))
        self._range.setChecked(d.get("useRange", True))
        self._lines.setEnabled(d.get("useLine", True))
        self._lines.setChecked(d.get("useLine", True))


class _AxesMap(QtWidgets.QGroupBox):
    def __init__(self, dim):
        super().__init__("Axes mapping")
        self._dim = dim
        self._axes = [AxisSelectionLayout("Axis " + str(d), dim, init=d) for d in range(dim)]
        self._map = {d: d for d in range(dim)}

        layout = QtWidgets.QVBoxLayout()
        for ax in self._axes:
            layout.addLayout(ax)
            ax.axisChanged.connect(self.__axisChanged)

        self.setLayout(layout)

    def getAxesMap(self):
        return self._map

    @ avoidCircularReference
    def __axisChanged(self):
        # find index that is changed
        index = -1
        for n, ax in enumerate(self._axes):
            axis = ax.getAxis()
            if self._map[n] != axis:
                index = n
                oldAxis = self._map[n]
                self._map[n] = axis
        if index == -1:
            return

        # update replaced
        for n, ax in enumerate(self._axes):
            axis = ax.getAxis()
            if axis == self._axes[index].getAxis() and index != n:
                ax.setAxis(oldAxis)
                self._map[n] = oldAxis
