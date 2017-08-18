from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ExtendAnalysis.GraphWindow import *
from ExtendAnalysis.ExtendWidgets import *

class AnalysisTab(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.__parent=parent
        self.__initLayout()

    def __initLayout(self):
        #left part
        vbox_l=QVBoxLayout()

        self.__tree=FileSystemView()
        tree=self.__tree
        tree.SetPath(self.__parent.TreeFolder())
        tree.clicked.connect(self._treeclicked)
        list=QListWidget()
        list.setContextMenuPolicy(Qt.CustomContextMenu)
        list.customContextMenuRequested.connect(self._menu_list)
        vbox_l.addWidget(tree)
        vbox_l.addWidget(list)

        #center part
        vbox_c=QVBoxLayout()

        table=QTableWidget()
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(self._menu_table)

        exe=QPushButton('Execute',self)

        hbox_combos=QHBoxLayout()
        xaxis=QComboBox(self)
        xaxis.addItems(['Delay','Power','Index'])
        area=QComboBox(self)
        area.addItems(['Circle','Square'])
        bg=QComboBox(self)
        bg.addItems(['Linear','None'])
        hbox_combos.addWidget(QLabel('X axis'))
        hbox_combos.addWidget(xaxis)
        hbox_combos.addWidget(QLabel('Area'))
        hbox_combos.addWidget(area)
        hbox_combos.addWidget(QLabel('BG'))
        hbox_combos.addWidget(bg)

        vbox_c.addWidget(exe)
        vbox_c.addLayout(hbox_combos)
        vbox_c.addWidget(table)

        #right part
        vbox_r=QVBoxLayout()
        combo=QComboBox(self)
        combo.addItems(['Normalized','Probe','Pump'])
        result=QListWidget(self)
        vbox_r.addWidget(combo)
        vbox_r.addWidget(result)

        hbox=QHBoxLayout()
        hbox.addLayout(vbox_l)
        hbox.addLayout(vbox_c)
        hbox.addLayout(vbox_r)

        self.setLayout(hbox)

    def _menu_table(self):
        menu=QMenu(self)
        cp=QAction('Copy',self,triggered=print)
        menu.addAction(cp)
        pst=QAction('Paste',self,triggered=print)
        menu.addAction(pst)
        chk=QAction('Check all',self,triggered=print)
        menu.addAction(chk)
        append=QAction('Append to graph',self,triggered=print)
        menu.addAction(append)
        shift=QAction('shift',self,triggered=print)
        menu.addAction(shift)
        setr=QAction('Set radius',self,triggered=print)
        menu.addAction(setr)
        menu.exec_(QCursor.pos())
    def _rangePath(self):
        return self.__parent.TreeToData(self.__tree.currentPath())+"/AreaRange"
    def _treeclicked(self,index):
        path=self._rangePath()
        if os.path.exists(path):
            print(path)
    def _menu_list( self, qPoint ):
        menu = QMenu(self)
        newr=QAction("New Range",self,triggered=self._newRange)
        menu.addAction(newr)
        menu.exec_(QCursor.pos())
    def _newRange(self):
        text, ok = QInputDialog.getText(self,'---Input Dialog---', 'Range name:')
        if ok and not len(text)==0:
            path=self._rangePath()
            mkdir(path)
