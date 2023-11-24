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
    affiliation: 1
affiliations:
 - name: RIKEN Center for Emergent Matter Science, Japan
   index: 1
date: 29 June 2023
bibliography: paper.bib

---

# Summary

Analyzing and visualizing scientific data is an essential part of scientific research, by which researchers investigate complex phenomena behind it. In particular, the recent development of an open-source scientific Python ecosystem enables us to utilize state-of-the-art analysis and visualization. However, investigation of multi-dimensional data array still requires substantial coding, preventing intuitive and flexible analysis/visualization. `lys` is a Python-based multi-dimensional data analysis and visualization platform, which provides graphical user interfaces (GUI) to intuitively and flexibly manipulate multi-dimensional data arrays and publication-quality graphics. Massive multi-dimensional data over hundreds of gigabytes can be analyzed via automatic parallel calculation behind the GUI when `lys` is run in high-performance computers (HPCs). As well as the user-friendly GUIs, `lys` also provides flexibility for experts through its character user interface (CUI). The hybrid GUI/CUI architecture in `lys` enables an intuitive, low-code, parallel, flexible, and extensible multi-dimensional data analysis. `lys` is designed as a versatile data analysis and visualization platform that can handle all analysis processes from data loading to publication-quality figure generation. These features of `lys` enable us to minimize the time required for data analysis and visualization for a broad range of users.

# Statement of need

Data analysis and visualization are indispensable parts of scientific research. Understanding experimental and simulated data deeply is essential for extracting complex phenomena behind them. To this end, intuitive and fast analysis/visualization is highly required. There are several well-known software that focus on analysis and visualization, such as IGOR Pro (WaveMetrics, RRID: SCR_000325) and MATLAB (MathWorks, RRID: SCR_001622) as well as domain-specific software in respective fields. Although they have been utilized for scientific research for a long time, recent progress in experimental/computational methods has changed the situation. The data sizes obtained from experiments and calculations have increased rapidly over the past decade, reaching more than terabytes in many fields. As a result, the general analysis ecosystem maintained by the large scientific open-source community has an advantage in state-of-the-art analysis compared to proprietary/domain-specific software. Python and related scientific libraries are one of the most popular analysis/visualization environments at the moment. In the scientific Python ecosystem, flexible and fast analysis of numerical arrays has been done by several popular libraries such as `numpy` [@harris2020array], `scipy` [@2020SciPy-NMeth], `dask` [@rocklin2015dask] combined with visualization tools such as `matplotlib` [@Hunter:2007], `pyqtgraph` [@pyqtgraph] and `Mayavi` [@ramachandran2011mayavi]. Development of `Jupyter Notebook` [@Kluyver2016jupyter] and related libraries further enhance the capability of interactive data analysis. However, most of these libraries require users to be familiar with low-level application programming interfaces (APIs), which prevents intuitive analysis and visualization. In particular, when the analyzed data is a more than 3-dimensional array, even simple interactive visualization usually requires Python code of tens of lines. Such on-demand analysis and visualization programs should be modified (and tested) when the data change, although a very similar process is frequently applied to data with different dimensions. Furthermore, the code for such an analysis should be preserved to guarantee the reproducibility of scientific results. To solve these problems, several Python-based tools such as  `data-slicer` [@Kramer2021] and `napari` [@chiu_clack_2022] have been developed. Although both of them offer sophisticated GUIs, they are not designed as a general research platform. `data-slicer` focuses on quick data inspection and visualization rather than publication-quality figure generation. `napari` is mainly developed for multi-dimensional image data, and therefore visualization of other data types such as curves, contours, vectors are limited. In such situations, a versatile Python-based analysis and visualization platform that can handle all scientific analysis processes, from data loading to publication-quality figure generation of a variety of data types, is highly required.

The multi-dimensional data analysis and visualization platform, `lys`, offers a graphical user interface (GUI) for intuitive analysis and visualization of multi-dimensional arrays. It employs `dask` as a backend, which can be used for easy parallel calculations on high-performance clusters (HPCs). Publication-quality and fast data visualizations are provided by matplotlib and pyqtgraph, respectively. `lys` is a low-code system where most analysis and visualization processes can be done from the GUI without any knowledge of respective libraries. In particular, a tool for interactive and fast analysis of multi-dimensional arrays has been developed. This tool allows all analysis processes to be exported as a single file, ensuring scientific reproducibility. In contrast to such a user-friendly GUI, `lys` can be easily extended because it employs a hybrid CUI/GUI architecture. Users can edit and run their own Python code in `lys` to extend the functionalities of `lys`. 

The philosophy of lys is to serve as a versatile data analysis and visualization platform, rather than a basic image viewer/analysis program. It was developed to minimize the time required for data analysis and visualization for researchers. All of the processes from loading data to generating publication-quality figures can be done in `lys`. In addition, these processes (including user-defined Python code) are stored in a single directory and can be used to reproduce the results. The rich features of `lys` significantly reduce the time for analysis/visualization of multi-dimensional arrays.

# Overview

`lys` is a hybrid GUI/CUI platform oriented towards multi-dimensional data analysis. Figure 1 shows the main features of `lys`. Arbitrary Python commands can be executed from an integrated Python shell (#1). User-defined Python scripts can be edited by the internal editor (#2) and can be executed. Matplotlib graphs that contain curves, images, vector fields, and RGB images can be displayed (#3) and edited via GUI in the sidebar (#4). 

`MultiCut` is a central tool in `lys`, which enables intuitive, low-code, parallel, flexible, and extensible analysis for multi-dimensional arrays. In the following, the data analysis and visualization processes are explained, using three-dimensional movie data $A(x_i,y_j,t_k)$ as an example ($i,j,k$ represent indices of the array). The data analysis in `MultiCut` is done in four steps. First, the original $N$-dimensional data $A$ is modified by preprocessing as $A' = P(A)$, where $P$ is an arbitrary function that translates $N$ dimensional data to $M$ dimensional data. In the example case in Fig. 2, impulsive noise in the original data is removed using $3 \times 3 \times 3$ median filter: 

$$A'(x_i,y_j,t_k) = \mathcal{M}[A(x_i,y_j,t_k)],$$

![Screenshot of lys. Users can execute arbitrary Python commands from embedded CUI (#1), which can be extended by the user-defined scripts (#2). Matplotlib figures that contain curves, images, vector fields, and RGB images can be displayed (#3). These figures can be edited via GUI in the sidebar (#4).](Fig1.png)

where $P = \mathcal{M}$ represents median filter to remove the noise. Since the median filter does not change the dimension of data, $N=3$ equals $M$ in this case. The preprocessing is used for heavy analysis that requires whole $N$-dimensional data. Second, MultiCut generates an arbitrary number of 2-dimensional images and 1-dimensional curves from $M$-dimensional $A'$ by taking a summation along arbitrary axes. In the example case in Fig. 2, an image $I(x_i,y_j)$ and a curve $C(t_k)$ is generated as:

$$
\begin{aligned}
I(x_i,y_j) &= \sum_{t_k}A'(x_i,y_j,t_k), \\
C(t_k) &= \sum_{x_i, y_j}A'(x_i,y_j,t_k).
\end{aligned}
$$

The range of the summation is specified from the GUI as described later. These images and curves are used for visualization in step 4. Third, each image and curve can be individually modified by postprocessing. In Fig. 2, Fourier transformation along time axis $\mathcal{F}_t$ is applied to time-dependent image intensity $C(t_k)$:

$$
C'(\omega_l) = \mathcal{F}_t[C(t_k)].
$$

Different from the preprocessing (step 1), the postprocessing function accesses only an image or a curve. In addition, the postprocessing should be executed within a short time (< 0.1 s) because it is repeatedly called whenever the summation range in step 2 is changed. Finally, these analyzed data are displayed in a GUI, where users can modify the ranges of the summation interactively. Once the summation range from step 2 is changed, the postprocess is recalculated and the result is automatically updated. Such four-step calculation enables flexible analysis of multi-dimensional data. In the above example, the spectrum of the image intensity $C'(\omega_l)$ within the user-specified image region can be interactively analyzed and displayed while the time-consuming median filter is done only once in step 1. It should be noted that a multi-dimensional array of arbitrary dimensions can be analyzed and visualized by `MultiCut` although the given example is for a 3-dimensional case. Constructing such an interactive analysis system is a hard task in conventional Python systems. Once the interactive analysis system is set up using MultiCut, the settings for the analysis can be exported as a file and reused. This guarantees the scientific reproducibility of the data analysis, which can be verified by other scientists. In addition, all of the processes in `lys` are implemented using `dask` arrays, and therefore all calculations can be performed in parallel when they are done on HPC systems.

![Example for 3-dimensional time-dependent data analysis and visualization by MultiCut. The median filter is applied to the original data (Step 1), from which several curves and images are generated (Step 2). Each curve and image are independently processed in Step 3, and visualized in a single GUI window (Step 4).](Fig2.png)

In addition to the features described above, `lys` provides some basic analysis such as data fitting and array editor GUIs. Combining these functionalities of `lys` offers intuitive, low-code, fast, and flexible analysis to users not familiar with Python while preserving the extensibility for experts.

As compared to other analysis/visualization software, `lys` has several advantages. First, it employs Python (`numpy`/`dask`) as a backend, and therefore variety of scientific computing libraries such as `scipy` can be used. This cannot be achieved by similar software such as `Igor Pro` and `Matlab`. Second, `lys` is an open-source software. Users can verify the software and modify it if needed, which cannot be realized in proprietary software. Third, `lys` offers interactive GUIs represented by `MultiCut`. Although there has been much effort to realize sophisticated GUIs such as `napari` [@chiu_clack_2022] and `data-slicer` [@Kramer2021], it is still very limited in the scientific Python ecosystems so far. Fourth, `lys` can treat massive multi-dimensional arrays of more than hundreds of gigabytes through `dask`. The coexistence of intuitive GUI and fast parallel calculation is very limited in other similar software/libraries so far. Finally, `lys` is a general platform for data analysis and visualization. All of the processes from loading data to generating publication-quality figures can be done in `lys`. Although `data-slicer` offers similar and interactive data manipulation, it is data inspection and visualization software rather than the general platform for research scientists. `napari` also offers similar functionalities for multi-dimensional images, `lys` is designed to handle a variety of data types (images, curves, contours, vector fields, and RGB images) to serve as a general-purpose platform. 

# Projects using the software

As `lys` is a general-purpose multi-dimensional data analysis system, it has been used in many works within the last five years, particularly for our experiments and simulations. Simple visualization functionalities are used for the analysis of movies obtained by ultrafast electron diffraction and microscopy [@APEX2018;@NanoLett2020]. A pre-release version of MultiCut was used for analyzing the propagation of nanometric acoustic waves [@NanoLett2023] and magnetic-texture dynamics [@SciAdv2021]. Analyzing massive five-dimensional data sets obtained by five-dimensional scanning transmission electron microscopy [@Faraday2022;@RSI2023;@JMicro2023] was also achieved using parallel calculations on an HPC, demonstrating the scalability of `lys`. It was also used for the postprocessing of finite-element simulation results [@StrDyn2021].


# Acknowledgements

We acknowledge contributions from Yusuke Chiashi, Jumpei Koga, Dongxue Han, and comments from Takahiro Shimojima and Kyoko Ishizaka. This work was partially supported by a Grant-in-Aid for Scientific Research (KAKENHI) (Grant  No.  21K14488). 

# References