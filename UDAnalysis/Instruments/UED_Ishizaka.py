import glob,os,LoadFile

def name():
    return "UED (Ishizaka Lab.)"
def GetRawItems(path,type):
    list=glob.glob(path+'/'+type+'/*.pxt')
    res=[]
    for l in list:
        path, ext = os.path.splitext(os.path.basename(l))
        res.append(path+ext)
    return res
def GetRawData(path,type,name):
    return LoadFile.load(path+'/'+type+'/'+name)
