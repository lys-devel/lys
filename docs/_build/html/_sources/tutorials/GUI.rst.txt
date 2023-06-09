Customizing GUIs
==========================

Add new window
---------------------

1. You can very easily add new window in lys. From "Python" menu, select "Create new window" and enter the name of the window as "TestWindow1".

2. Enter the code below to make new window::

    TestWindow1()

3. You see the new window is created. If you want to edit window, you can do it follwing the PyQt reference.

4. If you want to create the window from the main menu, see below.


Add menu
------------------------

1. Open proc.py (Ctrl+P) or other .py files.

2. Define the function below::

    from lys import glb

    def makeMenu():
        menu = glb.mainWindow().menuBar() # This is QMenuBar object.

        m = menu.addMenu('User-defined')
        act1 = m.addAction("Hello")
        act1.triggered.connect(lambda: print("Hello"))
        act2 = m.addAction("World")
        act2.triggered.connect(lambda: print("World"))

3. Calling "makeMenu()" in the command line add the menu. Do not call this function many times because the identical menu is added.


Add new tab in sidebar
-------------------------
1. Open proc.py (Ctrl+P) or other .py files.

2. Define the function below::

    from lys import glb
    from lys.Qt import QtWidgets # We recomment to load Qt like this.

    def makeTab():
        tab = glb.mainWindow().tabWidget("right") # If you want bottom tab, change "right" to "bottom".
        w = QtWidgets.QLabel("Hello, world")
        tab.addTab(w, "User")

3. Calling "makeTab()" in the command line add the tab. Do not call this function many times because the identical tab is added.


