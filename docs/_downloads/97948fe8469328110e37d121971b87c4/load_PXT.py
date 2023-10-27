import igor.packed
import igor.igorpy
import numpy as np

from lys import Wave, registerFileLoader


def __loadPxt(name):
    nam, ext = os.path.splitext(os.path.basename(name))
    (rec, data) = igor.packed.load(name)
    wav = igor.igorpy.Wave(data['root'][nam.encode('utf-8')])
    w = Wave()
    w.data = np.array(wav.data)
    w.data.flags.writeable = True
    note = [s.replace(" ", "").replace("\r", "").split("=") for s in wav.notes.decode().replace("\n\n", "\n").split("\n")]
    w.note = {}
    for n in note:
        if len(n) == 2:
            w.note[n[0].lower()] = n[1]
    if w.data.ndim == 1:
        w.x = wav.axis[0]
    if w.data.ndim >= 2:
        w.x = wav.axis[1]
        w.y = wav.axis[0]
    if w.data.ndim == 3:
        w.x = wav.axis[2]
        w.y = wav.axis[1]
        w.z = wav.axis[0]
    return w


registerFileLoader(".pxt", __loadPxt)
