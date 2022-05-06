from lys.widgets import LysSubWindow

from .FittingWidget import FittingWidget


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
