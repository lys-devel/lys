from setuptools import setup, find_packages
import sys
from pathlib import Path
sys.path.append('./lys')
sys.path.append('./test')


this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name="lys-python",
    packages=find_packages(exclude=("test*",)),
    package_data={"lys.resources": ["*.dic", "images/*.png"]},
    version="0.3.6",
    description="Interactive multi-dimensional data analysis and visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Asuka Nakamura",
    author_email="lys.devel@gmail.com",
    url="https://github.com/lys-devel/lys",
    license="GNU GPLv3",
    install_requires=open('requirements.txt').read().splitlines(),
)
