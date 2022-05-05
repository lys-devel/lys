from lys.widgets import LysSubWindow

from .FittingWidget import FittingWidget
from .LineProfile import LineProfileWidget


class FittingWindow(LysSubWindow):
    def __init__(self, parent, canvas):
        super().__init__()
        self._initlayout(canvas)
        self.attach(parent)
        self.attachTo()

    def _initlayout(self, canvas):
        self.setWindowTitle("Fitting Window")
        w = FittingWidget(canvas)
        self.setWidget(w)
        self.adjustSize()
        self.updateGeometry()
        self.show()


class LineProfileWindow(LysSubWindow):
    def __init__(self, parent, wavelist, canvas=None):
        super().__init__()
        self._initlayout(wavelist, canvas)
        self.adjustSize()
        self.updateGeometry()
        self.attach(parent)
        self.show()
        self.attachTo()

    def _initlayout(self, wavelist, canvas):
        self.setWindowTitle("Line Profile Window")
        w = LineProfileWidget(wavelist, canvas)
        self.setWidget(w)
