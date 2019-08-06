import numpy as np
import pdb

from . import columns
from . import h5utils
from .base import Base

class DDT(Base):
    def __init__(self,segid):
        self.segid=segid
        self.pix=[]
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
        return '{} for {}'.format(self.ttype,self.name)

    def npix(self):
        return len(self.pix)
        
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


    def writeH5(self,grp,**kwargs):
        new=grp.create_group(self.name)
        for k,v in kwargs.items():
            h5utils.writeAttr(new,k,v)

        data=h5utils.writeData(new,self.ttype,self.xyg,self.wav,self.val)
            
        pix=list(zip(*self.pix))
        x=columns.X()
        x.extend(list(pix[0]))
        y=columns.Y()
        y.extend(list(pix[1]))


        pix=h5utils.writeData(new,'pix',x,y)

        return new


    def readH5(self,grp):
        if self.name in grp:
            new=grp[self.name]
            data=h5utils.loadData(new,self.ttype)
            self.xyg=columns.XYG(data['xyg'])
            self.wav=columns.WAV(data['wav'])
            self.val=columns.VAL(data['val'])

            pix=h5utils.loadData(new,'pix')
            self.pix=list(zip(list(pix['x']),list(pix['y'])))
        else:
            self.notFound()
        
        #data=h5utils.loadData(grp)
        #self.xyg=columns.XYG(data['xyg'])
        #self.wav=columns.WAV(data['wav'])
        #self.val=columns.VAL(data['val'])



    
