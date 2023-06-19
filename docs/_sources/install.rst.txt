Installation
=============================

System requirements
-------------------------
- Python (version >= 3.6) installed.
- X11 client installed. For windows users using Windows Subsystem for Linux, it is recommended to use xvcsrv (https://sourceforge.net/projects/vcxsrv/) as X11 client.

Before installation
--------------------------
It is encouraged to use virtual environment to avoid conflict. You can skip this section if you want to install lys directly.

1. Open shell (we assume bash in linux). Go to home directory (or arbitrary directory you want to create virutual environment).

2. Create .venv directory and create "lys" (or arbitrary name you want) environment::

    mkdir .venv
    cd .venv
    python -m venv lys

3. Activate the environment::

    source lys/bin/activate

Installation
------------------------

1. Update pip::

    pip install --upgrade pip

2. Install lys by pip::

    pip install lys

3. Start lys by the commande below. Note that the current directory of the system is used as the working directory of lys::

    python -m lys

4. If you want to enable parallel computing, start *lys* with -n option::

    python -m lys -n [number of cores]


Library version
-------------------------

We confirmed that *lys* works well under the environment below. If *lys* does not work, try the library versions below.

- OS: AlmaLinux 8.3
- Python 3.6.8

- numpy 1.19.5
- scipy 1.5.4
- opencv-python-headless 4.5.5.64
- dask 2021.3.0
- dask-image 2021.12.0
- matplotlib 3.3.4
- pyqtgraph 0.11.1
- PyQt5 5.15.6
- qtpy 2.0.1
- autopep8 1.6.0

Unittest
---------------

Go to lys install directory, and run the code below::

    python -m unittest discover