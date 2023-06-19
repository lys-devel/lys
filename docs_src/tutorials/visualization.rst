Display graphs in lys
==============================

Plotting an 1D data
---------------------------
1. Type command below to prepare data (You can copy and paste the command below into lys command line)::

    import numpy as np
    x = np.linspace(0,100,101)


2. *display* is a built-in command in *lys* to show data in graph. Type command below to display data::

    display(x)


3. You see a line is displayed in graph.

.. image:: ./image_visualization/Graph1.png

4. Close the graph by clicking x button at the top right edge of the graph.


5. When you want to set the axis, you should use *Wave* class (:class:`lys.core.Wave`)::

    x = np.linspace(-5,5,101)
    y = x**2
    w = Wave(y,x)
    display(w)

6. You can append new curve by *append* method::

    append(Wave(3*x**2, x))

.. image:: ./image_visualization/Graph2.png


Make publication-quality graph by matplotlib
----------------------------------------------------------

1. Left click the graph and select "Graph Settings". Setting window appears in the right sidebar.

.. image:: ./image_visualization/Graph3.png

2. Set the "Width" and "Height" in "Area" tab to "Absolute 5 cm" and "Absolute 3 cm"

.. image:: ./image_visualization/modify1.png
    :scale: 50%

3. Go to "Axis" tab and then set the parameters below.


- Axis Range: -10 to 65
- Tick Setting - Interval: 20
- "Minor" in Tick Setting: Checked
- Set "Interval" below "Minor": 10


Change the combobox at the top to "Bottom", and set the paramteres below.


- Axis Range: -4 to 4
- Tick Setting - Interval: 0 (Auto)
- "Minor" in Tick Setting: Checked
- Set "Interval" below "Minor": 1

.. image:: ./image_visualization/modify2.png
    :scale: 50%

4. Change "Main" tab to "Label". Set the following. You can use tex syntax inside $$.

- Axis Label (Left): $y=ax^2$
- Position (Left): -0.14".
- Axis Label (Bottom): $x$ (m)
- Position (Bottom): -0.14

.. image:: ./image_visualization/modify3.png
    :scale: 50%

5. Goto "Lines" tab and then set the parameters below.

- Color (wave1): Black
- Width of Line (wave1): 1.00
- Color (wave2): Red
- Width of Line (wave2): 3.00

.. image:: ./image_visualization/modify4.png
    :scale: 50%


6. Now you have good publication-quality figure. You can modify most of features in the figure from Setting window.

.. image:: ./image_visualization/modify5.png
    :scale: 50%


Save and export
----------------------------------
1. Press Ctrl+S on the graph and save the graph as "curve.grf".

2. Close the graph by clicking x button at the right-top edge.

3. At the "File" tab in the sidebar, you see "curve.grf". Right click it and select "Load". You will see the graph is loaded.

.. image:: ./image_visualization/Load.png
    :scale: 50%

4. Double click the opened graph and select "Other" in the graph setting. You can export the image as pdf, png, and eps from "Export image" button.

.. image:: ./image_visualization/Export.png
    :scale: 50%

Now you can display, edit, save, and load graph in lys. Go to next step(:doc:`mcut`). For further learning, see tutorials below.

- 2D, vector, contour, and RGB plotting (:doc:`variousData`)