#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys, os, glob
import rlcompleter
from importlib import import_module, reload
from pathlib import Path
from .Tasks import *
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
        dic={}
        for i in list:
            if i.group()=="":
                self.tree.addTopLevelItem(QTreeWidgetItem([i.name(),i.status(),i.explanation()]))
            else:
                grps=i.group().split("/")
                parent=None
                name=""
                for g in grps:
                    name=name+g
                    if name in dic:
                        item=dic[name]
                    else:
                        item=QTreeWidgetItem([g,"",""])
                        dic[name]=item
                        if parent is None:
                            self.tree.addTopLevelItem(item)
                        else:
                            parent.addChild(item)
                        item.setExpanded(True)
                    parent=item
                    name=name+"/"
                parent.addChild(QTreeWidgetItem([i.name(),i.status(),i.explanation()]))
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
        self.setting=globalSetting()
        self.__initlayout()
        self.__load()
    def __initlayout(self):
        layout=QVBoxLayout()
        layout.addLayout(self.__graphSetting())
        layout.addWidget(self.__floatSetting())
        layout.addStretch()
        self.setLayout(layout)
    def __graphSetting(self):
        h1=QHBoxLayout()
        self.g1=QRadioButton("Matplotlib")
        self.g2=QRadioButton("pyqtGraph")
        self.g1.toggled.connect(lambda:self._lib(self.g1))
        self.g2.toggled.connect(lambda:self._lib(self.g2))
        h1.addWidget(QLabel("Graph library"))
        h1.addWidget(self.g1)
        h1.addWidget(self.g2)
        return h1
    def __floatSetting(self):
        self._float=QCheckBox("Floating Analysis Window")
        self._float.stateChanged.connect(self._floatChanged)
        return self._float
    def _floatChanged(self,b):
        self.setting["Floating"]=(not b==0)
    def _lib(self,btn):
        if btn==self.g1:
            Graph.graphLibrary="matplotlib"
        elif btn==self.g2:
            Graph.graphLibrary="pyqtgraph"
        self.setting["GraphLibrary"]=Graph.graphLibrary
    def __load(self):
        if "GraphLibrary" in self.setting:
            self.grfType=self.setting["GraphLibrary"]
        else:
            self.grfType="matplotlib"
        if self.grfType=="pyqtgraph":
            self.g2.toggle()
        else:
            self.g1.toggle()
        if "Floating" in self.setting:
            self._float.setChecked(self.setting["Floating"])

class TextEditLogger(logging.Handler):
    def __init__(self, parent=None):
        super().__init__()
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)
    def write(self, m):
        pass

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
        self._tab_up=QTabWidget()
        self.input=CommandLineEdit(self.__shell)
        self.output=QTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setUndoRedoEnabled(False)
        #self.output2=QTextEdit(self)
        #self.output2.setReadOnly(True)
        #self.output2.setUndoRedoEnabled(False)

        self._loglevel = QHBoxLayout()
        self._loglevel.addWidget(QRadioButton("Error",toggled=lambda:self._debugLevel(40)))
        war=QRadioButton("Warning",toggled=lambda:self._debugLevel(30))
        self._loglevel.addWidget(war)
        inf=QRadioButton("Info",toggled=lambda:self._debugLevel(20))
        self._loglevel.addWidget(inf)
        self._loglevel.addWidget(QRadioButton("Debug",toggled=lambda:self._debugLevel(10)))
        inf.toggle()
        self._log=TextEditLogger()
        logging.getLogger().addHandler(self._log)
        logging.getLogger().setLevel(20)
        self._log.setFormatter(logging.Formatter('%(asctime)s [%(levelname).1s] %(message)s',"%m/%d %H:%M:%S"))
        l2=QVBoxLayout()
        l2.addLayout(self._loglevel)
        l2.addWidget(self._log.widget)
        wid2=QWidget()
        wid2.setLayout(l2)

        self._tab_up.addTab(self.output,"Command")
        #self._tab_up.addTab(self.output2,"Error")
        self._tab_up.addTab(wid2,"Log")

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
        layout_h.addWidget(self._tab_up)
        layout_h.addWidget(self.input)
        layout_h.addWidget(self._tab)

        lay=QHBoxLayout()
        lay.addWidget(layout_h)
        self.setLayout(lay)
    def _debugLevel(self,level):
        logging.getLogger().setLevel(level)
    def __viewContextMenu(self,tree):
        cd=QAction('Set Current Directory',self,triggered=self.__setCurrentDirectory)
        ld=QAction('Load',self,triggered=self.__load)
        op=QAction('Open', self, triggered=self.__openpy)
        show=QAction('Show all graphs', self, triggered=self.__showgraphs)
        save=QAction('Save all graphs', self, triggered=self.__savegraphs)
        menu={}
        menu['dir']=[cd,tree.Action_NewDirectory(),tree.Action_Delete(), show, save]
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
    def __showgraphs(self):
        p = self.view.selectedPaths()[0]
        for f in glob.glob(p+"/*.grf"):
            Graph(f)
    def __savegraphs(self):
        p = self.view.selectedPaths()[0]
        i = 0
        while(True):
            g = Graph.active(i)
            if g is None:
                return
            else:
                g.Save(p+"/graph"+str(i)+".grf")
            i += 1
    def __work(self,path):
        name=self.view2.selectedPaths()[0].replace(AutoSavedWindow.folder_prefix,"")
        AutoSavedWindow.SwitchTo(name)
    def __addwork(self):
        text, ok = QInputDialog.getText(self, 'New worksapce', 'Name of workspace')
        if ok:
            AutoSavedWindow.SwitchTo(text)
