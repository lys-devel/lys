if __name__ == '__main__':
    import PyQt5.QtWidgets, PyQt5.QtCore, sys
    app = PyQt5.QtWidgets.QApplication([])

    from ExtendShell import ExtendShell
    shell=ExtendShell()
    shell.CommandWindow()
    sys.exit(app.exec())
    
