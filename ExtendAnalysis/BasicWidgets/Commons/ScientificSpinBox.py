
import math
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ScientificSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setRange(-np.inf, np.inf)
        self.setDecimals(16)
        self.setAccelerated(True)

    def textFromValue(self, value):
        return "{:.6g}".format(value)

    def valueFromText(self, text):
        return float(text)

    def validate(self, text, pos):
        try:
            float(text)
        except:
            try:
                float(text.replace("e", "").replace("-", ""))
            except:
                return (QValidator.Invalid, text, pos)
            else:
                return (QValidator.Intermediate, text, pos)
        else:
            return (QValidator.Acceptable, text, pos)

    def stepBy(self, steps):
        v = self.value()
        if v == 0:
            n = 1
        else:
            l = np.log10(abs(v))
            p = math.floor(l)
            if math.floor(abs(v) / (10**p)) == 1:  # and np.sign(steps) != np.sign(v):
                p = p - 1
            n = 10 ** p
        self.setValue(v + steps * n)
