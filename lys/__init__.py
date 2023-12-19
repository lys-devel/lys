from . import Qt
from . import resources
from . import errors
from .functions import home, load, edit, display, append, registerFileLoader, loadableFiles, registerFittingFunction, frontCanvas, multicut, lysPath, display3D, append3D, frontCanvas3D
from .core import SettingDict, Wave, DaskWave

from . import filters
from .filters import filtersGUI
from . import glb

# register file loaders
registerFileLoader(".npz", Wave)
registerFileLoader(".dic", SettingDict)
