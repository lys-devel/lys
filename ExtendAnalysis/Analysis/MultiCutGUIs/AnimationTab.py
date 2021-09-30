import logging

from matplotlib import animation
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ExtendAnalysis import *
from ExtendAnalysis import glb
from ..MultiCut import PointExecutor


class AnimationTab(QGroupBox):
    updated = pyqtSignal(int)

    class _axisWidget(QWidget):
        def __init__(self, dim):
            super().__init__()
            self.__initlayout(dim)

        def __initlayout(self, dim):
            self.grp1 = QButtonGroup(self)
            self._btn1 = [QRadioButton(str(d)) for d in range(dim)]
            layout = QHBoxLayout()
            layout.addWidget(QLabel("Axis"))
            for i, b in enumerate(self._btn1):
                self.grp1.addButton(b)
            for i, b in enumerate(self._btn1):
                layout.addWidget(b)
            layout.addStretch()
            self.setLayout(layout)

        def getAxis(self):
            return self._btn1.index(self.grp1.checkedButton())

    def __init__(self, executor):
        super().__init__("Animation")
        self.__initlayout()
        self.__exe = executor

    def __initlayout(self):
        self.layout = QVBoxLayout()

        self.__axis = self._axisWidget(2)

        btn = QPushButton("Create animation", clicked=self.__animation)
        self.__filename = QLineEdit()
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Filename"))
        hbox1.addWidget(self.__filename)
        self.layout.addWidget(self.__axis)
        self.layout.addLayout(hbox1)
        self.layout.addLayout(self.__makeTimeOptionLayout())
        self.layout.addLayout(self.__makeScaleOptionLayout())
        self.layout.addLayout(self.__makeGeneralFuncLayout())
        self.layout.addWidget(btn)
        self.setLayout(self.layout)

    def __makeTimeOptionLayout(self):
        self.__useTime = QCheckBox('Draw time')
        self.__timeoffset = QDoubleSpinBox()
        self.__timeoffset.setRange(float('-inf'), float('inf'))
        self.__timeunit = QComboBox()
        self.__timeunit.addItems(['', 'ps', 'ns'])
        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.__useTime)
        hbox1.addWidget(self.__timeoffset)
        hbox1.addWidget(self.__timeunit)
        return hbox1

    def __makeScaleOptionLayout(self):
        self.__usescale = QCheckBox('Draw scale (disabled)')
        self.__scalesize = QDoubleSpinBox()
        self.__scalesize.setValue(1)
        self.__scalesize.setRange(0, float('inf'))
        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.__usescale)
        hbox2.addWidget(self.__scalesize)
        return hbox2

    def __makeGeneralFuncLayout(self):
        self.__useFunc = QCheckBox("Use general func f(canv, i, axis)")
        self.__funcName = QLineEdit()
        h1 = QHBoxLayout()
        h1.addWidget(self.__useFunc)
        h1.addWidget(self.__funcName)
        return h1

    def _setWave(self, wave):
        self.wave = wave
        self.layout.removeWidget(self.__axis)
        self.__axis.deleteLater()
        self.__axis = self._axisWidget(wave.data.ndim)
        self.layout.insertWidget(0, self.__axis)

    def __loadCanvasSettings(self):
        import copy
        if Graph.active() is None:
            return None, None
        c = Graph.active().canvas
        dic = {}
        for t in ['AxisSetting', 'TickSetting', 'AxisRange', 'LabelSetting', 'TickLabelSetting', 'Size', 'Margin']:
            dic[t] = c.SaveSetting(t)
        wd = c.getWaveData()
        return dic, wd

    def __animation(self):
        logging.info('[Animation] Analysis started.')
        dic, data = self.__loadCanvasSettings()
        if dic is None:
            logging.warning('[Animation] Prepare graph for reference.')
            return
        axis = self.wave.axes[self.__axis.getAxis()]
        self.__pexe = PointExecutor((self.__axis.getAxis(),))
        self.__exe.saveEnabledState()
        self.__exe.append(self.__pexe)
        params = self.__prepareOptionalParams()
        file = self.__filename.text() + ".mp4"
        if file is None:
            file = "Animation.mp4"
        self._makeAnime(file, dic, data, axis, params, self.__pexe)

    def __prepareOptionalParams(self):
        params = {}
        if self.__useTime.isChecked():
            params['time'] = {"unit": self.__timeunit.currentText(), "offset": self.__timeoffset.value()}
        if self.__usescale.isChecked():
            params['scale'] = {"size": self.__scalesize.value()}
        if self.__useFunc.isChecked():
            params['gfunc'] = self.__funcName.text()
        return params

    def _makeAnime(self, file, dic, data, axis, params, exe):
        import copy
        c = ExtendCanvas()
        for key, value in dic.items():
            c.LoadSetting(key, value)
        for d in data:
            c.Append(d.wave, appearance=copy.deepcopy(d.appearance), offset=copy.deepcopy(d.offset))
        ani = animation.FuncAnimation(c.fig, _frame, fargs=(c, axis, params, exe), frames=len(axis), interval=30, repeat=False, init_func=_init)
        ani.save(file, writer='ffmpeg')
        self.__exe.remove(self.__pexe)
        self.__exe.restoreEnabledState()
        QMessageBox.information(None, "Info", "Animation is saved to " + file, QMessageBox.Yes)
        logging.info("[Animation] saved to " + file)
        return file


def _init():
    pass


def _frame(i, c, axis, params, exe):
    exe.setPosition(axis[i])
    if "time" in params:
        _drawTime(c, axis[i], **params["time"])
    if "gfunc" in params:
        f = glb.shell().eval(params["gfunc"])
        f(c, i, axis)


def _drawTime(c, data=None, unit="", offset=0):
    c.clearAnnotations('text')
    t = '{:.10g}'.format(round(data + float(offset), 1)) + " " + unit
    c.addText(t, x=0.1, y=0.1)


def _drawScale(c, size):
    xr = c.getAxisRange('Bottom')
    yr = c.getAxisRange('Left')
    x = xr[0] + (xr[1] - xr[0]) * 0.95
    y = yr[1] + (yr[0] - yr[1]) * 0.9
    id = c.addLine(([x - size, y], [x, y]))
    c.setAnnotLineColor('white', id)
