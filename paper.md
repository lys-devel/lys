---
title: 'lys: interactive multi-dimensional data analysis and visualization platform'
tags:
  - Python
  - dask
  - matplotlib
  - multi-dimensional data
authors:
  - name: Asuka Nakamura
    orcid: 0000-0002-3010-9475
    equal-contrib: false
affiliations:
 - name: RIKEN Center for Emergent Matter Science, Japan
date: 29 June 2023
bibliography: paper.bib

---

# Summary

`lys` is a Python-based multi-dimensional data analysis and visualization platform based on the several popular libraries such as `numpy`, `dask`, `matplotlib`, and `Qt`. It provides  graphical user interfaces (GUI) to intuitively and flexibly manipulate data array and graphics. In particular, multidimensional ($\ge$ 3D) data can be easily analyzed and visualized via optimized GUI interface, `MultiCut`. All the processes in `MultiCut` are automatically calculated in parallel using `dask` arrays, providing fast data analysis on high-performance computers (HPCs). These GUIs in `lys` offer interactive and low-code data analysis for users not familiar with the application programming interfaces (APIs) of the scientific Python ecosystems. In addition to the user-friendly GUIs, `lys` also provides flexibility for experts through its character user interface (CUI). Arbitrary Python code can be executed in the extended Python interpreter system, which can be integrated into `MultiCut`. The hybrid GUI/CUI architecture in `lys` enables an intuitive, low-code, parallel, flexible, and extensible multi-dimensional data analysis for a broad range of users. 

# Statement of need

Data analysis and visualization are indispensable parts of scientific research. Understanding the experimental and simulated data deeply is essential for extracting complex phenomena behind them. To this end, intuitive and fast analysis/visualization is highly required. In the scientific Python ecosystem, flexible and fast analysis of numerical arrays has been done by several popular libraries such as `numpy`[@harris2020array], `scipy`[@2020SciPy-NMeth], `dask`[@rocklin2015dask] combined with visualization tools such as `matplotlib`[@Hunter:2007], `pyqtgraph`[@pyqtgraph] and `Mayavi`[@ramachandran2011mayavi]. Development of `Jupyter Notebook` [@Kluyver2016jupyter] and related libraries further enhance the capability of interactive data analysis. However, most of these libraries require users to be familiar with low-level application programming interfaces (APIs), which prevents intuitive analysis and visualization. In particular, when the analyzed data is a more than 3-dimensional array, even simple interative visualization requires Python code of tens of lines. Such on-demand analysis and visualization programs should be modified (and tested) when the dimensions of the data change, although a very similar process is frequently applied to data with different dimensions. Furthermore, the code for such an analysis should be preserved to guarantee the reproducibility of scientific results.

The multi-dimensional data analysis and visualization platform, `lys`, offers a graphical user interface (GUI) for intuitive analysis and visualization of multi-dimensional arrays. It employs `dask` as a backend, which can be used for easy parallel calculations on high-performance clusters (HPCs). Publication-quality and fast data visualizations are provided by matplotlib and pyqtgraph, respectively. `lys` is a low-code system where most analysis and visualization processes can be done from the GUI without any knowledge of respective libraries. In particular, a tool for interactive and fast analysis of multi-dimensional array is realized, by which all analysis processes can be exported as a single file for reproducibility. In contrast to such a user-friendly GUI, `lys` can be easily extended because it employs a hybrid CUI/GUI architecture. Users can edit and run their own Python code in `lys` to extend and support the functionalities of `lys`. 

# Overview

`lys` is a hybrid GUI/CUI platform oriented towards the multi-dimensional data analysis. Figure 1 shows main features of `lys`. Arbitrary Python commands can be executed from integrated Python shell (#1). Python scripts can be edited by the internal editor (#2). Matplotlib graphs that contains curves, images, vector fields, and RGB images can be displayed (#3) and edited via GUI in sidebar (#4). 

![Figure 1: Screenshot of lys. Red rectangles (#1-#4) denote main features of lys.](Fig1.png)

`MultiCut` is a central tool in `lys`, which enables intuitive, low-code, parallel, flexible, and extensible analysis for multi-dimensional arrays. Figure 2 shows the flow of data processing for three-dimensional movie data $A(x_i,y_j,t_k)$, where $i,j,k$ represent indices of the array. The data analysis in `MultiCut` is done in four steps. First, the original data $A$ is modified by preprocess. For example, impulsive noise in the original data is removed using median filter: 

$$A'(x_i,y_j,t_k) = \mathcal{M}[A(x_i,y_j,t_k)],$$

where $\mathcal{M}$ represents median filter to remove the noise. Second, MultiCut generates images and curves from $A'$ by taking a summation:

$$
\begin{aligned}
I(x_i,y_j) &= \sum_{t_k}A'(x_i,y_j,t_k), \\
C(t_k) &= \sum_{x_i, y_i}A'(x_i,y_j,t_k). 
\end{aligned}
$$

The range of the summation is specified from the GUI as described later. Third, each piece of data can be individually modified by postprocessing. In Fig. 2(b) Fourier transformation along time axis $\mathcal{F}_t$ is applied to time-dependent image intensity $C(t_k)$:

$$
C'(\omega_l) = \mathcal{F}_t[C(t_k)].
$$

We employed preprocessing (step 1) for heavy analysis that requires whole data while relatively light on-demand work can be done as a postprocessing (step 3). Finally, these analyzed data are displayed in a GUI, where users can modify the ranges of the summation interactively. Once the summation range of Eqs. (1,2) is changed, the postprocess is recalculated and the result is automatically updated. Such four-step calculation enables flexible analysis of multi-dimensional data. In the above example, spectrum of the image intensity $C'(\omega_l)$ within the user-specified image region can be interactively analyzed and displayed. Constructing such interactive analysis system is a hard task in conventional Python systems. Once the interactive analysis system is constructed using MultiCut, the settings for the analysis can be exported as a file and can be reused. This guarantees the scientific reproducibility of the data analysis that can be confirmed by other scientists. In addition, all of the processes in `lys` are implemented using `dask`, and therefore all calculations can be performed in parallel when they are done on HPC systems.

![Figure 2: Data analysis and visualization in MultiCut.](Fig2.png)

In addition to the features described above, `lys` provides some basic analysis such as GUI data fitting and array editor. Combining these functionarities of `lys` offers intuitive, low-code, fast, and flexible analysis to users not familiar with Python while preserving the expansion capability for experts.

# Projects using the software

As `lys` is a general-purpose multi-dimensional data analysis system, it has been used in many works within the last five years, particularly for our experiments and simulations. Simple visualization fucntionarities are used for the analysis of movies obtained by ultrafast electron diffraction and microscopy [@APEX2018;@NanoLett2020]. A pre-release version of MultiCut was used for analyzing propagation of nanometric acoustic waves [@NanoLett2023] and magnetic-texture dynamics [@SciAdv2021]. Analyzing massive five-dimensional data sets obtained by five-dimensional scanning transmission electron microscopy [@Faraday2022;@RSI2023;@JMicro2023] was also achieved using parallel calculations on an HPC cluster, demonstrating the scalability of `lys`. It was also used for the postprocessing of  finite-element simulation results [@StrDyn2021].


# Acknowledgements

We acknowledge contributions from Yusuke Chiashi, Jumpei Koga, Dongxue Han and comments from Takahiro Shimojima and Kyoko Ishizaka. This  work  was  partially  supported  by  a Grant-in-Aid  for  Scientific  Research  (KAKENHI)  (Grant  No.  21K14488). 

# References