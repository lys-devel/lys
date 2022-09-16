import os
import weakref

from lys.Qt import QtCore, QtWidgets
from lys.widgets import LysSubWindow

from .CanvasBaseGUI import DataSelectionBox, OffsetAdjustBox
from .LineSettingsGUI import AppearanceBox, ErrorBox, LegendBox
from .ImageSettingsGUI import ImageColorAdjustBox, RGBColorAdjustBox, VectorAdjustBox, ContourAdjustBox

from .AxisSettingsGUI import AxisSelectionWidget, AxisAndTickBox
from .AxisLabelSettingsGUI import AxisAndTickLabelBox, AxisFontBox
from .AreaSettingsGUI import MarginAdjustBox, ResizeBox

from .TextAnnotationGUI import TextAnnotationBox
from .LineAnnotationGUI import LineAnnotationBox, InfiniteLineAnnotationBox
from .RegionAnnotationGUI import RectAnnotationBox, RegionAnnotationBox, FreeRegionAnnotationBox
from .CrossAnnotationGUI import CrossAnnotationBox
from .InfoGUI import RegionInfoBox

# temporary dictionary to save canvas settings
_saveDict = {}


class ModifyWindow(LysSubWindow):
    instance = None

    def __init__(self, canvas, parent=None, showArea=True):
        super().__init__()
        if ModifyWindow.instance is not None:
            if ModifyWindow.instance() is not None:
                ModifyWindow.instance().close()
        self._canvas = canvas
        self._initlayout(canvas, showArea)
        self.attach(parent)
        self.attachTo()
        ModifyWindow.instance = weakref.ref(self)

    def _initlayout(self, canvas, showArea):
        self.setWindowTitle("Modify Window")
        self._tab = QtWidgets.QTabWidget()
        self._tab.tabBar().setStyleSheet("QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;} ")
        self._tab.addTab(_AreaTab(canvas), "Area")
        self._tab.addTab(_AxisTab(canvas), "Axis")
        self._tab.addTab(_LineTab(canvas), "Lines")
        self._tab.addTab(_ImageTab(canvas), "Images")
        self._tab.addTab(_ContourTab(canvas), "Contours")
        self._tab.addTab(_RGBTab(canvas), "RGB")
        self._tab.addTab(_VectorTab(canvas), "Vector")
        self._tab.addTab(_AnnotationTab(canvas), "Annot.")
        self._tab.addTab(_OtherTab(canvas), 'Other')
        self.__setEnabled()
        if not showArea:
            self._tab.setTabEnabled(0, False)
            self._tab.setCurrentIndex(1)
        self.setWidget(self._tab)
        self.adjustSize()
        self.updateGeometry()
        self.show()

    def __setEnabled(self):
        self._tab.setTabEnabled(2, len(self._canvas.getLines()) != 0)
        self._tab.setTabEnabled(3, len(self._canvas.getImages()) != 0)
        self._tab.setTabEnabled(4, len(self._canvas.getContours()) != 0)
        self._tab.setTabEnabled(5, len(self._canvas.getRGBs()) != 0)
        self._tab.setTabEnabled(6, len(self._canvas.getVectorFields()) != 0)
        self._tab.setTabEnabled(7, len(self._canvas.getAnnotations()) != 0)

    def selectTab(self, tab):
        list = [self._tab.tabText(i) for i in range(self._tab.count())]
        self._tab.setCurrentIndex(list.index(tab))


class _AreaTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        self._size = ResizeBox(canvas)
        self._margin = MarginAdjustBox(canvas)

        sav = QtWidgets.QPushButton('Copy settings', clicked=self._save)
        lod = QtWidgets.QPushButton('Paste settings', clicked=self._load)
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(sav)
        hbox.addWidget(lod)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self._size)
        self.layout.addWidget(self._margin)
        self.layout.addStretch()
        self.layout.addLayout(hbox)
        self.setLayout(self.layout)

    def _save(self):
        d = {}
        for t in ['Size', 'Margin']:
            self.canvas.SaveAsDictionary(d)
            _saveDict[t] = d[t]

    def _load(self):
        d = {}
        for t in ['Size', 'Margin']:
            d[t] = _saveDict[t]
        self.canvas.LoadFromDictionary(d)


class _AxisTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        self._axis = AxisSelectionWidget(canvas)
        self._all = QtWidgets.QCheckBox("Apply to all axes")
        self._all.setChecked(False)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(self._axis)
        h1.addWidget(self._all, alignment=QtCore.Qt.AlignRight)

        ax_tick = AxisAndTickBox(self, canvas)
        ax_label = AxisAndTickLabelBox(self, canvas)
        font = AxisFontBox(self, canvas)
        self._axis.activated.connect(ax_tick.update)
        self._axis.activated.connect(ax_label.update)
        self._axis.activated.connect(font.update)

        tab = QtWidgets.QTabWidget()
        tab.addTab(ax_tick, 'Main')
        tab.addTab(ax_label, 'Label')
        tab.addTab(font, 'Font')

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QPushButton('Copy setttings', clicked=self._save))
        hbox.addWidget(QtWidgets.QPushButton('Paste settings', clicked=self._load))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(h1)
        layout.addWidget(tab)
        layout.addLayout(hbox)
        self.setLayout(layout)

    def getCurrentAxis(self):
        return self._axis.currentText()

    def isApplyAll(self):
        return self._all.isChecked()

    def _save(self):
        d = {}
        for t in ['AxisSetting', 'TickSetting', 'AxisRange', 'LabelSetting', 'TickLabelSetting']:
            self.canvas.SaveAsDictionary(d)
            _saveDict[t] = d[t]

    def _load(self):
        d = {}
        for t in ['AxisSetting', 'TickSetting', 'AxisRange', 'LabelSetting', 'TickLabelSetting']:
            d[t] = _saveDict[t]
        self.canvas.LoadFromDictionary(d)


class _LineTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        app = AppearanceBox(canvas)
        err = ErrorBox(canvas)
        off = OffsetAdjustBox()
        leg = LegendBox(canvas)
        sel = DataSelectionBox(canvas, 1, "line")
        sel.selected.connect(app.setLines)
        sel.selected.connect(err.setData)
        sel.selected.connect(off.setData)
        sel.selected.connect(leg.setData)

        tab = QtWidgets.QTabWidget()
        tab.addTab(app, 'Appearance')
        tab.addTab(err, 'Errorbar')
        tab.addTab(off, 'Offset')
        tab.addTab(leg, 'Legend')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _ImageTab(QtWidgets.QWidget):
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

        tab = QtWidgets.QTabWidget()
        tab.addTab(im, 'Color')
        tab.addTab(off, 'Offset')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _ContourTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        cn = ContourAdjustBox(canvas)
        off = OffsetAdjustBox()
        sel = DataSelectionBox(canvas, 2, "contour")
        sel.selected.connect(cn.setContours)
        sel.selected.connect(off.setData)

        tab = QtWidgets.QTabWidget()
        tab.addTab(cn, 'Appearance')
        tab.addTab(off, 'Offset')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _RGBTab(QtWidgets.QWidget):
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

        tab = QtWidgets.QTabWidget()
        tab.addTab(rgb, 'Color')
        tab.addTab(off, 'Offset')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _VectorTab(QtWidgets.QWidget):
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

        tab = QtWidgets.QTabWidget()
        tab.addTab(vec, 'Vector')
        tab.addTab(off, 'Offset')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(sel)
        layout.addWidget(tab)
        self.setLayout(layout)


class _AnnotationTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QtWidgets.QVBoxLayout(self)
        tab = QtWidgets.QTabWidget()
        if len(canvas.getTextAnnotations()) != 0:
            tab.addTab(TextAnnotationBox(canvas), 'Text')
        if len(canvas.getLineAnnotations()) != 0:
            tab.addTab(LineAnnotationBox(canvas), 'Line')
        if len(canvas.getInfiniteLineAnnotations()) != 0:
            tab.addTab(InfiniteLineAnnotationBox(canvas), 'V/H Line')
        if len(canvas.getRectAnnotations()) != 0:
            tab.addTab(RectAnnotationBox(canvas), 'Rect')
        if len(canvas.getRegionAnnotations()) != 0:
            tab.addTab(RegionAnnotationBox(canvas), 'Region')
        if len(canvas.getFreeRegionAnnotations()) != 0:
            tab.addTab(FreeRegionAnnotationBox(canvas), 'Free')
        if len(canvas.getCrossAnnotations()) != 0:
            tab.addTab(CrossAnnotationBox(canvas), 'Cross')
        self._test = QtWidgets.QPushButton('Legend(test)')
        self._test.clicked.connect(self.test)
        layout.addWidget(tab)
        self.setLayout(layout)

    def test(self):
        self.canvas.axes.legend()
        self.canvas.draw()


class _OtherTab(QtWidgets.QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(SaveBox(canvas))
        layout.addWidget(RegionInfoBox(canvas))
        layout.addStretch()
        self.setLayout(layout)


class SaveBox(QtWidgets.QGroupBox):
    def __init__(self, canvas):
        super().__init__("Export")
        self.canvas = canvas
        self.__initlayout()

    def __initlayout(self):
        lay = QtWidgets.QVBoxLayout()
        self._save = QtWidgets.QPushButton('Export image', clicked=self.Save)
        lay.addWidget(self._save)
        self._copy = QtWidgets.QPushButton('Copy to clipboard', clicked=self.Copy)
        lay.addWidget(self._copy)
        self.setLayout(lay)

    def Copy(self):
        self.canvas.copyToClipboard()

    def Save(self):
        filters = ['PDF file (*.pdf)', 'EPS file (*.eps)', 'PNG file (*.png)', 'SVG file (*.svg)']
        exts = ['.pdf', '.eps', '.png', '.svg']
        f = ""
        for fil in filters:
            f += fil + ";;"
        res = QtWidgets.QFileDialog.getSaveFileName(self, 'Open file', os.getcwd(), f, filters[0])
        if len(res[0]) == 0:
            return
        name, ext = os.path.splitext(res[0])
        savename = name
        if ext == exts[filters.index(res[1])]:
            savename += ext
        else:
            savename = name + ext + exts[filters.index(res[1])]
        self.canvas.saveFigure(savename, exts[filters.index(res[1])].replace('.', ''))
