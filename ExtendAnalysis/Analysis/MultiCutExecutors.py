from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from .filter.FreeLine import *
from .filters import Filters


class AllExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axis):
        super().__init__()
        self.axis = axis

    def getAxes(self):
        return (self.axis,)

    def set(self, wave, slices, sumlist, ignore=[]):
        if self.axis in ignore:
            return sl, []
        else:
            slices[self.axis] = slice(None, None, None)
            sumlist.append(self.axis)

    def __str__(self):
        return "All executor for axis = " + str(self.axis)


class DefaultExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axis):
        super().__init__()
        self.axis = axis

    def getAxes(self):
        return (self.axis,)

    def set(self, wave, slices, sumlist, ignore=[]):
        if self.axis in ignore:
            return
        else:
            slices[self.axis] = 0

    def __str__(self):
        return "Default executor for axis = " + str(self.axis)


class RegionExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axes, range=None):
        super().__init__()
        if isinstance(axes, int):
            self.axes = (axes,)
        else:
            self.axes = tuple(axes)
        if range is not None:
            self.setRange(range)

    def getAxes(self):
        return tuple(self.axes)

    def getRange(self):
        return self.range

    def setRange(self, range):
        self.range = []
        if isinstance(range[0], list):
            for r in range:
                self.range.append(r)
        else:
            self.range.append(range)
        self.updated.emit(self.axes)

    def set(self, wave, slices, sumlist, ignore=[]):
        for i, r in zip(self.axes, self.range):
            if not i in ignore:
                p1 = min(wave.posToPoint(r[0], i), wave.posToPoint(r[1], i))
                p2 = max(wave.posToPoint(r[0], i), wave.posToPoint(r[1], i))
                if p1 < 0:
                    p1 = 0
                if p2 < 0:
                    p2 = p1
                if p1 > wave.data.shape[i] - 1:
                    p1 = wave.data.shape[i] - 1
                if p2 > wave.data.shape[i] - 1:
                    p2 = wave.data.shape[i] - 1
                slices[i] = slice(p1, p2 + 1)
                sumlist.append(i)

    def callback(self, region):
        self.setRange(region)

    def Name(self):
        return "Region"

    def __str__(self):
        return "Region executor for axis = " + str(self.axes)

    def setting(self, parentWidget=None):
        self._oldval = self.getRange()[0]
        self._dialog = RegionExecutorDialog(self.axes, self, parentWidget)
        self._dialog.rejected.connect(self._reject)
        self._dialog.accepted.connect(self._accept)

    def _accept(self):
        del self._dialog

    def _reject(self):
        del self._dialog
        self.setRange(self._oldval)


class RegionExecutorDialog(LysSubWindow):
    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, axes, parent, parentWidget):
        super().__init__("Region Executor Setting")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.flg = False
        self.__parent = parent
        self.__parent.updated.connect(self._parentUpdated)
        self._axes = axes
        self.__initlayout()
        self._attach(parentWidget)
        self.attachTo()
        self.show()

    def __initlayout(self):
        self._vals = [[ScientificSpinBox() for i in range(2)] for i in self._axes]
        for v, val in zip(self._vals, self.__parent.getRange()):
            v[0].setValue(val[0])
            v[1].setValue(val[1])
            v[0].valueChanged.connect(self._updateValues)
            v[1].valueChanged.connect(self._updateValues)
        l = QGridLayout()
        for n, i in enumerate(self._axes):
            l.addWidget(QLabel("Axis " + str(i)), n, 0)
            l.addWidget(self._vals[n][0], n, 1)
            l.addWidget(self._vals[n][1], n, 2)
        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("O K", clicked=self.accept))
        h1.addWidget(QPushButton("CANCEL", clicked=self.reject))
        h2 = QHBoxLayout()
        h2.addWidget(QPushButton("Copy", clicked=self.copy))
        h2.addWidget(QPushButton("Paste", clicked=self.paste))

        v1 = QVBoxLayout()
        v1.addLayout(l)
        v1.addLayout(h2)
        v1.addLayout(h1)
        w = QWidget()
        w.setLayout(v1)
        self.setWidget(w)
        self.adjustSize()

    def _updateValues(self):
        if self.flg:
            return
        self.flg = True
        self.__parent.setRange([[v[0].value(), v[1].value()] for v in self._vals])
        self.flg = False

    def _parentUpdated(self, val):
        if self.flg:
            return
        self.flg = True
        for v, val in zip(self._vals, self.__parent.getRange()):
            v[0].setValue(val[0])
            v[1].setValue(val[1])
        self.flg = False

    def accept(self):
        self.close()
        self.accepted.emit()

    def reject(self):
        self.close()
        self.rejected.emit()

    def copy(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(str(self.__parent.getRange()), mode=cb.Clipboard)

    def paste(self):
        cb = QApplication.clipboard()
        v = eval(cb.text(mode=cb.Clipboard))
        for v, val in zip(self._vals, v):
            v[0].setValue(val[0])
            v[1].setValue(val[1])


class PointExecutor(QObject):
    updated = pyqtSignal(tuple)

    def __init__(self, axes, pos=None):
        super().__init__()
        if isinstance(axes, int):
            self.axes = (axes,)
        else:
            self.axes = axes
        if pos is not None:
            self.setPosition(pos)
        else:
            if hasattr(axes, "__iter__"):
                self.position = [0 for a in axes]
            else:
                self.position = [0]

    def getAxes(self):
        return tuple(self.axes)

    def setPosition(self, pos):
        if isinstance(pos, float) or isinstance(pos, int):
            self.position = [pos]
        else:
            self.position = pos
        self.updated.emit(tuple(self.axes))

    def getPosition(self):
        return self.position

    def set(self, wave, slices, sumlist, ignore=[]):
        for i, p in zip(self.axes, self.position):
            if not i in ignore:
                p = wave.posToPoint(p, i)
                if p < 0:
                    p = 0
                if p > wave.data.shape[i] - 1:
                    p = wave.data.shape[i] - 1
                slices[i] = p

    def callback(self, pos):
        self.setPosition(pos)

    def Name(self):
        return "Point"

    def __str__(self):
        return "Point executor for axis " + str(self.axes)

    def setting(self, parentWidget=None):
        self._oldval = self.getPosition()
        self._dialog = PointExecutorDialog(self.axes, self, parentWidget)
        self._dialog.rejected.connect(self._reject)
        self._dialog.accepted.connect(self._accept)

    def _accept(self):
        del self._dialog

    def _reject(self):
        del self._dialog
        self.setPosition(self._oldval)


class PointExecutorDialog(LysSubWindow):
    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, axes, parent, parentWidget):
        super().__init__("Point Executor Setting")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.flg = False
        self.__parent = parent
        self.__parent.updated.connect(self._parentUpdated)
        self._axes = axes
        self.__initlayout()
        self.show()
        self._attach(parentWidget)
        self.attachTo()

    def __initlayout(self):
        self._vals = [ScientificSpinBox() for i in self._axes]
        for v, val in zip(self._vals, self.__parent.getPosition()):
            v.setValue(val)
            v.valueChanged.connect(self._updateValues)
        l = QGridLayout()
        for n, i in enumerate(self._axes):
            l.addWidget(QLabel("Axis " + str(i)), n, 0)
            l.addWidget(self._vals[n], n, 1)
        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("O K", clicked=self.accept))
        h1.addWidget(QPushButton("CANCEL", clicked=self.reject))
        h2 = QHBoxLayout()
        h2.addWidget(QPushButton("Copy", clicked=self.copy))
        h2.addWidget(QPushButton("Paste", clicked=self.paste))

        v1 = QVBoxLayout()
        v1.addLayout(l)
        v1.addLayout(h2)
        v1.addLayout(h1)
        w = QWidget()
        w.setLayout(v1)
        self.setWidget(w)
        self.adjustSize()

    def _updateValues(self):
        if self.flg:
            return
        self.flg = True
        self.__parent.setPosition([v.value() for v in self._vals])
        self.flg = False

    def _parentUpdated(self, val):
        if self.flg:
            return
        self.flg = True
        for v, val in zip(self._vals, self.__parent.getPosition()):
            v.setValue(val)
        self.flg = False

    def accept(self):
        self.close()
        self.accepted.emit()

    def reject(self):
        self.close()
        self.rejected.emit()

    def copy(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(str(self.__parent.getPosition()), mode=cb.Clipboard)

    def paste(self):
        cb = QApplication.clipboard()
        v = eval(cb.text(mode=cb.Clipboard))
        self.__parent.setPosition(v)


class FreeLineExecutor(QObject):
    _id = 10000
    updated = pyqtSignal(tuple)

    def __init__(self, axes, pos=None):
        super().__init__()
        self.axes = axes
        self.id = FreeLineExecutor._id
        FreeLineExecutor._id += 1
        self.width = 1
        if pos is not None:
            self.setPosition(pos)

    def getAxes(self):
        return list(self.axes)

    def getPosition(self):
        return self.position

    def setPosition(self, pos):
        self.position = pos
        self.updated.emit((self.id,))

    def setting(self, parentWidget=None):
        self._oldpos = self.getPosition()
        self._oldwid = self.getWidth()
        self._dialog = FreeLineExecutorDialog(self.axes, self, parentWidget)
        self._dialog.rejected.connect(self._reject)
        self._dialog.accepted.connect(self._accept)

    def _accept(self):
        del self._dialog

    def _reject(self):
        del self._dialog
        self.setPosition(self._oldpos)
        self.setWidth(self._oldwid)

    def getWidth(self):
        return self.width

    def setWidth(self, w):
        self.width = w
        self.updated.emit((self.id,))

    def execute(self, wave, axes):
        f = FreeLineFilter(axes, self.position, self.width)
        Filters([f]).execute(wave)

    def getFilter(self, axes):
        return FreeLineFilter(axes, self.position, self.width)

    def callback(self, pos):
        self.setPosition(pos)

    def Name(self):
        return "Line" + str(self.id - 10000) + " (width = " + str(self.width) + ")"

    def ID(self):
        return self.id


class FreeLineExecutorDialog(LysSubWindow):
    accepted = pyqtSignal()
    rejected = pyqtSignal()

    def __init__(self, axes, parent, parentWidget):
        super().__init__("Free Line Executor Setting")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.flg = False
        self.__parent = parent
        self.__parent.updated.connect(self._parentUpdated)
        self._axes = axes
        self.__initlayout()
        self._attach(parentWidget)
        self.attachTo()
        self.show()

    def __initlayout(self):
        self._val1 = [ScientificSpinBox() for i in self._axes]
        self._val2 = [ScientificSpinBox() for i in self._axes]
        for v, val in zip(self._val1, self.__parent.getPosition()[0]):
            v.setValue(val)
            v.valueChanged.connect(self._updateValues)
        for v, val in zip(self._val2, self.__parent.getPosition()[1]):
            v.setValue(val)
            v.valueChanged.connect(self._updateValues)
        l = QGridLayout()
        for n, i in enumerate(self._axes):
            l.addWidget(QLabel("Point " + str(n)), n, 0)
            l.addWidget(self._val1[n], n, 1)
            l.addWidget(self._val2[n], n, 2)
        self.width = QSpinBox()
        self.width.setValue(self.__parent.getWidth())
        self.width.valueChanged.connect(self._updateValues)
        l.addWidget(QLabel("Width"), n + 1, 0)
        l.addWidget(self.width, n + 1, 1)
        h1 = QHBoxLayout()
        h1.addWidget(QPushButton("O K", clicked=self.accept))
        h1.addWidget(QPushButton("CANCEL", clicked=self.reject))
        h2 = QHBoxLayout()
        h2.addWidget(QPushButton("Copy", clicked=self.copy))
        h2.addWidget(QPushButton("Paste", clicked=self.paste))

        v1 = QVBoxLayout()
        v1.addLayout(l)
        v1.addLayout(h2)
        v1.addLayout(h1)
        w = QWidget()
        w.setLayout(v1)
        self.setWidget(w)
        self.adjustSize()

    def _updateValues(self):
        if self.flg:
            return
        self.flg = True
        self.__parent.setPosition([[self._val1[0].value(), self._val1[1].value()], [self._val2[0].value(), self._val2[1].value()]])
        self.__parent.setWidth(self.width.value())
        self.flg = False

    def _parentUpdated(self, val):
        if self.flg:
            return
        self.flg = True
        for v, val in zip(self._val1, self.__parent.getPosition()[0]):
            v.setValue(val)
        for v, val in zip(self._val2, self.__parent.getPosition()[1]):
            v.setValue(val)
        self.width.setValue(self.__parent.getWidth())
        self.flg = False

    def accept(self):
        self.close()
        self.accepted.emit()

    def reject(self):
        self.close()
        self.rejected.emit()

    def copy(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(str([self.__parent.getPosition(), self.__parent.getWidth()]), mode=cb.Clipboard)

    def paste(self):
        cb = QApplication.clipboard()
        v = eval(cb.text(mode=cb.Clipboard))
        self.__parent.setPosition(v[0])
        self.__parent.setWidth(v[1])
