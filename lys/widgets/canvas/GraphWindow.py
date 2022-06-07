from lys.Qt import QtCore, QtWidgets
from lys.decorators import suppressLysWarnings
from ..mdi import _AutoSavedWindow
from .Matplotlib import ExtendCanvas
from .pyqtGraph import pyqtCanvas


class _SizeAdjustableWindow(_AutoSavedWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidth(0)
        self.setHeight(0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

    def setWidth(self, val):
        if val == 0:
            self.setMinimumWidth(35)
            self.setMaximumWidth(10000)
        else:
            self.setMinimumWidth(val)
            self.setMaximumWidth(val)

    def setHeight(self, val):
        if val == 0:
            self.setMinimumHeight(35)
            self.setMaximumHeight(10000)
        else:
            self.setMinimumHeight(val)
            self.setMaximumHeight(val)


@suppressLysWarnings
def lysCanvas(lib="matplotlib"):
    if lib == "matplotlib":
        return ExtendCanvas()
    elif lib == "pyqtgraph":
        return pyqtCanvas()


class Graph(_SizeAdjustableWindow):
    graphLibrary = "matplotlib"

    def __init__(self, file=None, lib=None, **kwargs):
        super().__init__(file, **kwargs)
        self.canvas = self.__loadCanvas(file, lib)
        self.setWidget(self.canvas)
        self.canvas.show()
        self.canvas.saveCanvas.connect(self.__saveGraphSettings)
        self.canvas.loadCanvas.connect(self.__loadGraphSettings)
        self.canvas.canvasResized.connect(self.__resizeCanvas)
        self.canvas.keyPressed.connect(self.__keyPress)
        self.resized.connect(self.canvas.parentResized)
        self.canvas.updated.connect(lambda: self.Save(temporary=True))
        self.resizeFinished.connect(lambda: self.Save(temporary=True))
        self.moveFinished.connect(lambda: self.Save(temporary=True))
        if file is not None:
            self._load(file)
        else:
            self.canvas.setCanvasSize("Both", "Auto", 4)

    def __getattr__(self, key):
        if hasattr(self.canvas, key):
            return getattr(self.canvas, key)
        return super().__getattr__(key)

    def __loadCanvas(self, file, lib):
        if file is not None:
            lib = self.__loadLibType(file)
        if lib is None:
            lib = Graph.graphLibrary
        return lysCanvas(lib)

    def __loadLibType(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        if 'Library' in d:
            return d["Library"]
        else:
            return "matplotlib"

    def __saveGraphSettings(self, d):
        if isinstance(self.canvas, ExtendCanvas):
            d['Library'] = 'matplotlib'
        elif isinstance(self.canvas, pyqtCanvas):
            d['Library'] = 'pyqtgraph'
        d['Graph'] = {'Position_x': self.pos().x(), 'Position_y': self.pos().y()}

    def __loadGraphSettings(self, d):
        if "Graph" in d:
            self.move(d['Graph']['Position_x'], d['Graph']['Position_y'])

    def __resizeCanvas(self, canvas):
        self.setWidth(0)
        self.setHeight(0)
        self.adjustSize()
        wmode = canvas.getSizeParams('Width')['mode']
        hmode = canvas.getSizeParams('Height')['mode']
        if wmode in ["Absolute", "Per Unit"]:
            self.setWidth(self.width())
        elif wmode in ["Plan", "Aspect"] and hmode in ["Absolute", "Per Unit"]:
            self.setWidth(self.width())
        if hmode in ["Absolute", "Per Unit"]:
            self.setHeight(self.height())
        elif hmode in ["Plan", "Aspect"] and wmode in ["Absolute", "Per Unit"]:
            self.setHeight(self.height())

    def __keyPress(self, e):
        if e.key() == QtCore.Qt.Key_S:
            if e.modifiers() == QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier:
                self.__saveAs()
            elif e.modifiers() == QtCore.Qt.ControlModifier:
                if self.FileName() is None:
                    self.__saveAs()
                else:
                    self.Save()

    def __saveAs(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(filter="Graph (*.grf)")
        if len(path) != 0:
            if not path.endswith('.grf'):
                path += '.grf'
            self.Save(path)

    def _save(self, file):
        d = self.canvas.SaveAsDictionary()
        with open(file, 'w') as f:
            f.write(str(d))

    def _load(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        self.canvas.LoadFromDictionary(d)

    def _prefix(self):
        return 'graph'

    def _suffix(self):
        return '.grf'

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self.canvas.finalize()
