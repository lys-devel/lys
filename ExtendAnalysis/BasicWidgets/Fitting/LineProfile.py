from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ExtendAnalysis import *
import numpy as np
import os


class LineProfileWidget(QWidget):
    def __init__(self, wavelist, canvas, path=None):
        super().__init__()
        self.__canvas = canvas
        self._waves = wavelist
        self.__initlayout(wavelist, path)
        self.adjustSize()
        self.updateGeometry()
        self.show()

    def __initlayout(self, wavelist, path):
        vbox = QVBoxLayout()

        self._data = QComboBox()
        for w in wavelist:
            self._data.addItem(w.Name())

        self._grf = QCheckBox('Show graph')
        self._save = QCheckBox('Save to')
        self._path = QLineEdit()
        if path is not None:
            self._path.setText(path)
        else:
            p, ext = os.path.splitext(wavelist[0].Name())
            self._path.setText('Analysis/' + p)

        hbox5 = QHBoxLayout()
        hbox5.addWidget(self._grf)
        hbox5.addWidget(self._save)
        hbox5.addWidget(self._path)

        self._axis = QComboBox()
        self._axis.addItem('Horizontal')
        self._axis.addItem('Vertical')
        self._axis.addItem('Along lines')

        self._wid = QSpinBox()
        self._wid.setMinimum(1)
        self._wid.setMaximum(1000000)

        self._delta = QSpinBox()
        self._delta.setMinimum(1)
        self._delta.setMaximum(1000000)

        hbox4 = QGridLayout()
        hbox4.addWidget(QLabel('Axis'), 0, 0)
        hbox4.addWidget(self._axis, 1, 0)
        hbox4.addWidget(QLabel('Width'), 0, 1)
        hbox4.addWidget(self._wid, 1, 1)
        hbox4.addWidget(QLabel('Delta'), 0, 2)
        hbox4.addWidget(self._delta, 1, 2)

        self._cx = QSpinBox()
        self._cx.setMinimum(0)
        self._cx.setMaximum(1000000)
        self._cy = QSpinBox()
        self._cy.setMinimum(0)
        self._cy.setMaximum(1000000)

        hbox2 = QGridLayout()
        hbox2.addWidget(QLabel('Center'), 0, 0)
        hbox2.addWidget(QLabel('x'), 0, 1)
        hbox2.addWidget(QLabel('y'), 0, 2)
        self._loadAnchor = QPushButton('Load Anchor1', clicked=self.__loadAnch)
        hbox2.addWidget(self._loadAnchor)
        hbox2.addWidget(self._cx, 1, 1)
        hbox2.addWidget(self._cy, 1, 2)

        self._r1 = QSpinBox()
        self._r1.setMinimum(0)
        self._r1.setMaximum(1000000)
        self._r2 = QSpinBox()
        self._r2.setMinimum(0)
        self._r2.setMaximum(1000000)

        hbox3 = QGridLayout()
        hbox3.addWidget(QLabel('Range'), 0, 0)
        hbox3.addWidget(QLabel('from'), 0, 1)
        hbox3.addWidget(QLabel('to'), 0, 2)
        self._loadRange = QPushButton('Load Range', clicked=self.__loadRan)
        hbox3.addWidget(self._loadRange)
        hbox3.addWidget(self._r1, 1, 1)
        hbox3.addWidget(self._r2, 1, 2)

        self._cut = QPushButton('Cut', clicked=self.__exe)

        vbox.addWidget(self._data)
        vbox.addLayout(hbox5)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(self._cut)
        self.setLayout(vbox)

    def __loadAnch(self):
        info = self.__canvas.getAnchorInfo(1)
        if info is not None:
            w = info[0].wave
            r = w.posToPoint(info[1])
            self._cx.setValue(r[0])
            self._cy.setValue(r[1])
        else:
            self._cx.setValue(0)
            self._cy.setValue(0)

    def _selectedWave(self):
        n = self._data.currentIndex()
        return self._waves[n]

    def __loadRan(self):
        info = self.__canvas.SelectedRange()
        w = self._selectedWave()
        if info is not None:
            fr = w.posToPoint(info[0])
            to = w.posToPoint(info[1])
            if self._axis.currentText() == 'Horizontal':
                self._r1.setValue(fr[1])
                self._r2.setValue(to[1])
            if self._axis.currentText() == 'Vertical':
                self._r1.setValue(fr[0])
                self._r2.setValue(to[0])
        else:
            self._r1.setValue(0)
            if self._r2.value() == 0:
                if self._axis.currentText() == 'Horizontal':
                    self._r2.setValue(len(w.y) - 1)
                if self._axis.currentText() == 'Vertical':
                    self._r2.setValue(len(w.x) - 1)
            else:
                self._r2.setValue(0)

    def __exe(self):
        if self._axis.currentText() in ["Horizontal", "Vertical"]:
            ws, list, xdata = self.__cutline()
        else:
            ws, list, xdata = self.__alongline()
        if self._save.isChecked():
            p = os.getcwd() + '/' + self._path.text()
            xd = Wave()
            xd.data = xdata
            xd.Save(p + "/xdata.npz")
            for w, l in zip(ws, list):
                w.Save(p + "/data" + str(l) + ".npz")
        if self._grf.isChecked():
            g = Graph()
            for w in ws:
                g.Append(w)

    def __cutline(self):
        w = self._selectedWave()
        ran = [self._r1.value(), self._r2.value()]
        if self._axis.currentText() == "Horizontal":
            c = self._cy.value()
            xx = w.y
            rr = w.x
            axis = 'x'
        else:
            c = self._cx.value()
            xx = w.x
            rr = w.y
            axis = 'y'
        wid = self._wid.value()
        d = self._delta.value()

        list = []
        if ran[0] == 0 and ran[1] == 0:
            list.append(c)
        else:
            for i in range(len(xx)):
                if (c - i) % d == 0 and ran[0] <= i and ran[1] >= i:
                    list.append(i)

        res = []
        xdata = []
        for l in list:
            if axis == 'x':
                res.append(w.slice((0, l), (len(rr) - 1, l), axis, width=wid))
                xdata.append(w.pointToPos([l, 0])[0])
            if axis == 'y':
                res.append(w.slice((l, 0), (l, len(rr) - 1), axis, width=wid))
                xdata.append(w.pointToPos([0, l])[1])
        return res, list, xdata

    def __alongline(self):
        pass
