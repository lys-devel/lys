#!/usr/bin/env python
import random, weakref, gc, sys, os
from collections import namedtuple
from ColorWidgets import *
import numpy as np
from enum import Enum
from ExtendType import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure, SubplotParams
import matplotlib.pyplot as plt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from matplotlib import lines, markers, ticker
from GraphWindow import *

class RangeSelectableCanvas(ImageColorAdjustableCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi)
        self.rect = Rectangle((0,0), 0, 0, color='orange', alpha=0.5)
        self.axes.add_patch(self.rect)
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
            self.draw()
    def IsRangeSelected(self):
        return not self.rect.get_width()==0
    def ClearSelectedRange(self):
        self.rect.set_width(0)
        self.rect.set_height(0)
    def SelectedRange(self):
        return (self.rect_pos_start,self.rect_pos_end)

class AxisSelectableCanvas(RangeSelectableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
        self.axis_selected='Left'
        self.__listener=[]
    def setSelectedAxis(self, axis):
        self.axis_selected=axis
        for l in self.__listener:
            if l() is not None:
                l().OnAxisSelected(axis)
            else:
                self.__listener.remove(l)
    def getSelectedAxis(self):
        return self.axis_selected
    def addAxisSelectedListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def getAxes(self,axis):
        ax=axis
        if ax in ['Left','Bottom']:
            return self.axes
        if ax=='Right':
            if self.axes_ty is not None:
                return self.axes_ty
            else:
                return self.axes_txy
        if ax=='Top':
            if self.axes_tx is not None:
                return self.axes_tx
            else:
                return self.axes_txy
    def axisIsValid(self,axis):
        if axis in ['Left','Bottom']:
            return True
        if axis in ['Right']:
            return self.axes_ty is not None or self.axes_txy is not None
        if axis in ['Top']:
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
    def __init__(self,canvas,allAxis=False):
        super().__init__()
        self.canvas=canvas
        self.addItem('Left')
        if (canvas.axes_ty is not None or canvas.axes_txy is not None) or allAxis:
            self.addItem('Right')
        self.addItem('Bottom')
        if (canvas.axes_tx is not None or canvas.axes_txy is not None) or allAxis:
            self.addItem('Top')
        self.activated.connect(self._activated)
    def _activated(self):
        self.canvas.setSelectedAxis(self.currentText())

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
        self._emitAxisChanged()
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

    def addAxisChangeListener(self,listener):
        self.__listener.append(weakref.ref(listener))
    def _emitAxisChanged(self):
        for l in self.__listener:
            if l() is not None:
                l().OnAxisChanged()
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
        self._emitAxisChanged()
        self.draw()
    def isAutoScaled(self,axis):
        ax=axis
        axes=self.getAxes(axis=ax)
        if axes is None:
            return
        if ax in ['Left','Right']:
            return axes.get_autoscaley_on()
        if ax in ['Top','Bottom']:
            return axes.get_autoscaley_on()
class AxisRangeAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__('Axis Range')
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate(canvas)
        self.__changeflg=False
        self.canvas.addAxisSelectedListener(self)
        self.canvas.addAxisChangeListener(self)
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
        if not self.canvas.axisIsValid(axis):
            return
        mod=canvas.isAutoScaled(axis)
        if mod:
            self.__setMode('Auto')
        else:
            self.__setMode('Manual')
        ran=canvas.getAxisRange(axis)
        self.__spin1.setValue(ran[0])
        self.__spin2.setValue(ran[1])
        self.__loadflg=False
    def OnAxisChanged(self):
        if not self.__changeflg:
            self.__loadstate(self.canvas)

    def OnAxisSelected(self,axis):
        self.__loadstate(self.canvas)
    def __setMode(self,mode):
        if mode=='Auto':
            self.__combo.setCurrentIndex(0)
        else:
            self.__combo.setCurrentIndex(1)
        self.__OnModeChanged()
    def __OnModeChanged(self):
        type=self.__combo.currentText()
        if type=='Auto':
            self.__spin1.setReadOnly(True)
            self.__spin2.setReadOnly(True)
            if not self.__loadflg:
                self.__changeflg=True
                self.canvas.setAutoScaleAxis(self.canvas.getSelectedAxis())
                self.__changeflg=False
        else:
            self.__spin1.setReadOnly(False)
            self.__spin2.setReadOnly(False)
    def __spinChanged(self):
        if self.__combo.currentText()=='Manual':
            mi=self.__spin1.value()
            ma=self.__spin2.value()
            if not self.__loadflg:
                self.__changeflg=True
                self.canvas.setAxisRange([mi,ma],self.canvas.getSelectedAxis())
                self.__changeflg=False
class AxisRangeScrollableCanvas(AxisRangeAdjustableCanvas):
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

class AxisAdjustableCanvas(AxisRangeScrollableCanvas):
    def __init__(self, dpi=100):
        super().__init__(dpi=dpi)
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        dic={}
        for l in ['Left','Right','Top','Bottom']:
            if self.axisIsValid(l):
                dic[l+"_mode"]=self.getAxisMode(l)
            else:
                dic[l+"_mode"]=None
            dic[l+"_color"]=self.getAxisColor(l)
            dic[l+"_thick"]=self.getAxisThick(l)
        dictionary['AxisSetting']=dic
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        if 'AxisSetting' in dictionary:
            dic=dictionary['AxisSetting']
            for l in ['Left','Right','Top','Bottom']:
                mod=dic[l+"_mode"]
                if mod is not None:
                    self.setAxisMode(l,mod)
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
        self.draw()
    def getAxisMode(self,axis):
        axes=self.getAxes(axis)
        if axis in ['Left','Right']:
            return axes.get_yscale()
        else:
            return axes.get_xscale()
    def setAxisThick(self,axis,thick):
        self.axes.spines[axis.lower()].set_linewidth(thick)
        self.draw()
    def getAxisThick(self,axis):
        return self.axes.spines[axis.lower()].get_linewidth()
    def setAxisColor(self,axis,color):
        self.axes.spines[axis.lower()].set_edgecolor(color)
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(color=color,which='both')
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(color=color,which='both')
        self.draw()
    def getAxisColor(self,axis):
        color=self.axes.spines[axis.lower()].get_edgecolor()
        return color
    def setMirrorAxis(self,axis,value):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis == 'Left':
            axes.spines['right'].set_visible(value)
        if axis == 'Right':
            axes.spines['left'].set_visible(value)
        if axis == 'Top':
            axes.spines['bottom'].set_visible(value)
        if axis == 'Bottom':
            axes.spines['top'].set_visible(value)
        self.draw()
    def getMirrorAxis(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            return
        if axis == 'Left':
            return axes.spines['right'].get_visible()
        if axis == 'Right':
            return axes.spines['left'].get_visible()
        if axis == 'Top':
            return axes.spines['bottom'].get_visible()
        if axis == 'Bottom':
            return axes.spines['top'].get_visible()
        self.draw()
class AxisAdjustBox(QGroupBox):
    def __init__(self,canvas):
        super().__init__("Axis Setting")
        self.canvas=canvas
        self.__initlayout()
        self.__loadstate()
        self.canvas.addAxisSelectedListener(self)
    def __initlayout(self):
        gl=QGridLayout()

        self.__all=QCheckBox('All axes')
        self.__all.setChecked(True)
        gl.addWidget(self.__all,0,0)

        self.__mirror=QCheckBox('Mirror')
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
        axis=self.canvas.getSelectedAxis()
        self.__spin1.setValue(self.canvas.getAxisThick(axis))
        self.__color.setColor(self.canvas.getAxisColor(axis))
        if not self.canvas.axisIsValid(axis):
            return
        list=['linear','log','symlog']
        self.__mode.setCurrentIndex(list.index(self.canvas.getAxisMode(axis)))
        self.__mirror.setChecked(self.canvas.getMirrorAxis(axis))
    def OnAxisSelected(self,axis):
        self.__loadstate()
    def __mirrorChanged(self):
        axis=self.canvas.getSelectedAxis()
        value=self.__mirror.isChecked()
        if self.__all.isChecked():
            self.canvas.setMirrorAxis('Left',value)
            self.canvas.setMirrorAxis('Right',value)
            self.canvas.setMirrorAxis('Top',value)
            self.canvas.setMirrorAxis('Bottom',value)
        else:
            self.canvas.setMirrorAxis(axis,value)
    def __chgmod(self):
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
        axis=self.canvas.getSelectedAxis()
        if self.__all.isChecked():
            self.canvas.setAxisThick('Left',self.__spin1.value())
            self.canvas.setAxisThick('Right',self.__spin1.value())
            self.canvas.setAxisThick('Top',self.__spin1.value())
            self.canvas.setAxisThick('Bottom',self.__spin1.value())
        else:
            self.canvas.setAxisThick(axis,self.__spin1.value())
    def __changeColor(self):
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
    def _getTickLine(self,axis,which):
        axs=self.__getAxes(axis)
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
    def __getAxes(self,axis):
        axes=self.getAxes(axis)
        if axes is None:
            if axis=='Right':
                axes=self.getAxes('Left')
            else:
                axes=self.getAxes('Bottom')
        return axes
    def setAutoLocator(self,axis,n,which='major'):
        axs=self.__getAxes(axis)
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
        axes=self.__getAxes(axis)
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
        axes=self.__getAxes(axis)
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
        axes=self.__getAxes(axis)
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(width=value,which=which)
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(width=value,which=which)
        self.draw()
    def getTickWidth(self,axis,which='major'):
        return self._getTickLine(axis,which).get_markeredgewidth()
    def setTickLength(self,axis,value,which='major'):
        axes=self.__getAxes(axis)
        if axis in ['Left','Right']:
            axes.get_yaxis().set_tick_params(length=value,which=which)
        if axis in ['Top','Bottom']:
            axes.get_xaxis().set_tick_params(length=value,which=which)
        self.draw()
    def getTickLength(self,axis,which='major'):
        return self._getTickLine(axis,which).get_markersize()
    def setTickVisible(self,axis,tf):
        axes=self.__getAxes(axis)
        if tf:
            value="on"
        else:
            value="off"
        if axis == 'Left':
            axes.get_yaxis().set_tick_params(left=value,which='both')
        if axis == 'Right':
            axes.get_yaxis().set_tick_params(right=value,which='both')
        if axis == 'Top':
            axes.get_xaxis().set_tick_params(top=value,which='both')
        if axis == 'Bottom':
            axes.get_xaxis().set_tick_params(bottom=value,which='both')
        self.draw()
    def getTickVisible(self,axis):
        return self._getTickLine(axis,'major').get_visible()
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

        self.__all=QCheckBox('For all axes')
        self.__all.setChecked(True)
        layout.addWidget(self.__all)

        gl=QGridLayout()
        self.__on=QCheckBox('Ticks')
        self.__on.stateChanged.connect(self.__chon)
        gl.addWidget(self.__on,0,0)

        gl.addWidget(QLabel('Location'),1,0)
        self.__mode=QComboBox()
        self.__mode.addItems(['in','out','inout'])
        self.__mode.activated.connect(self.__chgmod)
        gl.addWidget(self.__mode,1,1)

        gl.addWidget(QLabel('Interval'),2,0)
        self.__spin1=QDoubleSpinBox()
        self.__spin1.valueChanged.connect(self.__chnum)
        gl.addWidget(self.__spin1,2,1)

        gl.addWidget(QLabel('Length'),3,0)
        self.__spin2=QDoubleSpinBox()
        self.__spin2.valueChanged.connect(self.__chlen)
        gl.addWidget(self.__spin2,3,1)

        gl.addWidget(QLabel('Width'),4,0)
        self.__spin3=QDoubleSpinBox()
        self.__spin3.valueChanged.connect(self.__chwid)
        gl.addWidget(self.__spin3,4,1)

        layout.addLayout(gl)
        self.setLayout(layout)
        self.__loadstate()
    def __chnum(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__spin1.value()
        if self.__all.isChecked():
            self.canvas.setAutoLocator('Left',value)
            self.canvas.setAutoLocator('Right',value)
            self.canvas.setAutoLocator('Top',value)
            self.canvas.setAutoLocator('Bottom',value)
        else:
            self.canvas.setAutoLocator(axis,value)
    def __chon(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__on.isChecked()
        if self.__all.isChecked():
            self.canvas.setTickVisible('Left',value)
            self.canvas.setTickVisible('Right',value)
            self.canvas.setTickVisible('Top',value)
            self.canvas.setTickVisible('Bottom',value)
        else:
            self.canvas.setTickVisible(axis,value)
    def __chgmod(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__mode.currentText()
        if self.__all.isChecked():
            self.canvas.setTickDirection('Left',value)
            self.canvas.setTickDirection('Right',value)
            self.canvas.setTickDirection('Top',value)
            self.canvas.setTickDirection('Bottom',value)
        else:
            self.canvas.setTickDirection(axis,value)
    def __chlen(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__spin2.value()
        if self.__all.isChecked():
            self.canvas.setTickLength('Left',value)
            self.canvas.setTickLength('Right',value)
            self.canvas.setTickLength('Top',value)
            self.canvas.setTickLength('Bottom',value)
        else:
            self.canvas.setTickLength(axis,value)
    def __chwid(self):
        if self.__flg:
            return
        axis=self.canvas.getSelectedAxis()
        value=self.__spin3.value()
        if self.__all.isChecked():
            self.canvas.setTickWidth('Left',value)
            self.canvas.setTickWidth('Right',value)
            self.canvas.setTickWidth('Top',value)
            self.canvas.setTickWidth('Bottom',value)
        else:
            self.canvas.setTickWidth(axis,value)
    def __loadstate(self):
        axis=self.canvas.getSelectedAxis()
        if not self.canvas.axisIsValid(axis):
            return
        self.__flg=True
        #self.__mode.setCurrentIndex(['in','out','inout'].index(self.canvas.getTickDirection(axis)))
        #self.__on.setChecked(self.canvas.getTickVisible(axis))
        #self.__spin1.setValue(self.canvas.getAutoLocator(axis))
        #self.__spin2.setValue(self.canvas.getTickLength(axis,'major'))
        #self.__spin3.setValue(self.canvas.getTickWidth(axis,'major'))
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
