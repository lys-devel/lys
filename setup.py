from setuptools import setup
import sys
sys.path.append('./lys')
sys.path.append('./test')

setup(
    name="lys",
    version="0.1.1",
    install_requires=["numpy", "scipy", "opencv-python-headless", "loky", "Pillow", "PyQt5", "matplotlib", "pyqtGraph", "dask[array]", "dask[distributed]", "dask_image", "autopep8"],
)
