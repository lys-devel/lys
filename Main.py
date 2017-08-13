from PyQt5.QtWidgets import *
class MainWindow(QMdiArea):
    def __init__(self):
        from ExtendShell import ExtendShell
        from GraphWindow import AutoSavedWindow
        super().__init__()
        AutoSavedWindow.mdimain=self
        shell=ExtendShell()
        self.com=shell.CommandWindow()
        self.addSubWindow(self.com)
        self.show()
    def closeEvent(self,event):
        from ExtendShell import ExtendShell
        from GraphWindow import AutoSavedWindow, PreviewWindow
        from AnalysisWindow import AnalysisWindow
        self.com.saveData()
        AutoSavedWindow.CloseAllWindows()
        AnalysisWindow.CloseAllWindows()
        PreviewWindow.CloseAllWindows()
        event.accept()

if __name__ == '__main__':
    import  PyQt5.QtCore, sys
    app = PyQt5.QtWidgets.QApplication([])
    main=MainWindow()
    sys.exit(app.exec())
