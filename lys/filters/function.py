# all filter classes
_filterClasses = {}
_filterGuis = {}
# all filter GUIs
_filterGroups = {}


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
        _filterGuis[filterName] = gui
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


def getFilterName(filter):
    for key, item in _filterClasses.items():
        if item == type(filter) or item == filter:
            return key


def getFilterGui(filter):
    return _filterGuis[getFilterName(filter)]


def getFilterGuiName(filter):
    for key, item in _filterGroups.items():
        if key == "":
            continue
        if isinstance(item, dict):
            for key2, item2 in item.items():
                if item2.getFilterClass() == filter or item2.getFilterClass() == type(filter):
                    return key2
        else:
            if item.getFilterClass() == filter or item.getFilterClass() == type(filter):
                return key


def fromFile(file):
    """
    Load filter from .fil file.
    Args: 
        file(str): The path to the .fil file

    Returns:
        filter: The filter loaded form the .fil file. 
    """
    from lys.filters import Filters
    return Filters.fromFile(file)


def toFile(filter, file):
    filter.saveAsFile(file)


def fromString(string):
    from lys.filters import Filters
    return Filters.fromString(string)


def toString(filter):
    from lys.filters import Filters
    return Filters.toString(filter)
