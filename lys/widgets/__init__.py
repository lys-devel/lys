
from lys import registerFileLoader

from .general import *
from .slider import RangeSlider
from .fileView import FileSystemView

from .mdi import LysSubWindow, _ExtendMdiArea
from .table import Table, lysTable, TableModifyWidget
from .canvas import lysCanvas, Graph, CanvasBase, getFrontCanvas, ModifyWidget
from .canvas3d import lysCanvas3D, Graph3D, getFrontCanvas3D, ModifyWidget3D

registerFileLoader(".grf", Graph)
registerFileLoader(".grf3", Graph3D)
registerFileLoader(".tbl", Table)
