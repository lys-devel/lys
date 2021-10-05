from .filter import *
from .filtersGUI import FiltersGUI, FiltersDialog, FilterSettingBase, filterGUI
from . import defaultFilterGUI

# all filter classes
_filterClasses = {}


def __register():
    import inspect
    from lys import filters
    for key, item in filters.__dict__.items():
        if inspect.isclass(item):
            if issubclass(item, FilterInterface):
                _filterClasses[key] = item


def addFilter(obj, name, group, gui=None):
    pass


__register()

fromFile = Filters.fromFile
