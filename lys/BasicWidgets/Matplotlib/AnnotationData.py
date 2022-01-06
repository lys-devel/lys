from ..CanvasInterface import LineAnnotation, TextAnnotation


class _MatplotlibLineAnnotation(LineAnnotation):
    def __init__(self, canvas, pos, axis):
        super().__init__(canvas, pos, axis)
        axes = canvas.getAxes(axis)
        self._obj, = axes.plot((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]), picker=5)

    def _setPosition(self, pos):
        self._obj.set_data((pos[0][0], pos[1][0]), (pos[0][1], pos[1][1]))

    def _setLineColor(self, color):
        self._obj.set_color(color)

    def _setLineStyle(self, style):
        self._obj.set_linestyle(style)

    def _setLineWidth(self, width):
        self._obj.set_linewidth(width)

    def _setZOrder(self, z):
        self._obj.set_zorder(z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)


class _MatplotlibTextAnnotation(TextAnnotation):
    def __init__(self, canvas, text, axis):
        axes = self.getAxes(axis)
        self._obj = axes.text(x, y, text, transform=axes.transAxes, picker=True)

    def _setText(self, txt):
        self._obj.set_text(txt)

    def _setPosition(self, pos):
        self._obj.set_position(pos)

    def _setZOrder(self, z):
        self._obj.set_zorder(z)

    def _setVisible(self, visible):
        self._obj.set_visible(visible)


"""

class AnnotationEditableCanvas(AnnotatableCanvas, TextAnnotationCanvas):
    def __init__(self, dpi):
        super().__init__(dpi)
        self.fontChanged.connect(self.__onFontChanged)

    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data = self.getAnnotations('text')
        for d in data:
            if 'Font' in d.appearance:
                self._setFont(d, FontInfo.FromDict(d.appearance['Font']))

    def __onFontChanged(self, name):
        list = self.getAnnotations('text')
        for l in list:
            if 'Font_def' in l.appearance:
                if l.appearance['Font_def'] is not None and name in [l.appearance['Font_def'], 'Default']:
                    f = self.getCanvasFont(name)
                    l.obj.set_family(f.family)
                    l.obj.set_size(f.size)
                    l.obj.set_color(f.color)
        self.draw()

    def _setFont(self, annot, font):
        if not isinstance(font, FontInfo):
            f = self.getCanvasFont(font)
        else:
            f = font
        annot.obj.set_family(f.family)
        annot.obj.set_size(f.size)
        annot.obj.set_color(f.color)
        annot.appearance['Font'] = f.ToDict()

    @saveCanvas
    def setAnnotationFont(self, indexes, font='Default', default=False):
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            self._setFont(l, font)
            if default and not isinstance(font, FontInfo):
                l.appearance['Font_def'] = font
            else:
                l.appearance['Font_def'] = None

    def getAnnotationFontDefault(self, indexes):
        res = []
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            if 'Font_def' in l.appearance:
                if l.appearance['Font_def'] is not None:
                    res.append(True)
                else:
                    res.append(False)
            else:
                res.append(False)
        return res

    def getAnnotationFont(self, indexes):
        res = []
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            res.append(FontInfo(l.obj.get_family()[0], l.obj.get_size(), l.obj.get_color()))
        return res


class AnnotationBoxAdjustableCanvas(AnnotationMovableCanvas):
    def saveAnnotAppearance(self):
        super().saveAnnotAppearance()
        data = self.getAnnotations('text')
        for d in data:
            d.appearance['BoxStyle'] = self.getAnnotBoxStyle([d.id])[0]
            d.appearance['BoxFaceColor'] = self.getAnnotBoxColor([d.id])[0]
            d.appearance['BoxEdgeColor'] = self.getAnnotBoxEdgeColor([d.id])[0]

    def loadAnnotAppearance(self):
        super().loadAnnotAppearance()
        data = self.getAnnotations('text')
        for d in data:
            if 'BoxStyle' in d.appearance:
                self.setAnnotBoxStyle([d.id], d.appearance['BoxStyle'])
                self.setAnnotBoxColor([d.id], d.appearance['BoxFaceColor'])
                self.setAnnotBoxEdgeColor([d.id], d.appearance['BoxEdgeColor'])

    @saveCanvas
    def setAnnotBoxStyle(self, indexes, style):
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if style == 'none':
                if box is not None:
                    box.set_visible(False)
            else:
                l.obj.set_bbox(dict(boxstyle=style))
                self.setAnnotBoxColor([l.id], 'w')
                self.setAnnotBoxEdgeColor([l.id], 'k')

    def _checkBoxStyle(self, box):
        if isinstance(box, BoxStyle.Square):
            return 'square'
        elif isinstance(box, BoxStyle.Circle):
            return 'circle'
        elif isinstance(box, BoxStyle.DArrow):
            return 'darrow'
        elif isinstance(box, BoxStyle.RArrow):
            return 'rarrow'
        elif isinstance(box, BoxStyle.LArrow):
            return 'larrow'
        elif isinstance(box, BoxStyle.Round):
            return 'round'
        elif isinstance(box, BoxStyle.Round4):
            return 'round4'
        elif isinstance(box, BoxStyle.Roundtooth):
            return 'roundtooth'
        elif isinstance(box, BoxStyle.Sawtooth):
            return 'sawtooth'
        return 'none'

    def getAnnotBoxStyle(self, indexes):
        res = []
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if box is None:
                res.append('none')
                continue
            if not box.get_visible():
                res.append('none')
                continue
            else:
                res.append(self._checkBoxStyle(box.get_boxstyle()))
                continue
        return res

    @saveCanvas
    def setAnnotBoxColor(self, indexes, color):
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if box is not None:
                box.set_facecolor(color)

    def getAnnotBoxColor(self, indexes):
        res = []
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if box is None:
                res.append('w')
            else:
                res.append(box.get_facecolor())
        return res

    @saveCanvas
    def setAnnotBoxEdgeColor(self, indexes, color):
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if box is not None:
                box.set_edgecolor(color)

    def getAnnotBoxEdgeColor(self, indexes):
        res = []
        list = self.getAnnotationFromIndexes(indexes)
        for l in list:
            box = l.obj.get_bbox_patch()
            if box is None:
                res.append('k')
            else:
                res.append(box.get_edgecolor())
        return res

"""
