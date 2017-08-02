#おまじない
import random, weakref, gc, sys, os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import GraphWindow

#テスト用Canvas
class TestCanvas(GraphWindow.BaseClass):
    #最初にInheritedClassから呼ばれ、BaseClassの処理をsuper().__init__(dpi=dpi)で呼び成さなければならない。
    def __init__(self,dpi=100):
        super().__init__(dpi=dpi)
        #ここから処理を書く。
        self.val=0#初期値

    #グラフの保存時に必要に応じて呼ばれる
    def SaveAsDictionary(self,dictionary,path):
        super().SaveAsDictionary(dictionary,path)
        #ここから処理を書く。dictionaryがグラフロード時にLoadFromDictionaryに渡される
        #保存するものが多いときは辞書にまとめる
        dictionary['Test']={}
        dictionary['Test']['Val']=self.val

    #グラフのロード時に呼ばれる。SaveAsDictionaryで保存した情報を再現しなければならない。
    def LoadFromDictionary(self,dictionary,path):
        super().LoadFromDictionary(dictionary,path)
        #ここから処理を書く。
        if 'Test' in dictionary:#この行がないとこのクラスを追加した瞬間に次の行でバグる(一度もSaveAsDictionaryが呼ばれていないため)
            m=dictionary['Test']
            self.setTest(m['Val'])

    #実際の処理を行う関数。LoadFromDictionaryやTestBoxから呼び出される。
    def setTest(self,val):
        self.val=val
        print('This is test of inherited Canvas.('+str(val)+')')

#テスト用ボックス。QWidgetさえ継承していればなんでもOK
class TestBox(QGroupBox):
    #最初に呼び出される。canvasは必ず引数に取る必要がある。
    def __init__(self,canvas):
        super().__init__(title="TestBox")
        self.canvas=canvas
        #ここから処理を書く。見た目はご自由に
        layout=QHBoxLayout()
        btn1=QPushButton("Button1",clicked=self.btn1)
        btn2=QPushButton("Button2",clicked=self.btn2)
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        self.setLayout(layout)

    #実際の処理を呼び出す。このクラスはあくまでGUIなので、Canvasを直接操作してはいけない
    #(CanvasのsetTest関数の中身は知らない体でここを書く)
    def btn1(self):
        self.canvas.setTest(1)
    def btn2(self):
        self.canvas.setTest(2)
        #これはダメ↓
        #self.canvas.val=2

#これ以下はテスト時の調整用
def addTestLayout(layout,canvas):
    #TestBoxを表示したくない場合は下の行をコメントアウト
    t=TestBox(canvas)
    layout.addWidget(t)

#下の行をコメントアウトするとこのファイルのクラスは実際のCanvasには継承されない
GraphWindow.InheritedClass=TestCanvas
