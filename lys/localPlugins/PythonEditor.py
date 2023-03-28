
import os

import autopep8

from lys import glb, home, registerFileLoader
from lys.Qt import QtWidgets, QtGui, QtCore
from lys.widgets import LysSubWindow


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
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


class PythonHighlighter(QtGui.QSyntaxHighlighter):
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
        '__init__', '__del__', 'format', 'len', 'super', 'cd', 'home', 'pwd', 'cp', 'mv', 'rm', 'range', 'open'
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
        QtGui.QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QtCore.QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QtCore.QRegExp('"""'), 2, STYLES['string2'])

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
        self.rules = [(QtCore.QRegExp(pat), index, fmt)
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


class _PlainTextEdit(QtWidgets.QPlainTextEdit):
    keyPressed = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, parent):
        super().__init__(parent)
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.metrics = self.fontMetrics()
        self.setTabStopWidth(self.metrics.width(" ") * 6)
        self.setViewportMargins(self.metrics.width("8") * 8, 0, 0, 0)
        self.numberArea = QtWidgets.QWidget(self)
        self.numberArea.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height())
        self.numberArea.installEventFilter(self)

    def keyPressEvent(self, event):
        self.keyPressed.emit(event)
        if event.key() == QtCore.Qt.Key_Tab:
            self.insertPlainText('    ')
            return event.ignore()
        super().keyPressEvent(event)
        if event.key() == QtCore.Qt.Key_Return:
            for i in range(self.textCursor().block().previous().text().count('    ')):
                self.insertPlainText('    ')

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


class PythonEditor(LysSubWindow):
    __list = []
    updated = False

    @classmethod
    def _Add(cls, win):
        cls.__list.append(win)

    @classmethod
    def _Remove(cls, win):
        cls.__list.remove(win)

    @classmethod
    def _loadedEditor(cls, file):
        for editor in cls.__list:
            if editor.file == file:
                return editor
        return None

    @classmethod
    def CloseAllEditors(cls, event=None):
        if hasattr(event, "isAccepted"):
            if not event.isAccepted():
                return
        for editor in cls.__list:
            try:
                res = editor.close()
                if not res:
                    if hasattr(event, "ignore"):
                        event.ignore()
                    return
            # Editor has been closed
            except RuntimeError:
                pass

    def __new__(cls, file):
        loaded = PythonEditor._loadedEditor(file)
        if loaded is not None:
            loaded.raise_()
            return None
        return super().__new__(cls)

    def __init__(self, file):
        super().__init__()
        self.widget = _PlainTextEdit(self)
        self.widget.keyPressed.connect(self.keyPressed)
        self.widget.setStyleSheet("background-color : #282C34; color: #eeeeee;")
        self.highlighter = PythonHighlighter(self.widget.document())
        self.__load(file)
        self.setWidget(self.widget)
        self.widget.textChanged.connect(self.updateText)
        self.resize(600, 600)
        PythonEditor._Add(self)
        self.refreshTitle()

    def __load(self, file):
        self.file = os.path.abspath(file)
        if not os.path.exists(self.file):
            with open(self.file, 'w') as data:
                if file.endswith("proc.py"):
                    data.write("# All .py files in module directory are automatically loaded in lys Python Interpreter.\nfrom lys import *")
                else:
                    data.write("from lys import *")
        with open(self.file, 'r') as data:
            fixed = self.__fix(data.read())
            self.widget.setPlainText(fixed)

    def refreshTitle(self):
        if self.updated:
            self.setWindowTitle(os.path.basename(self.file) + " (modified, Press Ctrl+S to save)")
        else:
            self.setWindowTitle(os.path.basename(self.file))

    def keyPressed(self, event):
        if event.key() == QtCore.Qt.Key_S:
            if (event.modifiers() == QtCore.Qt.ControlModifier):
                self.save()

    def save(self):
        text = self.widget.toPlainText()
        fixed = self.__fix(text)
        with open(self.file, 'w') as data:
            data.write(fixed)
        c = self.widget.textCursor()
        p = c.position()
        self.widget.selectAll()
        self.widget.insertPlainText(fixed)
        c.movePosition(QtGui.QTextCursor.Start)
        c.movePosition(QtGui.QTextCursor.Right, n=p)
        self.widget.setTextCursor(c)
        self.updated = False
        self.refreshTitle()
        glb.shell().refresh()

    def __fix(self, text):
        try:
            options = autopep8.parse_args(['--max-line-length', '100000', '-'])
            return autopep8.fix_code(text, options)
        except Exception:
            return text

    def closeEvent(self, event):
        if not self.updated:
            PythonEditor._Remove(self)
            return
        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("Do you want to save changes?")
        msg.setWindowTitle(os.path.basename(self.file))
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)
        ok = msg.exec_()
        if ok == QtWidgets.QMessageBox.Cancel:
            event.ignore()
            return
        if ok == QtWidgets.QMessageBox.No:
            self.updated = False
        if ok == QtWidgets.QMessageBox.Yes:
            self.save()
        event.accept()
        PythonEditor._Remove(self)

    def updateText(self):
        self.updated = True
        self.refreshTitle()


def _enterName():
    txt, ok = QtWidgets.QInputDialog.getText(glb.mainWindow(), "New .py file", "Enter filename")
    if ok and len(txt) != 0:
        if not txt.endswith(".py"):
            txt = txt + ".py"
        _makeNewPy(txt)


def _prepareInit():
    if not os.path.exists(home() + "/module/__init__.py"):
        os.makedirs(home() + "/module", exist_ok=True)
        with open(home() + "/module/__init__.py", 'w') as data:
            data.write("")


def _makeNewPy(name, text=""):
    _prepareInit()
    PythonEditor(home() + "/module/" + name)


def _makeFilterTemplate():
    name, ok = QtWidgets.QInputDialog.getText(glb.mainWindow(), "New filter", "Enter new filter name", text="Filter")
    if ok:
        pyfile = home() + "/module/" + name + ".py"
        if os.path.exists(pyfile):
            QtWidgets.QMessageBox.information(glb.mainWindow(), "Caution", "File " + name + ".py already exists.")
            return
        filename = os.path.dirname(__file__) + "/templates/template_filter.py"
        with open(filename, "r") as f:
            txt = f.read().replace("FilterName", name)
        _prepareInit()
        with open(pyfile, "w") as f:
            f.write(txt)
        PythonEditor(pyfile)


def _register():
    registerFileLoader(".py", PythonEditor)
    glb.mainWindow().beforeClosed.connect(PythonEditor.CloseAllEditors)

    menu = glb.mainWindow().menuBar()
    prog = menu.addMenu("Python")

    proc = prog.addAction("Open default proc.py")
    proc.triggered.connect(lambda: _makeNewPy("proc.py"))
    proc.setShortcut("Ctrl+P")

    prog.addSeparator()

    makeNew = prog.addAction("Create new .py file")
    makeNew.triggered.connect(_enterName)
    makeNew.setShortcut("Ctrl+Shift+P")

    makeFil = prog.addAction("Create new filter from template")
    makeFil.triggered.connect(_makeFilterTemplate)

    prog.addSeparator()

    closeAll = prog.addAction("Close all editors")
    closeAll.triggered.connect(PythonEditor.CloseAllEditors)


_register()
