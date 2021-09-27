import os

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
        self._file = file
        if os.path.exists(file):
            with open(file, 'r') as f:
                self.str = f.read()
            self.setPlainText(self.str)
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
        with open(self._file, 'w') as f:
            f.write(self.toPlainText())


_instance = StringTextEdit(".lys/memo.str")
plugin.mainWindow().addTab(_instance, "Memo", "up")
