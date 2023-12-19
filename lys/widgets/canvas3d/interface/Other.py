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