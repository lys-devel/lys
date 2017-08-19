#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
import rlcompleter
from .ExtendType import *
from .Widgets.ExtendWidgets import *
from .GraphWindow import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class Logger( object ):
    def __init__( self, editor, out=None, color=None ):
        self.editor = editor
        self.out    = out
        if not color:
            self.color = editor.textColor()
        else:
            self.color = color

    def write( self, message ):
        self.editor.moveCursor(QTextCursor.End)
        self.editor.setTextColor( self.color )
        self.editor.insertPlainText( message )
        if self.out:
            self.out.write( message )
    def flush(self):
        pass
class CommandLineEdit(QLineEdit):
    def __init__(self,shell):
        QLineEdit.__init__(self)
        self.shell=shell
        self.returnPressed.connect(self.__SendCommand)
        self.__logn=0
        self.completer=rlcompleter.Completer(self.shell.GetDictionary())

    def event(self,event):
        if event.type() == QEvent.KeyPress:
            if event.key()==Qt.Key_Tab:
                if self.__tabn==0:
                    self.__txt=self.text()
                try:
                    tmp=self.completer.complete(self.__txt,self.__tabn)
                    if tmp is None and not self.__tabn==0:
                        tmp=self.completer.complete(self.__txt,0)
                        self.__tabn=0
                    if not tmp is None:
                        self.setText(tmp)
                        self.__tabn+=1
                except Exception:
                    print("fail:",self.__txt, self.__tabn)
                return True
            else:
                self.__tabn=0

            if event.key()==Qt.Key_Up:
                log=self.shell.GetCommandLog()
                if len(log)==0:
                    return True
                if not len(log)==self.__logn:
                    self.__logn+=1
                self.setText(log[len(log)-self.__logn])
                return True

            if event.key()==Qt.Key_Down:
                log=self.shell.GetCommandLog()
                if not self.__logn==0:
                    self.__logn-=1
                if self.__logn==0:
                    self.setText("")
                else:
                    self.setText(log[max(0,len(log)-self.__logn)])
                return True

        return QLineEdit.event(self, event)

    def __SendCommand(self):
        txt=self.text()
        self.shell.SendCommand(txt)
        self.clear()
        self.__logn=0
class ColoredFileSystemModel(ExtendFileSystemModel):
    def __init__(self):
        super().__init__()
        self.__list=[]
        self.setNameFilters(['*.npz','*.str','*.val','*.dic','*.grf','*.pxt'])
        self.setNameFilterDisables(False)

    def OnCDChanged(self,cd):
        self.__icd=self.index(cd)
        i=self.index(cd)
        list_old=self.__list
        self.__list=[]
        while i.isValid():
            self.__list.append(i)
            i=self.parent(i)
        for index in self.__list:
            self.dataChanged.emit(index,index,[Qt.FontRole,Qt.BackgroundRole])
        for index in list_old:
            self.dataChanged.emit(index,index,[Qt.FontRole,Qt.BackgroundRole])

    def data(self,index,role=Qt.DisplayRole):
        if index in self.__list and role==Qt.FontRole:
            font=QFont()
            font.setBold(True)
            return font
        if index==self.__icd and role==Qt.BackgroundRole:
            return QColor(200,200,200)
        return super().data(index,role)

class CommandWindow(QMdiSubWindow):
    def __init__(self, shell, parent=None):
        super(CommandWindow, self).__init__(parent)
        self.setWindowTitle("Command Window")
        self.__shell=shell

        self.__CreateLayout()
        sys.stdout = Logger(self.output, sys.stdout)
        sys.stderr = Logger(self.output, sys.stderr, QColor(255,0,0))

        addCDChangeListener(self.__dirmodel)

        self.__loadData()
        self.show()

    def __loadData(self):
        mkdir(".com_settings")
        self._savepath=os.path.abspath("./")
        self.__clog=String("./.com_settings/commandlog.log")
        self.output.setPlainText(self.__clog.data)
        self.__log2=String("./.com_settings/commandlog2.log")
        if not len(self.__log2.data)==0:
            self.__shell.SetCommandLog(eval(self.__log2.data))
        wins=[]
        if os.path.exists('./.com_settings/winlist.log'):
            with open('./.com_settings/winlist.log','r') as f:
                wins=eval(f.read())
        for w in wins:
            g=LoadFile.load(w)
            if w.find("./.com_settings/.graphs")>-1:
                g.Disconnect()
                remove(w)
    def saveData(self):
        self.__clog.data=self.output.toPlainText()
        self.__clog.Save()
        self.__log2.data=str(self.__shell.GetCommandLog())
        mkdir(self._savepath+"/.com_settings/.graphs")
        wins=AutoSavedWindow.DisconnectedWindows()
        i=0
        for w in wins:
            w.Save(self._savepath+"/.com_settings/.graphs/graph"+str(i)+".grf")
            i+=1
        names=[]
        wins=AutoSavedWindow.AllWindows()
        for w in wins:
            names.append('./'+os.path.relpath(w.FileName(),self._savepath).replace('\\','/'))
        with open(self._savepath+'/.com_settings/winlist.log','w') as f:
            f.write(str(names))
    def closeEvent(self,event):
        event.ignore()
    def __CreateLayout(self):
        layout=QVBoxLayout()
        self.input=CommandLineEdit(self.__shell)
        self.output=QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setUndoRedoEnabled(False)
        layout.addWidget(self.output)
        layout.addWidget(self.input)

        wid=QWidget(self)
        wid.setLayout(layout)

        layout_h=QSplitter(Qt.Horizontal)
        self.__dirmodel = ColoredFileSystemModel()
        self.__tree=FileSystemView(self,self.__dirmodel)
        self.__tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.__treeContextMenu(self.__tree)
        self.__tree.SetPath(pwd())
        layout_h.addWidget(self.__tree)
        layout_h.addWidget(wid)

        self.setWidget(layout_h)
    def __treeContextMenu(self,tree):
        cd=QAction('Set Current Directory',self,triggered=self.__setCurrentDirectory)
        ld=QAction('Load',self,triggered=self.__load)
        menu={}
        menu['dir']=[cd,tree.Action_NewDirectory(),tree.Action_Delete()]
        menu['mix']=[ld,tree.Action_Delete()]
        menu['other']=[ld,tree.Action_Delete(),tree.Action_Print()]
        menu['.npz']=[tree.Action_Preview(),tree.Action_Display(),tree.Action_Edit(),ld,tree.Action_Print(),tree.Action_Delete()]
        tree.SetContextMenuActions(menu)

    def __setCurrentDirectory(self):
        cd(self.__tree.selectedPaths()[0])
    def __load(self):
        for p in self.__tree.selectedPaths():
            self.__shell.Load(p)
