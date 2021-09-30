
"""
def getShape(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            with zipfile.ZipFile(name) as archive:
                name = "data.npy"
                npy = archive.open(name)
                version = np.lib.format.read_magic(npy)
                shape, fortran, dtype = np.lib.format._read_array_header(npy, version)
                return shape
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.data.shape


def getDtype(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            with zipfile.ZipFile(name) as archive:
                name = "data.npy"
                npy = archive.open(name)
                version = np.lib.format.read_magic(npy)
                shape, fortran, dtype = np.lib.format._read_array_header(npy, version)
                return dtype
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.data.dtype


def getAxes(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            tmp = np.load(name, allow_pickle=True)
            return tmp["axes"].to_list()
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.axes


def getNotes(name, *args, **kwargs):
    path, ext = os.path.splitext(name)
    if ext == ".npz":
        try:
            tmp = np.load(name, allow_pickle=True)
            return tmp["note"].item()
        except:
            pass
    f = load(name, *args, **kwargs)
    return f.note

"""
