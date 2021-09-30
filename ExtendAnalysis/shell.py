import os
import glob


from LysQt.QtCore import QObject, pyqtSignal
from . import home


class ExtendShell(QObject):
    """
    Extended shell object that is used for Python Interface in lys.

    This object is basically used to realize custom functionarities of lys from plugins.

    Any expression can be executed and evaluated by :func:`exec` and :func:`eval` functions.
    Any object can be added by :func:`addObject`

    ExtendShell is basically singleton object. Developers should access the instance of ExtendShell from :func:`.glb.shell` function.

    Example:

        Execute some commands in lys Python Interface.

        >>> from lys import glb
        >>> shell = glb.shell()
        >>> shell.exec("a=1")
        >>> shell.eval(a)
        1

        Adding new function in lys Python Interface.

        >>> f = lambda: print("hello")
        >>> shell.addObject(f, name = "hello")

        Import new module in lys Python Interface.

        >>> # define *my_module* that is used in Python Interface
        >>> shell.importModule("my_module")

    """
    _instance = None
    commandExecuted = pyqtSignal(str)
    """
    *commandExecuted* signal is emitted after when :func:`eval` and :func:`exec` is called.
    """

    def __init__(self):
        super().__init__()
        ExtendShell._instance = self
        self.__dict = {}
        self.__log = _CommandLog()
        self.__mod = _ModuleManager(self.__dict)

    def eval(self, expr, save=False):
        """
        Evaluate expression in shell.

        Args:
            expr (str): expression to be evaluated
            save (bool): if True, *expr* is added to command log.

        Return:
            Any: Result

        Example:

            >>> from lys import glb
            >>> glb.shell().exec("a=1")
            >>> glb.shell().eval("a")
            1
        """
        self.__mod.reload()
        if save:
            self.__log.append(expr)
        res = eval(expr, self.__dict)
        self.commandExecuted.emit(expr)
        return res

    def exec(self, expr, save=False):
        """
        Execute expression in shell.

        Args:
            expr (str): expression to be executed
            save (bool): if True, *expr* is added to command log.

        Example:

            >>> from lys import glb
            >>> glb.shell().exec("a=1")
            >>> glb.shell().eval("a")
            1
        """
        self.__mod.reload()
        if save:
            self.__log.append(expr)
        exec(expr, self.__dict)
        self.commandExecuted.emit(expr)

    def importModule(self, module):
        """
        Import module

        This function import *module*, i.e. import *module* is called.

        If the module has been imported, it is reloaded by importlib.

        Args:
            module(str): module to be loaded.

        Example:
            >>> from lys import glb
            >>> glb.shell().importModule("time")

        """
        self.__mod.importModule(module)

    def importAll(self, module):
        """
        Import module

        This function import *module*, i.e. from *module* import * is called.

        If the module has been imported, it is reloaded by importlib.

        Args:
            module(str): module to be loaded.

        Example:
            >>> from lys import glb
            >>> glb.shell().importAll("time")

        """
        self.__mod.importAll(module)

    def addObject(self, obj, name=None, printResult=True):
        """
        Add object to shell.

        *name* represents name of object on shell.
        If None, obj.__name__ and obj.name is used as a name.
        If both methods are not defined, object is loaded as default name "obj".

        To avoid overlap, name is automatically changed.

        Args:
            obj(any): object to be loaded
            name(str): name of object
            printResult(bool): If True, message is printed after loading.
        """
        if name is None:
            if hasattr(obj, "__name__"):
                name = obj.__name__
            elif hasattr(obj, "name"):
                name = obj.name
            else:
                name = "obj"
        name = self.__GetValidName(name)
        self.__dict[name] = obj
        if printResult:
            print(name, "is added to shell.")

    @property
    def commandLog(self):
        """
        List of command log that is executed by user.

        Return:
            list: List of commands
        """
        return self.__log.get()

    @property
    def dict(self):
        """
        Global dictionary of shell.

        This is useful when developers want to access local variables in Python Interface.

        Return:
            dict: Global dictionary of shell
        """
        return self.__dict

    def __GetValidName(self, name):
        if name[0].isdigit():
            name = "data" + name
        if name not in self.__dict:
            return name.replace(" ", "_")
        number = 1
        while name + str(number) in self.__dict:
            number += 1
        return (name + str(number)).replace(" ", "_")


class _CommandLog:
    """Automatically save & load command log"""
    __logFile = home() + "/.lys/commandlog2.log"

    def __init__(self):
        self.__load()

    def __load(self):
        if os.path.exists(self.__logFile):
            with open(self.__logFile, 'r') as f:
                log = eval(f.read())
        else:
            log = []
        self.__comlog = log

    def append(self, txt):
        if len(txt) == 0:
            return
        while txt in self.__comlog:
            self.__comlog.remove(txt)
        while len(self.__comlog) > 3000:
            self.__comlog.pop(0)
        self.__comlog.append(txt)
        self._save()

    def _save(self):
        with open(self.__logFile, 'w') as f:
            f.write(str(self.__comlog))

    def get(self):
        return self.__comlog


class _ModuleManager:
    def __init__(self, dic):
        self.__dict = dic
        self.__importedModules = []
        exec("import importlib", self.__dict)

    def importModule(self, module):
        if module in self.__importedModules:
            exec("importlib.reload(" + module + ")", self.__dict)
        else:
            self.__importedModules.append(module)
            exec("import " + module, self.__dict)

    def importAll(self, module):
        self.importModule(module)
        exec("from " + module + " import *", self.__dict)

    def reload(self):
        if os.path.exists(home() + "/proc.py"):
            print("proc.py in home folder is deprecated. move it in module folder.")
        files = glob.glob(home() + "/module/*.py")
        for f in files:
            f = os.path.splitext(os.path.basename(f))[0]
            self.importAll("module." + f)


ExtendShell()
