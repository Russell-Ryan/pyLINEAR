from astropy.io import fits
import numpy as np


''' Set of classes to implement grism flat fielding

Written for pyLINEAR by R Ryan
'''


class FlatField(object):
    DTYPE=np.float32
    
class UnityFlatField(FlatField):
    def __init__(self,shape):
        FlatField.__init__(self)
        self.ftype='unity'
        self.shape=shape

    def __call__(self,x,y,l):
        g=(x >= 0) & (x < self.shape[1]) & (y >= 0) & (y < self.shape[0])
        return g.astype(self.DTYPE)
        
class ImageFlatField(FlatField):
    def __init__(self,filename):
        self.filename=filename
        with fits.open(self.filename) as hdul:
            self.data=[hdu.data for hdu in hdul]

        self.shape=self.data[0].shape
        self.order=len(self.data)
        if self.order > 1:
            self.wmin=hdul[0].header['WMIN']
            self.wmax=hdul[0].header['WMAX']
            self.ftype='polynomial'
            self.func=self.poly
        else:
            self.ftype='gray'
            self.func=self.gray
            
            
    def poly(self,x,y,l):
        ll=(l-self.wmin)/(self.wmax-self.wmin)
        ff=sum(datum[y,x]*ll**i for i,datum in enumerate(self.data))
        return ff

    def gray(self,x,y,l):
        return self.data[0][y,x]
 
    def __call__(self,x,y,l):
        f=np.zeros_like(x,dtype=self.DTYPE)
        g=(x >= 0) & (x < self.shape[1]) & (y >= 0) & (y < self.shape[0])
        f[g]=self.func(x[g],y[g],l[g])
        return f

   

if __name__=='__main__':
    ff=ImageFlatField('/Users/rryan/LINEAR/config/HST/WFC3/IR/G102_V2.0/WFC3.IR.G102.flat.2.fits')

    x=np.array([-2,1,2,3,4,1014])
    y=np.array([-2,5,6,7,8,1014])
    l=np.array([8900,9000,9100,9200,9300,9400])

    q=ff(x,y,l)


    ff=UnityFlatField((1014,1014))
    print(ff(x,y,l))
    print(ff)


        

        
        
