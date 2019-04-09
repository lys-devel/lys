from setuptools import setup
import sys
sys.path.append('./ExtendAnalysis')
sys.path.append('./test')

setup(
    name="ExtendAnalysis",
    version="0.1.0",
    install_requires=["numpy", "loky", "matplotlib", "opencv-python", "Pillow", "PyQt5", "pyqtGraph", "retry", "scipy", "watchdog"],
    test_suite="ExtendType_test.suite"
)
