import numpy as np


class ExtractionParameters(object):
    FLOAT=np.float64
    INT=np.uint64
    
    def __init__(self,lamb0,lamb1,dlamb):
        self._lamb0=lamb0
        self._lamb1=lamb1
        self._dlamb=dlamb
        
    @property
    def nwav(self):
        n=np.ceil((self.lamb1-self.lamb0)/self.dlamb)+1
        return self.INT(n)

    @property
    def waves(self):
        nwav=self.nwav
        delta=(self.lamb1-self.lamb0)/(nwav-1)
        return np.arange(nwav,dtype=self.FLOAT)*delta+self.lamb0

    @property
    def limits(self):
        nwav=self.nwav
        delta=(self.lamb1-self.lamb0)/(nwav-1)
        return (np.arange(nwav+1,dtype=self.FLOAT)-0.5)*delta+self.lamb0

    @property
    def lamb0(self):
        return self._lamb0
    @lamb0.setter
    def lamb0(self,lamb0):
        self._lamb0=self.FLOAT(lamb0)
        #self._setlimits()
        
    @property
    def lamb1(self):
        return self._lamb1
    @lamb1.setter
    def lamb1(self,lamb1):
        self._lamb1=self.FLOAT(lamb1)
        #self._setlimits()

    @property
    def dlamb(self):
        return self._dlamb
    @dlamb.setter
    def dlamb(self,dlamb):
        self._dlamb=self.FLOAT(dlamb)
        #self._setlimits()
