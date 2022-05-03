from PyQt5.QtWidgets import QLabel, QVBoxLayout, QGridLayout, QWidget, QTextEdit, QComboBox, QTabWidget

from lys.widgets import ColorSelection, ScientificSpinBox
from lys.decorators import avoidCircularReference

from .FontGUI import FontSelector
from .AnnotationGUI import AnnotationSelectionBox


class _TextEditBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        self.__font = FontSelector("Font")
        self.__font.fontChanged.connect(self.__fontChanged)
        self.__txt = QTextEdit()
        self.__txt.textChanged.connect(self.__txtChanged)
        self.__txt.setMinimumHeight(10)
        self.__txt.setMaximumHeight(50)

        v = QVBoxLayout()
        v.addWidget(self.__font)
        v.addWidget(self.__txt)
        self.setLayout(v)

    @avoidCircularReference
    def __loadstate(self):
        if not len(self.data) == 0:
            data = self.data[0]
            self.__txt.setText(data.getText())
            self.__font.setFont(**data.getFont())

    @avoidCircularReference
    def __txtChanged(self):
        txt = self.__txt.toPlainText()
        for d in self.data:
            d.setText(txt)

    @avoidCircularReference
    def __fontChanged(self, font):
        for d in self.data:
            d.setFont(**font)

    def setData(self, data):
        self.data = data
        self.__loadstate()


class _TextMoveBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.__initlayout()
        self.canvas = canvas

    def __initlayout(self):
        self.__modex = QComboBox()
        self.__modex.addItems(['data', 'axes'])
        self.__modex.activated.connect(self.__chgMod)

        self.__modey = QComboBox()
        self.__modey.addItems(['data', 'axes'])
        self.__modey.activated.connect(self.__chgMod)

        self.__x = ScientificSpinBox()
        self.__y = ScientificSpinBox()
        self.__x.setRange(-float('inf'), float('inf'))
        self.__y.setRange(-float('inf'), float('inf'))
        self.__x.setDecimals(5)
        self.__y.setDecimals(5)
        self.__x.valueChanged.connect(self.__changePos)
        self.__y.valueChanged.connect(self.__changePos)

        gl = QGridLayout()
        gl.addWidget(QLabel('x'), 0, 0)
        gl.addWidget(QLabel('y'), 0, 1)
        gl.addWidget(self.__x, 1, 0)
        gl.addWidget(self.__y, 1, 1)
        gl.addWidget(self.__modex, 2, 0)
        gl.addWidget(self.__modey, 2, 1)

        v = QVBoxLayout()
        v.addLayout(gl)
        v.addStretch()

        self.setLayout(v)

    def setData(self, data):
        self.data = data
        self.__loadstate()

    def __loadstate(self):
        if len(self.data) == 0:
            return
        d = self.data[0]
        t = d.getTransform()
        if isinstance(t, str):
            self.__modex.setCurrentText(t)
            self.__modey.setCurrentText(t)
        else:
            self.__modex.setCurrentText(t[0])
            self.__modey.setCurrentText(t[1])
        pos = d.getPosition()
        self.__x.setValue(pos[0])
        self.__y.setValue(pos[1])

    @avoidCircularReference
    def __chgMod(self, mod):
        mx, my = self.__modex.currentText(), self.__modey.currentText()
        for d in self.data:
            if mx == my:
                d.setTransform(mx)
            else:
                d.setTransform([mx, my])
        self.__loadstate()

    @avoidCircularReference
    def __changePos(self, value):
        p = self.__x.value(), self.__y.value()
        for d in self.data:
            d.setPosition(p)


class _AnnotationBoxAdjustBox(QWidget):
    list = ['none', 'square', 'circle', 'round', 'round4', 'larrow', 'rarrow', 'darrow', 'roundtooth', 'sawtooth']

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        self.__mode = QComboBox()
        self.__mode.addItems(self.list)
        self.__mode.activated.connect(self.__modeChanged)

        self.__fc = ColorSelection()
        self.__fc.colorChanged.connect(self.__colorChanged)
        self.__ec = ColorSelection()
        self.__ec.colorChanged.connect(self.__colorChanged)

        gl = QGridLayout()
        gl.addWidget(QLabel('Mode'), 0, 0)
        gl.addWidget(self.__mode, 0, 1)
        gl.addWidget(QLabel('Face Color'), 1, 0)
        gl.addWidget(self.__fc, 1, 1)
        gl.addWidget(QLabel('Edge Color'), 2, 0)
        gl.addWidget(self.__ec, 2, 1)

        v = QVBoxLayout()
        v.addLayout(gl)
        v.addStretch()
        self.setLayout(v)

    def __loadstate(self):
        if not len(self.data) == 0:
            d = self.data[0]
            self.__mode.setCurrentText(d.getBoxStyle())
            f, e = d.getBoxColor()
            self.__fc.setColor(f)
            self.__ec.setColor(e)

    @avoidCircularReference
    def __modeChanged(self, mode):
        for d in self.data:
            d.setBoxStyle(self.__mode.currentText())

    @avoidCircularReference
    def __colorChanged(self, color):
        for d in self.data:
            d.setBoxColor(self.__fc.getColor(), self.__ec.getColor())

    def setData(self, data):
        self.data = data
        self.__loadstate()


class TextAnnotationBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        sel = AnnotationSelectionBox(canvas)
        edit = _TextEditBox(canvas)
        move = _TextMoveBox(canvas)
        box = _AnnotationBoxAdjustBox(canvas)
        sel.selected.connect(edit.setData)
        sel.selected.connect(move.setData)
        sel.selected.connect(box.setData)

        tab = QTabWidget()
        tab.addTab(edit, 'Text')
        tab.addTab(move, 'Position')
        tab.addTab(box, 'Box')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)
