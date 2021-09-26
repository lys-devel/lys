import pydicom

from ExtendAnalysis import Wave, plugin


def __loadDcm(name):
    data = pydicom.read_file(name)
    return Wave(data.pixel_array)


plugin.registerFileLoader(".pxt", __loadDcm)
