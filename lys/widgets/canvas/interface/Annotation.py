import warnings
import numpy as np

from lys.Qt import QtCore

from lys.errors import NotImplementedWarning
from .LineAnnotation import LineAnnotation, InfiniteLineAnnotation
from .RectAnnotation import RectAnnotation
from .RegionAnnotation import RegionAnnotation, FreeRegionAnnotation
from .CrossAnnotation import CrossAnnotation
from .TextAnnotation import TextAnnotation
from .CanvasBase import CanvasPart, saveCanvas


class CanvasAnnotation(CanvasPart):
    """
    Interface to add, remove, and get annotations in canvas.

    All public methods in this class can be accessed from :class:`.CanvasBase.CanvasBase`.

    Args:
        canvas(.CanvasBase.CanvasBase): The parent canvas.
    """
    _axisDict = {1: "BottomLeft", 2: "TopLeft", 3: "BottomRight", 4: "TopRight", "BottomLeft": "BottomLeft", "TopLeft": "TopLeft", "BottomRight": "BottomRight", "TopRight": "TopRight"}
    annotationChanged = QtCore.pyqtSignal()
    """pyqtSignal that is emitted when annotations are added or removed."""

    def __init__(self, canvas):
        super().__init__(canvas)
        self._annotations = []
        self.canvas().saveCanvas.connect(self.__saveLines)
        self.canvas().loadCanvas.connect(self.__loadLines)
        self.canvas().saveCanvas.connect(self.__saveInfiniteLines)
        self.canvas().loadCanvas.connect(self.__loadInfiniteLines)
        self.canvas().saveCanvas.connect(self.__saveRect)
        self.canvas().loadCanvas.connect(self.__loadRect)
        self.canvas().saveCanvas.connect(self.__saveRegion)
        self.canvas().loadCanvas.connect(self.__loadRegion)
        self.canvas().saveCanvas.connect(self.__saveFreeRegions)
        self.canvas().loadCanvas.connect(self.__loadFreeRegions)
        self.canvas().saveCanvas.connect(self.__saveCross)
        self.canvas().loadCanvas.connect(self.__loadCross)
        self.canvas().saveCanvas.connect(self.__saveText)
        self.canvas().loadCanvas.connect(self.__loadText)

    def __getRange(self, dir, axis):
        if dir == "x":
            if 'Bottom' in axis:
                return self.canvas().getAxisRange('Bottom')
            else:
                return self.canvas().getAxisRange('Top')
        else:
            if 'Left' in axis:
                return self.canvas().getAxisRange('Left')
            else:
                return self.canvas().getAxisRange('Right')

    def __addObject(self, obj, appearance):
        obj.setZOrder(20000)
        self._annotations.append(obj)
        obj.loadAppearance(appearance)
        self.annotationChanged.emit()
        return obj

    @saveCanvas
    def addLineAnnotation(self, pos="auto", axis="BottomLeft", **appearance):
        """
        Add line annotation.

        Args:
            pos(2*2 sequence): The position of the line in the form of [(x0, y0), (x1 ,y1)]
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the line annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            LineAnnotation: The annotation added.
        """
        if pos == "auto":
            rl = self.__getRange("y", axis)
            rb = self.__getRange('x', axis)
            db = (np.max(rb) - np.min(rb))
            dl = (np.max(rl) - np.min(rl))
            start = (np.min(rb) + db / 2, np.min(rl) + dl / 2)
            end = (start[0] + db / 10, start[1] + dl / 10)
            pos = (start, end)
        obj = self._addLineAnnotation(pos, axis)
        return self.__addObject(obj, appearance)

    def getLineAnnotations(self):
        """
        Return list of all line annotations in canvas.

        Return:
            list: list of :class:`.LineAnnotation.LineAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, LineAnnotation)]

    def __saveLines(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getLineAnnotations()):
            dic[i] = {}
            pos = data.getPosition()
            dic[i]['Position0'] = list(pos[0])
            dic[i]['Position1'] = list(pos[1])
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['annot_lines'] = dic

    def __loadLines(self, dictionary):
        if 'annot_lines' in dictionary:
            dic = dictionary['annot_lines']
            i = 0
            while i in dic:
                p0 = dic[i]['Position0']
                p1 = dic[i]['Position1']
                p = (p0, p1)
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addLineAnnotation(p, axis, **appearance)
                i += 1

    @saveCanvas
    def addInfiniteLineAnnotation(self, pos=None, orientation='vertical', axis="BottomLeft", **appearance):
        """
        Add infinite line annotation.

        Args:
            pos(float): The position of the line.
            orientation('vertical' or 'horizontal'): The orientation of the line.
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            InfiniteLineAnnotation: The annotation added.
        """
        if pos is None:
            if orientation == 'vertical':
                r = self.__getRange("x", axis)
            else:
                r = self.__getRange("y", axis)
            pos = np.min(r) + (np.max(r) - np.min(r)) / 2
        obj = self._addInfiniteLineAnnotation(pos, orientation, axis)
        return self.__addObject(obj, appearance)

    def getInfiniteLineAnnotations(self):
        """
        Return list of all infinite line annotations in canvas.

        Return:
            list: list of :class:`.LineAnnotation.InfiniteLineAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, InfiniteLineAnnotation)]

    def __saveInfiniteLines(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getInfiniteLineAnnotations()):
            dic[i] = {}
            pos = data.getPosition()
            dic[i]['Position'] = pos
            dic[i]['Type'] = data.getOrientation()
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['annot_infiniteLines'] = dic

    def __loadInfiniteLines(self, dictionary):
        if 'annot_infiniteLines' in dictionary:
            dic = dictionary['annot_infiniteLines']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                t = dic[i]['Type']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addInfiniteLineAnnotation(p, t, axis, **appearance)
                i += 1

    @saveCanvas
    def addRectAnnotation(self, pos='auto', size='auto', axis="BottomLeft", **appearance):
        """
        Add rectangle annotation.

        Args:
            pos(length 2 sequence): The position of the rectangle edge in the form of (x, y).
            size(length 2 sequence): The size of the rectangle in the form of (width, height).
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            RectAnnotation: The annotation added.
        """
        rl = self.__getRange('y', axis)
        rb = self.__getRange('x', axis)
        if pos == 'auto':
            pos = (np.min(rb) + (np.max(rb) - np.min(rb)) / 2, np.min(rl) + (np.max(rl) - np.min(rl)) / 2)
        if size == 'auto':
            size = ((np.max(rb) - np.min(rb)) / 10, (np.max(rl) - np.min(rl)) / 10)
        obj = self._addRectAnnotation(pos, size, axis)
        return self.__addObject(obj, appearance)

    def getRectAnnotations(self):
        """
        Return list of all rectangle annotations in canvas.

        Return:
            list: list of :class:`.RectAnnotation.RectAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, RectAnnotation)]

    def __saveRect(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getRectAnnotations()):
            dic[i] = {}
            dic[i]['Position'] = data.getPosition()
            dic[i]['Size'] = data.getSize()
            dic[i]['Axis'] = data.getAxis()
            dic[i]['Appearance'] = str(data.saveAppearance())
        dictionary['annot_rect'] = dic

    def __loadRect(self, dictionary):
        if 'annot_rect' in dictionary:
            dic = dictionary['annot_rect']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                s = dic[i]['Size']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addRectAnnotation(p, s, axis, **appearance)
                i += 1

    @saveCanvas
    def addRegionAnnotation(self, region=None, orientation='vertical', axis="BottomLeft", **appearance):
        """
        Add region annotation.

        Args:
            region(length 2 sequence): The region in the form of (x1, x2).
            orientation('vertical' or 'horizontal'): The orientation of the annotation.
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            RegionAnnotation: The annotation added.
        """
        if region is None:
            if orientation == 'vertical':
                r = self.__getRange('x', axis)
            else:
                r = self.__getRange('y', axis)
            region = (np.min(r) + (np.max(r) - np.min(r)) * 4 / 10, np.min(r) + (np.max(r) - np.min(r)) * 6 / 10)
        obj = self._addRegionAnnotation(region, orientation, axis)
        return self.__addObject(obj, appearance)

    def getRegionAnnotations(self):
        """
        Return list of all region annotations in canvas.

        Return:
            list: list of :class:`.RegionAnnotation.RegionAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, RegionAnnotation)]

    def __saveRegion(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getRegionAnnotations()):
            dic[i] = {}
            dic[i]['Position'] = data.getRegion()
            dic[i]['Type'] = data.getOrientation()
            dic[i]['Axis'] = data.getAxis()
            dic[i]['Appearance'] = str(data.saveAppearance())
        dictionary['annot_region'] = dic

    def __loadRegion(self, dictionary):
        if 'annot_region' in dictionary:
            dic = dictionary['annot_region']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                t = dic[i]['Type']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addRegionAnnotation(p, t, axis, **appearance)
                i += 1

    @saveCanvas
    def addCrossAnnotation(self, pos='auto', axis="BottomLeft", **appearance):
        """
        Add cross annotation.

        Args:
            pos(length 2 sequence): The position in the form of (x, y).
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            CrossAnnotation: The annotation added.
        """
        if pos == 'auto':
            rb = self.__getRange('x', axis)
            rl = self.__getRange('y', axis)
            pos = (np.min(rb) + (np.max(rb) - np.min(rb)) / 2, np.min(rl) + (np.max(rl) - np.min(rl)) / 2)
        obj = self._addCrossAnnotation(pos, axis)
        return self.__addObject(obj, appearance)

    def getCrossAnnotations(self):
        """
        Return list of all cross annotations in canvas.

        Return:
            list: list of :class:`.CrossAnnotation.CrossAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, CrossAnnotation)]

    def __saveCross(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getCrossAnnotations()):
            dic[i] = {}
            dic[i]['Position'] = data.getPosition()
            dic[i]['Axis'] = data.getAxis()
            dic[i]['Appearance'] = str(data.saveAppearance())
        dictionary['annot_cross'] = dic

    def __loadCross(self, dictionary):
        if 'annot_cross' in dictionary:
            dic = dictionary['annot_cross']
            i = 0
            while i in dic:
                p = dic[i]['Position']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addCrossAnnotation(p, axis, **appearance)
                i += 1

    @saveCanvas
    def addFreeRegionAnnotation(self, region="auto", width='auto', axis="BottomLeft", **appearance):
        """
        Add free region annotation.

        Args:
            region(2*2 sequence): The position of the region in the form of [(x0, y0), (x1 ,y1)]
            width(float): The width of the region.
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            FreeRegionAnnotation: The annotation added.
        """
        if region == "auto":
            rl = self.__getRange("y", axis)
            rb = self.__getRange('x', axis)
            db = (np.max(rb) - np.min(rb))
            dl = (np.max(rl) - np.min(rl))
            start = (np.min(rb) + db / 2, np.min(rl) + dl / 2)
            end = (start[0] + db / 10, start[1] + dl / 10)
            region = (start, end)
        if width == "auto":
            width = np.sqrt((region[1][0] - region[0][0])**2 + (region[1][1] - region[0][1])**2) / 10
        obj = self._addFreeRegionAnnotation(region, width, axis)
        return self.__addObject(obj, appearance)

    def getFreeRegionAnnotations(self):
        """
        Return list of all free region annotations in canvas.

        Return:
            list: list of :class:`.RegionAnnotation.FreeRegionAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, FreeRegionAnnotation)]

    def __saveFreeRegions(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getFreeRegionAnnotations()):
            dic[i] = {}
            pos = data.getRegion()
            dic[i]['Position0'] = list(pos[0])
            dic[i]['Position1'] = list(pos[1])
            dic[i]['Width'] = data.getWidth()
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['annot_freeRegion'] = dic

    def __loadFreeRegions(self, dictionary):
        if 'annot_freeRegion' in dictionary:
            dic = dictionary['annot_freeRegion']
            i = 0
            while i in dic:
                p0 = dic[i]['Position0']
                p1 = dic[i]['Position1']
                p = (p0, p1)
                w = dic[i]['Width']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                self.addFreeRegionAnnotation(p, w, axis, **appearance)
                i += 1

    @saveCanvas
    def addText(self, text, pos='auto', axis="BottomLeft", **appearance):
        """
        Add text annotation.

        Args:
            text(str): The text to be shown.
            pos(length 2 sequence): The position in the form of (x, y).
            axis('BottomLeft', 'BottomRight', 'TopLeft', or 'TopRight'): The axis to which the annotation is added.
            appearance(dict): Appearance dictionary, which is generated by :meth:`.AnnotationData.saveAppearance` method.

        Return:
            TextAnnotation: The annotation added.
        """
        if pos == 'auto':
            pos = (0.5, 0.5)
        obj = self._addTextAnnotation(text, pos, axis)
        return self.__addObject(obj, appearance)

    def getTextAnnotations(self):
        """
        Return list of all text annotations in canvas.

        Return:
            list: list of :class:`.TextAnnotation.TextAnnotation`.
        """
        return [annot for annot in self._annotations if isinstance(annot, TextAnnotation)]

    def __saveText(self, dictionary):
        dic = {}
        for i, data in enumerate(self.getTextAnnotations()):
            dic[i] = {}
            dic[i]['Text'] = data.getText()
            dic[i]['Position'] = data.getPosition()
            dic[i]['Appearance'] = str(data.saveAppearance())
            dic[i]['Axis'] = data.getAxis()
        dictionary['Textlist'] = dic

    def __loadText(self, dictionary):
        if 'Textlist' in dictionary:
            dic = dictionary['Textlist']
            i = 0
            while i in dic:
                t = dic[i]['Text']
                appearance = eval(dic[i]['Appearance'])
                axis = self._axisDict[dic[i]['Axis']]
                pos = dic[i].get('Position', 'auto')
                self.addText(t, pos, axis=axis, **appearance)
                i += 1

    def getAnnotations(self, type="all"):
        """
        Return list of all annotations in canvas.

        Args:
            type(str): The type of annotations ('all', 'text', 'line', 'infiniteLine', 'rect', 'region', 'freeRegion', or 'cross')

        Return:
            list: list of :class:`.AnnotationData.AnnotationData`.
        """
        if type == "all":
            return self._annotations
        if type == "text":
            return self.getTextAnnotations()
        if type == "line":
            return self.getLineAnnotations()
        if type == "infiniteLine":
            return self.getInfiniteLineAnnotations()
        if type == "rect":
            return self.getRectAnnotations()
        if type == "region":
            return self.getRegionAnnotations()
        if type == "freeRegion":
            return self.getFreeRegionAnnotations()
        if type == "cross":
            return self.getCrossAnnotations()

    @saveCanvas
    def removeAnnotation(self, annot):
        """
        Remove annotation from the canvas.

        Args:
            annot(AnnotationData): The annotation removed.
        """
        self._annotations.remove(annot)
        self._removeAnnotation(annot)
        self.annotationChanged.emit()

    def _addLineAnnotation(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addLineAnnotation(pos, axis) method.", NotImplementedWarning)

    def _addInfiniteLineAnnotation(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addInfiniteLineAnnotation(pos, axis) method.", NotImplementedWarning)

    def _addRectAnnotation(self, pos, size, axis):
        warnings.warn(str(type(self)) + " does not implement _addRectAnnotation(pos, size, axis) method.", NotImplementedWarning)

    def _addRegionAnnotation(self, region, orientation, axis):
        warnings.warn(str(type(self)) + " does not implement _addRegionAnnotation(region, orientation, axis) method.", NotImplementedWarning)

    def _addFreeRegionAnnotation(self, region, width, axis):
        warnings.warn(str(type(self)) + " does not implement _addRegionAnnotation(region, width, axis) method.", NotImplementedWarning)

    def _addCrossAnnotation(self, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addCrossAnnotation(pos, axis) method.", NotImplementedWarning)

    def _addTextAnnotation(self, text, pos, axis):
        warnings.warn(str(type(self)) + " does not implement _addTextAnnotation(text, pos, axis) method.", NotImplementedWarning)

    def _removeAnnotation(self, obj):
        warnings.warn(str(type(self)) + " does not implement _removeAnnotation(obj) method.", NotImplementedWarning)