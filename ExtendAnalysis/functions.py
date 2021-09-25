import os
import sys

__home = os.getcwd()
sys.path.append(__home)


def home():
    return __home
