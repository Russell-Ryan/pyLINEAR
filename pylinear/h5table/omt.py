import numpy as np
import h5py

from .base import Base
from pylinear.utilities import indices
from . import columns
from . import h5utils

class OMT(Base):
    def __init__(self,segid):
        self.segid=segid
        self.xyg=columns.XYG()

    def extend(self,xyg,uniqify=False):
        self.xyg.extend(xyg)
        if uniqify:
            self.uniqify()
        
    def uniqify(self):
        xyg=indices.unique(self.xyg)
        self.xyg=columns.XYG(xyg)
                
    def writeH5(self,grp,**kwargs):
        new=grp.create_group(self.name)
        for k,v in kwargs.items():
            h5utils.writeAttr(new,k,v)
        data=h5utils.writeData(new,self.ttype,self.xyg)
        return new


    def readH5(self,grp):
        if self.name in grp:
            new=grp[self.name]
            data=h5utils.loadData(new,self.ttype)
            self.xyg=columns.XYG(data['xyg'])
        else:
            self.notFound()

    def __len__(self):
        return len(self.xyg)

    def __contains__(self,xyg):
        return xyg in self.xyg

    @property
    def name(self):
        return '{}'.format(self.segid)


    
    
