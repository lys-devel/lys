Understanding shell in lys
========================================

0. The commands below can be executed in usual Python interpreter as well as Python interpretr in lys main window.

1. The shell in `lys` is an :class:`lys.glb.shell.ExtendShell` instance::

    from lys import glb
    shell = glb.shell()
    print(shell) # <lys.glb.shell.ExtendShell object at somewhere>

2. When the user enter a command from GUI command line in the main window, the python command is executed via `exec` and `eval` methods. Similarly, you can execute arbitrary Python command by the methods above::

    # When a user enter "a=2" in Python interpreter in lys, the command below is executed.
    shell.exec("a=2")
    # When a user enter "a", the command below is executed.
    result = shell.eval("a")
    print("a =", result) # a = 2

3. All variables are stored as dictionary that can be obtained by `dict` property. This is corresponds to `locals` function in usual Python interpreter::

    var_a = shell.dict["a"]
    print(var_a) # 2 

4. To enable users to define original functions/classes, all .py files in `module` directory is automatically loaded before calling `shell.exec` and `shell.eval` methods. For example, if proc.py and test.py exist under `module` directory, these files are loaded automatically::

    result = shell.eval("a")
    # This is (almost) equivalent to the code below.
    # from module.proc import *
    # from module.test import *
    # result = eval("a", shell.dict)  # This is built-in eval function

5. (For developer/specialist only) Calling "from module.name import \*" do nothing when the module has already been loaded (This is a specification of Python). Please take care that special module manager class is implemented in lys.glb.shell module to avoid this problem. General users do not need to take care of this problem.