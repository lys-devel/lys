#!/usr/bin/python3
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ExtendAnalysis import home, SettingDict, Graph, glb


class GraphSetting(QGroupBox):
    def __init__(self):
        super().__init__("Graph settings")
        self.setting = SettingDict(home() + "/.lys/settings/graph.dic")
        self.__initUI()
        self.__load()

    def __initUI(self):
        self.g1 = QRadioButton("Matplotlib")
        self.g2 = QRadioButton("pyqtGraph")
        self.g1.toggled.connect(lambda: self._lib(self.g1))
        self.g2.toggled.connect(lambda: self._lib(self.g2))

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Library"))
        h1.addWidget(self.g1)
        h1.addWidget(self.g2)

        self.setLayout(h1)

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


_instance = GraphSetting()
glb.mainWindow().addSettingWidget(_instance)
_instance2 = GraphSetting()
glb.mainWindow().addSettingWidget(_instance2)
