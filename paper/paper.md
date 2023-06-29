---
title: 'lys: interactive multi-dimensional massive data analysis and visualization'
tags:
  - Python
  - dask
  - matplotlib
  - multi-dimensional data
authors:
  - name: Asuka Nakamura
    orcid: 0000-0002-3010-9475
    equal-contrib: true
    affiliation: 1 # (Multiple affiliations must be quoted)
affiliations:
 - name: RIKEN Center for Emergent Matter Science, Japan
   index: 1
date: 13 June 2023
bibliography: paper.bib

---

# Summary

`lys` is a Python-based multi-dimensional data analysis and visualization platform based on the several popular libraries such as `numpy`, `dask`, `matplotlib`, and `PyQt`. It provides  graphical user interfaces (GUI) to intuitively and flexibly manipulate data array and graphics. In particular, multidimensional ($\ge$ 3D) data can be easily analyzed and visualized via optimized GUI interface, `MultiCut`. All the processes in `MultiCut` is automatically calculated in parallel using `dask` array, providing the fast data analysis in high-performance computers (HPCs). These GUIs in `lys` offers interactive and low-code data analysis for users not familiar with the application programming interfaces (APIs) of the scientific Python ecosystems. In addition to the user-friendly GUI interfaces, character user interface (CUI) in `lys` also provides flexiblility for experts. Arbitrary Python code can be executed in the extended Python interpreter system, which can be merged in `MultiCut`. Hybrid GUI/CUI architecture in `lys` enables intuitive, low-code, parallel, flexible, and extensible multi-dimensional data analysis for broad range of users. 

# Statement of need

Data analysis and visualization are indispensable parts of the scientific research. Undestanding the experimental and simulated data deeply is essentially important for extracting complex phenomena behind them. To this end, intuiitive and fast analysis and visualization is highly required. In the scientific Python ecosystems, flexible and fast analysis of numerical arrays have been done by several poplar libraries such as `numpy`[@harris2020array], `scipy`[@2020SciPy-NMeth], `dask`[@rocklin2015dask] combined with visualization tools such as `matplotlib`[@Hunter:2007], `pyqtgraph`[@pyqtgraph] and `Mayavi`[@ramachandran2011mayavi]. Recent development of `Jupyter Notebook` [@Kluyver2016jupyter] and related libraries further enhance the capability of interactive data analysis. However, most of these libraries requires users to be familier with low-level application programming interfaces (APIs), preventing intuitive analysis and visualization. In particular, when the analyzed data is more than 3-dimensional array, even simple visualization requires Python code of tens of lines. Such on-demand analysis and visualization programs should be modified (and tested) when the dimension of data is changed although very similar process is very frequently applied to data with different dimension. Furthermore, the code for such analysis should be preserved to guarantee the reproducibility of the scientific results.

The multi-dimensional data analysis system `lys` offers graphical user interface (GUI) system for intuitive analysis and visualization for multi-dimensional array based on `Qt`. It employs `dask` as a backend, which can be used for the easy parallel calculation in high-performance clusters (HPCs). Publication-quality and fast data visualizations are realized by matplotlib and pyqtgraph, respectively. `lys` is a low-code system where most analysis and visualization process can be done from GUI without any knowledge regarding these libraries. In particular, a tool for interactive and fast analysis of multi-dimensional array is realized, by which all analysis process can be exported as a single file for reproducibility. In contrast to the such user-friendly GUI interface, `lys` can be easily extended because it employes hybrid CUI/GUI architecture. Users can edit and run their own Python code in `lys` to extend and support the functionarities of `lys`. 

# Overview

`lys` is a hybrid GUI/CUI platform oriented for the multi-dimensional data analysis. Figure 1 shows main features of `lys`. Arbitrary Python commands can be executed from integrated Python shell (#1). Python scripts can be edited by the internal editor. Matplotlib graphs that contains curves, images, vector fields, and RGB images can be displayed (#3) and edited via GUI in sidebar (#4). 

`MultiCut` is a central tool in `lys`, which enables intuitive, low-code, parallel, flexible, and extensible analysis for multi-dimensional array. Figure 2 shows GUI and flow of data processing for three-dimensional movie data $A(x_i,y_j,t_k)$, where $i,j,k$ represents indice of the array [Fig. 2(b)]. The data analysis in `MultiCut` is done in three steps. First, the original data $A$ is modified by preprocess as $A'=P_1(A)$. For example, impulsive noise in the original data is removed using median filter: 

$$A'(x_i,y_j,t_k) = \mathcal{M}[A(x_i,y_j,t_k)],$$

where $\mathcal{M}$ represents median filter to remove the noise.
Next, MultiCut generates images and curves from $A'$ by taking a summation:

$$
I(x_i,y_j) = \sum_{\omega_l}A'(x_i,y_j,t_k),\\
C(t_k) = \sum_{x_i}\sum_{y_j}A'(x_i,y_j,t_k).
$$

The range of the summation can be easily specified from GUI. Finally, each data can be indivisually modified by postprocessing. In Fig. 2(?) Fourier transformation along time axis $\mathcal{F}_t$ is applied to time-dependent image intensity $C(t_k)$:

$$
C'(\omega_l) = \mathcal{F}_t[C(t_k)].
$$

Once the summation range of Eqs. () is changed, such postprocess is recalculated and the result is automatically updated. Such three-step calculation enables flexible analysis of multi-dimensional data. In the above example, spectrum of the image intensity $C'(\omega_l)$ within the user-specified image region can be interactively analyzed and displayed in real-time. Construction of such interactive analysis is a hard task in conventional Python systems. Once the interactive analysis system is constructed using MultiCut, the setting for the analysis can be exported as a file and can be reused. This guarantees the scientific reproducibility of the data analysis that can be confirmed by other scientists. In addition, all of the processes in `lys` is implemented using `dask` and therefore all calculations can be performed in parallel when it is done in HPC systems.

In addition to the features described above, `lys` provides some basic analysis such as GUI data fitting and array editor. Combining these functionarities of `lys` offers intuitive, lowcode, fast, and flexible analysis to users not familiar with Python while the expansion capability for experts remains.

# Projects using the software

As the `lys` is a general-purpose multi-dimensional data analysis system, it has been used in many work within the last five years, particularly for our experiments and simulations. Simple visualization fuctionarities are used for the analysis of movies obtained by ultrafast electron diffraction and microscopy [@APEX2018;@NanoLett2020]. A pre-release version of MultiCut was used for analyzing propagation of nanometric acoustic waves [@NanoLett2023] and magnetic-texture dynamics [@SciAdv2021]. Analyzing massive five-dimensional data set obtained by five-dimensional scanning transmission electron microscopy data [@Faraday2022;@RSI2023;@JMicro2023] was also realized using parallel calculation in HPC cluster, showing the scalability of `lys`. It was also used for the postprocess of the finite-element simulation results [@StrDyn2021].

# Figures

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Yusuke Chiashi, Jumpei Koga, Dongxue Han and comments from Takahiro Shimojima and Kyoko Ishizaka. This  work  was  partially  supported  by  a Grant-in-Aid  for  Scientific  Research  (KAKENHI)  (Grant  No.  21K14488). 

# References