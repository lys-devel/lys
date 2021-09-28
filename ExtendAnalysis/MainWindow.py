import os
import sys
import traceback
import rlcompleter


from LysQt.QtWidgets import QMainWindow, QMdiArea, QSplitter, QLineEdit, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTextEdit
from LysQt.QtGui import QColor, QTextCursor, QTextOption
from LysQt.QtCore import Qt, pyqtSignal, QEvent

from . import plugin, home, Graph
from .FileView import FileSystemView

from .ExtendType import ExtendMdiSubWindow, AutoSavedWindow


class MainWindow(QMainWindow):
    closed = pyqtSignal(object)
    _instance = None

    def __init__(self):
        super().__init__()
        MainWindow._instance = self
        self.__initUI()
        self.__initMenu()
        ExtendMdiSubWindow.mdimain = self.area
        AutoSavedWindow.RestoreAllWindows()

    def closeEvent(self, event):
        AutoSavedWindow.StoreAllWindows()
        self.closed.emit(event)
        if not event.isAccepted():
            return
        ExtendMdiSubWindow.CloseAllWindows()

    def __initUI(self):
        self.setWindowTitle('lys')
        self.area = QMdiArea()
        self._side = self.__sideBar()

        sp = QSplitter(Qt.Horizontal)
        sp.addWidget(self.area)
        sp.addWidget(self._side)
        self.setCentralWidget(sp)
        self.show()

    def __sideBar(self):
        self._fileView = FileSystemView(home())
        self._setting = QVBoxLayout()
        self._setting.addStretch()
        setting = QWidget()
        setting.setLayout(self._setting)

        self._tab_up = QTabWidget()
        self._tab_up.addTab(_CommandLogWidget(self), "Command")

        self._tab = QTabWidget()
        self._tab.addTab(self._fileView, "File")
        self._tab.addTab(setting, "Settings")

        layout_h = QSplitter(Qt.Vertical)
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(_CommandLineEdit(plugin.shell()))
        layout_h.addWidget(self._tab)

        lay = QHBoxLayout()
        lay.addWidget(layout_h)
        w = QWidget()
        w.setLayout(lay)
        return w

    def __initMenu(self):
        menu = self.menuBar()
        file = menu.addMenu("File")

        act = file.addAction("Exit")
        act.triggered.connect(exit)

        win = menu.addMenu("Window")

        act = win.addAction("Close all graphs")
        act.triggered.connect(Graph.closeAllGraphs)
        act.setShortcut("Ctrl+K")

        act = win.addAction("Show/Hide Sidebar")
        act.triggered.connect(lambda: self._side.setVisible(not self._side.isVisible()))
        act.setShortcut("Ctrl+J")
        return

    def addTab(self, widget, name, position):
        if position == "up":
            self._tab_up.addTab(widget, name)
        if position == "down":
            self._tab.addTab(widget, name)

    def addSettingWidget(self, widget):
        self._setting.insertWidget(self._setting.count() - 1, widget)

    @property
    def fileView(self):
        return self._fileView


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
        sys.stdout = self._Logger(self, sys.stdout, self.textColor())
        sys.stderr = self._Logger(self, sys.stderr, QColor(255, 0, 0))
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


def addSubWindow(win):
    MainWindow._instance.area.addSubWindow(win)
