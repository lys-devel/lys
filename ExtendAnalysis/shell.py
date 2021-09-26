import cmd
import os
import glob


from LysQt.QtCore import QObject, pyqtSignal
from . import home


class ExtendShell(QObject):
    commandExecuted = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.__dict = {}
        self.__log = _CommandLog()
        self.__com = _ExtendCommand()
        self.__mod = _ModuleManager(self.__dict)
        print('Welcome to Analysis program lys. Loading .py files...')

    def eval(self, txt, save=False):
        self.__mod.reload()
        if save:
            self.__log.append(txt)
        res = eval(txt, self.__dict)
        self.commandExecuted.emit(txt)
        return res

    def exec(self, txt, save=False):
        self.__mod.reload()
        if save:
            self.__log.append(txt)
        exec(txt, self.__dict)
        self.commandExecuted.emit(txt)

    def importModule(self, module):
        self.__mod.importModule(module)

    def importAll(self, module):
        self.__mod.importAll(module)

    def addObject(self, obj, name=None, printResult=True):
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

    def _do(self, txt):
        return self.__com.onecmd(txt)

    @property
    def commandLog(self):
        return self.__log.get()

    @property
    def dict(self):
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
            self.importAll("proc")
        files = glob.glob(home() + "/module/*.py")
        for f in files:
            f = os.path.splitext(os.path.basename(f))[0]
            self.importAll("module." + f)


class _ExtendCommand(cmd.Cmd):
    """Extend shell commands (display, append, etc)"""

    def do_mkdir(self, arg):
        os.makedirs(arg, exist_ok=True)

    def do_ls(self, arg):
        tmp = os.listdir()
        for file in tmp:
            print(file)

    def do_display(self, arg):
        try:
            w = eval(arg, globals())
        except Exception:
            w = arg
        display(w)

    def do_append(self, arg):
        try:
            w = eval(arg, globals())
        except Exception:
            w = arg
        append(w)

    def default(self, line):
        raise NotImplementedError
