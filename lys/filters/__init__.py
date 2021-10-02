import inspect
from .filter import *
from .filtersGUI import FiltersGUI, FiltersDialog
from . import filterGUI


def __register():
    from lys import filters
    for key, item in filters.__dict__.items():
        if inspect.isclass(item):
            if issubclass(item, FilterInterface):
                _filterClasses[key] = item


# all filter classes
_filterClasses = {}
__register()

fromFile = Filters.fromFile
