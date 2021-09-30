from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ExtendAnalysis import glb, tasks


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


_instance = TaskWidget()
glb.mainWindow().addTab(_instance, "Tasks", "down")
