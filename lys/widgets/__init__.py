
from lys import registerFileLoader

from .general import *
from .fileView import FileSystemView

from .mdi import LysSubWindow, _ExtendMdiArea
from .table import Table, ExtendTable
from .canvas import lysCanvas, Graph, CanvasBase, getFrontCanvas

registerFileLoader(".grf", Graph)
