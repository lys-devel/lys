Copy graphs from lys to vector graphics software
=======================================================

Sometimes it fails to copy graphics from *lys* to vector graphics softwares such as illustrators.
For example, when you use *lys* in Windows Subsystem for Linux (WSL) via X11 servers such as xvcsrv.
This is because PDF/EPS data does not pass through the clipboard via X11 system.
If you can copy and paste graphics from *lys* to vector graphics softwares, you do not need read this page.

To avoid this problem, we developed very primitive tool to enable copy and paste.
We only tested this program on Windows 10 and 11 with WSL although it works for most of environment.

Installation
-----------------------------

- Python code: :download:`lys_clip.pyw` (Save it by right click)
- Binary for windows: :download:`lys_clip.exe`

To use Python code, you have to install Python in windows (not in WSL) and install PyQt5::

    pip install PyQt5

Then simply click lys_clip.pyw after downloading the code. Binary file is also used by clicking the software.

Usage
-------------------
After installation, you can copy the graphics by pressing Ctrl+C on the graph in *lys*.

The message will be shown if the vector graphics has been succesfully copied to clipboard.