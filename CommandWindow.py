#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os
import rlcompleter
from importlib import import_module, reload
from pathlib import Path
from .Tasks import tasks
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

from .ExtendType import *
from .BasicWidgets import *
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
        self.AddAcceptedFilter('*.py')

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

class PluginManager:
    class Handler(PatternMatchingEventHandler):
        def __init__(self, manager: 'PluginManager', *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.manager = manager
        def on_created(self, event: FileSystemEvent):
            if event.src_path.endswith('.py'):
                self.manager.load_plugin(Path(event.src_path))
        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                self.manager.load_plugin(Path(event.src_path))
    def __init__(self, path: str, shell):
        self.plugins = {}
        self.path = path
        self.observer = Observer()
        self.shell=shell
        sys.path.append(self.path)
    def start(self):
        self.scan_plugin()
        self.observer.schedule(self.Handler(self, patterns='*.py'), self.path)
        self.observer.start()
    def stop(self):
        self.observer.stop()
        self.observer.join()
    def scan_plugin(self):
        for file_path in Path(self.path).glob('*.py'):
            self.load_plugin(file_path)
    def load_plugin(self, file_path):
        module_name = file_path.stem
        if module_name not in self.plugins:
            if module_name.startswith('.'):
                return
            try:
                self.shell.SendCommand('from importlib import import_module, reload',message=False,save=False)
                self.shell.SendCommand('from '+module_name+' import *',message=True,save=False)
                self.plugins[module_name] = import_module(module_name)
                #print('{}.py has been loaded.'.format(module_name))
            except:
                print('Error on loading {}.py.'.format(module_name))
        else:
            try:
                self.plugins[module_name]=reload(self.plugins[module_name])
                self.shell.SendCommand('from '+module_name+' import *',message=False,save=False)
                print('{}.py has been reloaded.'.format(module_name))
            except Exception as e:
                import traceback
                sys.stderr.write('Error on reloading {}.py.'.format(module_name))
                print(traceback.format_exc())

class TaskWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.__initlayout()

    def __initlayout(self):
        layout=QVBoxLayout()
        self.tree=QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name","Status","Explanation"])
        self.tree.setContextMenuPolicy( Qt.CustomContextMenu )
        self.tree.customContextMenuRequested.connect( self.buildContextMenu )
        layout.addWidget(self.tree)

        tasks.updated.connect(self.__update)
        self.setLayout(layout)
    def __update(self):
        self.tree.clear()
        list=tasks.getTasks()
        for i in list:
            if i[0].isRunning():
                st="Running"
            else:
                st="Waiting"
            self.tree.addTopLevelItem(QTreeWidgetItem([i[1],st,i[2]]))
    def buildContextMenu(self):
        menu = QMenu( self.tree )
        menulabels = ['Delete']
        actionlist = []
        for label in menulabels:
            actionlist.append( menu.addAction( label ) )
        action = menu.exec_(QCursor.pos())
        for act in actionlist:
            if act.text() == "Delete":
                items=self.tree.selectedIndexes()
                if len(items)==0:
                    return
                list=tasks.getTasks()
                for i in items:
                    if i.column()==0:
                        tasks.removeTask(list[i.row()][0])

class SettingWidget(QWidget):
    path=home()+"/.lys/settings"
    def __init__(self):
        super().__init__()
        self.__initlayout()
        self.__load()
    def __initlayout(self):
        layout=QVBoxLayout()
        h1=QHBoxLayout()
        self.g1=QRadioButton("Matplotlib")
        self.g2=QRadioButton("pyqtGraph")
        self.g1.toggled.connect(lambda:self._lib(self.g1))
        self.g2.toggled.connect(lambda:self._lib(self.g2))
        h1.addWidget(QLabel("Graph library"))
        h1.addWidget(self.g1)
        h1.addWidget(self.g2)
        layout.addLayout(h1)
        layout.addStretch()
        self.setLayout(layout)
    def _lib(self,btn):
        if btn==self.g1:
            Graph.graphLibrary="matplotlib"
        elif btn==self.g2:
            Graph.graphLibrary="pyqtgraph"
        self.grfType.data=Graph.graphLibrary
    def __load(self):
        self.grfType=String(self.path+"/graphLib.str")
        if self.grfType.data=="pyqtgraph":
            self.g2.toggle()
        else:
            self.g1.toggle()

class CommandWindow(QWidget):
    def __init__(self, shell, parent=None):
        super(CommandWindow, self).__init__(parent)
        self.setWindowTitle("Command Window")
        self.resize(600,600)
        self.__shell=shell

        self.__CreateLayout()
        sys.stdout = Logger(self.output, sys.stdout)
        sys.stderr = Logger(self.output, sys.stderr, QColor(255,0,0))

        self.__loadData()
        self.show()

    def __loadData(self):
        self._savepath=os.path.abspath("./")
        self.__clog=String(".lys/commandlog.log")
        self.output.setPlainText(self.__clog.data)
        self.__log2=String(".lys/commandlog2.log")
        if not len(self.__log2.data)==0:
            self.__shell.SetCommandLog(eval(self.__log2.data))
        if not os.path.exists('proc.py'):
            with open("proc.py", "w") as file:
                file.write("from ExtendAnalysis import *")
        print('Welcome to Analysis program lys. Loading .py files...')
        m=PluginManager(home(),self.__shell)
        m.start()
    def saveData(self):
        self.__clog.data=self.output.toPlainText()
        self.__clog.Save()
        self.__log2.data=str(self.__shell.GetCommandLog())
        if not PythonEditor.CloseAllEditors():
            return False
        AutoSavedWindow.StoreAllWindows()
        return True
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

        layout_h=QSplitter(Qt.Vertical)
        self._tab=QTabWidget()

        self.__dirmodel = ColoredFileSystemModel()
        self.view=FileSystemView(self,self.__dirmodel)
        self.__viewContextMenu(self.view)
        self.view.SetPath(pwd())

        self.__dirmodel2 = ExtendFileSystemModel()
        self.view2=FileSystemView(self,self.__dirmodel2)
        self.__viewContextMenu2(self.view2)
        self.view2.SetPath(home()+"/.lys/workspace")

        self._tab.addTab(self.view,"File")
        self._tab.addTab(self.view2,"Workspace")
        self._tab.addTab(TaskWidget(),"Tasks")
        self._tab.addTab(SettingWidget(),"Settings")
        layout_h.addWidget(wid)
        layout_h.addWidget(self._tab)

        lay=QHBoxLayout()
        lay.addWidget(layout_h)
        self.setLayout(lay)
    def __viewContextMenu(self,tree):
        cd=QAction('Set Current Directory',self,triggered=self.__setCurrentDirectory)
        ld=QAction('Load',self,triggered=self.__load)
        op=QAction('Open', self, triggered=self.__openpy)
        menu={}
        menu['dir']=[cd,tree.Action_NewDirectory(),tree.Action_Delete()]
        menu['mix']=[ld,tree.Action_Delete()]
        menu['other']=[ld,tree.Action_Delete(),tree.Action_Print()]
        menu['.npz']=[tree.Action_Display(),tree.Action_Append(),tree.Action_Preview(),tree.Action_Edit(),ld,tree.Action_Print(),tree.Action_Delete()]
        menu['.py']=[op,tree.Action_Delete()]
        menu['.lst']=[op,tree.Action_Edit()]
        tree.SetContextMenuActions(menu)

    def __viewContextMenu2(self,tree):
        ld=QAction('Load workspace',self,triggered=self.__work)
        add=QAction('Add workspace',self,triggered=self.__addwork)
        menu={}
        menu['dir']=[ld,add,tree.Action_Delete()]
        menu['mix']=[add,tree.Action_Delete()]
        menu['other']=[add,tree.Action_Delete()]
        tree.SetContextMenuActions(menu)

    def __setCurrentDirectory(self):
        cd(self.view.selectedPaths()[0])
    def __load(self):
        for p in self.view.selectedPaths():
            self.__shell.Load(p)
    def __openpy(self):
        for p in self.view.selectedPaths():
            PythonEditor(p)
    def __work(self,path):
        name=self.view2.selectedPaths()[0].replace(AutoSavedWindow.folder_prefix,"")
        AutoSavedWindow.SwitchTo(name)
    def __addwork(self):
        text, ok = QInputDialog.getText(self, 'New worksapce', 'Name of workspace')
        if ok:
            AutoSavedWindow.SwitchTo(text)
