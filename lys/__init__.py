from . import errors
from . import QtSystem
from .functions import home, load, edit, display, append, registerFileLoader, loadableFiles, registerFittingFunction, frontCanvas, multicut
from .core import SettingDict, Wave, DaskWave

from .Tasks import task, tasks
from . import filters
from .filters import filtersGUI
from .Analysis import MultiCut
from . import glb

# register file loaders
registerFileLoader(".npz", Wave)
registerFileLoader(".dic", SettingDict)
