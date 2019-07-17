import numpy as np


class LSQRResult(object):
    def __init__(self,*args):
        self.x=args[0]
        self.istop=args[1]
        self.iters=args[2]
        self.r1norm=args[3]
        self.r2norm=args[4]
        self.anorm=args[5]
        self.acond=args[6]
        self.arnorm=args[7]
        self.xnorm=args[8]
        self.lo=np.sqrt(args[9])
        self.hi=self.lo.copy()     
        self.damp=args[10]
        self.time=args[11]

        
    @property
    def xy(self):
        return (np.log10(self.r1norm),np.log10(self.xnorm))

    @property
    def logdamp(self):
        return np.log10(self.damp)

