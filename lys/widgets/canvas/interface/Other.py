import io

from lys.Qt import QtCore, QtGui, QtWidgets
from lys.widgets import LysSubWindow

from .CanvasBase import CanvasPart, saveCanvas


class CanvasUtilities(CanvasPart):
    """
    Extra canvas utilities.
    """

    def openModifyWindow(self):
        """
        Open graph setting window.
        """
        from lys import glb
        glb.editCanvas(self.canvas())

    def openFittingWindow(self):
        """
        Open fitting window.
        """
        from lys import glb
        glb.startFitting(self.canvas())

    def getParent(self):
        """
        Get Parent LysSubWindow if it exists.

        Returns:
            LysSubWindow: The parent LysSubWindow. If the canvas is not embedded in LysSubWindow, None is returned.
        """
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

    def saveFigure(self, path, format, dpi=100):
        self.__duplicateCanvas().getFigure().savefig(path, transparent=True, format=format, dpi=dpi)

    def copyToClipboard(self, dpi=100):
        c = self.__duplicateCanvas()
        clipboard = QtWidgets.QApplication.clipboard()
        mime = QtCore.QMimeData()
        mime.setData('Encapsulated PostScript', self.__toData(c, 'eps', dpi=dpi))
        mime.setData('application/postscript', self.__toData(c, 'eps', dpi=dpi))
        mime.setData('Scalable Vector Graphics', self.__toData(c, 'svg', dpi=dpi))
        mime.setData('application/svg+xml', self.__toData(c, 'svg', dpi=dpi))
        mime.setData('Portable Document Format', self.__toData(c, 'pdf', dpi=dpi))
        mime.setData('application/pdf', self.__toData(c, 'pdf', dpi=dpi))
        try:
            mime.setText(self.__toData(c, 'pdf', dpi=dpi).hex())
        except Exception:
            import traceback
            print(traceback.format_exc())
        buf = io.BytesIO()
        c.getFigure().savefig(buf, transparent=True, dpi=dpi)
        mime.setImageData(QtGui.QImage.fromData(buf.getvalue()))
        buf.close()
        clipboard.setMimeData(mime)

    def __toData(self, canvas, format, dpi=100):
        buf = io.BytesIO()
        canvas.getFigure().savefig(buf, format=format, transparent=True, dpi=dpi)
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
