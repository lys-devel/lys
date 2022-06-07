"""
The template for making new filter that can be used in MultiCut.
This file can be used without edit. The sample filter is registered in 'User Defined Filters' in MultiCut.
See Section 'Making a new filter' in menu (Help -> Open lys reference) for detail
"""


# Required lys modules for making filter
from lys import DaskWave
from lys.filters import FilterSettingBase, filterGUI, addFilter, FilterInterface

# We recommend users to import Qt widgets from llys, which is alias to Qt5 libraries (PyQt5 or PySide2)
from lys.Qt import QtWidgets


class FilterName(FilterInterface):
    """Filter class"""

    def __init__(self, param1, param2):
        """ Save parameters """
        self._param1 = param1
        self._param2 = param2

    def _execute(self, wave, *args, **kwargs):
        """ execute and return result as DaskWave. This filter simply add param1 to data. """
        newData = wave.data + self._param1
        newAxes = wave.axes
        newNote = wave.note
        return DaskWave(newData, *newAxes, **newNote)

    def getParameters(self):
        """ Return dictionary. Keys must be consistent with arguments of __init__. """
        return {"param1": self._param1, "param2": self._param2}

    def getRelativeDimension(self):
        """ Return change of dimension. For example, when 2D data is changed to 3D, return 1 """
        return 0


@filterGUI(FilterName)
class _FilterNameSetting(FilterSettingBase):
    """GUI (QWidget) for filter used by MultiCut."""

    def __init__(self, dimension):
        """
        __init__ must take an argument that indicate dimension of input data.
        Initialize widgets (see manuals of PyQt5 and PySide2) after calling super().__init__(dimension).
        """
        super().__init__(dimension)
        self._spin1 = QtWidgets.QSpinBox()
        self._spin2 = QtWidgets.QSpinBox()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._spin1)
        layout.addWidget(self._spin2)

        self.setLayout(layout)

    def getParameters(self):
        """ Return dictionary. Keys must be consistent with arguments of FilterName.__init__. """
        return {"param1": self._spin1.value(), "param2": self._spin2.value()}

    def setParameters(self, param1, param2):
        """ Set widget values. Arguments should be consistent with FilterName.__init__. """
        self._spin1.setValue(param1)
        self._spin2.setValue(param2)


# Add filte to lys. You can use new filter from MultiCut
addFilter(
    FilterName,
    gui=_FilterNameSetting,
    guiName="FilterName",
    guiGroup="User Defined Filters"
)
