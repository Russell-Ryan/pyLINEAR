from dataclasses import dataclass
import numpy as np
from ..header_utils import get_last_keyword


@dataclass
class Result(object):
    method: str
    x: np.array
    istop: int
    itn: int
    r1norm: float
    r2norm: float
    anorm: float
    acond: float
    arnorm: float
    xnorm: float
    lo: np.array
    hi: np.array
    damp: float


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
    n=10
    r=(np.arange(n),1,24,2.3,25.,12.,100000.,456.,123.,np.arange(n)+2)


    x=Result(*r,r[-1].copy(),43.)

    print(x.logdamp)
    
