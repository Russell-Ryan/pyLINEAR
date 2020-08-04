import numpy as np
import scipy.constants as sc
import os
from ..utilities.ascii_files import read_ascii_columns


class Bandpass(object):
    
    def __init__(self,filename):
        self.filename=filename
        (self.lamb,self.tran),meta=read_ascii_columns(self.filename,
                                                      names=('lamb','tran'))

        self.zeropoint=meta['ZEROPOINT']
        
        # compute frequency and range
        self.freq=(sc.c/self.lamb)*1e10
        self.wmin=np.amin(self.lamb)
        self.wmax=np.amax(self.lamb)
        
        # compute pivot wavelength
        den=np.trapz(self.tran/self.lamb,x=self.lamb)
        num=np.trapz(self.tran*self.lamb,x=self.lamb)
        self.photplam=np.sqrt(num/den)
                
        # compute photflam
        self.photflam=10**(-0.4*self.zeropoint)*0.1088/(self.photplam*self.photplam)
        
        
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


    @classmethod
    def load(cls,fileroot):
        path=os.path.split(__file__)[0]
        filename=os.path.join(path,'filters','{}.filt'.format(fileroot))
        if os.path.exists(filename):
            return cls(filename)
        else:
            print('[warn]Filter not found: {}'.format(filename))
            return None
        
        
    def __str__(self):
        return 'Bandpass: {}'.format(self.filename)

    #@property
    #def nu2lamb(self):
    #    jacob=(sc.c/self.photplam)*(1e10/self.photplam)
    #    return jacob
    #
    

    
    def aveflux(self,sed,magnitude=False,flam=False):
        #ex=(sed.minmax[0] > self.minmax[0]) or (sed.minmax[1] < self.minmax[1])

        if (sed.wmin > self.wmin) or (sed.wmax < self.wmax):
            print("[warn]Extrapolation warning.")
            #print('SED RANGE: {} {}'.format(sed.wmin,sed.wmax))
            #print('BAND range: {} {}'.format(self.wmin,self.wmax))
                  
            
        fnu=np.interp(self.lamb,sed.lamb,sed.fnu(),left=0.,right=0.)
        ave=np.trapz(fnu*self.tran,x=self.freq)


        if flam:
            ave*=(sc.c/self.photplam)*(1e10/self.photplam)
        
        if magnitude:
            ave=-2.5*np.log10(ave)+self.zeropoint

        return ave
        
if __name__=='__main__':
    x=Bandpass.load('hst_acs_f814w')
    print(x)
