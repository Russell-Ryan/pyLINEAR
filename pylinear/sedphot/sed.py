import numpy as np
import scipy.constants as sc
import os
#from ..utilities.ascii_files import read_ascii_columns

#from astropy import units as u

class SED(object):
    def __init__(self,lamb,flam):
        self.lamb=np.array(lamb)
        self.flam=np.array(flam)
        self.wmin=np.amin(self.lamb)
        self.wmax=np.amax(self.lamb)
        

    @classmethod
    def load(cls,filename):
        if os.path.exists(filename):
            lamb,flam=np.loadtxt(filename,usecols=(0,1),unpack=True)
            return cls(lamb,flam)
        else:
            return None


    def write(self,filename):
        with open(filename,'w') as fp:
            print('# 1: wavelength (A)',file=fp)
            print('# 2: f_lam (erg/s/cm2/A)',file=fp)
            print('',file=fp)
        
            for l,f in zip(self.lamb,self.flam):
                print('{} {}'.format(l,f),file=fp)

    def interpolate(self,wav):
        g=np.where(np.isfinite(self.flam))[0]
        flam=np.interp(wav,self.lamb[g],self.flam[g],
                       left=self.flam[g[0]],right=self.flam[g[-1]])
        return flam

    def redshift(self,z):
        self.lamb*=(1+z)

    def __mul__(self,v):
        self.flam*=v
        return self
    def __imul__(self,v):
        self.flam*=v
        return self
    def __rmul__(self,v):
        self.flam*=v
        return self

    def fnu(self):
        fnu=self.flam*(self.lamb/sc.c)*(self.lamb/1e10)
        return fnu
                       
