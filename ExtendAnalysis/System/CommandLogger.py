import sys

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ExtendAnalysis import String


class Logger(object):
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


class CommandLogWidget(QTextEdit):
    updated = pyqtSignal(str, QColor)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.__clog = String(".lys/commandlog.log")
        self.setPlainText(self.__clog.data)
        sys.stdout = Logger(self, sys.stdout, self.textColor())
        sys.stderr = Logger(self, sys.stderr, QColor(255, 0, 0))
        self.updated.connect(self.update)

    def save(self):
        self.__clog.data = self.toPlainText()

    def update(self, message, color):
        self.moveCursor(QTextCursor.End)
        self.setTextColor(color)
        self.insertPlainText(message)
        self.moveCursor(QTextCursor.StartOfLine)
