import pydicom

from ExtendAnalysis import Wave, registerFileLoader


def __loadDcm(name):
    data = pydicom.read_file(name)
    return Wave(data.pixel_array)


registerFileLoader(".pxt", __loadDcm)
