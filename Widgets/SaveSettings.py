#!/usr/bin/env python
import random, sys, os, math, io
from PyQt5.QtGui import *
from .AnchorSettings import *

class SaveSettingCanvas(AnchorSettingCanvas):
    def __init__(self,dpi=100):
        super().__init__(dpi)
    def Save(self,path,format):
        self.fig.savefig(path,transparent=True,format=format)
    def CopyToClipboard(self):
        clipboard=QApplication.clipboard()
        mime=QMimeData()
        mime.setData('Encapsulated PostScript',self.toData('eps'))
        mime.setData('application/postscript',self.toData('eps'))
        mime.setData('Scalable Vector Graphics',self.toData('svg'))
        mime.setData('application/svg+xml',self.toData('svg'))
        mime.setData('Portable Document Format',self.toData('pdf'))
        mime.setData('application/pdf',self.toData('pdf'))
        buf = io.BytesIO()
        self.fig.savefig(buf,transparent=True)
        mime.setImageData(QImage.fromData(buf.getvalue()))
        buf.close()
        clipboard.setMimeData(mime)
    def toData(self,format):
        buf = io.BytesIO()
        self.fig.savefig(buf,format=format,transparent=True)
        buf.seek(0)
        data=buf.read()
        buf.close()
        return data
    def keyPressEvent(self, e):
        super().keyPressEvent(e)
        if e.modifiers() == Qt.ControlModifier:
            if e.key() == Qt.Key_C:
                self.CopyToClipboard()

class SaveBox(QWidget):
    def __init__(self,canvas):
        super().__init__()
        self.canvas=canvas
        self.__initlayout()
    def __initlayout(self):
        l=QVBoxLayout()
        self._save=QPushButton('Save',clicked=self.Save)
        l.addWidget(self._save)
        self._copy=QPushButton('Copy',clicked=self.Copy)
        l.addWidget(self._copy)
        self.setLayout(l)
    def Copy(self):
        self.canvas.CopyToClipboard()
    def Save(self):
        filters=['PDF file (*.pdf)','EPS file (*.eps)','PNG file (*.png)','SVG file (*.svg)']
        exts=['.pdf','.eps','.png','.svg']
        f=""
        for fil in filters:
            f+=fil+";;"
        res=QFileDialog.getSaveFileName(self, 'Open file', pwd(),f,filters[0])
        if len(res[0])==0:
            return
        name, ext = os.path.splitext(res[0])
        savename=name
        if ext==exts[filters.index(res[1])]:
            savename+=ext
        else:
            savename=name+ext+exts[filters.index(res[1])]
        self.canvas.Save(savename,exts[filters.index(res[1])].replace('.',''))
