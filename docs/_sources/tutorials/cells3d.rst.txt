Display cells3d data in scikit-image
=======================================================

This example shows how to open four-dimensional array, which is obtained from scikit-image.
After loading and displaying data, we will try to smooth the image.

1. This example requires latest scikit-image. If you have not installed scikit-image, install it before launching `lys`::

    pip install scikit-image

2. Launch `lys` and open cells3d data by `MultiCut` by typing the command below::

    from scikit-image import data
    multicut(data.cells3d())

.. image:: ./image_examples/cell3d1.png

3. The shape of the cells3d data is (z, c, y, x) = (60, 2, 256, 256). Click `Add` button in `MultiCut` tab.

.. image:: ./image_examples/cell3d2.png

4. Set (axis1, axis2) = (3, 4) and click `OK`.

.. image:: ./image_examples/cell3d3.png

5. Select where to display the image.

.. image:: ./image_examples/cell3d4.png

6. Click `Add` button in `MultiCut` tab again. Set the dimension to 1 and axis1 to 1. Click `OK`.

.. image:: ./image_examples/cell3d5.png

7. Select where to display the curve.

.. image:: ./image_examples/cell3d6.png

8. Click the bottom graph and click `Line` button.

.. image:: ./image_examples/cell3d7.png

9. You can change `z` by changing the line annotation. It is also possible to change `z` and `c` by changing slidebar in `Range` tab. It is noted that only 0 or 1 can be set for the axis 2 (c axis).

.. image:: ./image_examples/cell3d8.png

10. Go to `Filter` tab and select `Add Filter` from the right-click menu.

.. image:: ./image_examples/cell3d9.png

11. Select `Smoothing` -> `Average`.

.. image:: ./image_examples/cell3d10.png
    :scale: 50%

12. Set the kernel size to be (1,1,5,5) and click `Apply filters` button. The image will be smoothed.

.. image:: ./image_examples/cell3d11.png
