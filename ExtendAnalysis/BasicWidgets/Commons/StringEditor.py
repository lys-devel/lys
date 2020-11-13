import sys
import os

import autopep8

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from ExtendAnalysis import *


class StringTextEdit(QPlainTextEdit):
    keyPressed = pyqtSignal(QKeyEvent)

    def __init__(self, file, parent=None):
        super().__init__(parent)
        self.metrics = self.fontMetrics()
        self.setTabStopWidth(self.metrics.width(" ") * 6)
        self.setViewportMargins(self.metrics.width("8") * 8, 0, 0, 0)
        self.numberArea = QWidget(self)
        self.numberArea.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height())
        self.numberArea.installEventFilter(self)
        # self.widget.setStyleSheet("background-color : #282C34; color: #eeeeee;")
        #self.highlighter = PythonHighlighter(self.widget.document())
        self.str = String(file)
        self.setPlainText(self.str.data)
        self.textChanged.connect(self.save)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return:
            for i in range(self.textCursor().block().previous().text().count('\t')):
                self.insertPlainText('\t')

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.numberArea.height() == self.height():
            num = 1
        else:
            num = 0
        self.numberArea.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height() + num)

    def eventFilter(self, obj, event):
        if obj == self.numberArea and event.type() == QEvent.Paint:
            self.drawLineNumbers(obj)
            return True
        return False

    def drawLineNumbers(self, o):
        c = self.cursorForPosition(QPoint(0, 0))
        block = c.block()
        paint = QPainter()
        paint.begin(o)
        paint.setPen(QColor('gray'))
        paint.setFont(QFont())
        while block.isValid():
            c.setPosition(block.position())
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10:
                break
            paint.drawText(QPoint(10, r.bottom() - 3), str(block.blockNumber() + 1))
            block = block.next()
        paint.end()

    def save(self):
        self.str.data = self.toPlainText()


class StringEditor(ExtendMdiSubWindow):
    def __init__(self, file):
        super().__init__()
        self.widget = StringTextEdit(file, self)
        self.setWidget(self.widget)
        self.resize(600, 600)
        self.setWindowTitle(os.path.basename(file))
