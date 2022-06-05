
from lys import registerFileLoader

from .general import ScientificSpinBox, ColorSelection, ColormapSelection
from .fileView import FileSystemView

from .mdi import LysSubWindow, AutoSavedWindow, _ExtendMdiArea
from .table import Table, ExtendTable
from .canvas import lysCanvas, Graph, CanvasBase, getFrontCanvas

registerFileLoader(".grf", Graph)
