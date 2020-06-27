#!/usr/bin/env python
import sys
import os
from PyQt5.QtGui import *

from ExtendAnalysis.ExtendType import *
from ExtendAnalysis.BasicWidgets.pyqtGraph.ExtendCanvas import ExtendCanvas as pyqtCanvas
from ExtendAnalysis.BasicWidgets.Matplotlib.ExtendCanvas import *
from .LineSettingsGUI import *
from .ImageSettingsGUI import *
from .AxisSettingsGUI import *
from .CanvasBaseGUI import *
from .FontGUI import *
from .AxisLabelSettingsGUI import *
from .AreaSettingsGUI import *
from .AnnotationGUI import *
from .LineAnnotationGUI import *
from .InfoGUI import *


class ModifyWindow(ExtendMdiSubWindow):
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
        self._attach(parent)
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
        if isinstance(canvas, ExtendCanvas):
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
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self._size)
        self.layout.addWidget(self._margin)
        sav = QPushButton('Save', clicked=self._save)
        lod = QPushButton('Load', clicked=self._load)
        hbox = QHBoxLayout()
        hbox.addWidget(sav)
        hbox.addWidget(lod)
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
        layout = QVBoxLayout(self)
        layout.addWidget(AxisSelectionWidget(canvas))
        tab = QTabWidget()
        tab.addTab(AxisAndTickBox(canvas), 'Main')
        tab.addTab(AxisAndTickLabelBox(canvas), 'Label')
        tab.addTab(AxisFontBox(canvas), 'Font')
        sav = QPushButton('Save', clicked=self._save)
        lod = QPushButton('Load', clicked=self._load)
        hbox = QHBoxLayout()
        hbox.addWidget(sav)
        hbox.addWidget(lod)
        layout.addWidget(tab)
        layout.addLayout(hbox)

        self.setLayout(layout)

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
        layout = QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas, "line"))

        tab = QTabWidget()
        tab.addTab(ApperanceBox(canvas), 'Appearance')
        tab.addTab(OffsetAdjustBox(canvas, "line"), 'Offset')

        layout.addWidget(tab)
        self.setLayout(layout)


class _ImageTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas, "image"))
        tab = QTabWidget()
        tab.addTab(ImageColorAdjustBox(canvas), 'Color')
        tab.addTab(ImagePlaneAdjustBox(canvas), 'Slice')
        tab.addTab(OffsetAdjustBox(canvas, "image"), 'Offset')
        tab.addTab(AnimationBox(canvas), 'Animation')
        layout.addWidget(tab)
        self.setLayout(layout)


class _RGBTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas, "rgb"))
        tab = QTabWidget()
        tab.addTab(RGBColorAdjustBox(canvas), 'Color')
        tab.addTab(OffsetAdjustBox(canvas, "rgb"), 'Offset')
        layout.addWidget(tab)
        self.setLayout(layout)


class _VectorTab(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self._initlayout(canvas)

    def _initlayout(self, canvas):
        layout = QVBoxLayout()
        layout.addWidget(RightClickableSelectionBox(canvas, "vector"))
        tab = QTabWidget()
        #tab.addTab(RGBColorAdjustBox(canvas), 'Color')
        tab.addTab(OffsetAdjustBox(canvas, "vector"), 'Offset')
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
        if canvas.hasAnnotType('line'):
            tab.addTab(LineAnnotationBox(canvas), 'Line')
        if canvas.hasAnnotType('rect'):
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
