import os
import sys
import traceback
import rlcompleter

from lys import home, SettingDict
from lys.widgets import _ExtendMdiArea, FileSystemView, Graph
from lys.resources import lysIcon
from lys.Qt import QtWidgets, QtCore, QtGui

from .shell import ExtendShell
from .Tabs import GraphTab, TableTab, MulticutTab, FittingTab


class MainWindow(QtWidgets.QMainWindow):
    """
    *Main window* class gives several methods to customize lys GUI.

    Tabs can be customized by :meth:`tabWidget` method.

    Developers can access :class:`lys.widgets.fileView.FileSystemView` by :attr:`fileView` property.

    Do not instanciate this class because it is automatically done by lys.
    """
    beforeClosed = QtCore.pyqtSignal(QtCore.QEvent)
    """
    beforeClosed(event) signal is emitted when close button of lys is clicked.

    Developers can connect any functions/methods to this signal.

    If the main window should not be closed, call event.ignore() in the connected functions/methods.

    Example::

        from lys import glb
        glb.mainWindow().beforeClosed.connect(lambda event: print("Main window closed."))
    """

    closed = QtCore.pyqtSignal()
    """
    closed(event) signal is emitted when main window of lys is closed.

    Example::

        from lys import glb
        glb.mainWindow().closed.connect(lambda: print("Main window closed."))
    """

    def __init__(self, show=True, restore=False, selfClose=False):
        super().__init__()
        self._workspace = []
        self._settingDict = SettingDict(home() + "/.lys/workspace/works.dic")
        self._selfClose = selfClose
        self.__initUI()
        self.__initMenu()
        if restore:
            self._restoreWorkspaces()
        if show:
            self.show()

    def closeEvent(self, event):
        """
        Reimplementation of closeEvent in QMainWindow.closeEvent for realization of beforeClosed and closed signals.
        """
        if not self._selfClose:
            msg = QtWidgets.QMessageBox(parent=self)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Caution")
            msg.setText("Lys is closing. Are you sure?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            ok = msg.exec_()
            if ok != QtWidgets.QMessageBox.Yes:
                return event.ignore()
        self.beforeClosed.emit(event)
        if not event.isAccepted():
            return
        self.closed.emit()
        self._settingDict["workspaces"] = [w._workspace for w in self._workspace]

    def __initUI(self):
        self.setWindowTitle('lys')
        self.setWindowIcon(lysIcon)

        self._mainTab = QtWidgets.QTabWidget()
        self._mainTab.setTabsClosable(True)
        self.__addWorkspace("default")
        self._mainTab.addTab(QtWidgets.QWidget(), "+")
        self._mainTab.tabBar().tabButton(0, QtWidgets.QTabBar.RightSide).resize(0, 0)
        self._mainTab.tabBar().tabButton(1, QtWidgets.QTabBar.RightSide).resize(0, 0)
        self.__loadWorkspace()
        self._mainTab.setCurrentIndex(0)
        self._mainTab.currentChanged.connect(self._changeTab)
        self._mainTab.tabCloseRequested.connect(self._closeTab)
        self._mainTab.tabBar().setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._mainTab.tabBar().customContextMenuRequested.connect(self.__tabContextMenu)
        self._side = self.__sideBar()
        self._bottom = self.__bottomBar()

        self._showBtn = QtWidgets.QPushButton("Show", clicked=self.__setVisible)

        h = QtWidgets.QHBoxLayout()
        h.addWidget(_CommandLineEdit(ExtendShell._instance))
        h.addWidget(self._showBtn)
        h.setContentsMargins(0, 0, 0, 0)

        sp1 = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        sp1.setHandleWidth(0)
        sp1.addWidget(self._mainTab)
        sp1.addWidget(self._side)

        self._sp2 = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._sp2.setHandleWidth(0)
        self._sp2.addWidget(sp1)
        self._sp2.addWidget(self._bottom)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._sp2)
        layout.addLayout(h)
        layout.setContentsMargins(2, 0, 2, 2)
        layout.setSpacing(2)

        w = QtWidgets.QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)
        self._bottom.hide()

    def __sideBar(self):
        from . import addSidebarWidget, _side

        self._fileView = FileSystemView(home(), drop=True)
        addSidebarWidget(GraphTab())
        addSidebarWidget(TableTab())
        addSidebarWidget(MulticutTab())
        addSidebarWidget(FittingTab())

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(self._fileView, "File")

        for i, widget in enumerate(_side):
            self._tab.addTab(widget, widget.title)
            self._tab.setTabVisible(self._tab.count()-1, widget.visible)
        return self._tab

    def __bottomBar(self):
        self._tab_up = QtWidgets.QTabWidget()
        self._tab_up.addTab(_CommandLogWidget(self), "Command")
        return self._tab_up

    def __setVisible(self):
        self._tab_up.setVisible(not self._tab_up.isVisible())
        if self._tab_up.isVisible():
            self._showBtn.setText("Hide")
        else:
            self._showBtn.setText("Show")

    def __tabContextMenu(self, qPoint):
        index = self._mainTab.tabBar().tabAt(qPoint)
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction("Rename", self, triggered=lambda: self.__renameTab(index)))
        menu.exec_(QtGui.QCursor.pos())

    def __renameTab(self, index):
        text, ok = QtWidgets.QInputDialog.getText(self, "Rename tab", "Enter new name", text=self._mdiArea()._workspace)
        if ok:
            self._mdiArea().setName(text)
            self._mainTab.setTabText(index, text)

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
            work.restoreWorkspace()
            self._mainTab.setTabText(i, work.getName())
            self.closed.connect(work.storeWorkspace)
        self._mainTab.setCurrentIndex(0)

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Sidebar")

        act = win.addAction("Show/Hide sidebar")
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
        self._workspace[index].closeAllWindows()
        self._workspace.pop(index)
        self._mainTab.setCurrentIndex(index - 1)
        self._mainTab.removeTab(index)

    def tabWidget(self, position):
        """
        Get tab widget that is located at the right and bottom of the main window.

        Args:
            position('right' or 'bottom')

        Returns:
            QTabWidget: The tab widget.
        """
        if position == "right":
            return self._tab
        else:
            return self._tab_up

    @property
    def fileView(self):
        """
        Returns :class:`lys.widgets.fileView.FileSystemView` object in main window.

        Developers can get selected paths and add new context menu in FileSystemView.

        See :class:`lys.widgets.fileView.FileSystemView` for detail.
        """
        return self._fileView

    def closeAllGraphs(self, workspace=None):
        """
        Close all graphs in the workspace.

        Args:
            workspace(str): The name of the workspace to close all graphs. If it is None, present workspace is selected.
        """
        list = self._mdiArea(workspace=workspace).subWindowList(order=QtWidgets.QMdiArea.ActivationHistoryOrder)
        for item in reversed(list):
            if isinstance(item, Graph):
                item.close(force=True)

    def _mdiArea(self, workspace=None):
        if workspace == "__all__":
            return self._workspace
        i = self._mainTab.currentIndex()
        if i > len(self._workspace) - 1:
            i = len(self._workspace) - 1
        return self._workspace[i]


class _CommandLogWidget(QtWidgets.QTextEdit):
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
    updated = QtCore.pyqtSignal(str, QtGui.QColor)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.__load()
        sys.stdout = self._out = self._Logger(self, sys.stdout, self.textColor())
        sys.stderr = self._err = self._Logger(self, sys.stderr, QtGui.QColor(255, 0, 0))
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
        self.moveCursor(QtGui.QTextCursor.End)
        self.setTextColor(color)
        self.insertPlainText(message)
        self.moveCursor(QtGui.QTextCursor.StartOfLine)
        self._save()


class _CommandLineEdit(QtWidgets.QTextEdit):
    def __init__(self, shell):
        super().__init__()
        self.setPlaceholderText("Type python command and press enter, press tab to auto-complete")
        self.shell = shell
        self.__logn = 0
        self.completer = rlcompleter.Completer(self.shell.dict)
        self.textChanged.connect(self.__onTextChanged)
        self.textChanged.emit()

    def __onTextChanged(self):
        doc = self.document()
        margins = self.contentsMargins()
        h = doc.size().toSize().height() + (doc.documentMargin() + self.frameWidth()) * 2 + margins.top() + margins.bottom()
        self.setFixedHeight(int(h))

    def __findBlock(self):
        text = self.toPlainText()
        end = self.textCursor().position()
        for i in range(1, end + 1):
            if text[end - i] in [",", "(", " ", "=", "[", ":", "\n"]:
                return end - i + 1, end
        return 0, end

    def _resetComplete(self):
        self.__tabn = -1

    def _complete(self):
        if len(self.toPlainText()) == 0:
            return True
        if self.__tabn == -1:
            self._printComplete()
            self.__tabn += 1
            return True
        if self.__tabn == 0:
            s, e = self.__findBlock()
            self.__prefix = self.toPlainText()[:s]
            self.__suffix = self.toPlainText()[e:]
            self.__txt = self.toPlainText()[s:e]
        try:
            tmp = self.completer.complete(self.__txt, self.__tabn)
            if tmp is None and not self.__tabn == 0:
                tmp = self.completer.complete(self.__txt, 0)
                self.__tabn = 0
            if tmp is not None:
                self.setText(self.__prefix + tmp + self.__suffix)
                c = self.textCursor()
                c.movePosition(QtGui.QTextCursor.Start)
                c.movePosition(QtGui.QTextCursor.Right, n=len(self.__prefix + tmp))
                self.setTextCursor(c)
                self.__tabn += 1
        except Exception:
            print("fail to complete:", self.__txt, self.__tabn)
        return True

    def _printComplete(self):
        if len(self.toPlainText()) == 0:
            return
        s, e = self.__findBlock()
        self.__txt = self.toPlainText()[s:e]
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
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Tab:
                return self._complete()
            else:
                self._resetComplete()

            if event.key() == QtCore.Qt.Key_Up:
                log = self.shell.commandLog
                if len(log) == 0:
                    return True
                self.__logn += 1
                if len(log) < self.__logn:
                    self.__logn = len(log)
                self.setText(log[len(log) - self.__logn])
                return True

            if event.key() == QtCore.Qt.Key_Down:
                log = self.shell.commandLog
                if not self.__logn == 0:
                    self.__logn -= 1
                if self.__logn == 0:
                    self.setText("")
                else:
                    self.setText(log[max(0, len(log) - self.__logn)])
                return True
            if event.key() == QtCore.Qt.Key_Return and (event.modifiers() == QtCore.Qt.NoModifier):
                self.__SendCommand()
                return True

        return super().event(event)

    def __SendCommand(self):
        for c in self.toPlainText().splitlines():
            self.__exeCommand(c)
        self.clear()
        self.__logn = 0

    def __exeCommand(self, txt):
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
