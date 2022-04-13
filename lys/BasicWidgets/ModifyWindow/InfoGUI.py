import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class RegionInfoBox(QGroupBox):
    def __init__(self, canvas):
        super().__init__("Region Info")
        self.canvas = canvas
        self.__initlayout()
        self.canvas.selectedRangeChanged.connect(self._changed)

    def __initlayout(self):
        layout = QVBoxLayout()
        self.label = QLabel("Information for selected region will be displayed here")
        layout.addWidget(self.label)
        self.setLayout(layout)

    def _changed(self, range):
        if range is None:
            return
        else:
            r = np.array(range).T
            txt = "Selected Range in axis units:\n"
            p1 = np.array([min(*r[0]), min(*r[1])]) #left-bottom edge of the selected region
            p2 = np.array([max(*r[0]), max(*r[1])]) #right-top edge of the selected region
            txt += "x = [{:.3f}, {:.3f}], y= [{:.3f}, {:.3f}]\n".format(p1[0],p2[0], p1[1], p2[1])
            txt += "distance = {:.3f}\n".format(np.linalg.norm(p1 - p2))
            waves = self.canvas.getWaveData()
            if len(waves) != 0:
                txt += "\n\n" + str(len(waves)) + " waves in this graph."
                txt += "Primaly wave data\n"
                w = waves[0]
            self.label.setText(txt)
