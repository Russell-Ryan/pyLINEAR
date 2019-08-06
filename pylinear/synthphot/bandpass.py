import numpy as np
import scipy.constants as sc
import os


from .filters import filters    # this is a list of filters for pyLINEAR

class Bandpass(object):
    
    def __init__(self,fileroot):
        self.filename='{}.filt'.format(fileroot)

        # get the data for the filters
        try:
            self.name,self.zeropoint=filters[fileroot].values()
        except:
            raise FileNotFoundError("{} not in manifest".format(fileroot))
        
        path=os.path.join(os.path.split(__file__)[0],'filters')

        fullfile=os.path.join(path,self.filename)
        self.lamb,self.tran=np.loadtxt(fullfile,usecols=(0,1),unpack=True)
        
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

        # remove the frequency
        self.tran/=self.freq
        
        # compute normalization for AB mag integration
        self.norm=np.trapz(self.tran,x=self.freq)
        
        # normalize the curve
        self.tran/=self.norm
        

        
        
    def __str__(self):
        return self.filename

    @property
    def nu2lamb(self):
        jacob=(sc.c/self.photplam)*(1e10/self.photplam)
        return jacob
    
        
    def aveflux(self,sed,magnitude=False,flam=False):
        ex=(sed.minmax[0] > self.minmax[0]) or (sed.minmax[1] < self.minmax[1])

        if ex:
            print("[warn]Extrapolation warning.")
            
        fnu=np.interp(self.lamb,sed.lamb,sed.fnu,left=0.,right=0.)
        ave=np.trapz(fnu*self.tran,x=self.freq)


        if flam:
            ave*=self.nu2lamb
        
        if magnitude:
            ave=-2.5*np.log10(ave)+self.zeropoint

        return ave
        
