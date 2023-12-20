from .CanvasBase import CanvasPart3D


class CanvasUtilities3D(CanvasPart3D):
    """
    Extra canvas utilities.
    """

    def openModifyWindow(self):
        """
        Open graph setting window.
        """
        from lys import glb
        glb.editCanvas3D(self.canvas())


    def duplicate(self):
        """
        Duplicate canvas as a new 3D graph.
        """
        from lys import display3D
        d = self.canvas().SaveAsDictionary()
        g = display3D()
        g.LoadFromDictionary(d)
        return g
