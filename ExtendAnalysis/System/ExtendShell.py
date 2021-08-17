import cmd
import os
import traceback
import rlcompleter

# For plug-in managers
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer
from pathlib import Path
from importlib import import_module, reload

from ExtendAnalysis import *


class ExtendShell(QObject):
    commandExecuted = pyqtSignal(str)

    def __init__(self, com, logpath):
        super().__init__()
        self.__com = com
        self.__comlog = []
        self.__ecom = ExtendCommand(self)
        self.__log2 = String(logpath)
        if not len(self.__log2.data) == 0:
            self.SetCommandLog(eval(self.__log2.data))
        print('Welcome to Analysis program lys. Loading .py files...')
        m = PluginManager(home(), self)
        m.start()

    def SendCommand(self, txt, message=True, save=True):
        if message:
            print(">", txt)
        if not len(txt) == 0 and save:
            while txt in self.__comlog:
                self.__comlog.remove(txt)
            while len(self.__comlog) > 3000:
                self.__comlog.pop(0)
            self.__comlog.append(txt)
        if txt == "cd":
            cd()
            return
        if txt == "pwd":
            print(pwd())
            return
        if txt == "exit()" or txt == "exit":
            self.__com.close()
        flg = False
        try:
            tmp = eval(txt, globals())
            if not tmp is None:
                print(tmp)
        except Exception:
            flg = True
        if flg:
            try:
                exec(txt, globals())
            except Exception:
                err = traceback.format_exc()
                try:
                    res = self.__ecom.onecmd(txt)
                except Exception as e:
                    sys.stderr.write('Invalid command.\n')
                    print(err)
        self.commandExecuted.emit(txt)

    def save(self):
        self.__log2.data = str(self.GetCommandLog())

    def GetCommandLog(self):
        return self.__comlog

    def SetCommandLog(self, log):
        self.__comlog = log

    def GetDictionary(self):
        return globals()

    def __GetValidName(self, name):
        flg = True
        number = 0
        while flg:
            if name + str(number) in globals():
                number += 1
            else:
                flg = False
        if name[0].isdigit():
            return "data" + name + str(number)
        return name + str(number)

    def Load(self, name):
        nam, ext = os.path.splitext(os.path.basename(name))
        nam = self.__GetValidName(nam).replace(" ", "_")
        exec(nam + '=LoadFile.load(\'' + name + '\')', globals())
        print(nam + ' is loaded from ' + ext + ' file')
        return eval(nam, globals())

    def clearLog(self):
        self.__com.clearLog()


class ExtendCommand(cmd.Cmd):
    def __init__(self, shell):
        self.__shell = shell

    def do_cd(self, arg):
        cd(arg)

    def do_mkdir(self, arg):
        mkdir(arg)

    def do_rm(self, arg):
        remove(arg)

    def do_cp(self, arg):
        lis = arg.split(" ")

    def do_workspace(self, arg):
        lis = arg.split(" ")
        w = lis[0].replace(" ", "")
        AutoSavedWindow.SwitchTo(lis[0])

    def do_mv(self, arg):
        lis = arg.split(" ")
        move(lis[0], lis[1])

    def do_rename(self, arg):
        lis = arg.split(" ")
        move(lis[0], lis[1])

    def do_ls(self, arg):
        tmp = os.listdir()
        for file in tmp:
            print(file)

    def do_load(self, arg):
        self.__shell.Load(arg)

    def do_pwd(self, arg):
        print(pwd())

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

    def do_clear(self, arg):
        self.__shell.clearLog()


class PluginManager:
    class Handler(PatternMatchingEventHandler):
        def __init__(self, manager: 'PluginManager', *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.manager = manager

        def on_created(self, event: FileSystemEvent):
            if event.src_path.endswith('.py'):
                self.manager.load_plugin(Path(event.src_path))

        def on_modified(self, event):
            if event.src_path.endswith('.py'):
                self.manager.load_plugin(Path(event.src_path))

    def __init__(self, path: str, shell):
        self.plugins = {}
        self.path = path
        self.observer = Observer()
        self.shell = shell
        sys.path.append(self.path)

    def start(self):
        self.scan_plugin()
        self.observer.schedule(self.Handler(self, patterns=['*.py']), self.path)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def scan_plugin(self):
        for file_path in Path(self.path).glob('*.py'):
            self.load_plugin(file_path)

    def load_plugin(self, file_path):
        module_name = file_path.stem
        if module_name not in self.plugins:
            if module_name.startswith('.'):
                return
            try:
                self.shell.SendCommand('from importlib import import_module, reload', message=False, save=False)
                self.shell.SendCommand('from ' + module_name + ' import *', message=False, save=False)
                self.plugins[module_name] = import_module(module_name)
                # print('{}.py has been loaded.'.format(module_name))
            except:
                print('Error on loading {}.py.'.format(module_name))
        else:
            try:
                self.plugins[module_name] = reload(self.plugins[module_name])
                self.shell.SendCommand('from ' + module_name + ' import *', message=True, save=False)
                print('{}.py has been reloaded.'.format(module_name))
            except Exception as e:
                import traceback
                sys.stderr.write('Error on reloading {}.py.'.format(module_name))
                print(traceback.format_exc())


class CommandLineEdit(QLineEdit):
    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self.returnPressed.connect(self.__SendCommand)
        self.__logn = 0
        self.completer = rlcompleter.Completer(self.shell.GetDictionary())

    def __findBlock(self):
        text = self.text()
        end = self.cursorPosition()
        i = 1
        while(True):
            if text[end - i] in [",", "(", " "]:
                start = end - i
                break
            if end == i:
                start = -1
                break
            i += 1
        return start, end

    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                if self.__tabn == 0:
                    s, e = self.__findBlock()
                    self.__prefix = self.text()[:s + 1]
                    self.__suffix = self.text()[e:]
                    self.__txt = self.text()[s + 1:e]
                try:
                    tmp = self.completer.complete(self.__txt, self.__tabn)
                    if tmp is None and not self.__tabn == 0:
                        tmp = self.completer.complete(self.__txt, 0)
                        self.__tabn = 0
                    if not tmp is None:
                        self.setText(self.__prefix + tmp + self.__suffix)
                        self.setCursorPosition(len(self.__prefix + tmp))
                        self.__tabn += 1
                except Exception:
                    print("fail:", self.__txt, self.__tabn)
                return True
            else:
                self.__tabn = 0

            if event.key() == Qt.Key_Control:
                s, e = self.__findBlock()
                self.__txt = self.text()[s + 1:e]
                tmp = 0
                res = ""
                for i in range(100):
                    tmp = self.completer.complete(self.__txt, i)
                    if tmp is None:
                        break
                    res += tmp + ", "
                if i == 99:
                    res += "etc..."
                print(res)

            if event.key() == Qt.Key_Up:
                log = self.shell.GetCommandLog()
                if len(log) == 0:
                    return True
                if not len(log) - 2 == self.__logn:
                    self.__logn += 1
                self.setText(log[len(log) - self.__logn])
                return True

            if event.key() == Qt.Key_Down:
                log = self.shell.GetCommandLog()
                if not self.__logn == 0:
                    self.__logn -= 1
                if self.__logn == 0:
                    self.setText("")
                else:
                    self.setText(log[max(0, len(log) - self.__logn)])
                return True

        return QLineEdit.event(self, event)

    def __SendCommand(self):
        txt = self.text()
        self.shell.SendCommand(txt)
        self.clear()
        self.__logn = 0
