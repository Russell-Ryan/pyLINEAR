import numpy as np
import scipy.constants as sc
        

class SED(object):
    def __init__(self,*args,filename=None):
        self._lamb=[]
        self._flam=[]
        if filename is not None:
            self.load_from_file(filename)
        if len(args)==2:
            self.load_from_data(*args)
            
    def load_from_data(self,lamb,flam):
        if len(lamb) == len(flam):
            self.lamb=np.array(lamb)
            self.flam=np.array(flam)
            #self._initialize(flam=True)
            
    def load_from_file(self,filename):
        self.filename=filename
        self.lamb,self.flam=np.loadtxt(self.filename,usecols=(0,1), \
                                       unpack=True)

        #self._initialize()

    def interpolate(self,wav,flam=True):

        if flam:
            f=np.interp(wav,self.lamb,self.flam,left=self.flam[0], \
                        right=self.flam[-1])
        else:
            f=np.interp(wav,self.lamb,self.fnu,left=self.fnu[0], \
                        right=self.fnu[-1])
        return f

    def redshift(self,z):
        self.lamb*=(1+z)
        
    def __mul__(self,val):
        self.flam*=val
        return self
        

    
    #def _initialize(self,flam=True):
    #    nu=(sc.c/self.lamb)
    #    self.freq=nu*1e10
    #    self.minmax=[np.amin(self.lamb),np.amax(self.lamb)]
    #    
    #    dlamdnu=(self.lamb/1e10)/nu
    #    if flam:
    #        self._fnu=self._flam*dlamdnu                
    #    else:
    #        self._flam=self._fnu/dlamdnu


    @property
    def lamb(self):
        return self._lamb

    @lamb.setter
    def lamb(self,lamb):
        #self._freq=(sc.c/self.lamb)*1e10
        self.minmax=[np.amin(lamb),np.amax(lamb)]
        self._lamb=lamb
        #self._initialize()

    @property
    def flam(self):
        return self._flam

    @flam.setter
    def flam(self,flam):
        self._flam=flam
        #self._initialize(flam=True)
        
    @property
    def fnu(self):
        dlam_dnu=(self.lamb/sc.c)*(self.lamb/1e10)
        fnu=self.flam*dlam_dnu
        return fnu
    
    #@fnu.setter
    #def fnu(self,fnu):
    #    self._fnu=fnu
        #self._initialize(flam=False)
