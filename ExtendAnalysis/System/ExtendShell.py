import sys
import traceback
import rlcompleter
from LysQt.QtWidgets import QLineEdit
from LysQt.QtCore import QEvent, Qt


class CommandLineEdit(QLineEdit):
    def __init__(self, shell):
        super().__init__()
        self.shell = shell
        self.returnPressed.connect(self.__SendCommand)
        self.__logn = 0
        self.completer = rlcompleter.Completer(self.shell.dict)

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
                log = self.shell.commandLog
                if len(log) == 0:
                    return True
                if not len(log) - 2 == self.__logn:
                    self.__logn += 1
                self.setText(log[len(log) - self.__logn])
                return True

            if event.key() == Qt.Key_Down:
                log = self.shell.commandLog
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
        self.clear()
        self.__logn = 0
        print(">", txt)
        try:
            res = self.shell.eval(txt, save=True)
            if res is not None:
                print(res)
            return
        except Exception:
            pass
        try:
            self.shell.exec(txt)
            return
        except Exception:
            err = traceback.format_exc()
            try:
                res = self.shell._do(txt)
            except Exception:
                sys.stderr.write('Invalid command.\n')
                print(err)
