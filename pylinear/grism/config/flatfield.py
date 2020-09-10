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

    def __str__(self):
        return 'Unity Flat Field'

    
class ImageFlatField(FlatField):
    def __init__(self,filename):
        self.filename=filename
        with fits.open(self.filename) as hdul:
            self.data=[hdu.data for hdu in hdul if hdu.data is not None]

        self.order=len(self.data)
        if self.order ==0:
            # null flat
            print('[warn]Flat-field is invalid, using ones')
            self.ftype='Unity'
            self.func=self.unity
        elif self.order==1:
            # gray flat
            self.shape=self.data[0].shape
            self.ftype='Gray'
            self.func=self.gray
        else:
            # chromatic flat
            self.shape=self.data[0].shape
            self.wmin=hdul[0].header['WMIN']
            self.wmax=hdul[0].header['WMAX']
            self.ftype='Polynomial'
            self.func=self.poly
        
            

    def __str__(self):
        s='{} Flat Field'.format(self.ftype)
        if self.ftype =='Polynomial':
            s+=' with {} terms'.format(self.order)
        return s

            
    def poly(self,x,y,l):
        ll=(l-self.wmin)/(self.wmax-self.wmin)
        ff=sum(datum[y,x]*ll**i for i,datum in enumerate(self.data))
        return ff

    def gray(self,x,y,l):
        return self.data[0][y,x]

    def unity(self,x,y,l):
        return np.ones_like(x,dtype=self.DTYPE)
    
    def __call__(self,x,y,l):
        f=np.zeros_like(x,dtype=self.DTYPE)
        g=(x >= 0) & (x < self.shape[1]) & (y >= 0) & (y < self.shape[0])
        f[g]=self.func(x[g],y[g],l[g])
        return f

   

if __name__=='__main__':

    x=np.array([-2,1,2,3,4,1014])
    y=np.array([-2,5,6,7,8,1014])
    l=np.array([8900,9000,9100,9200,9300,9400])


    ff=ImageFlatField('/Users/rryan/LINEAR/config/HST/WFC3/IR/G102_V2.0/WFC3.IR.G102.flat.2.fits')
    print(ff)
    print(ff(x,y,l))

    ff=ImageFlatField('/Users/rryan/PYLINEAR_CONFIG/WFC3IR/F105W_pfl.fits')
    print(ff)
    print(ff(x,y,l))


    ff=UnityFlatField((1014,1014))
    print(ff)
    print(ff(x,y,l))



        

        
        
