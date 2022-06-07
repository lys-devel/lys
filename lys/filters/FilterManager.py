from lys.Qt import QtWidgets

# all filter classes
_filterClasses = {}

# all filter GUIs
_filterGroups = {}


def __registerLocals():
    _filterGroups[''] = _DeleteSetting


class _DeleteSetting(QtWidgets.QWidget):
    def __init__(self, dimension=2):
        super().__init__(None)

    @classmethod
    def _havingFilter(cls, f):
        return None

    def getFilter(self):
        return None

    def getRelativeDimension(self):
        return 0


def addFilter(filter, filterName=None, gui=None, guiName=None, guiGroup=None):
    """
    Add new filter to lys.

    Args:
        filter(class that implements FilterInterface): filter to be added.
        filterName(str): name of filter. If omitted, default name is used.
        gui(class that implements FilterSettingBase, and is decorated by filterGUI): Widget that is used in MultiCut.
        guiName(str): name of filter in GUI.
        guiGroup(str): name of group in GUI.
    """
    # set default name
    if filterName is None:
        filterName = filter.__name__
    if guiName is None:
        guiName = filterName
    # register filter
    _filterClasses[filterName] = filter
    # register gui
    if gui is not None:
        if guiGroup is None:
            _filterGroups[guiName] = gui
        elif guiGroup in _filterGroups:
            _filterGroups[guiGroup][guiName] = gui
        else:
            _filterGroups[guiGroup] = {guiName: gui}


def getFilter(name):
    if name in _filterClasses:
        return _filterClasses[name]
    else:
        return None


__registerLocals()
