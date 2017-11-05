#!/usr/bin/env python
import random, weakref, sys, os
import numpy as np
from enum import Enum
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib as mpl
import matplotlib.font_manager as fm
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker

from ExtendAnalysis import *
from .ColorWidgets import *
from .ImageSettings import *

class RangeSelectableCanvas(ImageSettingCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi)
        self.rect = Rectangle((0,0), 0, 0, color='orange', alpha=0.5)
        patch=self.axes.add_patch(self.rect)
        patch.set_zorder(20000)
        self.Selection=False

        self.mpl_connect('button_press_event',self.OnMouseDown)
        self.mpl_connect('button_release_event', self.OnMouseUp)
        self.mpl_connect('motion_notify_event', self.OnMouseMove)
    def __GlobalToAxis(self, x, y, ax):
        loc=self.__GlobalToRatio(x,y,ax)
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()
        x_ax=xlim[0]+(xlim[1]-xlim[0])*loc[0]
        y_ax=ylim[0]+(ylim[1]-ylim[0])*loc[1]
        return [x_ax,y_ax]
    def __GlobalToRatio(self, x, y, ax):
        ran=ax.get_position()
        x_loc=(x - ran.x0 * self.width())/((ran.x1 - ran.x0)*self.width())
        y_loc=(y - ran.y0 * self.height())/((ran.y1 - ran.y0)*self.height())
        return [x_loc,y_loc]
    def OnMouseDown(self, event):
        if event.button == 1:
            self.Selection=True
            self.__saved = self.copy_from_bbox(self.axes.bbox)
            self.rect_pos_start=[event.x,event.y]
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            self.rect.set_xy(ax)
    def OnMouseUp(self, event):
        if self.Selection == True and event.button == 1:
            self.rect_pos_end=[event.x,event.y]
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            self.rect.set_width(ax[0]-self.rect.xy[0])
            self.rect.set_height(ax[1]-self.rect.xy[1])
            self.draw()
            self.Selection=False
    def OnMouseMove(self, event):
        if self.Selection == True:
            ax=self.__GlobalToAxis(event.x,event.y,self.axes)
            self.rect.set_width(ax[0]-self.rect.xy[0])
            self.rect.set_height(ax[1]-self.rect.xy[1])
            self.restore_region(self.__saved)
            self.axes.draw_artist(self.rect)
            self.blit(self.axes.bbox)
            self.flush_events()
    def IsRangeSelected(self):
        return not self.rect.get_width()==0
    def ClearSelectedRange(self):
        self.rect.set_width(0)
        self.rect.set_height(0)
    def SelectedRange(self):
        start=self.__GlobalToAxis(self.rect_pos_start[0],self.rect_pos_start[1],self.axes)
        end=self.__GlobalToAxis(self.rect_pos_end[0],self.rect_pos_end[1],self.axes)
        return (start,end)

class AxisSelectableCanvas(RangeSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.axis_selected='Left'
        self.__listener=[]
    def setSelectedAxis(self, axis):
        self.axis_selected=axis
        self._emitAxisSelected()
    def getSelectedAxis(self):
        return self.axis_selected
    def addAxisSelectedListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emitAxisSelected(self):
        for l in self.__listener:
            if l() is not None:
                l().OnAxisSelected(self.axis_selected)
            else:
                self.__listener.remove(l)
    def getAxes(self,axis):
        ax=axis
        if ax in ['Left','Bottom']:
            return self.axes
        if ax=='Top':
            if self.axes_ty is not None:
                return self.axes_ty
            else:
                return self.axes_txy
        if ax=='Right':
            if self.axes_tx is not None:
                return self.axes_tx
            else:
                return self.axes_txy
    def axisIsValid(self,axis):
        if axis in ['Left','Bottom']:
            return True
        if axis in ['Top']:
            return self.axes_ty is not None or self.axes_txy is not None
        if axis in ['Right']:
            return self.axes_tx is not None or self.axes_txy is not None
    def axisList(self):
        res=['Left']
        if self.axisIsValid('Right'):
            res.append('Right')
        res.append('Bottom')
        if self.axisIsValid('Top'):
            res.append('Top')
        return res
class AxisSelectionWidget(QComboBox):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.canvas.addAxisChangeListener(self)
        self.canvas.addAxisSelectedListener(self)
        self.flg=False
        self.__setItem()
        self.activated.connect(self._activated)
    def __setItem(self):
        self.addItem('Left')
        if self.canvas.axisIsValid('Right'):
            self.addItem('Right')
        self.addItem('Bottom')
        if self.canvas.axisIsValid('Top'):
            self.addItem('Top')
    def _activated(self):
        self.flg=True
        self.canvas.setSelectedAxis(self.currentText())
        self.flg=False
    def OnAxisChanged(self,axis):
        self.clear()
        self.__setItem()
    def OnAxisSelected(self,axis):
        if self.flg:
            return
        else:
            Items = [self.itemText(i) for i in range(self.count())]
            self.setCurrentIndex(Items.index(axis))

class AxisRangeAdjustableCanvas(AxisSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__listener=[]
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        list=['Left','Right','Top','Bottom']
        for l in list:
            if self.axisIsValid(l):
                dic[l+"_auto"]=self.isAutoScaled(l)
                dic[l]=self.getAxisRange(l)
            else:
                dic[l+"_auto"]=None
                dic[l]=None
        dictionary['AxisRange']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'AxisRange' in dictionary:
            dic=dictionary['AxisRange']
            for l in ['Left','Right','Top','Bottom']:
                auto=dic[l+"_auto"]
                if auto is not None:
                    if auto:
                        self.setAutoScaleAxis(l)
                    else:
                        self.setAxisRange(dic[l],l)

    def setAxisRange(self,range,axis):
        ax=axis
        axes=self.getAxes(axis)
        if axes is None:
            return
        if ax in ['Left','Right']:
            axes.set_ylim(range)
        if ax in ['Top','Bottom']:
            axes.set_xlim(range)
        self._emitAxisRangeChanged()
        self.draw()
    def getAxisRange(self,axis):
        ax=axis
        axes=self.getAxes(axis)
        if axes is None:
            return
        if ax in ['Left','Right']:
            return axes.get_ylim()
        if ax in ['Top','Bottom']:
            return axes.get_xlim()

    def addAxisRangeChangeListener(self,listener):
        self.__listener.append(weakref.WeakMethod(listener))
    def _emitAxisRangeChanged(self):
        for l in self.__listener:
            if l() is not None:
                l()()
            else:
                self.__listener.remove(l)

    def setAutoScaleAxis(self,axis):
        ax=axis
        axes=self.getAxes(axis=ax)
        if axes is None:
            return
        if ax in ['Left','Right']:
            axes.autoscale(axis='y')
        if ax in ['Top','Bottom']:
            axes.autoscale(axis='x')
        self._emitAxisRangeChanged()
        self.draw()
    def isAutoScaled(self,axis):
        ax=axis
        axes=self.getAxes(axis=ax)
        if axes is None:
            return
        if ax in ['Left','Right']:
            return axes.get_autoscaley_on()
        if ax in ['Top','Bottom']:
            return axes.get_autoscalex_on()
class AxisRangeRightClickCanvas(AxisRangeAdjustableCanvas):
    def __GlobalToAxis(self, x, y, ax):
        loc=self.__GlobalToRatio(x,y,ax)
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()
        x_ax=xlim[0]+(xlim[1]-xlim[0])*loc[0]
        y_ax=ylim[0]+(ylim[1]-ylim[0])*loc[1]
        return [x_ax,y_ax]
    def __GlobalToRatio(self, x, y, ax):
        ran=ax.get_position()
        x_loc=(x - ran.x0 * self.width())/((ran.x1 - ran.x0)*self.width())
        y_loc=(y - ran.y0 * self.height())/((ran.y1 - ran.y0)*self.height())
        return [x_loc,y_loc]
    def __ExpandAndShrink(self,mode,axis):
        if not self.axisIsValid(axis):
            return
        ax=self.getAxes(axis)
        pos=self.__GlobalToAxis(self.rect_pos_start[0],self.rect_pos_start[1],ax)
        pos2=self.__GlobalToAxis(self.rect_pos_end[0],self.rect_pos_end[1],ax)
        width=pos2[0]-pos[0]
        height=pos2[1]-pos[1]
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()

        if axis in ['Bottom', 'Top']:
            if mode in ['Expand','Horizontal Expand']:
                minVal=min(pos[0], pos[0]+width)
                maxVal=max(pos[0], pos[0]+width)
                self.setAxisRange([minVal,maxVal],axis)
            if mode in ['Shrink','Horizontal Shrink']:
                ratio=abs((xlim[1]-xlim[0])/width)
                a=min(pos[0], pos[0]+width)
                b=max(pos[0], pos[0]+width)
                minVal=xlim[0]-ratio*(a-xlim[0])
                maxVal=xlim[1]+ratio*(xlim[1]-b)
                self.setAxisRange([minVal,maxVal],axis)
        else:
            if mode in ['Vertical Expand', 'Expand']:
                minVal=min(pos[1], pos[1]+height)
                maxVal=max(pos[1], pos[1]+height)
                self.setAxisRange([minVal,maxVal],axis)
            if mode in ['Shrink','Vertical Shrink']:
                ratio=abs((ylim[1]-ylim[0])/height)
                a=min(pos[1], pos[1]+height)
                b=max(pos[1], pos[1]+height)
                minVal=ylim[0]-ratio*(a-ylim[0])
                maxVal=ylim[1]+ratio*(ylim[1]-b)
                self.setAxisRange([minVal,maxVal],axis)
    def constructContextMenu(self):
        menu = super().constructContextMenu()
        menu.addAction(QAction('Auto scale axes',self,triggered=self.__auto))
        if self.IsRangeSelected():
            m=menu.addMenu('Expand and Shrink')
            m.addAction(QAction('Expand',self,triggered=self.__expand))
            m.addAction(QAction('Horizontal Expand',self,triggered=self.__expandh))
            m.addAction(QAction('Vertical Expand',self,triggered=self.__expandv))
            m.addAction(QAction('Shrink',self,triggered=self.__shrink))
            m.addAction(QAction('Horizontal Shrink',self,triggered=self.__shrinkh))
            m.addAction(QAction('Vertical Shrink',self,triggered=self.__shrinkv))
        return menu
    def __expand(self):
        self.__exec('Expand')
    def __expandh(self):
        self.__exec('Horizontal Expand')
    def __expandv(self):
        self.__exec('Vertical Expand')
    def __shrink(self):
        self.__exec('Shrink')
    def __shrinkh(self):
        self.__exec('Horizontal Shrink')
    def __shrinkv(self):
        self.__exec('Vertical Shrink')
    def __exec(self,text):
        for axis in ['Left','Right','Top','Bottom']:
            self.__ExpandAndShrink(text,axis)
        self.ClearSelectedRange()
        self.draw()
    def __auto(self):
        for axis in ['Left','Right','Bottom','Top']:
            self.setAutoScaleAxis(axis)
        self.ClearSelectedRange()
        self.draw()

class AxisRangeAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__('Axis Range')
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate(canvas)
        self.canvas.addAxisSelectedListener(self)
        self.canvas.addAxisRangeChangeListener(self.OnAxisRangeChanged)
    def __initlayout(self):
        layout=QVBoxLayout()

        self.__combo=QComboBox()
        self.__combo.addItem('Auto')
        self.__combo.addItem('Manual')
        self.__combo.activated.connect(self.__OnModeChanged)

        layout_h1=QHBoxLayout()
        self.__spin1=QDoubleSpinBox()
        self.__spin1.setDecimals(5)
        self.__spin1.valueChanged.connect(self.__spinChanged)
        self.__spin1.setRange(-10000,10000)

        layout_h1.addWidget(QLabel('Min'))
        layout_h1.addWidget(self.__spin1)

        layout_h2=QHBoxLayout()
        self.__spin2=QDoubleSpinBox()
        self.__spin2.setDecimals(5)
        self.__spin2.valueChanged.connect(self.__spinChanged)
        self.__spin2.setRange(-10000,10000)
        layout_h2.addWidget(QLabel('Max'))
        layout_h2.addWidget(self.__spin2)

        layout.addWidget(self.__combo)
        layout.addLayout(layout_h1)
        layout.addLayout(layout_h2)
        self.setLayout(layout)
    def __loadstate(self,canvas):
        self.__loadflg=True
        axis=canvas.getSelectedAxis()
        mod=canvas.isAutoScaled(axis)
        if mod:
            self.__combo.setCurrentIndex(0)
        else:
            self.__combo.setCurrentIndex(1)
        self.__spin1.setReadOnly(mod)
        self.__spin2.setReadOnly(mod)
        ran=canvas.getAxisRange(axis)
        self.__spin1.setValue(ran[0])
        self.__spin2.setValue(ran[1])
        self.__loadflg=False
    def OnAxisRangeChanged(self):
        self.__loadstate(self.canvas)
    def OnAxisSelected(self,axis):
        self.__loadstate(self.canvas)
    def __OnModeChanged(self):
        if self.__loadflg:
            return
        type=self.__combo.currentText()
        axis=self.canvas.getSelectedAxis()
        if type=="Auto":
            self.canvas.setAutoScaleAxis(axis)
        else:
            self.canvas.setAxisRange(self.canvas.getAxisRange(axis),axis)
        self.__loadstate(self.canvas)
    def __spinChanged(self):
        if self.__loadflg:
            return
        mi=self.__spin1.value()
        ma=self.__spin2.value()
        self.canvas.setAxisRange([mi,ma],self.canvas.getSelectedAxis())

class AxisRangeScrollableCanvas(AxisRangeRightClickCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi)
        self.mpl_connect('scroll_event',self.onScroll)
    def onScroll(self,event):
        region=self.__FindRegion(event.x,event.y)
        if region == "OnGraph":
            self.__ExpandGraph(event.x,event.y,"Bottom",event.step)
            self.__ExpandGraph(event.x,event.y,"Left",event.step)
        elif not region == "OutOfFigure":
            self.__ExpandGraph(event.x,event.y,region,event.step)
        self.draw()
    def __GlobalToAxis(self, x, y, ax):
        loc=self.__GlobalToRatio(x,y,ax)
        xlim=ax.get_xlim()
        ylim=ax.get_ylim()
        x_ax=xlim[0]+(xlim[1]-xlim[0])*loc[0]
        y_ax=ylim[0]+(ylim[1]-ylim[0])*loc[1]
        return [x_ax,y_ax]
    def __GlobalToRatio(self, x, y, ax):
        ran=ax.get_position()
        x_loc=(x - ran.x0 * self.width())/((ran.x1 - ran.x0)*self.width())
        y_loc=(y - ran.y0 * self.height())/((ran.y1 - ran.y0)*self.height())
        return [x_loc,y_loc]
    def __ExpandGraph(self,x,y,axis,step):
        ratio=1.05**step
        loc=self.__GlobalToRatio(x,y,self.axes)
        if axis in {"Bottom"}:
            old=self.getAxisRange('Bottom')
            cent=(old[1]-old[0])*loc[0]+old[0]
            self.setAxisRange([cent-(cent-old[0])*ratio,cent+(old[1]-cent)*ratio],'Bottom')
        if axis in {"Left"}:
            old=self.getAxisRange('Left')
            cent=(old[1]-old[0])*loc[1]+old[0]
            self.setAxisRange([cent-(cent-old[0])*ratio,cent+(old[1]-cent)*ratio],'Left')
        if axis in {"Right","Left"} and self.axisIsValid('Right'):
            old=self.getAxisRange('Right')
            cent=(old[1]-old[0])*loc[1]+old[0]
            self.setAxisRange([cent-(cent-old[0])*ratio,cent+(old[1]-cent)*ratio],'Right')
        if axis in {"Top","Bottom"} and self.axisIsValid('Top'):
            old=self.getAxisRange('Top')
            cent=(old[1]-old[0])*loc[0]+old[0]
            self.setAxisRange([cent-(cent-old[0])*ratio,cent+(old[1]-cent)*ratio],'Top')
    def __FindRegion(self,x,y):
        ran=self.axes.get_position()
        x_loc=x/self.width()
        y_loc=y/self.height()
        pos_mode="OutOfFigure"
        if x_loc < 0 or y_loc < 0 or x_loc > 1 or y_loc > 1:
            pos_mode="OutOfFigure"
        elif x_loc < ran.x0:
            if ran.y0 < y_loc and y_loc < ran.y1:
                pos_mode="Left"
        elif x_loc > ran.x1:
            if ran.y0 < y_loc and y_loc < ran.y1:
                pos_mode="Right"
        elif y_loc < ran.y0:
            pos_mode="Bottom"
        elif y_loc > ran.y1:
            pos_mode="Top"
        else:
            pos_mode="OnGraph"
        return pos_mode

opposite={'Left':'right','Right':'left','Bottom':'top','Top':'bottom'}
Opposite={'Left':'Right','Right':'Left','Bottom':'Top','Top':'Bottom'}
class AxisAdjustableCanvas(AxisRangeScrollableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.addAxisChangeListener(self)
    def OnAxisChanged(self,axis):
        if self.axisIsValid('Right'):
            self.setMirrorAxis('Left',False)
            self.setMirrorAxis('Right',False)
        if self.axisIsValid('Top'):
            self.setMirrorAxis('Bottom',False)
            self.setMirrorAxis('Top',False)
        self._emitAxisSelected()
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        for l in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(l):
                dic[l+"_mode"]=self.getAxisMode(l)
                dic[l+"_mirror"]=self.getMirrorAxis(l)
                dic[l+"_color"]=self.getAxisColor(l)
                dic[l+"_thick"]=self.getAxisThick(l)
            else:
                dic[l+"_mode"]=None
                dic[l+"_mirror"]=None
                dic[l+"_color"]=None
                dic[l+"_thick"]=None

        dictionary['AxisSetting']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'AxisSetting' in dictionary:
            dic=dictionary['AxisSetting']
            for l in ['Left','Right','Top','Bottom']:
                if self.axisIsValid(l):
                    self.setAxisMode(l,dic[l+"_mode"])
                    self.setMirrorAxis(l,dic[l+"_mirror"])
                    self.setAxisColor(l,dic[l+"_color"])
                    self.setAxisThick(l,dic[l+"_thick"])

    def setAxisMode(self,axis,mod):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.set_yscale(mod)
        else:
            axes.set_xscale(mod)
        axes.minorticks_on()
        self.draw()
    def getAxisMode(self,axis):
        axes=self.getAxes(axis)
        if axis in ['Left','Right']:
            return axes.get_yscale()
        else:
            return axes.get_xscale()
    def setAxisThick(self,axis,thick):
        axes=self.getAxes(axis)
        if axes is None:
            return
        axes.spines[axis.lower()].set_linewidth(thick)
        axes.spines[opposite[axis]].set_linewidth(thick)
        self.draw()
    def getAxisThick(self,axis):
        axes=self.getAxes(axis)
        return axes.spines[axis.lower()].get_linewidth()
    def setAxisColor(self,axis,color):
        axes=self.getAxes(axis)
        if axes is None:
            return
        axes.spines[axis.lower()].set_edgecolor(color)
        axes.spines[opposite[axis]].set_edgecolor(color)
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(color=color,which='both')
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(color=color,which='both')
        self.draw()
    def getAxisColor(self,axis):
        axes=self.getAxes(axis)
        color=axes.spines[axis.lower()].get_edgecolor()
        return color
    def setMirrorAxis(self,axis,value):
        axes=self.getAxes(axis)
        if axes is None:
            return
        axes.spines[opposite[axis]].set_visible(value)
        self.draw()
    def getMirrorAxis(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        return axes.spines[opposite[axis]].get_visible()
class AxisAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Axis Setting")
        self.canvas=canvas
        self.__flg=False
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __initlayout(self):
        gl=QGridLayout()

        self.__all=QCheckBox('All axes')
        self.__all.setChecked(True)
        gl.addWidget(self.__all,0,0)

        self.__mirror=QCheckBox("Mirror")
        self.__mirror.stateChanged.connect(self.__mirrorChanged)
        gl.addWidget(self.__mirror,0,1)

        gl.addWidget(QLabel('Mode'),1,0)
        self.__mode=QComboBox()
        self.__mode.addItems(['linear','log','symlog'])
        self.__mode.activated.connect(self.__chgmod)
        gl.addWidget(self.__mode,1,1)

        gl.addWidget(QLabel('Color'),2,0)
        self.__color=ColorSelection()
        self.__color.colorChanged.connect(self.__changeColor)
        gl.addWidget(self.__color,2,1)

        gl.addWidget(QLabel('Thick'),3,0)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__setThick)
        gl.addWidget(self.__spin1,3,1)

        self.setLayout(gl)
    def __loadstate(self):
        self.__flg=True
        axis=self.canvas.getSelectedAxis()
        self.__spin1.setValue(self.canvas.getAxisThick(axis))
        self.__color.setColor(self.canvas.getAxisColor(axis))
        list=['linear','log','symlog']
        self.__mode.setCurrentIndex(list.index(self.canvas.getAxisMode(axis)))
        if self.canvas.axisIsValid(Opposite[axis]):
            self.__mirror.setEnabled(False)
        else:
            self.__mirror.setEnabled(True)
        self.__mirror.setChecked(self.canvas.getMirrorAxis(axis))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __mirrorChanged(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__mirror.isChecked()
        if self.__all.isChecked():
            if not self.canvas.axisIsValid('Right'):
                self.canvas.setMirrorAxis('Left',value)
                self.canvas.setMirrorAxis('Right',value)
            if not self.canvas.axisIsValid('Top'):
                self.canvas.setMirrorAxis('Top',value)
                self.canvas.setMirrorAxis('Bottom',value)
        else:
            self.canvas.setMirrorAxis(axis,value)
    def __chgmod(self):
        if self.__flg:
            return
        mod=self.__mode.currentText()
        axis=self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisMode('Left',mod)
            self.canvas.setAxisMode('Right',mod)
            self.canvas.setAxisMode('Top',mod)
            self.canvas.setAxisMode('Bottom',mod)
        else:
            self.canvas.setAxisMode(axis,mod)
    def __setThick(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisThick('Left',self.__spin1.value())
            self.canvas.setAxisThick('Right',self.__spin1.value())
            self.canvas.setAxisThick('Top',self.__spin1.value())
            self.canvas.setAxisThick('Bottom',self.__spin1.value())
        else:
            self.canvas.setAxisThick(axis,self.__spin1.value())
    def __changeColor(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisColor('Left',self.__color.getColor())
            self.canvas.setAxisColor('Right',self.__color.getColor())
            self.canvas.setAxisColor('Top',self.__color.getColor())
            self.canvas.setAxisColor('Bottom',self.__color.getColor())
        else:
            self.canvas.setAxisColor(axis,self.__color.getColor())

class TickAdjustableCanvas(AxisAdjustableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.__data={}
        self.setTickDirection('Left','in')
        self.setTickDirection('Bottom','in')
        self.setTickVisible('Left',False,which='minor')
        self.setTickVisible('Bottom',False,which='minor')
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        for l in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(l):
                dic[l+"_major_on"]=self.getTickVisible(l,mirror=False,which='major')
                dic[l+"_majorm_on"]=self.getTickVisible(l,mirror=True,which='major')
                dic[l+"_ticklen"]=self.getTickLength(l)
                dic[l+"_tickwid"]=self.getTickWidth(l)
                dic[l+"_ticknum"]=self.getAutoLocator(l)
                dic[l+"_minor_on"]=self.getTickVisible(l,mirror=False,which='minor')
                dic[l+"_minorm_on"]=self.getTickVisible(l,mirror=True,which='minor')
                dic[l+"_ticklen2"]=self.getTickLength(l,which='minor')
                dic[l+"_tickwid2"]=self.getTickWidth(l,which='minor')
                dic[l+"_ticknum2"]=self.getAutoLocator(l,which='minor')
                dic[l+"_tickdir"]=self.getTickDirection(l)
        dictionary['TickSetting']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'TickSetting' in dictionary:
            dic=dictionary['TickSetting']
            for l in ['Left','Right','Top','Bottom']:
                if self.axisIsValid(l):
                    self.setTickVisible(l,dic[l+"_major_on"],mirror=False,which='major')
                    self.setTickVisible(l,dic[l+"_majorm_on"],mirror=True,which='major')
                    self.setTickLength(l,dic[l+"_ticklen"])
                    self.setTickWidth(l,dic[l+"_tickwid"])
                    self.setAutoLocator(l,dic[l+"_ticknum"])
                    self.setTickVisible(l,dic[l+"_minor_on"],mirror=False,which='minor')
                    self.setTickVisible(l,dic[l+"_minorm_on"],mirror=True,which='minor')
                    self.setTickLength(l,dic[l+"_ticklen2"],which='minor')
                    self.setTickWidth(l,dic[l+"_tickwid2"],which='minor')
                    self.setAutoLocator(l,dic[l+"_ticknum2"],which='minor')
                    self.setTickDirection(l,dic[l+"_tickdir"])
    def setAutoLocator(self,axis,n,which='major'):
        axs=self.getAxes(axis)
        if axs is None:
            return
        if n==0:
            loc=ticker.AutoLocator()
        else:
            loc=ticker.MultipleLocator(n)
        if axis in ['Left','Right']:
            ax=axs.get_yaxis()
        if axis in ['Bottom','Top']:
            ax=axs.get_xaxis()
        if which=='major':
            ax.set_major_locator(loc)
        elif which=='minor':
            ax.set_minor_locator(loc)
        self.draw()
    def getAutoLocator(self,axis,which='major'):
        axes=self.getAxes(axis)
        if axis in ['Left','Right']:
            ax=axes.get_yaxis()
        if axis in ['Bottom','Top']:
            ax=axes.get_xaxis()
        if which=='major':
            l=ax.get_major_locator()
        elif which=='minor':
            l=ax.get_minor_locator()
        if isinstance(l,ticker.AutoLocator):
            return 0
        else:
            return l()[1]-l()[0]
    def setTickDirection(self,axis,direction):
        axes=self.getAxes(axis)
        if axes==None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(direction=direction,which='both')
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(direction=direction,which='both')
        self.draw()
    def getTickDirection(self,axis):
        data=['in','out','inout']
        marker=self._getTickLine(axis,'major').get_marker()
        if axis=='Left':
            list=[1,0,'_']
        if axis=='Right':
            list=[0,1,'_']
        elif axis=='Bottom':
            list=[2,3,'|']
        elif axis=='Top':
            list=[3,2,'|']
        return data[list.index(marker)]
    def setTickWidth(self,axis,value,which='major'):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(width=value,which=which)
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(width=value,which=which)
        self.draw()
    def getTickWidth(self,axis,which='major'):
        return self._getTickLine(axis,which).get_markeredgewidth()
    def setTickLength(self,axis,value,which='major'):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(length=value,which=which)
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(length=value,which=which)
        self.draw()
    def getTickLength(self,axis,which='major'):
        return self._getTickLine(axis,which).get_markersize()
    def _getTickLine(self,axis,which):
        axs=self.getAxes(axis)
        if axis in ['Left','Right']:
            ax=axs.get_yaxis()
        if axis in ['Bottom','Top']:
            ax=axs.get_xaxis()
        if which=='major':
            tick=ax.get_major_ticks()[0]
        elif which=='minor':
            tick=ax.get_minor_ticks()[0]
        if axis in ['Left','Bottom']:
            return tick.tick1line
        else:
            return tick.tick2line
    def setTickVisible(self,axis,tf,mirror=False,which='both'):
        axes=self.getAxes(axis)
        if axes==None:
            return
        if tf:
            value="on"
        else:
            value="off"
        if (axis == 'Left' and not mirror) or (axis == 'Right' and mirror):
            axes.get_yaxis().set_tick_params(left=value,which=which)
        if (axis == 'Right' and not mirror) or (axis == 'Left' and mirror):
            axes.get_yaxis().set_tick_params(right=value,which=which)
        if (axis == 'Top' and not mirror) or (axis == 'Bottom' and mirror):
            axes.get_xaxis().set_tick_params(top=value,which=which)
        if (axis == 'Bottom' and not mirror) or (axis == 'Top' and mirror):
            axes.get_xaxis().set_tick_params(bottom=value,which=which)
        self.draw()
    def getTickVisible(self,axis,mirror=False,which='major'):
        axs=self.getAxes(axis)
        if axis in ['Left','Right']:
            ax=axs.get_yaxis()
        if axis in ['Bottom','Top']:
            ax=axs.get_xaxis()
        if which=='major':
            tick=ax.get_major_ticks()[0]
        elif which=='minor':
            tick=ax.get_minor_ticks()[0]
        if axis in ['Left','Bottom']:
            if mirror:
                return tick.tick2On
            else:
                return tick.tick1On
        else:
            if mirror:
                return tick.tick1On
            else:
                return tick.tick2On
class TickAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Tick Setting")
        self.canvas=canvas
        self.__flg=False
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __initlayout(self):
        layout=QVBoxLayout()

        layout_h=QHBoxLayout()
        self.__all=QCheckBox('All axes')
        self.__all.setChecked(True)
        layout_h.addWidget(self.__all)

        self.__mir=QCheckBox('Mirror')
        self.__mir.stateChanged.connect(self.__chon)
        layout_h.addWidget(self.__mir)

        layout.addLayout(layout_h)

        gl=QGridLayout()

        gl.addWidget(QLabel('Location'),0,0)
        self.__mode=QComboBox()
        self.__mode.addItems(['in','out','inout','none'])
        self.__mode.activated.connect(self.__chgmod)
        gl.addWidget(self.__mode,0,1)

        gl.addWidget(QLabel('Interval'),1,0)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__chnum)
        gl.addWidget(self.__spin1,1,1)

        gl.addWidget(QLabel('Length'),2,0)
        self.__spin2=QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__chlen)
        gl.addWidget(self.__spin2,2,1)

        gl.addWidget(QLabel('Width'),3,0)
        self.__spin3=QDoubleSpinBox()
        self.__spin3.valueChanged.connect(self.__chwid)
        gl.addWidget(self.__spin3,3,1)

        self.__minor=QCheckBox('Minor')
        self.__minor.stateChanged.connect(self.__minorChanged)
        gl.addWidget(self.__minor,0,2)

        gl.addWidget(QLabel('Interval'),1,2)
        self.__spin4=QDoubleSpinBox()
        self.__spin4.valueChanged.connect(self.__chnum2)
        gl.addWidget(self.__spin4,1,3)

        gl.addWidget(QLabel('Length'),2,2)
        self.__spin5=QDoubleSpinBox()
        self.__spin5.valueChanged.connect(self.__chlen2)
        gl.addWidget(self.__spin5,2,3)

        gl.addWidget(QLabel('Width'),3,2)
        self.__spin6=QDoubleSpinBox()
        self.__spin6.valueChanged.connect(self.__chwid2)
        gl.addWidget(self.__spin6,3,3)

        layout.addLayout(gl)
        self.setLayout(layout)
        self.__loadstate()
    def __axis(self):
        if self.__all.isChecked():
            return ['Left','Right','Top','Bottom']
        else:
            return [self.canvas.getSelectedAxis()]
    def __chnum(self):
        if self.__flg:
            return
        value=self.__spin1.value()
        for ax in self.__axis():
            self.canvas.setAutoLocator(ax,value)
    def __chnum2(self):
        if self.__flg:
            return
        value=self.__spin4.value()
        for ax in self.__axis():
            self.canvas.setAutoLocator(ax,value,which='minor')
    def __chon(self):
        if self.__flg:
            return
        value=self.__mir.isChecked()
        for ax in self.__axis():
            if not self.__mode.currentText()=="none":
                self.canvas.setTickVisible(ax,value,mirror=True,which='major')
                if self.__minor.isChecked():
                    self.canvas.setTickVisible(ax,value,mirror=True,which='minor')
    def __chgmod(self):
        if self.__flg:
            return
        value=self.__mode.currentText()
        if value=="none":
            self.__mir.setChecked(False)
            for ax in self.__axis():
                self.canvas.setTickVisible(ax,False)
                self.canvas.setTickVisible(ax,False,mirror=True)
        else:
            for ax in self.__axis():
                self.canvas.setTickVisible(ax,True)
                if self.__mir.isChecked():
                    self.canvas.setTickVisible(ax,True,mirror=True)
                self.canvas.setTickDirection(ax,value)
    def __chlen(self):
        if self.__flg:
            return
        value=self.__spin2.value()
        for ax in self.__axis():
            self.canvas.setTickLength(ax,value)
    def __chlen2(self):
        if self.__flg:
            return
        value=self.__spin5.value()
        for ax in self.__axis():
            self.canvas.setTickLength(ax,value,which='minor')
    def __chwid(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__spin3.value()
        for ax in self.__axis():
            self.canvas.setTickWidth(ax,value)
    def __chwid2(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__spin6.value()
        for ax in self.__axis():
            self.canvas.setTickWidth(ax,value,which='minor')
    def __minorChanged(self):
        if self.__flg:
            return
        value=self.__minor.isChecked()
        if self.__mode.currentText()=="none":
            value=False
        for ax in self.__axis():
            self.canvas.setTickVisible(ax,value,mirror=False,which='minor')
            if self.__mir.isChecked():
                self.canvas.setTickVisible(ax,value,mirror=True,which='minor')
            else:
                self.canvas.setTickVisible(ax,False,mirror=True,which='minor')
    def __loadstate(self):
        axis=self.canvas.getSelectedAxis()
        self.__flg=True
        self.__mir.setChecked(self.canvas.getTickVisible(axis,mirror=True))
        self.__minor.setChecked(self.canvas.getTickVisible(axis,which='minor'))
        if self.canvas.getTickVisible(axis):
            self.__mode.setCurrentIndex(['in','out','inout'].index(self.canvas.getTickDirection(axis)))
        else:
            self.__mode.setCurrentIndex(3)
        self.__spin1.setValue(self.canvas.getAutoLocator(axis))
        self.__spin2.setValue(self.canvas.getTickLength(axis,'major'))
        self.__spin3.setValue(self.canvas.getTickWidth(axis,'major'))
        self.__spin4.setValue(self.canvas.getAutoLocator(axis,which='minor'))
        self.__spin5.setValue(self.canvas.getTickLength(axis,'minor'))
        self.__spin6.setValue(self.canvas.getTickWidth(axis,'minor'))
        self.__flg=False
    def OnAxisSelected(self,axis):
        self.__loadstate()

class AxisAndTickBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        layout=QVBoxLayout(self)
        layout_h1=QHBoxLayout()
        layout_h1.addWidget(AxisRangeAdjustBox(canvas))
        layout_h1.addWidget(AxisAdjustBox(canvas))
        layout.addLayout(layout_h1)
        layout.addWidget(TickAdjustBox(canvas))
        self.setLayout(layout)
