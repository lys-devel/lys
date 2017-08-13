if __name__ == '__main__':
    import  PyQt5.QtCore, sys
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    app = PyQt5.QtWidgets.QApplication([])

    from ExtendShell import ExtendShell
    shell=ExtendShell()
    com=shell.CommandWindow()
    main=QMdiArea()
    main.show()
    main.addSubWindow(com)
    sys.exit(app.exec())
