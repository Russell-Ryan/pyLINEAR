from dataclasses import dataclass
import numpy as np

@dataclass
class LSQRResult(object):
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



if __name__=='__main__':
    n=10
    r=(np.arange(n),1,24,2.3,25.,12.,100000.,456.,123.,np.arange(n)+2)


    x=LSQRResult(*r,r[-1].copy(),43.)

    print(x.logdamp)
    
