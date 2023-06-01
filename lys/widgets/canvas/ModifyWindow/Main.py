import os
import weakref

from lys.Qt import QtCore, QtWidgets
from lys.errors import suppressLysWarnings
from lys.widgets import LysSubWindow

from .CanvasBaseGUI import DataSelectionBox, OffsetAdjustBox
from .LineSettingsGUI import AppearanceBox, ErrorBox, LegendBox
from .ImageSettingsGUI import ImageColorAdjustBox, ColorbarAdjustBox, RGBColorAdjustBox, RGBMapAdjustBox, VectorAdjustBox, ContourAdjustBox

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

    def __init__(self, canvas, parent=None):
        super().__init__()
        if ModifyWindow.instance is not None:
            if ModifyWindow.instance() is not None:
                ModifyWindow.instance().close()
        self._initlayout(canvas)
        self.attach(canvas.getParent())
        self.attachTo()
        ModifyWindow.instance = weakref.ref(self)

    def _initlayout(self, canvas):
        self.setWindowTitle("Modify Window")
        self._tab = ModifyWidget(canvas)
        self.setWidget(self._tab)
        self.adjustSize()
        self.updateGeometry()
        self.show()

    def selectTab(self, tab):
        return self._tab.selectTab(tab)


class ModifyWidget(QtWidgets.QTabWidget):
    def __init__(self, canvas):
        super().__init__()
        self._initlayout(canvas)
        self.__setEnabled(canvas)

    @suppressLysWarnings
    def _initlayout(self, canvas):
        self.tabBar().setStyleSheet("QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;} ")
        self.addTab(_AreaTab(canvas), "Area")
        self.addTab(_AxisTab(canvas), "Axis")
        self.addTab(_LineTab(canvas), "Lines")
        self.addTab(_ImageTab(canvas), "Images")
        self.addTab(_ContourTab(canvas), "Contours")
        self.addTab(_RGBTab(canvas), "RGB")
        self.addTab(_VectorTab(canvas), "Vector")
        self.addTab(_AnnotationTab(canvas), "Annot.")
        self.addTab(_OtherTab(canvas), 'Other')

    def __setEnabled(self, canvas):
        from lys.widgets import Graph
        if not isinstance(canvas.getParent(), Graph):
            self.setTabEnabled(0, False)
            self.setCurrentIndex(1)
        self.setTabEnabled(2, len(canvas.getLines()) != 0)
        self.setTabEnabled(3, len(canvas.getImages()) != 0)
        self.setTabEnabled(4, len(canvas.getContours()) != 0)
        self.setTabEnabled(5, len(canvas.getRGBs()) != 0)
        self.setTabEnabled(6, len(canvas.getVectorFields()) != 0)
        self.setTabEnabled(7, len(canvas.getAnnotations()) != 0)

    def selectTab(self, tab):
        list = [self.tabText(i) for i in range(self.count())]
        self.setCurrentIndex(list.index(tab))


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
        col = ColorbarAdjustBox(canvas)
        sel = DataSelectionBox(canvas, 2, "image")
        sel.selected.connect(im.setImages)
        sel.selected.connect(off.setData)
        sel.selected.connect(col.setData)

        tab = QtWidgets.QTabWidget()
        tab.addTab(im, 'Color')
        tab.addTab(off, 'Offset')
        tab.addTab(col, 'Colorbar')

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
        map = RGBMapAdjustBox(canvas)
        sel = DataSelectionBox(canvas, 3, "rgb")
        sel.selected.connect(rgb.setRGBs)
        sel.selected.connect(off.setData)
        sel.selected.connect(map.setRGBs)

        tab = QtWidgets.QTabWidget()
        tab.addTab(rgb, 'Color')
        tab.addTab(off, 'Offset')
        tab.addTab(map, 'Colormap')

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
        self._save = QtWidgets.QPushButton('Export image', clicked=self.Save)
        self._copy = QtWidgets.QPushButton('Copy to clipboard', clicked=self.Copy)

        self._dpi = QtWidgets.QSpinBox()
        self._dpi.setRange(1, 10000)
        self._dpi.setValue(100)

        h1 = QtWidgets.QHBoxLayout()
        h1.addWidget(QtWidgets.QLabel("dpi:"))
        h1.addWidget(self._dpi)

        lay = QtWidgets.QVBoxLayout()
        lay.addWidget(self._save)
        lay.addWidget(self._copy)
        lay.addLayout(h1)
        self.setLayout(lay)

    def Copy(self):
        self.canvas.copyToClipboard(dpi=self._dpi.value())

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
        self.canvas.saveFigure(savename, exts[filters.index(res[1])].replace('.', ''), dpi=self._dpi.value())
