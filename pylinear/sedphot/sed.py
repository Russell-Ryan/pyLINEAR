import numpy as np
import scipy.constants as sc
import os
from astropy.io import fits
#from ..utilities.ascii_files import read_ascii_columns

#from astropy import units as u

class SED(object):
    def __init__(self,*args):
        if len(args)==2:
            self.assign(*args)
        else:
            pass

    def assign(self,lamb,flam):
        assert len(lamb)==len(flam),'mismatched sizes'
        
        #self.lambunit='A'
        #self.fluxunit='erg/s/cm2/A'
        self.lamb=np.array(lamb)
        self.flam=np.array(flam)
        self.wmin=np.amin(self.lamb)
        self.wmax=np.amax(self.lamb)


    #def make_fits_table(self):
    #    # make the FITS table columns
    #    col1=fits.Column(name='wavelength',format='1D',unit='A',
    #                     array=self.lamb)
    #    col2=fits.Column(name='flam',format='1D',unit=self.fluxunit,
    #                     array=self.flam)
    #    col3=fits.Column(name='flounc',format='1D',unit=self.fluxunit,
    #                     array=ferr)
    #    col4=fits.Column(name='fhiunc',format='1D',unit=self.fluxunit,
    #                     array=ferr)
    #    cols=fits.ColDefs([col1,col2,col3,col4])
    #    
    #    # package into a fits object
    #    hdu=fits.BinTableHDU.from_columns(cols)
    #    return hdu

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
                       
