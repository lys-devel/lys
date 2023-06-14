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

`lys` is a Python-based multi-dimensional data analysis and visualization tool based on the several popular . 

# Statement of need

Data analysis and visualization are indispensable parts of the scientific research. Undestanding the experimental and simulated data deeply is essentially important for extracting complex phenomena behind them. To this end, intuiitive and fast analysis and visualization is highly required. In the scientific Python ecosystems, flexible and fast analysis of numerical arrays have been done by several poplar libraries such as `numpy`[ref], `scipy`[ref], `dask`[ref] combined with visualization tools such as `matplotlib`[ref], `pyqtgraph`[ref] and `Mayavi`[ref]. Recent development of `Jupyter Notebook` [ref] and related libraries further enhance the capability of interactive data analysis. However, most of these libraries requires users to be familier with low-level application programming interfaces (APIs), preventing intuitive analysis and visualization. In particular, when the analyzed data is more than 3-dimensional array, even simple visualization requires Python code of tens of lines. Such on-demand analysis and visualization programs should be modified (and tested) when the dimension of data is changed although very similar process is very frequently applied to data with different dimension. Furthermore, the code for such analysis should be preserved to guarantee the reproducibility of the scientific results.

The multi-dimensional data analysis system `lys` offers graphical user interface (GUI) system for intuitive analysis and visualization for multi-dimensional array based on `PyQt` [ref]. It employs `dask` as a backend, which can be used for the easy parallel calculation in high-performance clusters (HPCs). Publication-quality and fast Data visualizations are realized by matplotlib and pyqtgraph, respectively. `lys` is a low-code system where most analysis and visualization process can be done from GUI without any knowledge regarding these libraries. In particular, a tool for interactive and fast analysis of multi-dimensional array is realized, by which all analysis process can be exported as a single file for reproducibility. In contrast to the such user-friendly GUI interface, `lys` can be easily extended because it employes hybrid CUI/GUI architecture. Users can edit and run their own Python code in `lys` to extend and support the functionarities of `lys`. 

# Overview

`lys` is a hybrid GUI/CUI platform oriented for the multi-dimensional data analysis. Figure 1 shows main features of `lys`. Arbitrary Python commands can be executed from integrated Python shell (#1). Python scripts can be edited by the internal editor. Matplotlib graphs that contains curves, images, vector fields, and RGB images can be displayed (#3) and edited via GUI in sidebar (#4). 

`MultiCut` is a central tool in `lys`, which enables intuitive, low-code, parallel, flexible, and extensible analysis for multi-dimensional array. Figure 2 shows GUI and flow of data processing for four-dimensional data $A(i,j,k,l)$, where $i,j,k,l$ represents indice of the array. The data analysis in `MultiCut` is done in three step. First, the original data $A$ is modified by preprocess as $A'=P_1(A)$. For example, 

カット、ポストプロセス
全てdaskで実行するが、preprocessの後でpersistされる
pre, cut, postprocessの組がフレキシブルなデータ解析を可能にする


# Projects Using lys



# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

We acknowledge contributions from Brigitta Sipocz, Syrtis Major, and Semyeong
Oh, and support from Kathryn Johnston during the genesis of this project.

# References