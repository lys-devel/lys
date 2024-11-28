from . import Qt
from . import resources
from . import errors
from .functions import home, load, edit, display, append, registerFileLoader, loadableFiles, registerFittingFunction, frontCanvas, multicut, lysPath
from .core import SettingDict, Wave, DaskWave, Version

from . import filters
from .filters import filtersGUI
from . import glb

# register file loaders
registerFileLoader(".npz", Wave)
registerFileLoader(".dic", SettingDict)
