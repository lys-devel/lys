import os
import sys
import traceback
import rlcompleter


from LysQt.QtWidgets import QMainWindow, QSplitter, QLineEdit, QWidget, QHBoxLayout, QTabWidget, QTextEdit, QTabBar
from LysQt.QtGui import QColor, QTextCursor, QTextOption
from LysQt.QtCore import Qt, pyqtSignal, QEvent

from . import glb, home, SettingDict

from .FileView import FileSystemView
from .widgets import _ExtendMdiArea


class MainWindow(QMainWindow):
    """
    *Main window* class gives several methods to customize lys GUI.

    New tabs in side bar can be added by :meth:`addTab` method.

    Developers can access :class:`.FileView.FileSystemView` by :attr:`fileView` property.
    """
    beforeClosed = pyqtSignal(QEvent)
    """
    beforeClosed(event) signal is submitted when close button of lys is clicked.

    Developers can connect any functions/methods to this signal.

    If the main window should not be closed, call event.ignore() in the connected functions/methods.

    Example:

        >>> from lys import glb
        >>> main = glb.mainWindow()
        >>> main.beforeClosed.connect(lambda event: print("Main window closed."))
    """
    closed = pyqtSignal()
    """
    beforeClosed(event) signal is submitted when main window of lys is closed.

    Developers can connect any functions/methods to this signal for finalization.

    Example:

        >>> from lys import glb
        >>> main = glb.mainWindow()
        >>> main.closed.connect(lambda: print("Main window closed."))
    """

    def __init__(self, show=True):
        super().__init__()
        self._workspace = []
        self._settingDict = SettingDict(home() + "/.lys/workspace/works.dic")
        self.__initUI()
        self.__initMenu()
        if show:
            self.show()

    def closeEvent(self, event):
        """
        Reimplementation of closeEvent in QMainWindow.closeEvent for realization of beforeClosed and closed signals.
        """
        self.beforeClosed.emit(event)
        if not event.isAccepted():
            return
        self.closed.emit()
        self._settingDict["workspaces"] = [w._workspace for w in self._workspace]

    def __initUI(self):
        self.setWindowTitle('lys')

        self._mainTab = QTabWidget()
        self._mainTab.setTabsClosable(True)
        self.__addWorkspace("default")
        self._mainTab.addTab(QWidget(), "+")
        self._mainTab.tabBar().tabButton(0, QTabBar.RightSide).resize(0, 0)
        self._mainTab.tabBar().tabButton(1, QTabBar.RightSide).resize(0, 0)
        self.__loadWorkspace()
        self._mainTab.setCurrentIndex(0)
        self._mainTab.currentChanged.connect(self._changeTab)
        self._mainTab.tabCloseRequested.connect(self._closeTab)
        self._side = self.__sideBar()

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self._mainTab)
        sp.addWidget(self._side)
        self.setCentralWidget(sp)

    def __sideBar(self):
        self._fileView = FileSystemView(home(), drop=True)

        self._tab_up = QTabWidget()
        self._tab_up.addTab(_CommandLogWidget(self), "Command")

        self._tab = QTabWidget()
        self._tab.addTab(self._fileView, "File")

        layout_h = QSplitter(Qt.Vertical)
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(_CommandLineEdit(glb.shell()))
        layout_h.addWidget(self._tab)

        lay = QHBoxLayout()
        lay.addWidget(layout_h)
        w = QWidget()
        w.setLayout(lay)
        return w

    def __addWorkspace(self, workspace="default"):
        work = _ExtendMdiArea(self, workspace)
        self._workspace.append(work)
        self._mainTab.insertTab(max(0, self._mainTab.count() - 1), work, workspace)
        self._mainTab.setCurrentIndex(self._mainTab.count() - 1)

    def __loadWorkspace(self):
        list = self._settingDict.get("workspaces", [])
        for w in list:
            if w != "default":
                self.__addWorkspace(w)

    def _restoreWorkspaces(self):
        for i, work in enumerate(self._workspace):
            self._mainTab.setCurrentIndex(i)
            work.RestoreAllWindows()
            self.closed.connect(work.StoreAllWindows)
        self._mainTab.setCurrentIndex(0)

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Sidebar")

        act = win.addAction("Show/Hide Sidebar")
        act.triggered.connect(lambda: self._side.setVisible(not self._side.isVisible()))
        act.setShortcut("Ctrl+J")
        return

    def _changeTab(self, index):
        def getName():
            for i in range(1, 1000):
                name = "workspace" + str(i)
                if name not in [w._workspace for w in self._workspace]:
                    return name

        if index == self._mainTab.count() - 1:
            name = getName()
            self.__addWorkspace(name)
            self._mainTab.setCurrentIndex(index)

    def _closeTab(self, index):
        self._workspace[index].CloseAllWindows()
        self._workspace.pop(index)
        self._mainTab.setCurrentIndex(index - 1)
        self._mainTab.removeTab(index)

    def addTab(self, widget, name, position):
        """
        This method adds tab in the side bar.

        Args:
            widget(QWidget): widget to be added.
            name(str): Name of a tab.
            position('up' or 'down'): TabWidget to be added to.

        Example:

            >>> from lys import glb
            >>> main = glb.mainWindow()
            >>> main.addTab(QWidget(), "TestTab", "up")

        """
        if position == "up":
            self._tab_up.addTab(widget, name)
        if position == "down":
            self._tab.addTab(widget, name)

    @property
    def fileView(self):
        """
        Returns :class:`.FileView.FileSystemView` object in main window.

        Developers can get selected paths and add new context menu in FileSystemView.

        See :class:`.FileView.FileSystemView` for detail.
        """
        return self._fileView

    def _mdiArea(self, workspace="default"):
        if workspace == "__all__":
            return self._workspace
        i = self._mainTab.currentIndex()
        if i > len(self._workspace) - 1:
            i = len(self._workspace) - 1
        return self._workspace[i]


class _CommandLogWidget(QTextEdit):
    """Simple command log widget"""
    class _Logger(object):
        def __init__(self, editor, out, color):
            self.editor = editor
            self.out = out
            self.color = color

        def write(self, message):
            self.editor.updated.emit(message, self.color)
            if self.out:
                self.out.write(message)

        def flush(self):
            pass
    __logFile = ".lys/commandlog.log"
    updated = pyqtSignal(str, QColor)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.__load()
        sys.stdout = self._out = self._Logger(self, sys.stdout, self.textColor())
        sys.stderr = self._err = self._Logger(self, sys.stderr, QColor(255, 0, 0))
        self.updated.connect(self._update)

    def __load(self):
        if os.path.exists(self.__logFile):
            with open(self.__logFile, 'r') as f:
                self.__clog = f.read()
        else:
            self.__clog = ""
        self.setPlainText(self.__clog)

    def _save(self):
        data = self.toPlainText()
        if len(data) > 300000:
            data = data[-300000:]
        with open(self.__logFile, 'w') as f:
            f.write(data)

    def _update(self, message, color):
        self.moveCursor(QTextCursor.End)
        self.setTextColor(color)
        self.insertPlainText(message)
        self.moveCursor(QTextCursor.StartOfLine)
        self._save()


class _CommandLineEdit(QLineEdit):
    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self.returnPressed.connect(self.__SendCommand)
        self.__logn = 0
        self.completer = rlcompleter.Completer(self.shell.dict)

    def __findBlock(self):
        text = self.text()
        end = self.cursorPosition()
        for i in range(1, end + 1):
            if text[end - i] in [",", "(", " ", "=", "["]:
                return end - i + 1, end
        return 0, end

    def _resetComplete(self):
        self.__tabn = -1

    def _complete(self):
        if len(self.text()) == 0:
            return True
        if self.__tabn == -1:
            self._printComplete()
            self.__tabn += 1
            return True
        if self.__tabn == 0:
            s, e = self.__findBlock()
            self.__prefix = self.text()[:s]
            self.__suffix = self.text()[e:]
            self.__txt = self.text()[s:e]
        try:
            tmp = self.completer.complete(self.__txt, self.__tabn)
            if tmp is None and not self.__tabn == 0:
                tmp = self.completer.complete(self.__txt, 0)
                self.__tabn = 0
            if tmp is not None:
                self.setText(self.__prefix + tmp + self.__suffix)
                self.setCursorPosition(len(self.__prefix + tmp))
                self.__tabn += 1
        except Exception:
            print("fail to complete:", self.__txt, self.__tabn)
        return True

    def _printComplete(self):
        if len(self.text()) == 0:
            return
        s, e = self.__findBlock()
        self.__txt = self.text()[s:e]
        res = ""
        for i in range(100):
            tmp = self.completer.complete(self.__txt, i)
            if tmp is None:
                break
            res += tmp.replace("(", "") + ", "
        if i == 99:
            res += "etc..."
        if res != "":
            print(res)

    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                return self._complete()
            else:
                self._resetComplete()

            if event.key() == Qt.Key_Up:
                log = self.shell.commandLog
                if len(log) == 0:
                    return True
                if not len(log) - 2 == self.__logn:
                    self.__logn += 1
                self.setText(log[len(log) - self.__logn])
                return True

            if event.key() == Qt.Key_Down:
                log = self.shell.commandLog
                if not self.__logn == 0:
                    self.__logn -= 1
                if self.__logn == 0:
                    self.setText("")
                else:
                    self.setText(log[max(0, len(log) - self.__logn)])
                return True

        return QLineEdit.event(self, event)

    def __SendCommand(self):
        txt = self.text()
        self.clear()
        self.__logn = 0
        print(">", txt)
        try:
            res = self.shell.eval(txt, save=True)
            if res is not None:
                print(res)
            return
        except Exception:
            pass
        try:
            self.shell.exec(txt)
            return
        except Exception:
            err = traceback.format_exc()
            try:
                res = self.shell._do(txt)
            except Exception:
                sys.stderr.write('Invalid command.\n')
                print(err)
