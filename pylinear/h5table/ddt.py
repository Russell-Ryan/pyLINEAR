import numpy as np

from . import columns
from .h5utils import H5Utils


class DDT(H5Utils):
    def __init__(self,segid):
        self.segid=segid
        self.xyg=columns.XYG()
        self.wav=columns.WAV()
        self.val=columns.VAL()

        
    def extend(self,xyg,wav,val):
        assert(len(xyg)==len(wav)==len(val)),'Must have same lengths'

        self.xyg.extend(xyg)
        self.wav.extend(wav)
        self.val.extend(val)

    def select(self,g):

        if len(self)!=0 and len(g)!=0:
            xyg,wav,val=[],[],[]
            for i in g:
                xyg.append(self.xyg[i])
                wav.append(self.wav[i])
                val.append(self.val[i])
            
            self.xyg=columns.XYG(xyg)
            self.wav=columns.WAV(wav)
            self.val=columns.VAL(val)


        
    def __str__(self):
        return 'DDT for {}'.format(self.name)

        
    def __len__(self):
        return len(self.xyg)

    def __getitem__(self,key):
        return self.xyg[key],self.wav[key],self.val[key]
    
    def __imul__(self,values):
        self.val=columns.VAL([s*v for s,v in zip(self.val,values)])        
        return self


    def __eq__(self,other):
        if isinstance(self,other.__class__):
            return self.__dict__==other.__dict__
        else:
            return False
        
    @property
    def name(self):
        return '{}'.format(self.segid)


    def writeH5(self,grp):
        dset=self.writeData(grp,self.xyg,self.wav,self.val)
        return dset


    def readH5(self,grp):
        data=self.loadData(grp)
        self.xyg=columns.XYG(data['xyg'])
        self.wav=columns.WAV(data['wav'])
        self.val=columns.VAL(data['val'])



    
