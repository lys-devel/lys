import os

from lys import glb
from lys.Qt import QtWidgets, QtCore, QtGui


class StringTextEdit(QtWidgets.QPlainTextEdit):
    keyPressed = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, file, parent=None):
        super().__init__(parent)
        self.metrics = self.fontMetrics()
        self.setTabStopWidth(self.metrics.width(" ") * 6)
        self.setViewportMargins(self.metrics.width("8") * 8, 0, 0, 0)
        self.numberArea = QtWidgets.QWidget(self)
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
        if event.key() == QtCore.Qt.Key_Return:
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
        if obj == self.numberArea and event.type() == QtCore.QEvent.Paint:
            self.drawLineNumbers(obj)
            return True
        return False

    def drawLineNumbers(self, o):
        c = self.cursorForPosition(QtCore.QPoint(0, 0))
        block = c.block()
        paint = QtGui.QPainter()
        paint.begin(o)
        paint.setPen(QtGui.QColor('gray'))
        paint.setFont(QtGui.QFont())
        while block.isValid():
            c.setPosition(block.position())
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10:
                break
            paint.drawText(QtCore.QPoint(10, r.bottom() - 3), str(block.blockNumber() + 1))
            block = block.next()
        paint.end()

    def save(self):
        with open(self._file, 'w') as f:
            f.write(self.toPlainText())


_instance = StringTextEdit(".lys/memo.str")
glb.mainWindow().tabWidget("bottom").addTab(_instance, "Memo")
