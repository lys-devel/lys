import dm3_lib as dm3
import numpy as np

from ExtendAnalysis import Wave, plugin


def __loadDm3(name):
    data = dm3.DM3(name)
    w = Wave()
    w.data = data.imagedata
    if w.data.ndim == 2:  # image
        w.x = np.arange(0, data.pxsize[0] * w.data.shape[0], data.pxsize[0])
        w.y = np.arange(0, data.pxsize[0] * w.data.shape[1], data.pxsize[0])
    elif w.data.ndim == 3:  # spectrum imaging
        w.data = w.data.transpose(1, 2, 0)
        w.x = np.arange(0, data.pxsize[0] * w.data.shape[0], data.pxsize[0])
        w.y = np.arange(0, data.pxsize[0] * w.data.shape[1], data.pxsize[0])
        e0 = float(data.tags['root.ImageList.1.ImageData.Calibrations.Dimension.2.Origin'])
        de = float(data.tags['root.ImageList.1.ImageTags.EELS Spectrometer.Dispersion (eV/ch)'])
        w.z = np.linspace(-e0, -e0 + de * w.data.shape[2], w.data.shape[2])
    w.note = {}
    try:
        w.note['unit'] = data.pxsize[1]
        w.note['specimen'] = data.info['specimen'].decode()
        w.note['date'] = data.info['acq_date'].decode()
        w.note['mag'] = float(data.info['mag'].decode())
        w.note['time'] = data.info['acq_time'].decode()
        w.note['voltage'] = float(data.info['hv'].decode())
        w.note['mode'] = data.info['mode'].decode()
        w.note['exposure'] = data.tags['root.ImageList.1.ImageTags.DataBar.Exposure Time (s)']
        w.note['hbin'] = data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.hbin']
        w.note['vbin'] = data.tags['root.ImageList.1.ImageTags.Acquisition.Parameters.Detector.vbin']
        w.note['delay'] = data.tags['root.ImageList.1.ImageTags.Experiment.Laser.delay']
        w.note['power'] = data.tags['root.ImageList.1.ImageTags.Experiment.Laser.power']
        w.note['scanMode'] = data.tags['root.ImageList.1.ImageTags.Experiment.mode']
    except:
        pass
    return w


plugin.registerFileLoader(".dm3", __loadDm3)
