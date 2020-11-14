
from ..BasicWidgets import *


class ColoredFileSystemModel(ExtendFileSystemModel):
    def __init__(self):
        super().__init__()
        for ext in LoadFile.getExtentions():
            self.AddAcceptedFilter('*' + ext)
        self.AddAcceptedFilter('*.py')
        self.AddAcceptedFilter('*.fil')

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.FontRole:
            if pwd().find(self.filePath(index)) > -1:
                font = QFont()
                font.setBold(True)
                return font
        if role == Qt.BackgroundRole:
            if pwd() == self.filePath(index):
                return QColor(200, 200, 200)
        return super().data(index, role)


class FileWidget(FileSystemView):
    def __init__(self, parent, shell):
        self.model = ColoredFileSystemModel()
        super().__init__(parent, self.model)
        self.__shell = shell
        self.SetPath(pwd())
        self.__viewContextMenu(self)

    def __viewContextMenu(self, tree):
        cd = QAction('Set Current Directory', self, triggered=self.__setCurrentDirectory)
        ld = QAction('Load', self, triggered=self.__load)
        op = QAction('Open', self, triggered=self.__openpy)
        show = QAction('Show all graphs', self, triggered=self.__showgraphs)
        save = QAction('Save all graphs', self, triggered=self.__savegraphs)
        menu = {}
        menu['dir'] = [cd, tree.Action_NewDirectory(), tree.Action_Delete(), show, save]
        menu['mix'] = [ld, tree.Action_Delete()]
        menu['other'] = [ld, tree.Action_Delete(), tree.Action_Print()]
        menu['.npz'] = [tree.Action_Display(), tree.Action_Append(), tree.Action_MultiCut(), tree.Action_Edit(), ld, tree.Action_Print(), tree.Action_Delete()]
        menu['.py'] = [op, tree.Action_Delete()]
        menu['.lst'] = [op, tree.Action_Edit()]
        tree.SetContextMenuActions(menu)

    def __showgraphs(self):
        p = self.selectedPaths()[0]
        for f in glob.glob(p + "/*.grf"):
            Graph(f)

    def __savegraphs(self):
        p = self.selectedPaths()[0]
        i = 0
        while(True):
            g = Graph.active(i)
            if g is None:
                return
            else:
                g.Save(p + "/graph" + str(i) + ".grf")
            i += 1

    def __setCurrentDirectory(self):
        cd(self.selectedPaths()[0])

    def __load(self):
        for p in self.selectedPaths():
            self.__shell.Load(p)

    def __openpy(self):
        for p in self.selectedPaths():
            PythonEditor(p)
