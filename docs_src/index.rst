.. lys documentation master file, created by
   sphinx-quickstart on Thu Sep 23 22:03:39 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

lys documentation
===============================

*lys* is a Python-based multi-dimensional data analysis and visualization platform based on the several popular libraries such as numpy, dask, matplotlib, and Qt. 

To use *lys*, go to :doc:`install` and :doc:`tutorials/tutorial`.

What can *lys* do in visualization:

- Publication-quality visualization of 1D and 2D data, which can be edited by GUI interface.
- Interactive, intuitive, and flexible visualization of multi-dimensional (> 3D) data based on GUI.
- Creating an animation based on the multi-dimensional data.
- Saving graphics in editable format, or standard vector/raster format (png, eps, pdf, ...).

What can *lys* do in analysis:

- Applying pre-defined and user-defined processes (such as smoothing, interpolation, fast Fourier transform, and integration) to multi-dimensional data.
- Exporting arbitrary data analysis as a file, which can be used to reproduce the scientific result.
- Executing arbitrary Python command in CUI interface, supporting flexible analysis.
- Standard fitting for 1D data.

Characteristics of *lys*:

- Low code: Most of operation can be done without coding.
- Intuitive: GUI-based visualization and analysis for users who does not familier with scientific Python libraries.
- Parallelized: Automatic parallel computation using *dask* can be done in high-performance computers.
- Extendable: Both CUI and GUI can be customized by users.
- Open source: Free to use. You can confirm what is done in lys and change it.



.. toctree::
   :maxdepth: 1
   :caption: Contents:

   install
   tutorials/tutorial
   api
   contributing

