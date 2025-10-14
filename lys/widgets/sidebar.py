
from lys.Qt import QtWidgets


class SidebarWidget(QtWidgets.QWidget):
    """
    Base class for widgets in sidebar of MainWindow.

    Args:
        title(string): The title of the tab in the sidebar.
        visible(bool): Wheather the tab is visible just after the initialization.
    """
    def __init__(self, title, visible=False):
        super().__init__()
        self._title = title
        self._visible = visible

    @property
    def title(self):
        return self._title

    @property
    def visible(self):
        return self._visible

    def show(self, b=True):
        from lys import glb
        tab = glb.mainWindow().tabWidget("right")
        list = [tab.tabText(i) for i in range(tab.count())]
        if self._title in list:
            tab.setTabVisible(list.index(self._title), b)
            if b:
                tab.setCurrentIndex(list.index(self._title))
                glb.mainWindow()._side.setVisible(True)
