from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ExportDataTab(QGroupBox):
    def __init__(self):
        super().__init__("Data")
        self.__initlayout()

    def __initlayout(self):
        hb = QHBoxLayout()
        hb.addWidget(QPushButton("Export", clicked=self.__export))
        hb.addWidget(QPushButton("MultiCut", clicked=self.__mcut))

        self.layout = QVBoxLayout()
        self.layout.addLayout(hb)
        self.setLayout(self.layout)

    def _setWave(self, wave):
        self.wave = wave

    def __mcut(self):
        from ..MultiCutGUI import MultiCut
        MultiCut(self.wave)

    def __export(self):
        filt = ""
        for f in self.wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            self.wave.export(path, type=type)
