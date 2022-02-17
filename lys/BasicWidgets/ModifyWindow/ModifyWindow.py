import os
import weakref
from LysQt.QtWidgets import QWidget, QCheckBox, QTabWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFileDialog

from lys.widgets import LysSubWindow
from lys.BasicWidgets.Matplotlib.ExtendCanvas import *
from .LineSettingsGUI import *
from .ImageSettingsGUI import *
from .AxisSettingsGUI import AxisSelectionWidget, AxisAndTickBox
from .CanvasBaseGUI import DataSelectionBox, OffsetAdjustBox
from .FontGUI import *
from .AxisLabelSettingsGUI import AxisAndTickLabelBox, AxisFontBox
from .AreaSettingsGUI import MarginAdjustBox, ResizeBox
from .AnnotationGUI import *
from .LineAnnotationGUI import *
from .InfoGUI import *


class ModifyWindow(LysSubWindow):
    instance = None

    def __init__(self, canvas, parent=None, showArea=True):
        super().__init__()
        if ModifyWindow.instance is not None:
            if ModifyWindow.instance() is not None:
                ModifyWindow.instance().close()
        self._initlayout(canvas, parent, showArea)
        self.adjustSize()
        self.updateGeometry()
        self.show()
        self.canvas = canvas
        self._parent = parent
        self.attach(parent)
        self.attachTo()
        ModifyWindow.instance = weakref.ref(self)

    def _initlayout(self, canvas, win, showArea):
        self.__list = []
        self.setWindowTitle("Modify Window")
        self._tab = QTabWidget()
        if showArea:
            self._tab.addTab(_AreaTab(canvas), "Area")
            self.__list.append('Area')
        self._tab.addTab(_AxisTab(canvas), "Axis")
        if len(canvas.getLines()) != 0:
            self._tab.addTab(_LineTab(canvas), "Lines")
        if len(canvas.getImages()) != 0:
            self._tab.addTab(_ImageTab(canvas), "Images")
        if len(canvas.getRGBs()) != 0:
            self._tab.addTab(_RGBTab(canvas), "RGB")
        if len(canvas.getVectorFields()) != 0:
            self._tab.addTab(_VectorTab(canvas), "Vector")
        self._tab.addTab(_AnnotationTab(canvas), "Annot.")
        self._tab.addTab(_OtherTab(canvas), 'Other')
        self.__list.append('Axis')
        self.__list.append('Lines')
        self.__list.append('Images')
        self.__list.append('Annot.')
        self.setWidget(self._tab)

    def selectTab(self, tab):
        self._tab.setCurrentIndex(self.__list.index(tab))


class _AreaTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        self._size = ResizeBox(canvas)
        self._margin = MarginAdjustBox(canvas)

        sav = QPushButton('Save', clicked=self._save)
        lod = QPushButton('Load', clicked=self._load)
        hbox = QHBoxLayout()
        hbox.addWidget(sav)
        hbox.addWidget(lod)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self._size)
        self.layout.addWidget(self._margin)
        self.layout.addStretch()
        self.layout.addLayout(hbox)
        self.setLayout(self.layout)

    def _save(self):
        self.canvas.SaveSetting('Size')
        self.canvas.SaveSetting('Margin')

    def _load(self):
        self.canvas.LoadSetting('Size')
        self.canvas.LoadSetting('Margin')


class _AxisTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        self._axis = AxisSelectionWidget(canvas)
        self._all = QCheckBox("Apply to all axes")
        self._all.setChecked(False)

        h1 = QHBoxLayout()
        h1.addWidget(self._axis)
        h1.addWidget(self._all, alignment=Qt.AlignRight)

        ax_tick = AxisAndTickBox(self, canvas)
        ax_label = AxisAndTickLabelBox(self, canvas)
        font = AxisFontBox(self, canvas)
        self._axis.activated.connect(ax_tick.update)
        self._axis.activated.connect(ax_label.update)
        self._axis.activated.connect(font.update)

        tab = QTabWidget()
        tab.addTab(ax_tick, 'Main')
        tab.addTab(ax_label, 'Label')
        tab.addTab(font, 'Font')

        hbox = QHBoxLayout()
        hbox.addWidget(QPushButton('Save', clicked=self._save))
        hbox.addWidget(QPushButton('Load', clicked=self._load))

        layout = QVBoxLayout(self)
        layout.addLayout(h1)
        layout.addWidget(tab)
        layout.addLayout(hbox)
        self.setLayout(layout)

    def getCurrentAxis(self):
        return self._axis.currentText()

    def isApplyAll(self):
        return self._all.isChecked()

    def _save(self):
        for t in ['AxisSetting', 'TickSetting', 'AxisRange', 'LabelSetting', 'TickLabelSetting']:
            self.canvas.SaveSetting(t)

    def _load(self):
        for t in ['AxisSetting', 'TickSetting', 'AxisRange', 'LabelSetting', 'TickLabelSetting']:
            self.canvas.LoadSetting(t)


class _LineTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        app = AppearanceBox(canvas)
        off = OffsetAdjustBox()
        sel = DataSelectionBox(canvas, 1, "line")
        sel.selected.connect(app.setLines)
        sel.selected.connect(off.setData)

        tab = QTabWidget()
        tab.addTab(app, 'Appearance')
        tab.addTab(off, 'Offset')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _ImageTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        im = ImageColorAdjustBox(canvas)
        off = OffsetAdjustBox()
        sel = DataSelectionBox(canvas, 2, "image")
        sel.selected.connect(im.setImages)
        sel.selected.connect(off.setData)

        tab = QTabWidget()
        tab.addTab(im, 'Color')
        tab.addTab(off, 'Offset')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _RGBTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        rgb = RGBColorAdjustBox(canvas)
        off = OffsetAdjustBox()
        sel = DataSelectionBox(canvas, 3, "rgb")
        sel.selected.connect(rgb.setRGBs)
        sel.selected.connect(off.setData)

        tab = QTabWidget()
        tab.addTab(rgb, 'Color')
        tab.addTab(off, 'Offset')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _VectorTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        vec = VectorAdjustBox(canvas)
        off = OffsetAdjustBox()
        sel = DataSelectionBox(canvas, 2, "vector")
        sel.selected.connect(vec.setVectors)
        sel.selected.connect(off.setData)

        tab = QTabWidget()
        tab.addTab(vec, 'Vector')
        tab.addTab(off, 'Offset')

        layout = QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _AnnotationTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QVBoxLayout(self)
        tab = QTabWidget()
        tab.addTab(AnnotationBox(canvas), 'Text')
        if len(canvas.getLineAnnotations()) != 0:
            tab.addTab(LineAnnotationBox(canvas), 'Line')
        if len(canvas.getRectAnnotations()) != 0:
            tab.addTab(RectAnnotationBox(canvas), 'Rect')
        self._test = QPushButton('Legend(test)')
        self._test.clicked.connect(self.test)
        tab.addTab(self._test, 'Legend')
        layout.addWidget(tab)
        self.setLayout(layout)

    def test(self):
        a = self.canvas.axes.legend()
        self.canvas.draw()


class _OtherTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QVBoxLayout()
        layout.addWidget(SaveBox(canvas))
        layout.addWidget(RegionInfoBox(canvas))
        layout.addStretch()
        self.setLayout(layout)


class SaveBox(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        lay = QVBoxLayout()
        self._save = QPushButton('Save', clicked=self.Save)
        lay.addWidget(self._save)
        self._copy = QPushButton('Copy', clicked=self.Copy)
        lay.addWidget(self._copy)
        self.setLayout(lay)

    def Copy(self):
        self.canvas.CopyToClipboard()

    def Save(self):
        filters = ['PDF file (*.pdf)', 'EPS file (*.eps)', 'PNG file (*.png)', 'SVG file (*.svg)']
        exts = ['.pdf', '.eps', '.png', '.svg']
        f = ""
        for fil in filters:
            f += fil + ";;"
        res = QFileDialog.getSaveFileName(self, 'Open file', os.getcwd(), f, filters[0])
        if len(res[0]) == 0:
            return
        name, ext = os.path.splitext(res[0])
        savename = name
        if ext == exts[filters.index(res[1])]:
            savename += ext
        else:
            savename = name + ext + exts[filters.index(res[1])]
        self.canvas.SaveFigure(savename, exts[filters.index(res[1])].replace('.', ''))
