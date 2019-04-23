import sys
import  PyQt5.QtWidgets
from PyQt5 import uic

class MyWindow(PyQt5.QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('form1.ui', self)
        self.btn1.clicked.connect(self.pr)
        self.show()
    def pr(self):
        print("debug001")

if __name__ == '__main__':
    __app = PyQt5.QtWidgets.QApplication([])
    window = MyWindow()
    sys.exit(__app.exec_())
