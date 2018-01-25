#!/usr/bin/env python
import random, sys, os, math
from enum import Enum
from PyQt5.QtGui import *
from matplotlib import patches
from matplotlib.axis import XAxis,YAxis
from matplotlib.lines import Line2D
from matplotlib.image import AxesImage
from matplotlib.text import Text
from .Annotation import *
from .CanvasBase import _saveCanvas

class AnchorData(object):
    def __init__(self,obj,obj2,idn,target):
        self.obj=obj
        self.obj2=obj2
        self.id=idn
        self.target=target
class PicableCanvas(AnnotationSettingCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi)
        self.mpl_connect('pick_event',self.OnPick)
        self.__pick=False
        self._resetSelection()
    def _resetSelection(self):
        self.selLine=None
        self.selImage=None
        self.selAxis=None
        self.selAnnot=None
    def OnMouseUp(self,event):
        super().OnMouseUp(event)
        self._resetSelection()
        self.__pick=False
    def OnMouseDown(self,event):
        super().OnMouseDown(event)
        if not self.__pick:
            self._resetSelection()
        self.__pick=False
    def OnPick(self,event):
        self.__pick=True
        if isinstance(event.artist,Text):
            self.selAnnot=event.artist
        elif isinstance(event.artist,XAxis) or isinstance(event.artist,YAxis):
            self.selAxis=event.artist
        elif isinstance(event.artist,Line2D):
            if event.artist.get_zorder() < 0:
                self.selLine=event.artist
        elif isinstance(event.artist,AxesImage):
            if event.artist.get_zorder() < 0:
                self.selImage=event.artist
    def getPickedLine(self):
        return self.selLine
    def getPickedImage(self):
        return self.selImage
    def getPickedAxis(self):
        return self.selAxis
    def getPickedAnnotation(self):
        return self.selAnnot
class AnchorCanvas(PicableCanvas):
    anchorChanged=pyqtSignal()
    def __init__(self,dpi=100):
        super().__init__(dpi)
        self.anchors={}
        self.cpos=(0,0)
        self.__listener=[]
    def addAnchorChangedListener(self,listener):
        self.__listener.append(weakref.WeakMethod(listener))
    def _emitAnchorChanged(self):
        for l in self.__listener:
            if l() is not None:
                l()()
            else:
                self.__listener.remove(l)
    def OnMouseDown(self, event):
        super().OnMouseDown(event)
        if event.button == 3:
            self.cpos=(event.xdata,event.ydata)
    def __findpos_line(self,pos,line):
        xdata=line.get_xdata()
        ydata=line.get_ydata()
        n=np.argmin(np.sqrt((xdata-pos[0])**2+(ydata-pos[1])**2))
        return (xdata[n],ydata[n])
    def __findpos_image(self,pos,image):
        ext=image.get_extent()
        w=self.getWaveDataFromArtist(image)
        shape=w.wave.data.shape
        wx=(ext[1]-ext[0])/shape[0]
        wy=(ext[3]-ext[2])/shape[1]
        p=(pos[0]-ext[0],pos[1]-ext[2])
        return (ext[0]+wx*math.floor(p[0]/wx)+wx/2,ext[2]+wy*math.floor(p[1]/wy)+wy/2)
    def getAnchorInfo(self,num):
        if not num in self.anchors:
            return
        anc=self.anchors[num]
        if not anc.obj.get_visible():
            return
        x=anc.obj.get_xdata()[0]
        y=anc.obj.get_ydata()[0]
        return self.getWaveDataFromArtist(anc.target),(x,y)
    def addAnchor(self,num,pos):
        t=self.getPickedLine()
        if t is not None:
            p=self.__findpos_line(self.cpos,t)
            size=10
        else:
            t=self.getPickedImage()
            p=self.__findpos_image(self.cpos,t)
            size=3000
        id=18000+num
        if num in self.anchors:
            anc=self.anchors[num]
            anc.obj.set_data([p[0]],[p[1]])
            anc.obj.set_visible(True)
            anc.obj2.set_data([p[0]],[p[1]])
            anc.obj2.set_visible(True)
            anc.target=t
        else:
            obj, = self.axes.plot([p[0]],[p[1]])
            obj.set_linestyle('None')
            obj.set_marker('o')
            obj.set_markersize(10)
            obj.set_fillstyle('none')
            obj.set_zorder(id)

            obj2, = self.axes.plot([p[0]],[p[1]])
            obj2.set_linestyle('None')
            obj2.set_marker('+')
            obj2.set_fillstyle('none')
            obj2.set_zorder(id)
            col=self.getAnchorColor(num)
            obj.set_color(col)
            obj2.set_color(col)

            self.anchors[num]=AnchorData(obj,obj2,id,t)
            anc=self.anchors[num]
        anc.obj2.set_markersize(size)
        self._emitAnchorChanged()
        self.draw()
    def getAnchorColor(self,num):
        return ['blue','green','red'][num-1]
    def constructContextMenu(self):
        menu = super().constructContextMenu()
        m=menu.addMenu('Anchor')
        if not self.IsRangeSelected() and (self.getPickedImage() is not None or self.getPickedLine() is not None):
            m.addAction(QAction('Anchor 1',self,triggered=self.__adda))
            m.addAction(QAction('Anchor 2',self,triggered=self.__addb))
            m.addAction(QAction('Anchor 3',self,triggered=self.__addc))
        m.addAction(QAction('Remove Anchor 1',self,triggered=self.__rema))
        m.addAction(QAction('Remove Anchor 2',self,triggered=self.__remb))
        m.addAction(QAction('Remove Anchor 3',self,triggered=self.__remc))
        return menu
    def __adda(self):
        self.addAnchor(1,self.cpos)
    def __addb(self):
        self.addAnchor(2,self.cpos)
    def __addc(self):
        self.addAnchor(3,self.cpos)
    def __rem(self,num):
        if num in self.anchors:
            a=self.anchors[num]
            a.obj.set_visible(False)
            a.obj2.set_visible(False)
            self.draw()
            self._emitAnchorChanged()
    def __rema(self):
        self.__rem(1)
    def __remb(self):
        self.__rem(2)
    def __remc(self):
        self.__rem(3)

class AnchorSettingCanvas(AnchorCanvas):
    pass
