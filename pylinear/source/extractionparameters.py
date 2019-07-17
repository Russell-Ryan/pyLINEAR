import numpy as np


class ExtractionParameters(object):
    def __init__(self,lamb0,lamb1,dlamb):
        self._lamb0=lamb0
        self._lamb1=lamb1
        self._dlamb=dlamb

    @property
    def nwav(self):
        return int(np.ceil((self.lamb1-self.lamb0)/self.dlamb)+1)

    @property
    def waves(self):
        nwav=self.nwav
        delta=(self.lamb1-self.lamb0)/(nwav-1)
        return np.arange(nwav,dtype=float)*delta+self.lamb0

    @property
    def limits(self):
        nwav=self.nwav
        delta=(self.lamb1-self.lamb0)/(nwav-1)
        return (np.arange(nwav+1,dtype=float)-0.5)*delta+self.lamb0

    @property
    def lamb0(self):
        return self._lamb0
    @lamb0.setter
    def lamb0(self,lamb0):
        self._lamb0=float(lamb0)
        #self._setlimits()
        
    @property
    def lamb1(self):
        return self._lamb1
    @lamb1.setter
    def lamb1(self,lamb1):
        self._lamb1=float(lamb1)
        #self._setlimits()

    @property
    def dlamb(self):
        return self._dlamb
    @dlamb.setter
    def dlamb(self,dlamb):
        self._dlamb=float(dlamb)
        #self._setlimits()
