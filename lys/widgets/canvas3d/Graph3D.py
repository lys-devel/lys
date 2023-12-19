from lys.Qt import QtCore, QtWidgets
from ..mdi import _ConservableWindow
from .pyvista import Canvas3d


def lysCanvas3D():
    """
    Return 3D canvas widget.
    """
    return Canvas3d()


class Graph3D(_ConservableWindow):
    def __init__(self, file=None, **kwargs):
        super().__init__(file, **kwargs)
        self.canvas = Canvas3d()
        self.setWidget(self.canvas)
        self.canvas.show()

    def __getattr__(self, key):
        if hasattr(self.canvas, key):
            return getattr(self.canvas, key)
        return super().__getattr__(key)

    def __saveAs(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(filter="Graph3D (*.grf3)")
        if len(path) != 0:
            if not path.endswith('.grf3'):
                path += '.grf3'
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
        return '3D Graph'

    def _suffix(self):
        return '.grf3'
