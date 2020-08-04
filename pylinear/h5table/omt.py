import numpy as np
#import h5py
from scipy.spatial import ConvexHull

from .h5tablebase import H5TableBase
#from .ovt import OVT
from . import columns

class OMT(H5TableBase):
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
        self.x.extend(x)
        self.y.extend(y)
       
    def write_h5(self,h5,**kwargs):
        #hs=self.write_group(h5,self.name,**kwargs)
        #ht=self.write_group(hs,'omt')
        #hd=self.write_data(ht,self.beam,self.x,self.y,**kwargs)

        hd=self.write_data(h5,self.name,self.x,self.y,**kwargs)

        
    @classmethod
    def load(cls,segid,beam,h5):
        #hf=h5[str(segid)+'/omt']

        data=cls.load_data(h5,str(beam))
        omt=cls(segid,beam,data['x'],data['y'])
        return omt


    def compute_vertices(self):
        ovt=OVT(self.segid,self.beam)
        if len(self):
            xy=[(x,y) for x,y in zip(self.x,self.y)]

            # make the hull
            hull=ConvexHull(xy)

            # get the hull coordinates
            xh=self.x.to_numpy(g=hull.vertices)
            yh=self.y.to_numpy(g=hull.vertices)
            
            ovt.extend(xh,yh)

        return ovt
