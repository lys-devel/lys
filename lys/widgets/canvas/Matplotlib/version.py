import matplotlib
import numpy as np

if not hasattr(matplotlib.cm, "get_cmap"):
    matplotlib.cm.get_cmap = lambda name: matplotlib.colormaps[name]
