Loading various data
==================================================

These are examples Python codes to load several types of data format.
To try these examples, simply download the .py files and put it in *module* folder of your working directory.
Then you can load corresponding files by *load* function as follows::

    from lys import *
    data = load("Replace this string with your filename to be loaded")

It is noted that the Python codes in this page is not fully tested. So there may be bugs.
If you want to make your own file loader, see :doc:`newLoader`

.. contents:: List of examples
   :depth: 2
   :local:

Gatan Digital Micrograph .dm3 files 
----------------------------------------

Install dm3_lib(https://bitbucket.org/piraynal/pydm3reader/src/master/) and put :download:`examples/load_dm3.py` into *module* folder.

.. literalinclude:: examples/load_dm3.py
    :language: Python
    :linenos:

WaveMetrics Igor .pxt files
-----------------------------------------

Install igor package(https://pypi.org/project/igor/) by excuting::

    pip install igor

Then put :download:`examples/load_PXT.py` into *module folder*.

.. literalinclude:: examples/load_PXT.py
    :language: Python
    :linenos:

DICOM .dicom files
----------------------------------------

Install pydicom package(https://github.com/pydicom/pydicom) by executin::

    pip install pydicom

Then put :download:`examples/load_DICOM.py` into *module folder*.

.. literalinclude:: examples/load_DICOM.py
    :language: Python
    :linenos:
