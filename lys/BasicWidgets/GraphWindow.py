from LysQt.QtCore import Qt
from LysQt.QtWidgets import QSizePolicy, QMdiArea, QFileDialog, QWidget, QGridLayout

from lys import registerFileLoader, frontCanvas, Wave
from lys.widgets import AutoSavedWindow, _ExtendMdiArea, LysSubWindow
from .Commons.ExtendTable import ExtendTable
from .Matplotlib import ExtendCanvas
from .pyqtGraph import pyqtCanvas


class _SizeAdjustableWindow(AutoSavedWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWidth(0)
        self.setHeight(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

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


class Graph(_SizeAdjustableWindow):
    graphLibrary = "matplotlib"

    @classmethod
    def closeAllGraphs(cls):
        list = _ExtendMdiArea.current().subWindowList(order=QMdiArea.ActivationHistoryOrder)
        for item in reversed(list):
            if isinstance(item, Graph):
                item.close(force=True)

    def _prefix(self):
        return 'graph'

    def _suffix(self):
        return '.grf'

    def __init__(self, file=None, lib=None, **kwargs):
        super().__init__(file, **kwargs)
        if file is not None:
            lib = self._loadLibType(file)
        if lib is None:
            lib = Graph.graphLibrary
        if lib == "matplotlib":
            self.canvas = ExtendCanvas()
        elif lib == "pyqtgraph":
            self.canvas = pyqtCanvas()
        self.setWidget(self.canvas)
        self.canvas.show()
        self.canvas.canvasResized.connect(self._resizeCanvas)
        self.canvas.keyPressed.connect(self.keyPress)
        self.resized.connect(self.canvas.parentResized)
        self.canvas.updated.connect(lambda: self.Save(temporary=True))
        if file is not None:
            self._load(file)
        else:
            self.canvas.setCanvasSize("Both", "Auto", 4)

    def __getattr__(self, key):
        if hasattr(self.canvas, key):
            return getattr(self.canvas, key)
        return super().__getattr__(key)

    def _save(self, file):
        d = {}
        if isinstance(self.canvas, ExtendCanvas):
            d['Library'] = 'matplotlib'
        elif isinstance(self.canvas, pyqtCanvas):
            d['Library'] = 'pyqtgraph'
        self.canvas.SaveAsDictionary(d)
        d['Graph'] = {}
        d['Graph']['Position_x'] = self.pos().x()
        d['Graph']['Position_y'] = self.pos().y()
        with open(file, 'w') as f:
            f.write(str(d))

    def _load(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        self.move(d['Graph']['Position_x'], d['Graph']['Position_y'])
        self.canvas.LoadFromDictionary(d)

    def _loadLibType(self, file):
        with open(file, 'r') as f:
            d = eval(f.read())
        if 'Library' in d:
            return d["Library"]
        else:
            return "matplotlib"

    def _resizeCanvas(self, canvas):
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

    def keyPress(self, e):
        if e.key() == Qt.Key_S:
            if e.modifiers() == Qt.ShiftModifier | Qt.ControlModifier:
                self.__saveAs()
            elif e.modifiers() == Qt.ControlModifier:
                if self.FileName() is None:
                    self.__saveAs()
                else:
                    self.Save()

    def __saveAs(self):
        path, _ = QFileDialog.getSaveFileName(filter="Graph (*.grf)")
        if len(path) != 0:
            if not path.endswith('.grf'):
                path += '.grf'
            self.Save(path)

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self.canvas.finalize()


def display(*args, lib=None, **kwargs):
    g = Graph(lib=lib)
    append(*args, canvas=g.canvas, **kwargs)
    return g


def append(*args, canvas=None, exclude=[], **kwargs):
    if canvas is None:
        c = frontCanvas(exclude=exclude)
    else:
        c = canvas
    for wave in args:
        if isinstance(wave, Wave):
            c.Append(wave, **kwargs)
        else:
            c.Append(Wave(wave), **kwargs)
    return c


class MultipleGrid(LysSubWindow):
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.resize(400, 400)

    def __initlayout(self):
        self.layout = QGridLayout()
        w = QWidget()
        w.setLayout(self.layout)
        self.setWidget(w)

    def Append(self, widget, x, y, w, h):
        for i in range(x, x + w):
            for j in range(y, y + h):
                wid = self.itemAtPosition(i, j)
                if wid is not None:
                    self.layout.removeWidget(wid)
                    wid.deleteLater()
                    # if isinstance(wid, BasicEventCanvasBase):
                    #    wid.emitCloseEvent()
        self.layout.addWidget(widget, x, y, w, h)

    def setSize(self, size):
        for s in range(size):
            self.layout.setColumnStretch(s, 1)
            self.layout.setRowStretch(s, 1)

    def itemAtPosition(self, i, j):
        item = self.layout.itemAtPosition(i, j)
        if item is not None:
            return item.widget()
        else:
            return None


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


registerFileLoader(".grf", Graph)
