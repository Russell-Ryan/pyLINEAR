from dataclasses import dataclass,field
import numpy as np
from ..header_utils import get_last_keyword


@dataclass
class Result(object):
    method: str=''
    x: np.ndarray=field(default = np.zeros(0))
    istop: int=-1
    itn: int=0
    r1norm: float=0.0
    r2norm: float=0.0
    anorm: float=0.0
    acond: float=0.0
    arnorm: float=0.0
    xnorm: float=0.0
    lo: np.ndarray=field(default = np.zeros(0))
    hi: np.ndarray=field(default = np.zeros(0))
    damp: float=1.0


    @property
    def logdamp(self):
        return np.log10(self.damp)

    @property
    def xy(self):
        return np.log10(self.r1norm),np.log10(self.xnorm)


    def update_header(self,hdr,after=None):
        #*other,last=hdr.keys()    # get the last keyword
        last=get_last_keyword(hdr)
        
        
        
        hdr.set('INVERTER',value=self.method,after=last,
                comment='method for inversion')
        hdr.set('ACOND',value=self.acond,after='INVERTER',
                comment='Condition of the matrix')
        hdr.set('ANORM',value=self.anorm,after='ACOND',
                comment='norm of matrix')
        hdr.set('ARNORM',value=self.arnorm,after='ANORM',
                comment='norm of matrix')
        hdr.set('R1NORM',value=self.r1norm,after='ARNORM',
                comment='chi2')
        hdr.set('R2NORM',value=self.r2norm,after='R1NORM',
                comment='norm of damped chi2')
        hdr.set('XNORM',value=self.xnorm,after='R2NORM',
                comment='norm of x')
        hdr.set('ISTOP',value=self.istop,after='XNORM',
                comment='stopping condition')
        hdr.set('ITER',value=self.itn,after='ISTOP',
                comment='number of iterations')
        hdr.set('',value='',before='INVERTER')
        hdr.set('',value='      / Linear Results',before='INVERTER')
        hdr.set('',value='',before='INVERTER')


if __name__=='__main__':
    #n=10
    #r=(np.arange(n),1,24,2.3,25.,12.,100000.,456.,123.,np.arange(n)+2)
    #x=Result(*r,r[-1].copy(),43.)
    x=Result('kjdk')
    print(x.method)
    #print(x.logdamp)
    
