import numpy as np
from shapely.geometry import Polygon


from .h5tablebase import H5TableBase
from . import columns

class OVT(H5TableBase):
    def __init__(self,segid,beam,*args):
        self.segid=segid
        self.beam=beam
        self.x=columns.X()
        self.y=columns.Y()
        if len(args)==2:
            self.extend(*args)
    def __len__(self):
        return len(self.x)

            
    @property
    def name(self):
        return str(self.segid)

            
    def extend(self,x,y):
        assert len(x)==len(y),'OVT: mismatched sizes'
        self.x.extend(x)
        self.y.extend(y)
        
    def write_h5(self,h5,**kwargs):
        hs=self.write_group(h5,self.name,**kwargs)
        ht=self.write_group(hs,'ovt')
        hd=self.write_data(ht,self.beam,self.x,self.y,**kwargs)
        
    @classmethod
    def load(cls,segid,beam,h5):
        hf=h5[str(segid)+'/ovt']

        data=cls.load_data(hf,str(beam))
        omt=cls(segid,beam,data['x'],data['y'])
        return omt


    def as_polygon(self):
        xy=[(x,y) for x,y in zip(self.x,self.y)]
        p=Polygon(xy)
        return p
