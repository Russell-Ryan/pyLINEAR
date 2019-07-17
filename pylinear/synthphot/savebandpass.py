import numpy as np
import scipy.constants as sc
import os
#from .manifest import Manifest
from .filters import filters

class Bandpass(object):
    def __init__(self,filename=None,zeropoint=None):
        self.zeropoint=zeropoint
        self.name=''
        self._lamb=[]
        self._tran=[]
        if filename is not None:
            self.load_from_file(filename)

    def load_from_file(self,filename):
        base=os.path.basename(filename)
        self.name,zero=filters[base].values()
        if self.zeropoint is None:
            self.zeropoint=zero

        path=os.path.join(os.path.split(__file__)[0],'filters')
                    
        self.filename=filename
        self.lamb,self.tran=np.loadtxt(os.path.join(path,self.filename),\
                                       usecols=(0,1),unpack=True)
        #skiprows=1,

    def __str__(self):
        return self.filename

    @property
    def nu2lamb(self):
        jacob=(sc.c/self.photplam)*(1e10/self.photplam)
        return jacob
    
        
    def aveflux(self,sed,magnitude=False,flam=False):
        ex=(sed.minmax[0] > self.minmax[0]) or (sed.minmax[1] < self.minmax[1])

        if ex:
            print("Extrapolation warning.")
            
        fnu=np.interp(self.lamb,sed.lamb,sed.fnu,left=0.,right=0.)
        ave=np.trapz(fnu*self.tran,x=self.freq)


        if flam:
            ave*=self.nu2lamb

        
        if magnitude:
            ave=-2.5*np.log10(ave)
            if self.zeropoint is None:
                ave+=self.zeropoint


        return ave
        
        

    def _initialize(self):
        if len(self._lamb) == len(self._tran) and len(self._lamb) !=0:
        
            
            # compute frequency and range
            self.freq=(sc.c/self.lamb)*1e10
            self.minmax=[np.amin(self.lamb),np.amax(self.lamb)]
            
            # compute pivot wavelength
            den=np.trapz(self.tran/self.lamb,x=self.lamb)
            num=np.trapz(self.tran*self.lamb,x=self.lamb)
            self.photplam=np.sqrt(num/den)


            
            # compute photflam
            self.photflam=10**(-0.4*self.zeropoint)*0.1088/\
                           (self.photplam*self.photplam)
            
            # compute the average wavelength
            den=np.trapz(self.tran,x=self.lamb)
            self.avelam=num/den

            
            # compute width
            num=np.trapz(self.tran*(self.lamb-self.avelam)**2,x=self.lamb)
            self.rms=np.sqrt(num/den)
            
            # compute normalization for AB mag integration
            self.norm=np.trapz(self.tran/self.freq,x=self.freq)

            
            # normalize the curve
            self._tran=self.tran/(self.norm*self.freq)
        
        
    @property
    def lamb(self):
        return self._lamb

    @lamb.setter
    def lamb(self,lamb):
        self._lamb=lamb
        self._initialize()

    @property
    def tran(self):
        return self._tran

    @tran.setter
    def tran(self,tran):
        self._tran=tran
        self._initialize()

        
