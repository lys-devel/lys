import io
from LysQt.QtWidgets import QApplication
from LysQt.QtCore import QMimeData
from LysQt.QtGui import QImage
from lys.widgets import LysSubWindow

from .CanvasBase import CanvasPart, saveCanvas


class CanvasUtilities(CanvasPart):
    """
    Extra canvas utilities.
    """

    def openModifyWindow(self):
        from lys import ModifyWindow, Graph
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
        from ..Matplotlib import ExtendCanvas
        d = self.canvas().SaveAsDictionary()
        c = ExtendCanvas()
        c.LoadFromDictionary(d)
        return c

    def saveFigure(self, path, format):
        self.__duplicateCanvas().getFigure().savefig(path, transparent=True, format=format)

    def copyToClipboard(self):
        c = self.__duplicateCanvas()
        clipboard = QApplication.clipboard()
        mime = QMimeData()
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
        mime.setImageData(QImage.fromData(buf.getvalue()))
        buf.close()
        clipboard.setMimeData(mime)

    def __toData(self, canvas, format):
        buf = io.BytesIO()
        canvas.getFigure().savefig(buf, format=format, transparent=True)
        buf.seek(0)
        data = buf.read()
        buf.close()
        return data
