import os

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from lys import *
from .filters import Filters


class FilterViewWidget(FileSystemView):
    def __init__(self, parent):
        super().__init__(parent)
        os.makedirs(home() + "/.lys/filters", exist_ok=True)
        self.Model.AddAcceptedFilter("*.fil")
        self.SetPath(home() + "/.lys/filters")
        self.__viewContextMenu(self)

    def __viewContextMenu(self, tree):
        save = QAction('Save to file', self, triggered=self._Action_Save)
        load = QAction('Load from file', self, triggered=self._Action_Load)
        print = QAction('Print', self, triggered=self._Action_Print)
        menu = {}
        menu['dir'] = [tree.Action_NewDirectory(), load, tree.Action_Delete()]
        menu['mix'] = [tree.Action_Delete()]
        menu['.fil'] = [print, save, tree.Action_Delete()]
        tree.SetContextMenuActions(menu)

    def _Action_Save(self):
        path = self.selectedPath()
        if path is None:
            return
        f = Filters.fromFile(path)
        fname = QFileDialog.getSaveFileName(self, 'Save Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
        if fname[0]:
            if os.path.exists(fname[0] + ".fil"):
                res = QMessageBox.information(None, "Confirmation", "The old filter will be deleted. Do you really want to overwrite?", QMessageBox.Yes, QMessageBox.No)
                if res == QMessageBox.No:
                    return
            f.saveAsFile(fname[0])

    def _Action_Load(self):
        path = self.selectedPath()
        if path is not None:
            fname = QFileDialog.getOpenFileName(self, 'Open Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
            if fname[0]:
                f = Filters.fromFile(fname[0])
                text, ok = QInputDialog.getText(self, 'Import Filter', 'Enter filter name:')
                path += "/" + text
                if not ok:
                    return
                if os.path.exists(path) or os.path.exists(path + ".fil"):
                    res = QMessageBox.information(None, "Confirmation", "The old filter will be deleted. Do you really want to overwrite?", QMessageBox.Yes, QMessageBox.No)
                    if res == QMessageBox.No:
                        return
                f.saveAsFile(path)

    def _Action_Print(self):
        res = ""
        path = self.selectedPath()
        if path is None:
            print("Invalid path")
            return
        filt = Filters.fromFile(path)
        if hasattr(filt, "dimension"):
            res += "Dimension: " + str(filt.dimension) + ", "
        filt = filt.getFilters()
        res += "Number of Filters: " + str(len(filt)) + "  "
        res += "\n"
        for f in filt:
            res += ">> " + f.__class__.__name__ + " "
        print(res)


class FilterExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export filter")
        self.__initlayout()
        self.path = None
        self.show()

    def __initlayout(self):
        self.view = FilterViewWidget(self)

        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("O K", clicked=self.__ok))
        h1.addWidget(QPushButton("CANCEL", clicked=self.reject))

        v1 = QVBoxLayout()
        v1.addWidget(self.view)
        v1.addLayout(h1)
        self.setLayout(v1)

    def __ok(self):
        self.path = self.view.selectedPath()
        if os.path.isdir(self.path):
            text, ok = QInputDialog.getText(self, 'Export Filter', 'Enter filter name:')
            self.path += "/" + text
            if not ok:
                return
        if os.path.exists(self.path) or os.path.exists(self.path + ".fil"):
            res = QMessageBox.information(None, "Confirmation", "The old filter will be deleted. Do you really want to overwrite?", QMessageBox.Yes, QMessageBox.No)
            if res == QMessageBox.No:
                return
        self.accept()

    def getExportPath(self):
        return self.path


class FilterImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import filter")
        self.__initlayout()
        self.path = None
        self.show()

    def __initlayout(self):
        self.view = FilterViewWidget(self)

        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("O K", clicked=self.__ok))
        h1.addWidget(QPushButton("CANCEL", clicked=self.reject))

        v1 = QVBoxLayout()
        v1.addWidget(self.view)
        v1.addLayout(h1)
        self.setLayout(v1)

    def __ok(self):
        self.path = self.view.selectedPath()
        if os.path.isdir(self.path):
            QMessageBox.information(None, "Caution", "Please select .fil file!", QMessageBox.Yes)
            return
        self.accept()

    def getImportPath(self):
        return self.path
