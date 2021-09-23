import sys
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


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
    __logFile = ".lys/commandlog.log"
    updated = pyqtSignal(str, QColor)

    def __init__(self, parent):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.__load()
        sys.stdout = Logger(self, sys.stdout, self.textColor())
        sys.stderr = Logger(self, sys.stderr, QColor(255, 0, 0))
        self.updated.connect(self.update)

    def __load(self):
        if os.path.exists(self.__logFile):
            with open(self.__logFile, 'r') as f:
                self.__clog = f.read()
        else:
            self.__clog = ""
        self.setPlainText(self.__clog)

    def save(self):
        data = self.toPlainText()
        if len(data) > 300000:
            data = data[-300000:]
        with open(self.__logFile, 'w') as f:
            f.write(data)

    def update(self, message, color):
        self.moveCursor(QTextCursor.End)
        self.setTextColor(color)
        self.insertPlainText(message)
        self.moveCursor(QTextCursor.StartOfLine)
