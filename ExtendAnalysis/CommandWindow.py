#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import glob
from .Tasks import *

from .ExtendType import *
from .BasicWidgets import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .System import *


class TaskWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.__initlayout()

    def __initlayout(self):
        layout = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Status", "Explanation"])
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.buildContextMenu)
        layout.addWidget(self.tree)

        tasks.updated.connect(self.__update)
        self.setLayout(layout)

    def __update(self):
        self.tree.clear()
        list = tasks.getTasks()
        dic = {}
        for i in list:
            if i.group() == "":
                self.tree.addTopLevelItem(QTreeWidgetItem([i.name(), i.status(), i.explanation()]))
            else:
                grps = i.group().split("/")
                parent = None
                name = ""
                for g in grps:
                    name = name + g
                    if name in dic:
                        item = dic[name]
                    else:
                        item = QTreeWidgetItem([g, "", ""])
                        dic[name] = item
                        if parent is None:
                            self.tree.addTopLevelItem(item)
                        else:
                            parent.addChild(item)
                        item.setExpanded(True)
                    parent = item
                    name = name + "/"
                parent.addChild(QTreeWidgetItem([i.name(), i.status(), i.explanation()]))

    def buildContextMenu(self):
        menu = QMenu(self.tree)
        menulabels = ['Delete']
        actionlist = []
        for label in menulabels:
            actionlist.append(menu.addAction(label))
        action = menu.exec_(QCursor.pos())
        for act in actionlist:
            if act.text() == "Delete":
                items = self.tree.selectedIndexes()
                if len(items) == 0:
                    return
                list = tasks.getTasks()
                for i in items:
                    if i.column() == 0:
                        tasks.removeTask(list[i.row()][0])


class SettingWidget(QWidget):
    path = home() + "/.lys/settings"

    def __init__(self):
        super().__init__()
        self.setting = globalSetting()
        self.__initlayout()
        self.__load()

    def __initlayout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.__graphSetting())
        layout.addWidget(self.__floatSetting())
        layout.addStretch()
        self.setLayout(layout)

    def __graphSetting(self):
        h1 = QHBoxLayout()
        self.g1 = QRadioButton("Matplotlib")
        self.g2 = QRadioButton("pyqtGraph")
        self.g1.toggled.connect(lambda: self._lib(self.g1))
        self.g2.toggled.connect(lambda: self._lib(self.g2))
        h1.addWidget(QLabel("Graph library"))
        h1.addWidget(self.g1)
        h1.addWidget(self.g2)
        return h1

    def __floatSetting(self):
        self._float = QCheckBox("Floating Analysis Window")
        self._float.stateChanged.connect(self._floatChanged)
        return self._float

    def _floatChanged(self, b):
        self.setting["Floating"] = (not b == 0)

    def _lib(self, btn):
        if btn == self.g1:
            Graph.graphLibrary = "matplotlib"
        elif btn == self.g2:
            Graph.graphLibrary = "pyqtgraph"
        self.setting["GraphLibrary"] = Graph.graphLibrary

    def __load(self):
        if "GraphLibrary" in self.setting:
            self.grfType = self.setting["GraphLibrary"]
        else:
            self.grfType = "matplotlib"
        if self.grfType == "pyqtgraph":
            self.g2.toggle()
        else:
            self.g1.toggle()
        if "Floating" in self.setting:
            self._float.setChecked(self.setting["Floating"])


class WorkspaceWidget(FileSystemView):
    def __init__(self, parent):
        self.model = ExtendFileSystemModel()
        super().__init__(parent, self.model)
        self.model.AddExcludedFilter("winlist.lst")
        self.model.AddExcludedFilter("wins")
        self.SetPath(home() + "/.lys/workspace")
        self.__viewContextMenu2(self)

    def __viewContextMenu2(self, tree):
        ld = QAction('Load workspace', self, triggered=self.__work)
        add = QAction('Add workspace', self, triggered=self.__addwork)
        menu = {}
        menu['dir'] = [ld, add, tree.Action_Delete()]
        menu['mix'] = [add, tree.Action_Delete()]
        menu['other'] = [add, tree.Action_Delete()]
        tree.SetContextMenuActions(menu)

    def __work(self, path):
        name = self.selectedPaths()[0].replace(AutoSavedWindow.folder_prefix, "")
        AutoSavedWindow.SwitchTo(name)

    def __addwork(self):
        text, ok = QInputDialog.getText(self, 'New worksapce', 'Name of workspace')
        if ok:
            AutoSavedWindow.SwitchTo(text)


class CommandWindow(QWidget):
    def __init__(self, parent=None):
        super(CommandWindow, self).__init__(parent)
        self.setWindowTitle("Command Window")
        self.resize(600, 600)
        self.__loadData()
        self.__shell = ExtendShell(self, ".lys/commandlog2.log")
        self.__CreateLayout()
        self.show()

    def __loadData(self):
        if not os.path.exists('proc.py'):
            with open("proc.py", "w") as file:
                file.write("from ExtendAnalysis import *")

    def clearLog(self):
        self.output.clear()

    def saveData(self):
        self.output.save()
        self.__shell.save()
        if not PythonEditor.CloseAllEditors():
            return False
        AutoSavedWindow.StoreAllWindows()
        return True

    def closeEvent(self, event):
        event.ignore()

    def __CreateLayout(self):
        self.output = CommandLogWidget(self)

        self._tab_up = QTabWidget()
        self._tab_up.addTab(self.output, "Command")
        self._tab_up.addTab(LogWidget(), "Log")
        self._tab_up.addTab(StringTextEdit(".lys/memo.str"), "Memo")

        self._tab = QTabWidget()
        self._tab.addTab(FileWidget(self, self.__shell), "File")
        self._tab.addTab(WorkspaceWidget(self), "Workspace")
        self._tab.addTab(TaskWidget(), "Tasks")
        self._tab.addTab(SettingWidget(), "Settings")

        layout_h = QSplitter(Qt.Vertical)
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(CommandLineEdit(self.__shell))
        layout_h.addWidget(self._tab)

        lay = QHBoxLayout()
        lay.addWidget(layout_h)
        self.setLayout(lay)
