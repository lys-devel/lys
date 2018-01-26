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
        for ext in LoadFile.getExtentions():
            self.AddAcceptedFilter('*'+ext)

    def data(self,index,role=Qt.DisplayRole):
        if role==Qt.FontRole:
            if pwd().find(self.filePath(index)) > -1:
                font=QFont()
                font.setBold(True)
                return font
        if role==Qt.BackgroundRole:
            if pwd()==self.filePath(index):
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

        self.__loadData()
        self.show()

    def __loadData(self):
        mkdir(".com_settings")
        self._savepath=os.path.abspath("./")
        self.__clog=String(".lys/commandlog.log")
        self.output.setPlainText(self.__clog.data)
        self.__log2=String(".lys/commandlog2.log")
        if not len(self.__log2.data)==0:
            self.__shell.SetCommandLog(eval(self.__log2.data))
        AutoSavedWindow.RestoreAllWindows()
    def saveData(self):
        self.__clog.data=self.output.toPlainText()
        self.__clog.Save()
        self.__log2.data=str(self.__shell.GetCommandLog())
        AutoSavedWindow.StoreAllWindows()
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
        self.view=FileSystemView(self,self.__dirmodel)
        self.__viewContextMenu(self.view)
        self.view.SetPath(pwd())
        layout_h.addWidget(self.view)
        layout_h.addWidget(wid)

        self.setWidget(layout_h)
    def __viewContextMenu(self,tree):
        cd=QAction('Set Current Directory',self,triggered=self.__setCurrentDirectory)
        ld=QAction('Load',self,triggered=self.__load)
        menu={}
        menu['dir']=[cd,tree.Action_NewDirectory(),tree.Action_Delete()]
        menu['mix']=[ld,tree.Action_Delete()]
        menu['other']=[ld,tree.Action_Delete(),tree.Action_Print()]
        menu['.npz']=[tree.Action_Display(),tree.Action_Append(),tree.Action_Preview(),tree.Action_Edit(),ld,tree.Action_Print(),tree.Action_Delete()]
        tree.SetContextMenuActions(menu)

    def __setCurrentDirectory(self):
        cd(self.view.selectedPaths()[0])
    def __load(self):
        for p in self.view.selectedPaths():
            self.__shell.Load(p)
