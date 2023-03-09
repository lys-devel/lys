from lys import Wave, glb, multicut
from lys.Qt import QtWidgets


class ExportDataTab(QtWidgets.QGroupBox):
    def __init__(self, cui):
        super().__init__("Data")
        self._cui = cui
        self.__initlayout()

    def __initlayout(self):
        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(QtWidgets.QPushButton("Export", clicked=self.__export))
        hb.addWidget(QtWidgets.QPushButton("MultiCut", clicked=self.__mcut))
        hb.addWidget(QtWidgets.QPushButton("Send to shell", clicked=self.__send))
        self.setLayout(hb)

    def __mcut(self):
        multicut(self._cui.getFilteredWave())

    def __export(self):
        filt = ""
        for f in Wave.SupportedFormats():
            filt = filt + f + ";;"
        filt = filt[:len(filt) - 2]
        path, type = QtWidgets.QFileDialog.getSaveFileName(filter=filt)
        if len(path) != 0:
            self._cui.getFilteredWave().compute().export(path, type=type)

    def __send(self):
        wave = self._cui.getFilteredWave()
        text, ok = QtWidgets.QInputDialog.getText(None, "Send to shell", "Enter wave name", text=wave.name)
        if ok:
            w = wave.compute()
            w.name = text
            glb.shell().addObject(w)
