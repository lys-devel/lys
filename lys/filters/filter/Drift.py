import cv2
import numpy as np
from scipy import signal, ndimage

from lys import DaskWave, load
from lys.Qt import QtWidgets
from lys.filters import FilterSettingBase, filterGUI, addFilter, FilterInterface
from lys.widgets import RegionSelectWidget, AxisCheckLayout


class DriftCorrection(FilterInterface):
    """
    Drift correction for 2D image.

    See :class:`.FilterInterface.FilterInterface` for general description of Filters.

    Args:
        axes (array of integer): The axes to which the drift correction is applied.
        region (dim*2 array): The region that specified the part of the data in the form of [(x1,x2), (y1,y2), ...]. dim should match the ndim of the data.
        apply (bool): If True, the corrected data will be returned. Otherwise the amout of shift will be returned.
        method ('Phase correlation', 'Cross correlation', or 'From file'): The method to be used.

    """
    def __init__(self, axes, region, apply=True, method="Phase correlation"):
        self._axes = axes
        self._region = region
        self._apply = apply
        self._method = method

    def _execute(self, wave, *args, **kwargs):
        if self._method == "Phase correlation":
            shift = self._calcShift1(wave)
        elif self._method == "Cross correlation":
            shift = self._calcShift(wave)
        elif self._method == "From file":
            shift = load(self._region).data[:,::-1].T
        if not self._apply:
            return DaskWave(shift[::-1,:].T, *[ax for i, ax in enumerate(wave.axes) if i not in self._axes], **wave.note)
        else:
            sign = ",".join("abcdefghijklmn"[0:len(self._axes)])
            sign = "(" + sign + "),(z)->(" + sign + ")"
            uf = self._generalizedFunction(wave, ndimage.interpolation.shift, signature=sign, axes=[self._axes, [0], self._axes])
            return DaskWave(uf(wave.data, -shift), *wave.axes, **wave.note)

    def _calcShift1(self, wave):
        region = [wave.posToPoint(r, ax) for ax, r in zip(self._axes, self._region)]
        ref, data = self._makeReferenceData1(wave.data, region, self._axes)
        window = cv2.createHanningWindow(ref.shape, cv2.CV_32F).astype(np.float32).T
        def f(d):
            return np.array(cv2.phaseCorrelate(d.astype(np.float32), ref.astype(np.float32))[0])[::-1]
        sign = "(" + ",".join("abcdefghijklmn"[0:len(self._axes)]) + ")->(z)"
        uf = self._generalizedFunction(None, f, signature=sign, axes=[self._axes, [0]], output_dtypes=float, output_sizes={"z": 2})
        return -uf(data)

    def _makeReferenceData1(self, data, region, axes):
        sl = []
        for i in range(data.ndim):
            if i in axes:
                sl.append(slice(*region[axes.index(i)]))
            else:
                sl.append(0)
        ref = data[tuple(sl)]
        sl = [slice(None) if s==0 else s for s in sl]
        return ref.compute(), data[tuple(sl)]

    def _calcShift(self, wave):
        region = [wave.posToPoint(r, ax) for ax, r in zip(self._axes, self._region)]
        reference, s0 = self._makeReferenceData(wave.data, region, self._axes)
        def f(d):
            return _findShift(d, reference, region, s0)
        sign = "(" + ",".join("abcdefghijklmn"[0:len(self._axes)]) + ")->(z)"
        uf = self._generalizedFunction(wave, f, signature=sign, axes=[self._axes, [0]], output_dtypes=float, output_sizes={"z": 2})
        return uf(wave.data)

    def _makeReferenceData(self, data, region, axes):
        sl = []
        for i in range(data.ndim):
            if i in axes:
                sl.append(slice(None))
            else:
                sl.append(0)
        reg_ref = self._makeReferenceRegion(data, axes, region)
        ref_nor = _normalize(data[tuple(sl)], reg_ref)
        return ref_nor, _findShift(data[tuple(sl)].compute(), ref_nor.compute(), region)

    def _makeReferenceRegion(self, data, axes, region):
        result = []
        for ax, r in zip(axes, region):
            ref = [r[0] - int((r[1] - r[0]) / 2), r[1] + int((r[1] - r[0]) / 2)]
            if ref[0] < 0:
                ref[0] = 0
            if ref[1] > data.shape[ax]:
                ref[1] = data.shape[ax]
            result.append(ref)
        return result

    def getParameters(self):
        return {"axes": self._axes, "region": self._region, "apply": self._apply, "method": self._method}

    def getRelativeDimension(self):
        if self._apply:
            return 0
        else:
            return -len(self._axes) + 1


def _normalize(data, region):
    sl = [slice(r[0], r[1]) for r in region]
    d = data[tuple(sl)]
    return d - d.mean()


def _findShift(data, ref, region, s_ref=0):
    d_c = _normalize(data, region)
    c = signal.correlate(ref, d_c, mode='valid')
    return np.array(np.unravel_index(np.argmax(data), data.shape)) - s_ref


@filterGUI(DriftCorrection)
class _DriftCorrectionSetting(FilterSettingBase):
    def __init__(self, dim):
        super().__init__(dim)
        self._dim = dim
        self.__initLayout(dim)

    def __initLayout(self, dim):
        self._method = QtWidgets.QComboBox()
        self._method.addItems(["Phase correlation", "Cross correlation", "From file"])
        self._method.currentTextChanged.connect(self.__methodChanged)
        h0 = QtWidgets.QHBoxLayout()
        h0.setContentsMargins(0,0,0,0)
        h0.addWidget(QtWidgets.QLabel("Method"))
        h0.addWidget(self._method)

        self._combo = QtWidgets.QComboBox()
        self._combo.addItems(["Corrected data", "Amount of shift"])
        h1 = QtWidgets.QHBoxLayout()
        h1.setContentsMargins(0,0,0,0)
        h1.addWidget(QtWidgets.QLabel("Output"))
        h1.addWidget(self._combo)
        self._frame_output = QtWidgets.QFrame()
        self._frame_output.setContentsMargins(0,0,0,0)
        self._frame_output.setLayout(h1)

        self.range = RegionSelectWidget(self, dim, check=True)
        self.range.setContentsMargins(0,0,0,0)
        self._frame_range = QtWidgets.QFrame()
        self._frame_range.setLayout(self.range)
        self._frame_range.setContentsMargins(0,0,0,0)

        self._axes = AxisCheckLayout(dim)
        self._axes.setContentsMargins(0,0,0,0)
        self._frame_axes = QtWidgets.QFrame()
        self._frame_axes.setContentsMargins(0,0,0,0)
        self._frame_axes.setLayout(self._axes)

        self._file = QtWidgets.QLineEdit()
        h2 = QtWidgets.QHBoxLayout()
        h2.setContentsMargins(0,0,0,0)
        h2.addWidget(QtWidgets.QLabel("File"))
        h2.addWidget(self._file)
        h2.addWidget(QtWidgets.QPushButton("...", clicked=self.__loadFile))
        self._frame_file = QtWidgets.QFrame()
        self._frame_file.setLayout(h2)
        self._frame_file.setContentsMargins(0,0,0,0)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(h0)
        layout.addWidget(self._frame_output)
        layout.addWidget(self._frame_file)
        layout.addWidget(self._frame_range)
        layout.addWidget(self._frame_axes)
        self.setLayout(layout)

        self.__methodChanged()

    def __methodChanged(self):
        if self._method.currentText() == "From file":
            self._frame_output.hide()
            self._frame_range.hide()
            self._frame_axes.show()
            self._frame_file.show()
        else:
            self._frame_output.show()
            self._frame_range.show()
            self._frame_axes.hide()
            self._frame_file.hide()

    def __loadFile(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Load fitting', filter="Numpy npz (*.npz);;All files (*.*)")
        if fname[0]:
            self._file.setText(fname[0])

    def getParameters(self):
        if self._method.currentText() == "From file":
            axes = self._axes.GetChecked()
            region = self._file.text()
            apply = True
        else:
            axes = [i for i, c in enumerate(self.range.getChecked()) if c]
            region = [self.range.getRegion()[ax] for ax in axes]
            apply = self._combo.currentText()=="Corrected data"
        return {"region": region, "axes": axes, "apply": apply, "method": self._method.currentText()}

    def setParameters(self, axes, region, apply=False, method="Phase correlation"):
        if method == "From file":
            self._axes.SetChecked(axes)
            self._file.setText(region)
        else:
            for i, r in zip(axes, region):
                self.range.setRegion(i, r)
            check = [False] * self._dim
            for ax in axes:
                check[ax] = True
            self.range.setChecked(check)
            if apply:
                self._combo.setCurrentIndex(0)
            else:
                self._combo.setCurrentIndex(1)
        self._method.setCurrentText(method)


# Add filte to lys. You can use new filter from MultiCut
addFilter(
    DriftCorrection,
    gui=_DriftCorrectionSetting,
    guiName="Drift correction",
    guiGroup="Image transformation"
)

