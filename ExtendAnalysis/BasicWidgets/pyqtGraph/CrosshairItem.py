from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph import GraphicsObject, InfiniteLine

class CrosshairItem(GraphicsObject):
    sigRegionChangeFinished = pyqtSignal(object)
    sigRegionChanged = pyqtSignal(object)

    def __init__(self, values=(0, 1), pen=None):
        GraphicsObject.__init__(self)
        self.bounds = QRectF()
        self.blockLineSignal = False
        self.moving = False
        self.mouseHovering = False
        self._bounds = None
        self.lines = [InfiniteLine(angle=0), InfiniteLine(angle=90)]
        self.lines[0].scale(1, -1)
        self.lines[1].scale(1, -1)
        for l in self.lines:
            l.setParentItem(self)
            l.sigPositionChangeFinished.connect(self.lineMoveFinished)
        self.lines[0].sigPositionChanged.connect(lambda: self.lineMoved(0))
        self.lines[1].sigPositionChanged.connect(lambda: self.lineMoved(1))
        self.setMovable(True)
    def getPosition(self):
        r = (self.lines[0].value(), self.lines[1].value())
        return r
    def setPosition(self, pos):
        if self.lines[0].value() == pos[0] and self.lines[1].value() == pos[1]:
            return
        self.blockLineSignal = True
        self.lines[0].setValue(pos[0])
        self.blockLineSignal = False
        self.lines[1].setValue(pos[1])
        #self.blockLineSignal = False
        self.lineMoved(0)
        self.lineMoved(1)
        self.lineMoveFinished()
    def setMovable(self, m):
        for l in self.lines:
            l.setMovable(m)
        self.movable = m
        self.setAcceptHoverEvents(m)
    def boundingRect(self):
        br = self.viewRect()  # bounds of containing ViewBox mapped to local coords.
        br = self.lines[0].boundingRect() & self.lines[1].boundingRect()
        br = br.normalized()

        if self._bounds != br:
            self._bounds = br
            self.prepareGeometryChange()

        return br
    def paint(self, p, *args):
        #p.drawEllipse(self.boundCircle())
        pass
    def lineMoved(self, i):
        if self.blockLineSignal:
            return
        self.prepareGeometryChange()
        self.sigRegionChanged.emit(self)

    def lineMoveFinished(self):
        self.sigRegionChangeFinished.emit(self)
    """
    def hoverEvent(self, ev):
        if self.movable and (not ev.isExit()) and ev.acceptDrags(Qt.LeftButton):
            self.setMouseHover(True)
        else:
            self.setMouseHover(False)

    def setMouseHover(self, hover):
        ## Inform the item that the mouse is(not) hovering over it
        if self.mouseHovering == hover:
            return
        print(hover)
        self.mouseHovering = hover
        if hover:
            self.currentBrush = self.hoverBrush
        else:
            self.currentBrush = self.brush
        self.update()
    def mouseDragEvent(self, ev):
        print(ev)
        if not self.movable or int(ev.button() & QtCore.Qt.LeftButton) == 0:
            return
        ev.accept()

        if ev.isStart():
            bdp = ev.buttonDownPos()
            print(bdp)
            return
            self.cursorOffsets = [l.pos() - bdp for l in self.lines]
            self.startPositions = [l.pos() for l in self.lines]
            self.moving = True

        if not self.moving:
            return

        self.lines[0].blockSignals(True)  # only want to update once
        for i, l in enumerate(self.lines):
            l.setPos(self.cursorOffsets[i] + ev.pos())
        self.lines[0].blockSignals(False)
        self.prepareGeometryChange()

        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)

    def mouseClickEvent(self, ev):
        if self.moving and ev.button() == QtCore.Qt.RightButton:
            ev.accept()
            for i, l in enumerate(self.lines):
                l.setPos(self.startPositions[i])
            self.moving = False
            self.sigRegionChanged.emit(self)
            self.sigRegionChangeFinished.emit(self)

    """
