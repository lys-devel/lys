import os,sys, fnmatch
from ExtendAnalysis.ExtendType import *
from ExtendAnalysis.GraphWindow import Graph, PreviewWindow, Table
from ExtendAnalysis import LoadFile
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class ExtendFileSystemModel(QSortFilterProxyModel):
    def __init__(self,model=QFileSystemModel()):
        super().__init__()
        self.mod=model
        self.setSourceModel(self.mod)
        self._exclude=[]
        self._include=[]
    def setRootPath(self,path):
        self.mod.setRootPath(path)
    def indexFromPath(self,path):
        return self.mapFromSource(self.mod.index(path))
    def AddAcceptedFilter(self,filter):
        self._include.append(filter)
    def AddExcludedFilter(self,filter):
        self._exclude.append(filter)
    def filterAcceptsRow(self,row,parent):
        index=self.mod.index(row, 0, parent)
        name=self.mod.data(index,Qt.DisplayRole)
        for inc in self._include:
            if fnmatch.fnmatch(name,inc):
                return True
        for exc in self._exclude:
            if fnmatch.fnmatch(name,exc):
                return False
        return super().filterAcceptsRow(row,parent)

    def isDir(self,index):
        return self.mod.isDir(self.mapToSource(index))
    def filePath(self,index):
        return self.mod.filePath(self.mapToSource(index))
    def parent(self,index):
        return self.mapFromSource(self.mod.parent(self.mapToSource(index)))
class _FileSystemViewBase(QWidget):
    def __init__(self,view,parent=None,model=ExtendFileSystemModel(),path=''):
        super().__init__()
        self._path=path
        self.__view=view
        self.Model=model
        self.__view.setModel(self.Model)
        self.__actions={}
    def SetContextMenuActions(self,dict):
        self.__actions=dict
    def AddContextMenuActions(self,type,actionlist):
        self.__actions[type]=actionlist

    def _buildContextMenu( self, qPoint ):
        menu = QMenu(self)
        indexes=self.selectedIndexes()
        tp=self._judgeFileType(indexes)
        if not tp in self.__actions and 'other' in self.__actions:
            tp='other'
        if tp in self.__actions:
            for key in self.__actions[tp]:
                menu.addAction(key)
            menu.exec_(QCursor.pos())
    def SetPath(self,path):
        self._path=path
        self.Model.setRootPath(path)
        self.__view.setRootIndex(self.Model.indexFromPath(path))

    def currentPath(self):
        return self.Model.filePath(self.tree.currentIndex())
    def selectedPaths(self):
        list=self.selectedIndexes()
        res=[]
        for l in list:
            res.append(self.Model.filePath(l))
        return res
    def _judgeFileType(self,indexes):
        flg=True
        for i in indexes:
            flg=flg and self.Model.isDir(i)
        if flg:
            return "dir"
        else:
            flg=True
            path,ext=os.path.splitext(self.Model.filePath(indexes[0]))
            for i in indexes:
                path2, ext2=os.path.splitext(self.Model.filePath(i))
                if not ext == ext2:
                    flg=False
            if flg:
                return ext
            else:
                return "mix"
    def Action_NewDirectory(self):
        return QAction('New Directory',self,triggered=self._Action_NewDirectory)
    def _Action_NewDirectory(self):
        paths=self.selectedPaths()
        text, ok = QInputDialog.getText(self,'---Input Dialog---', 'Directory name:')
        if ok and not len(text)==0:
            for p in paths:
                mkdir(p+'/'+text)
    def Action_Delete(self):
        return QAction('Delete',self,triggered=self._Action_Delete)
    def _Action_Delete(self):
        paths=self.selectedPaths()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Are you really want to delete "+str(len(paths))+" items?")
        msg.setWindowTitle("Caution")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ok = msg.exec_()
        if ok==QMessageBox.Ok:
            for p in self.selectedPaths():
                remove(p)
    def Action_Display(self):
        return QAction('Display',self,triggered=self.__display)
    def __display(self):
        g=Graph()
        for p in self.selectedPaths():
            w=Wave(p)
            g.Append(w)
    def Action_Append(self):
        return QAction('Append',self,triggered=self.__append)
    def __append(self):
        g=Graph.active()
        if g is None:
            return
        for p in self.selectedPaths():
            w=Wave(p)
            g.Append(w)
    def Action_Preview(self):
        return QAction('Preview',self,triggered=self.__preview)
    def __preview(self):
        list=[]
        for p in self.selectedPaths():
            list.append(Wave(p))
        PreviewWindow(list)
    def Action_Edit(self):
        return QAction('Edit',self,triggered=self.__edit)
    def __edit(self):
        t=Table()
        for p in self.selectedPaths():
            w=Wave(p)
            print(t)
            t.Append(w)
    def Action_Print(self):
        return QAction('Print',self,triggered=self.__print)
    def __print(self):
        for p in self.selectedPaths():
            w=LoadFile.load(p)
            print(w)

class FileSystemView(_FileSystemViewBase):
    def __init__(self,parent=None,model=None,path=''):
        layout=QVBoxLayout()
        self.tree=QTreeView(parent=parent)
        super().__init__(self.tree,parent,model,path)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._buildContextMenu)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setColumnHidden(3,True)
        self.tree.setColumnHidden(2,True)
        self.tree.setColumnHidden(1,True)
        layout.addWidget(self.tree)
        self.edit=QLineEdit()
        layout.addWidget(self.edit)
        self.setLayout(layout)

    def selectedIndexes(self):
        indexes=self.tree.selectedIndexes()
        if len(indexes)==0:
            indexes.append(self.Model.indexFromPath(self._path))
        return indexes
class FileSystemList(QListView,_FileSystemViewBase):
    def __init__(self,parent=None,model=None,path=''):
        QListView.__init__(self,parent=parent)
        _FileSystemViewBase.__init__(self,QListView,parent,model,path)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._buildContextMenu)
    def selectedIndexes(self):
        indexes=QListView.selectedIndexes(self)
        if len(indexes)==0:
            indexes.append(self.Model.index(self._path))
        return indexes
