from enum import IntEnum

class Axis(IntEnum):
    BottomLeft=1
    TopLeft=2
    BottomRight=3
    TopRight=4

class WaveData(object):
    def __init__(self,wave,obj,axis,idn,appearance,offset=(0,0,0,0),zindex=0):
        self.wave=wave
        self.obj=obj
        self.axis=axis
        self.axes=axis
        self.id=idn
        self.appearance=appearance
        self.offset=offset
        self.zindex=zindex
