import numpy as np
from scipy.integrate import dblquad
from timeit import default_timer
''' Gaussian kernels should probably be something like

.. math::
        \sigma_{kernel} = \sqrt{\left(1.22\frac{\lambda}{D}\right)^2 - \sigma^2}

Where D is diameter of telescope, \sigma the Gaussian dispersion for the 
direct-image PSF, and \sigma_{kernel} is the sigma for the `GaussianKernel`

'''


class Kernel(object):
    def __init__(self,size):
        if not isinstance(size,int):
            print('[warn]Forcing size to be an integer.')
            size=int(size)
            
        if size % 2 == 0:
            print('[warn]Forcing kernel should be an odd number.')
            size+=1

        self.size=size
        self.dx=None
        self.dy=None
        self.value=None
        self.shape=(self.size,self.size)

        
    def __iter__(self):
        yield from zip(self.dx,self.dy,self.value)

    def __len__(self):
        return len(self.dx)


    def as_image(self):
        x0,y0=np.amin(self.dx),np.amin(self.dy)
        img=np.zeros(self.shape,dtype=float)
        img[self.dy-y0,self.dx-x0]=self.value
        return img

        
    
class SquareKernel(Kernel):
    def __init__(self,width):
        self.wid2=width/2.
        rad=int(np.ceil(self.wid2))
        Kernel.__init__(self,2*rad+1)

        dx,dy,value=[],[],[]
        for i in range(-rad,rad+1,1):
            for j in range(-rad,rad+1,1):
                
                v,dv=dblquad(self,i-0.5,i+0.5,lambda y: j-0.5,lambda y: j+0.5)
                #v,dv=dblquad(self,i,i+1.0,lambda y: j,lambda y: j+1.0)
                dx.append(i)
                dy.append(j)
                value.append(v)
        self.dx=np.array(dx,dtype=np.int)
        self.dy=np.array(dy,dtype=np.int)
        self.value=np.array(value,dtype=np.float)


        g=np.where(self.value !=0)
        self.dx=self.dx[g]
        self.dy=self.dy[g]
        self.value=self.value[g]
        self.value/=np.sum(self.value)
        #self.size=np.amax(self.dx)

        #self.shape=(np.amax(self.dy),np.amax(self.dx))

    
        
    def __call__(self,x,y):
        v=(-self.wid2<x) & (x<self.wid2) & (-self.wid2<y) & (y<self.wid2)
        return float(v)



class GaussianKernel(Kernel):    
    def __init__(self,sigma,size,center=(0,0)):
        
        # init the base class
        Kernel.__init__(self,size)

        # save some things related to the Gaussian function
        self.sigma=sigma
        self.variance=self.sigma*self.sigma
        self.center=center
        
        # do every (x,y) pair
        #dx,dy,value = [],[],[]
        #rad = int((size-1)/2)
        #for i in range(-rad,rad+1,1):
        #    for j in range(-rad,rad+1,1):                
        #        dx.append(i)
        #        dy.append(j)
        #        v=dblquad(volume,i-0.5,i+0.5,lambda y: j-0.5,lambda y: j+0.5)
        #        value.append(v[0])
 




        dx,dy,value=[],[],[]
        rad=int((size-1)/2)
        for i in range(-rad,rad+1,1):
            for j in range(-rad,rad+1,1):
                v,dv=dblquad(self,i-0.5,i+0.5,lambda y: j-0.5,lambda y: j+0.5)
                dx.append(i)
                dy.append(j)
                value.append(v)
            
                
        '''
        
        # only evaluate integral in Quadrant 1, then replicate the result.
        # this saves typically a factor of 3 CPU time for these integrals
        dx,dy,value = [],[],[]
        rad = int((size-1)/2)
        for i in range(0,rad+1,1):
            for j in range(0,rad+1,1):                

                # integrate over a pixel
                v,dv=dblquad(self,i-0.5,i+0.5,lambda y: j-0.5,lambda y: j+0.5)

                if i==0 and j!=0:           # flip over the y-axis
                    dx.extend([+i,+i])
                    dy.extend([+j,-j])
                    value.extend([v,v])
                elif i!=0 and j==0:         # flip over the x-axis
                    dx.extend([+i,-i])
                    dy.extend([+j,+j])
                    value.extend([v,v])
                elif i!=0 and j!=0:         # flip over x- & y-axes
                    dx.extend([+i,-i,+i,-i])
                    dy.extend([+j,+j,-j,-j])
                    value.extend([v,v,v,v])
                else:                       # no flipping, at the origin
                    dx.append(i)
                    dy.append(j)
                    value.append(v)

        '''


                    
        # recast results to arrays and put in their place holders
        self.dx=np.array(dx,dtype=np.int)
        self.dy=np.array(dy,dtype=np.int)
        self.value=np.array(value,dtype=np.float)
        
        # force normalization
        self.value/=np.sum(self.value)
        

    def __call__(self,x,y):
        # a function to compute the Kernel
        xx=(x-self.center[0])
        yy=(y-self.center[1])
        
        return np.exp(-0.5*(xx*xx+yy*yy)/self.variance)/(2*np.pi*self.variance)

        
if __name__=='__main__':
    sigma=0.5
    nsigma=15.
    #
    size=int(np.ceil(sigma*nsigma))
    size=15
    kern=GaussianKernel(sigma,size)


    #kern=SquareKernel(3.1,center=)
    from astropy.convolution import convolve,Gaussian2DKernel
    from astropy.utils.data import get_pkg_data_filename
    from astropy.io import fits
    image_file = get_pkg_data_filename('tutorials/FITS-images/HorseHead.fits')
    img = fits.getdata(image_file, ext=0)
    new=convolve(img,kern.as_image())

    k2=Gaussian2DKernel(sigma,x_size=size)

    
    import matplotlib.pyplot as plt
    fig,(a1,a2,a3)=plt.subplots(1,3,sharex=True,sharey=True)
    a1.imshow(kern.as_image(),origin='lower')
    a2.imshow(k2,origin='lower')
    a3.imshow(kern.as_image()-k2.array,origin='lower')
    print(kern.as_image().shape)
    print(k2.shape)
    #a1.imshow(img,origin='lower')
    #a2.imshow(kern.as_image(),origin='lower')
    #a2.imshow(new,origin='lower')
    
    plt.show()

    
