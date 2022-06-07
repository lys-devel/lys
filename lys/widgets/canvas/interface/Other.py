import io

from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import LysSubWindow

from .CanvasBase import CanvasPart, saveCanvas


class CanvasUtilities(CanvasPart):
    """
    Extra canvas utilities.
    """

    def openModifyWindow(self):
        from lys.widgets import Graph
        from ..ModifyWindow import ModifyWindow
        parent = self._getParent()
        mod = ModifyWindow(self.canvas(), parent, showArea=isinstance(parent, Graph))
        return mod

    def openFittingWindow(self):
        from lys.fitting import FittingWindow
        fit = FittingWindow(self._getParent(), self.canvas())
        return fit

    def _getParent(self):
        parent = self.canvas().parentWidget()
        while(parent is not None):
            if isinstance(parent, LysSubWindow):
                return parent
            parent = parent.parentWidget()

    def __duplicateCanvas(self):
        from lys.widgets import lysCanvas
        d = self.canvas().SaveAsDictionary()
        c = lysCanvas()
        c.LoadFromDictionary(d)
        return c

    def saveFigure(self, path, format):
        self.__duplicateCanvas().getFigure().savefig(path, transparent=True, format=format)

    def copyToClipboard(self):
        c = self.__duplicateCanvas()
        clipboard = QtWidgets.QApplication.clipboard()
        mime = QtCore.QMimeData()
        mime.setData('Encapsulated PostScript', self.__toData(c, 'eps'))
        mime.setData('application/postscript', self.__toData(c, 'eps'))
        mime.setData('Scalable Vector Graphics', self.__toData(c, 'svg'))
        mime.setData('application/svg+xml', self.__toData(c, 'svg'))
        mime.setData('Portable Document Format', self.__toData(c, 'pdf'))
        mime.setData('application/pdf', self.__toData(c, 'pdf'))
        try:
            mime.setText(self.__toData(c, 'pdf').hex())
        except Exception:
            import traceback
            print(traceback.format_exc())
        buf = io.BytesIO()
        c.getFigure().savefig(buf, transparent=True)
        mime.setImageData(QtGui.QImage.fromData(buf.getvalue()))
        buf.close()
        clipboard.setMimeData(mime)

    def __toData(self, canvas, format):
        buf = io.BytesIO()
        canvas.getFigure().savefig(buf, format=format, transparent=True)
        buf.seek(0)
        data = buf.read()
        buf.close()
        return data

    def duplicate(self, lib=None):
        from lys import display
        d = self.canvas().SaveAsDictionary()
        g = display(lib=lib)
        g.LoadFromDictionary(d)
        return g
