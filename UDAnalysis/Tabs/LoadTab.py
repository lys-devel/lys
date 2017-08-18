from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ExtendAnalysis.GraphWindow import *
from ExtendAnalysis.ExtendWidgets import *

class LoadTab(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.__parent=parent
        parent.AddRawFolderChangeListener(self)
        self.__initLayout()

    def __initLayout(self):
        hbox=QHBoxLayout()

        self.__list_view=FileSystemList(self)
        self.__list_view.Model.setNameFilters(['*.npz'])
        self.__list_view.Model.setNameFilterDisables(False)

        hbox.addWidget(self.__list_view)

        btn_load=QPushButton('Load')
        btn_load.clicked.connect(self.__load)
        hbox.addWidget(btn_load)

        self.__tree_loaded=FileSystemView()
        tree=self.__tree_loaded
        tree.SetPath(self.__parent.TreeFolder())
        dele=QAction('Delete',self,triggered=self._delete)
        tree.AddContextMenuActions("dir",[tree.Action_NewDirectory(),dele])
        tree.AddContextMenuActions("other",[dele])
        tree.AddContextMenuActions("mix",[dele])

        tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tree.clicked.connect(self.__clicked)
        hbox.addWidget(tree)

        vbox1=QVBoxLayout()
        self.__list_raw=QListWidget()
        self.__list_raw.currentItemChanged.connect(self._raw_sel)
        self.__list_raw.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__list_raw.customContextMenuRequested.connect(self._raw_menu)
        self.__modelist=QComboBox()
        self.__modelist.addItem('Probe')
        self.__modelist.addItem('Pump')
        self.__modelist.activated[str].connect(self._onUpdate)
        label=QLabel("Saved data")
        self.__list_saved=QListWidget()
        self.__list_saved.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__list_saved.customContextMenuRequested.connect(self._saved_menu)
        vbox1.addWidget(self.__modelist)
        vbox1.addWidget(self.__list_raw)
        vbox1.addWidget(label)
        vbox1.addWidget(self.__list_saved)

        hbox.addLayout(vbox1)
        self.setLayout(hbox)

        self._path=""
    def _delete(self):
        for p in self.__tree_loaded.selectedPaths():
            path=self.__parent.TreeToData(p)
            if os.path.exists(path):
                remove(path)
            remove(p)

    def _onUpdate(self,type=None):
        self.__list_raw.clear()
        path=self._path
        if not len(path)==0:
            type=self.__modelist.currentText()
            self.__list_raw.addItems(self.__parent.GetRawItems(path,type))
        self.__list_saved.clear()
        path=self._createPath()
        if os.path.exists(path):
            lis=os.listdir(path)
            for l in lis:
                self.__list_saved.addItem(l)

    def _raw_menu(self,pos):
        menu=QMenu(self)
        prev=QAction('Preview',self,triggered=self._showPreview)
        menu.addAction(prev)
        save=QAction('Save',self,triggered=self._saveRaw)
        menu.addAction(save)
        menu.exec_(QCursor.pos())
    def _showPreview(self):
        path=self._path
        type=self.__modelist.currentText()
        w=self.__parent.GetRawData(path,type,self.__list_raw.currentItem().text())
        PreviewWindow(w)
    def _createPath(self):
        target=self.__tree_loaded.currentPath()
        path=self.__parent.TreeToData(target)
        return path+'/RawData/'+self.__modelist.currentText()

    def _saved_menu(self,pos):
        menu=QMenu(self)
        menu.addAction(QAction('Preview',self,triggered=self._savedPreview))
        menu.addAction(QAction('Graph',self,triggered=self._savedGraph))
        menu.exec_(QCursor.pos())
    def _savedGraph(self):
        w=Wave(self._createPath()+"/"+self.__list_saved.currentItem().text())
        g=Graph()
        g.Append(w)
    def _savedPreview(self):
        w=Wave(self._createPath()+"/"+self.__list_saved.currentItem().text())
        PreviewWindow(w)
    def _saveRaw(self):
        path=self._path
        type=self.__modelist.currentText()
        name=self.__list_raw.currentItem().text()
        nam, ext = os.path.splitext(os.path.basename(name))
        w=self.__parent.GetRawData(path,type,name)
        path=self._createPath()
        mkdir(path)
        w2=Wave(path+"/"+nam+".npz")
        w2.Overwrite(w)
        self._onUpdate()

    def _raw_sel(self,current,previous):
        path=self._path
        typ=self.__modelist.currentText()
        if current is not None:
            w=self.__parent.GetRawData(path,typ,current.text())
            self.__parent.showPreview(w)

    def __clicked(self,index):
        path=self.__tree_loaded.Model.filePath(index)
        if not self.__tree_loaded.Model.isDir(index):
            s=String(path)
            self._path=self.__parent.RawDataFolder()+"/"+s.data
            self._onUpdate()

    def __load(self):
        paths=self.__list_view.selectedPaths()
        if not len(paths)==0:
            list=[]
            for p in paths:
                path=os.path.relpath(p,self.__parent.RawDataFolder())
                list.append(path)
            paths2=self.__tree_loaded.selectedPaths()
            for p2 in paths2:
                for p in list:
                    name=os.path.basename(p)
                    s=String(p2+"/"+name)
                    s.data=p

    def OnRawFolderChanged(self,fold):
        if fold is not None:
            self.__list_view.SetPath(fold)
