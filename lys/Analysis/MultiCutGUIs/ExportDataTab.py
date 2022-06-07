from lys import Wave, glb
from lys.Qt import QtWidgets


class ExportDataTab(QtWidgets.QGroupBox):
    def __init__(self):
        super().__init__("Data")
        self.__initlayout()

    def __initlayout(self):
        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(QtWidgets.QPushButton("Export", clicked=self.__export))
        hb.addWidget(QtWidgets.QPushButton("MultiCut", clicked=self.__mcut))
        hb.addWidget(QtWidgets.QPushButton("Send to shell", clicked=self.__send))

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(hb)
        self.setLayout(self.layout)

    def _setWave(self, wave):
        self.wave = wave

    def __mcut(self):
        from .. import MultiCut
        MultiCut(self.wave)

    def __export(self):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            self.wave.compute().export(path, type=type)

    def __send(self):
        w = self.wave.compute()
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=w.name)
        if ok:
            w.name = text
            glb.shell().addObject(w)
