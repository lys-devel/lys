Interactive GUI analysis system MultiCut
==============================================

MultiCut is a GUI tool implemented in *lys*. Itenables users to efficiently visualize and analyze multi-dimensional arrays.

Use default template
----------------------------

1. Load sample data by typing the code below in the command line of main window::

    data = resources.gauss_3d_data()

2. Open MultiCut by the command below. You will find an empty window (MultiCut window) and "MultiCut" tab in sidebar.::

    multicut(data)

3. Click "Template" button in the sidebar.

.. image:: ./image_mcut/MultiCutTab.png

4. In the dialog box, confirm that the "Default" is displayed in Information and click "OK" at the bottom.

.. image:: ./image_mcut/template1.png

5. Click "Yes" in the message box.

.. image:: ./image_mcut/template2.png

6. The analyzed data is shown in the MultiCut window. The original data is a sequence of 2D gaussian image with noise. The central position of gaussian is moved depending on the 3rd-axis. 
The top image is one of the gaussian image at the line in the bottom window. And the bottom curve represents integrated intensity inside the rectangle of top window.

.. image:: ./image_mcut/mcut1.png
    :scale: 50%

7. When you change the position of the line in the bottom figure, the gaussian image is changed. Similarly, when you change the position of rectangle in top window, the bottom curve is changed.
These functionarities are very useful to visualize multi-dimensional data more than 3D.


Manually setup MultiCut
---------------------------------

1. The default template is powerfull but non-flexible way to use MultiCut. Try to setup MultiCut manually. You can close MultiCut window if it is still opened.

2. Open MultiCut by the command below::

    multicut(resources.gauss_3d_data())

3. Click "Add" button in the main tab in the sidebar. A dialog box is opened.

.. image:: ./image_mcut/add1.png
    :scale: 50%

4. In the dialog box, set the following parameters, and press "OK". The parameters means the "image1" is 2D image whose axes are 1st and 2nd axes of original 3D data.

- Name: image1
- Dimension: 2 (default)
- Axis1: 1 (default)
- Axis2: 2 (default)

.. image:: ./image_mcut/add2.png

5. You are asked to select where to display the data in MultiCut window. Select like the image below. Orange region is selected.

.. image:: ./image_mcut/add3.png
    :scale: 50 %

6. Go to "Range" tab in the sidebar and change a slider for "Axis 3". The "image1" is changed. Since "image1" is along 1st and 2nd axes, changing sliders of axis 1 and 2 do not affect "image1".

.. image:: ./image_mcut/add4.png

7. Go back to "Main" tab and click "Add" button. In the dialog box, set the following parameters. This means "curve1" is 1D curve whose axis is along 3rd axis of original 3D data.

- Name: curve1
- Dimension: 1
- Axis1: 2

.. image:: ./image_mcut/add5.png

8. Press "OK" in the dialog and select region to show data.

.. image:: ./image_mcut/add6.png
    :scale: 50 %

9. Since "curve1" is along the 3rd axis of the original data, it is changed when you change Axis 1 and 2 in the "Range" tab.

.. image:: ./image_mcut/add7.png

10. It is useful to add annotations that are synchronized with the contents of "Range" tab. Click the top image in MultiCut window, and click "Rect" in "Main" tab.

.. image:: ./image_mcut/add8.png

11. When you change the position of the rectangle annotation in top graph, values in "Range" tab is synchronously changed.

.. image:: ./image_mcut/add9.png

12. Click bottom figure in the MultiCut window and click "Line (X)" button in the "Main" tab. You can edit the value of "Axis 3" from the line annnotation.

.. image:: ./image_mcut/add10.png

13. It's done! All you do in this section is identical to use default template.


Cut along free line
------------------------------------

1. *lys* can cut the image along arbitrary line in an interactive way. Close old MultiCut window it is still opended.

2. Open MultiCut by the command below::

    multicut(resources.gauss_3d_data())

3. From the "Add" button in the sidebar, add an image by setting below.

- Name: image1
- Dimension: 2 (default)
- Axis1: 1 (default)
- Axis2: 2 (default)

.. image:: ./image_mcut/line1.png
    :scale: 50%

4. We want to cut this image along arbitrary direction. Click the image in the MultiCut window and click "Free Line" in the sidebar.

.. image:: ./image_mcut/line2.png

5. It is hard to see the annotation. Double click the image in the MultiCut window to open graph setting.

.. image:: ./image_mcut/line3.png

6. Go to "images" tab, select data1, and change colormap to "GnBu".

.. image:: ./image_mcut/line4.png

7. There is a annotation that you can change position freely. Set the position of the annotation to cross gaussian. You can move the annotation by drag and drop.

.. image:: ./image_mcut/line5.png
    :scale: 50%

8. Go back to "MultiCut" tab in the sidebar, and click "Lines" tab.
.. image:: ./image_mcut/line6.png

9. You can edit the position and width of line. Set the parameters below. This means the annotation is between (x0,y0)=(0,-4) and (x1,y1)=(0,4).

- Point 0: 0, -4
- Point 1: 0, 4

.. image:: ./image_mcut/line7.png

10. Go back to "Main" tab, and click "Add" button.

.. image:: ./image_mcut/line8.png

11. In the dialog box, set the parameters below.

- Name: fline1
- Dimension: 1
- Axis1: Line (Line0)

.. image:: ./image_mcut/line9.png
    :scale: 50%

12. Click OK and select where to show the graph.

.. image:: ./image_mcut/line10.png
    :scale: 50%

13. You see the line profile along the annotation. When you change the position of annotation, data is automatically updated.

.. image:: ./image_mcut/line11.png

14. Confirm that the data is also changed when you change the value of 3rd axis in "Range" tab.

15. It's done! You can cut the image along arbitrary line.

Apply filter
------------------------------

1. The tutorials above are just visualization of multi-dimensional data. MultiCut also enables you to analyze data. Close old MultiCut window it is still opended.

2. Open MultiCut by the command below::

    multicut(resources.gauss_3d_data())

3. Click "Template" in the "Main" tab. Click "OK" to apply default template. You see an image and a curve. 

.. image:: ./image_mcut/filt1.png

4. The image is a bit noizy. We want to smooth data along 1st and 2nd axes.

5. Go to "Filter" tab, right click in the "Filters" box. Select "Add a filter"

.. image:: ./image_mcut/filt2.png

6. In *lys*, we call an analysis process as "filter". You see list of filters that can be applicable to the data in the dialog box. 

.. image:: ./image_mcut/filt3.png
    :scale: 50%

7. Select "Smoothing"-"Median" to apply median filter. Click "OK".

.. image:: ./image_mcut/filt4.png
    :scale: 50%

8. The median filter is added to the "Filters" box. Click "Apply filters" at the bottom.

.. image:: ./image_mcut/filt5.png

9. The data is smoothed by median filter.

.. image:: ./image_mcut/filt6.png
    :scale: 50%

10. It's done! You can add arbitrary number of filters sequencially. List of filters implemented in *lys* is given in :doc:`../lys_/filters`. When you want to add your own filter, see :doc:`newFilter`.

Postprocessing
-----------------------

1. The filter can be applied to the analysis result, not to the original data. Close old MultiCut window it is still opended.

2. Open MultiCut by the command below::

    multicut(resources.gauss_3d_data())

3. Click "Template" in the "Main" tab. Click "OK" to apply default template. You see an image and a curve. 

4. You want to smooth only the curve and compare it with original one. Click "Add" button in "Main" tab. Set the parameters below.

- Name: smoothed
- Dimension: 1
- Axis1: 3
- Uncheck "Display generated data"

.. image:: ./image_mcut/post1.png

5. To apply smoothing, click "Postprocess" at the right-bottom edge. Add "Median Filter" in "Smoothing".

.. image:: ./image_mcut/post2.png

6. Click "OK". You see "smoothed" is added in the list in the sidebar.

.. image:: ./image_mcut/post3.png

7. Click the bottom graph in MultiCut window, and right click "smoothed" in the list. You see context menu.

.. image:: ./image_mcut/post4.png

8. Select "Connected"-"Append". This will append the data to the last-clicked graph.

.. image:: ./image_mcut/post5.png

9. You see smoothed data is shown in the bottom graph. When you change the rectangle annotation in the top graph, both curves changes at the same time.

.. image:: ./image_mcut/post6.png

10. It's done! The postprocess greatly enhance the analysis flexibility.

11. (You can skip this part) The image below shows processing flow of MultiCut, for your information. When one of the filter, range, lines, or postprocess ischanged, corresponding data is automatically updated.

.. image:: ./image_mcut/post7.png

12. (You can skip this part) The generated data is displayed or appended in MultiCut window. This process is almost independent of dat processing part above. Therefore it is also possible to add same data to different graph.

.. image:: ./image_mcut/post8.png

Make your own template
------------------------------------

1. Once you set up the analysis on MultiCut, it can be saved as template. Do not close the MultiCut window in the previous section. 

2. Click "Template" button in the sidebar. You see "Template Manager".

.. image:: ./image_mcut/template3.png

3. Right click the list box at the left-edge, and select "Save present state".

.. image:: ./image_mcut/template4.png

4. Usually, default setting works well. Click "OK". If you want to integrated range in "Range" tab and free lines in "Lines" tab, you should check them.

.. image:: ./image_mcut/template5.png

5. "template1" is created. Click "CANCEL" and close MultiCut window.

.. image:: ./image_mcut/template6.png

6. Open new MultiCut window by the code below::

    multicut(resources.gauss_3d_data())

7. Click "Template" button in the sidebar.

.. image:: ./image_mcut/template7.png

8. Select "template1" and click "OK".

.. image:: ./image_mcut/template8.png

9. It's done! Settings are loaded from the template. You see the smoothed data in Main tab and in the bottom graph.

.. image:: ./image_mcut/template9.png

Create publication-quality figure
----------------------------------------

1. In MultiCut, we use pyqtgraph to show graphs because it is much faster than matplotlib. Close old MultiCut window it is still opended.

2. However, matplotlib is more suitable for publication-quality figure. You should export analysis result to matplotlib figure.

3. Open new MultiCut window by the code below::

    multicut(resources.gauss_3d_data())

4. Apply default template for simplicity.

.. image:: ./image_mcut/export2.png

5. Right click "data1" in the sidebar, select "Copied"-"Display"-"image".

.. image:: ./image_mcut/export1.png
    :scale: 50%

6. It's done, you have the image in matplotlib graph. Data in "Copied" is not updated even when MultiCut parameters are changed.

7. Go back to :doc:`visualization` for further setting of graph.

All tutorial has been done! You can analyze multi-dimensional data using filters and visualize them by MultiCut. 
You can also create publication-quality figures based on the matplotlib graph.

For futher learning, go to Advanced tutorial in :doc:`tutorial`.