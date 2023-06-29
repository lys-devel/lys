"""
This program enables copy and paste from lys running in windows subsystem for linux.
The flow of copy and paste is as following.

1. lys copy the graphics as text in clipboard, which can usually pass through x11 system.
2. This program detect it and translate it as pdf binary.
3. Paste the translated pdf file to the clipboard.
"""

import sys
from PyQt5 import QtGui, QtCore, QtWidgets

base64_icon = b'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'


def loadIcon():
    ba = QtCore.QByteArray.fromBase64(base64_icon)
    image = QtGui.QImage.fromData(ba, 'PNG')
    pixmap = QtGui.QPixmap.fromImage(image)
    icon = QtGui.QIcon(pixmap)
    return icon


class clipcheck(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.clip = QtWidgets.QApplication.clipboard()
        self.clip.dataChanged.connect(self.onClipChanged)
        self.__initTrayIcon()

    def __initTrayIcon(self):
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            QtWidgets.QMessageBox.information(None, "Caution", "We could't detect any system tray on this system.")
            self.quit()

        self.quit_action = QtWidgets.QAction("&Quit", self)
        self.quit_action.triggered.connect(self.quit)

        self.trayIconMenu = QtWidgets.QMenu()
        self.trayIconMenu.addAction(self.quit_action)

        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setToolTip("Tool for copying lys graphics from x11 system")
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setIcon(loadIcon())
        self.trayIcon.show()
        self.trayIcon.showMessage("lys clip", "lys clip started. You can copy and paste graphics.")

    def onClipChanged(self):
        self.text = self.clip.text()
        if len(self.text) > 1000:  # Length of PDF file is usually more than 1000.
            QtCore.QTimer.singleShot(0, self.update)

    def update(self):
        try:
            data = bytes.fromhex(self.text)
            mime = QtCore.QMimeData()
            mime.setData('Encapsulated PostScript', data)
            mime.setData('application/postscript', data)
            mime.setData('Portable Document Format', data)
            mime.setData('application/pdf', data)
            self.clip.setMimeData(mime)
            self.trayIcon.showMessage("lys clip", "Your graphics is succesfully copied to clipboard.")
        except Exception:
            pass


if __name__ == '__main__':
    c = clipcheck([])
    sys.exit(c.exec())
