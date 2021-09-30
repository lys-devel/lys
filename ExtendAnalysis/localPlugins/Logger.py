import logging
import os

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from ExtendAnalysis import glb


class TextEditLogger(logging.Handler):
    def __init__(self, parent=None):
        super().__init__()
        self.records = []
        self.messages = []
        self.maxsize = 3000
        self.filt = None
        self.count = 0
        self.parent = parent

    def __update(self):
        txt = ""
        for r, m in zip(reversed(self.records), reversed(self.messages)):
            if self.filt is None:
                txt += r + "\n"
            elif self.filt in m:
                txt += r + "\n"
        self.parent.updated.emit(txt)

    def emit(self, record):
        msg = self.format(record)
        if len(self.messages) != 0:
            if record.message == self.messages[len(self.messages) - 1]:
                self.count += 1
                self.records[len(self.records) - 1] = msg + " (" + str(self.count) + ")"
                self.__update()
                return
            else:
                self.count = 1
        if len(self.records) > self.maxsize:
            self.records.pop(0)
            self.messages.pop(0)
        self.records.append(msg)
        self.messages.append(record.message)
        self.__update()

    def setTextFilter(self, filter):
        self.filt = filter
        self.__update()

    def write(self, m):
        pass


class LogWidget(QWidget):
    updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.__initlog()
        self.__initlayout()

    def __initlayout(self):
        self._loglevel = QHBoxLayout()
        self._loglevel.addWidget(QRadioButton("Error", toggled=lambda: self._debugLevel(40)))
        war = QRadioButton("Warning", toggled=lambda: self._debugLevel(logging.WARNING))
        self._loglevel.addWidget(war)
        inf = QRadioButton("Info", toggled=lambda: self._debugLevel(logging.INFO))
        self._loglevel.addWidget(inf)
        self._loglevel.addWidget(QRadioButton("Debug", toggled=lambda: self._debugLevel(10)))
        war.toggle()

        self.filt = QLineEdit()
        self.filt.textChanged.connect(self._filter)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Filter"))
        h1.addWidget(self.filt)

        self.widget = QPlainTextEdit(self)
        self.widget.setReadOnly(True)
        self.updated.connect(self.widget.setPlainText)

        l2 = QVBoxLayout()
        l2.addLayout(self._loglevel)
        l2.addLayout(h1)
        l2.addWidget(self.widget)
        self.setLayout(l2)

    def _filter(self):
        f = self.filt.text()
        if len(f) == 0:
            self._log.setTextFilter(None)
        else:
            self._log.setTextFilter(f)

    def _debugLevel(self, level):
        self._log.setLevel(level)

    def __initlog(self):
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger().addHandler(self.__createTextEditLogger())
        logging.getLogger().addHandler(self.__createFileLogger(logging.DEBUG, "debug"))
        logging.getLogger().addHandler(self.__createFileLogger(logging.INFO, "info"))
        logging.getLogger().addHandler(self.__createFileLogger(logging.WARNING, "warning"))

    def __createTextEditLogger(self):
        self._log = TextEditLogger(self)
        self._log.setLevel(20)
        self._log.setFormatter(logging.Formatter('%(asctime)s [%(levelname).1s] %(message)s', "%m/%d %H:%M:%S"))
        return self._log

    def __createFileLogger(self, level, name):
        import logging.handlers
        os.makedirs(".lys/log", exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(".lys/log/" + name + ".log", maxBytes=100000, backupCount=10)
        fh.setLevel(level)
        fh_formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(filename)s-%(name)s-%(funcName)s-%(message)s')
        fh.setFormatter(fh_formatter)
        return fh


_instance = LogWidget()
glb.mainWindow().addTab(_instance, "Log", "up")
