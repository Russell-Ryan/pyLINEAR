import numpy as np


from .base import Base
from . import columns
from . import h5utils


class PDT(Base):
    def __init__(self,xy):
        assert(len(xy)==2),'must specify an xy pair'
        self.pixel=xy
        self.xyg=columns.XYG()
        self.lam=columns.LAM()
        self.val=columns.VAL()

        
    def extend(self,xyg,lam,val):
        assert(len(xyg)==len(lam)==len(val)),'must have same length'
        
        self.xyg.extend(xyg)
        self.lam.extend(lam)
        self.val.extend(val)


        
    @property
    def name(self):
        return '({},{})'.format(*self.pixel)


    def __mul__(self,v):
        self.val=columns.VAL([v*val for val in self.val])
        return self
    
    def __str__(self):
        return '{} for {}'.format(self.ttype,self.name)
        
    def __len__(self):
        return len(self.xyg)

    def __iter__(self):
        for x,l,v in zip(self.xyg,self.lam,self.val):
            yield x,l,v

    def writeH5(self,grp,**kwargs):
        new=grp.create_group(self.name)
        for k,v in kwargs.items():
            h5utils.writeAttr(new,k,v)
        data=h5utils.writeData(new,self.ttype,self.xyg,self.lam,self.val)
        #dset=h5utils.writeData(grp,self.xyg,self.lam,self.val)
        #return dset
        return data
        
    def readH5(self,grp):
        if self.name in grp:
            new=grp[self.new]
            data=h5utils.loadData(new,self.__class__.__name__)
            self.xyg=columns.XYG(data['xyg'])
            self.lam=columns.XYG(data['lam'])
            self.val=columns.XYG(data['val'])
        else:
            print("{} for {} not found.".format(self.ttype,self.name))

            
        #data=h5utils.loadData(grp)
        #self.xyg=columns.XYG(data['xyg'])
        #self.lam=columns.LAM(data['lam'])
        #self.val=columns.VAL(data['val'])


    @property
    def x(self):
        return self.pixel[0]
    @x.setter
    def x(self,v):
        self.pixel[0]=v

    @property
    def y(self):
        return self.pixel[1]
    @x.setter
    def y(self,v):
        self.pixel[1]=v
        

if __name__=='__main__':
    x=PDT((1,2))

    x.extend([1,2,3],[2,3,4],[1.,2.,3.])


        
    
