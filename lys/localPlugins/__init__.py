
from lys import glb
if glb.mainWindow() is not None:  # This is required to avoid local plugins imported by unittest
    # File loaders
    from . import ImageLoad

    # Additional GUIs
    from . import Logger
    from . import StringEditor
    from . import WaveViewer

    # Menus
    from . import PythonEditor
    from . import GraphSetting
    from . import manualView

    # Basic file menus
    from . import fileMenu
