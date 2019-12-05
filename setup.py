from setuptools import setup
import sys
sys.path.append('./ExtendAnalysis')
sys.path.append('./test')
sys.path.append('./test/BasicWidgets')

setup(
    name="ExtendAnalysis",
    version="0.1.1",
    install_requires=["numpy", "loky", "matplotlib", "opencv-python", "Pillow", "PyQt5", "pyqtGraph", "retry", "scipy", "watchdog", "dask[array]", "autopep8"],
    test_suite="TestSuite.suite"
)
