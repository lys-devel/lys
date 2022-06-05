from .. import LysSubWindow
from .ExtendTable import ExtendTable


class Table(LysSubWindow):
    def __init__(self, wave=None):
        super().__init__()
        self.setWindowTitle("Table Window")
        self.resize(400, 400)
        self.__initlayout(wave)

    def __initlayout(self, wave):
        self._etable = ExtendTable(wave)
        self.setWidget(self._etable)
        self.show()

    def Append(self, wave):
        self._etable.Append(wave)

    def checkState(self, index):
        self._etable.checkState(index)

    def SetSize(self, size):
        self._etable.SetSize(size)
