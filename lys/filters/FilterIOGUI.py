import os

from LysQt.QtWidgets import QMenu, QAction, QFileDialog, QMessageBox, QInputDialog, QDialog, QPushButton, QHBoxLayout, QVBoxLayout

from lys import home, filters
from lys.FileView import FileSystemView


class FilterViewWidget(FileSystemView):
    def __init__(self, parent):
        os.makedirs(home() + "/.lys/filters", exist_ok=True)
        super().__init__(home() + "/.lys/filters", filter=False, drop=True)
        self.__addContextMenu()

    def __addContextMenu(self):
        save = QAction('Save to external file', self, triggered=self._Action_Save)
        load = QAction('Load from external file', self, triggered=self._Action_Load)
        print = QAction('Print', self, triggered=self._Action_Print)
        menu = QMenu()
        menu.addAction(save)
        menu.addAction(print)
        menu2 = QMenu()
        menu2.addAction(load)
        self.registerFileMenu(".fil", menu)
        self.registerFileMenu("dir", menu2)

    def _Action_Save(self):
        path = self.selectedPaths()[0]
        if path is None:
            return
        f = filters.fromFile(path)
        fname = QFileDialog.getSaveFileName(self, 'Save Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
        if fname[0]:
            if os.path.exists(fname[0] + ".fil"):
                res = QMessageBox.information(None, "Confirmation", "The old filter will be deleted. Do you really want to overwrite?", QMessageBox.Yes, QMessageBox.No)
                if res == QMessageBox.No:
                    return
            f.saveAsFile(fname[0])

    def _Action_Load(self):
        path = self.selectedPaths()[0]
        if path is not None:
            fname = QFileDialog.getOpenFileName(self, 'Open Filter', home(), filter="Filter files(*.fil);;All files(*.*)")
            if fname[0]:
                name = os.path.basename(fname[0])
                path += "/" + name
                if os.path.exists(path) or os.path.exists(path + ".fil"):
                    res = QMessageBox.information(None, "Confirmation", "File " + name + " already exits. Do you want to overwrite it?", QMessageBox.Yes, QMessageBox.No)
                    if res == QMessageBox.No:
                        return
                f = filters.fromFile(fname[0])
                f.saveAsFile(path)

    def _Action_Print(self):
        res = ""
        path = self.selectedPaths()[0]
        if path is None:
            print("Invalid path")
            return
        filt = filters.fromFile(path)
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
        self.path = self.view.selectedPaths()[0]
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
        self.path = self.view.selectedPaths()[0]
        if os.path.isdir(self.path):
            QMessageBox.information(None, "Caution", "Please select .fil file!", QMessageBox.Yes)
            return
        self.accept()

    def getImportPath(self):
        return self.path
