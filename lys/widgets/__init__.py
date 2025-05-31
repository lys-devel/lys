
from lys import registerFileLoader

from .general import *
from .slider import RangeSlider
from .fileView import FileSystemView
from .sidebar import SidebarWidget

from .mdi import LysSubWindow, _ExtendMdiArea
from .table import Table, lysTable, TableModifyWidget
from .canvas import lysCanvas, Graph, CanvasBase, getFrontCanvas, ModifyWidget

registerFileLoader(".grf", Graph)
registerFileLoader(".tbl", Table)
