# syntax.py

import sys, os

from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtWidgets import *

from ExtendAnalysis import *

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format

# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('#C578DD'),
    'keyword2': format('#56B5C2'),
    'operator': format('#eeeeee'),
    'brace': format('#eeeeee'),
    'defclass': format('#D19965'),
    'defmethod': format('#56B5C2'),
    'string': format('#97C279'),
    'string2': format('#97C279'),
    'comment': format('gray', 'italic'),
    'self': format('#DF6B75'),
    'numbers': format('#D19965'),
}

class PythonHighlighter (QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False', 'with', 'as'
    ]
    keywords2 = [
        '__init__','__del__','format','len','super', 'cd', 'home', 'pwd', 'cp', 'mv', 'rm', 'range', 'open'
    ]
    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]
    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in PythonHighlighter.keywords]
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword2'])
            for w in PythonHighlighter.keywords2]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defmethod']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False

class _PlainTextEdit(QPlainTextEdit):
    keyPressed=pyqtSignal(QKeyEvent)
    def __init__(self,parent):
        super().__init__(parent)
        self.metrics=self.fontMetrics()
        self.setTabStopWidth(self.metrics.width(" ")*12)
        self.setViewportMargins(self.metrics.width("8")*8, 0, 0, 0)
        self.numberArea = QWidget(self)
        self.numberArea.setGeometry(0,0,self.fontMetrics().width("8")*8,self.height())
        self.numberArea.installEventFilter(self);
    def keyPressEvent(self,event):
        self.keyPressed.emit(event)
        super().keyPressEvent(event)
        if event.key()==Qt.Key_Return:
            for i in range(self.textCursor().block().previous().text().count('\t')):
                self.insertPlainText('\t')
    def paintEvent(self,e):
        super().paintEvent(e)
        if self.numberArea.height() == self.height():
            num = 1
        else:
            num = 0
        self.numberArea.setGeometry(0,0,self.fontMetrics().width("8")*8,self.height()+num)
    def eventFilter(self,obj,event):
        if obj == self.numberArea and event.type() == QEvent.Paint:
            self.drawLineNumbers(obj)
            return True
        return False;
    def drawLineNumbers(self,o):
        c = self.cursorForPosition(QPoint(0,0))
        block = c.block()
        paint = QPainter()
        paint.begin(o)
        paint.setPen(QColor('gray'))
        paint.setFont(QFont())
        while block.isValid():
            c.setPosition(block.position())
            r = self.cursorRect(c)
            if r.bottom() > self.height()+10: break
            paint.drawText(QPoint(10,r.bottom()-3),str(block.blockNumber()+1))
            block = block.next()
        paint.end()
class PythonEditor(ExtendMdiSubWindow):
    __list=[]
    @classmethod
    def _Add(cls,win):
        cls.__list.append(weakref.ref(win))
    @classmethod
    def CloseAllEditors(cls):
        for w in cls.__list:
            if w() is not None:
                res=w().close()
                if not res:
                    return False
        return True
    def __init__(self,file):
        super().__init__()
        self.setWindowTitle(os.path.basename(file))
        self.widget=_PlainTextEdit(self)
        self.widget.keyPressed.connect(self.keyPressed)
        self.widget.setStyleSheet("background-color : #282C34; color: #eeeeee;")
        self.highlighter=PythonHighlighter(self.widget.document())
        self.file=os.path.abspath(file)
        with open(self.file, 'r') as data:
            self.widget.setPlainText(data.read())
        self.setWidget(self.widget)
        self.resize(600,600)
        PythonEditor._Add(self)
    def keyPressed(self,event):
        if event.key() == Qt.Key_S:
            if (event.modifiers() and Qt.ControlModifier):
                self.save()
    def save(self):
        with open(self.file, 'w') as data:
            data.write(self.widget.toPlainText())
    def closeEvent(self,event):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Do you want to save changes?")
        msg.setWindowTitle(os.path.basename(self.file))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        ok = msg.exec_()
        if ok==QMessageBox.Cancel:
            event.ignore()
        if ok==QMessageBox.No:
            event.accept()
        if ok==QMessageBox.Yes:
            self.save()
            event.accept()
