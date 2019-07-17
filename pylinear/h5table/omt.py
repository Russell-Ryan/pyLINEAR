import numpy as np
import h5py

from .h5utils import H5Utils
from pylinear.utilities import indices
from . import columns


class OMT(H5Utils):
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
                
    def writeH5(self,grp):
        dset=self.writeData(grp,self.xyg)
        return dset


    def readH5(self,grp):
        try:
            data=self.loadData(grp)
            self.xyg=columns.XYG(data['xyg'])
        except:
            print("{} OMT not found.".format(self.name))

    def __len__(self):
        return len(self.xyg)

    def __contains__(self,xyg):
        return xyg in self.xyg

    @property
    def name(self):
        return '{}'.format(self.segid)


    
    
