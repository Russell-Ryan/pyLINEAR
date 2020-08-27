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


        
    def __iter__(self):
        yield from zip(self.dx,self.dy,self.value)

    def __len__(self):
        return len(self.dx)
    
        

class GaussianKernel(Kernel):
    
    
    def __init__(self,sigma,size):

        # init the base class
        Kernel.__init__(self,size)

        # save some things related to the Gaussian function
        self.sigma=sigma
        self.variance=self.sigma*self.sigma
        
        # do every (x,y) pair
        #dx,dy,value = [],[],[]
        #rad = int((size-1)/2)
        #for i in range(-rad,rad+1,1):
        #    for j in range(-rad,rad+1,1):                
        #        dx.append(i)
        #        dy.append(j)
        #        v=dblquad(volume,i-0.5,i+0.5,lambda y: j-0.5,lambda y: j+0.5)
        #        value.append(v[0])
 

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
                elif i!=0 and j!=0:         # flip over the x/y-axes
                    dx.extend([+i,-i,+i,-i])
                    dy.extend([+j,+j,-j,-j])
                    value.extend([v,v,v,v])
                else:                       # no flipping, at the origin
                    dx.append(i)
                    dy.append(j)
                    value.append(v)




                    
        # recast results to arrays and put in their place holders
        self.dx=np.array(dx,dtype=np.int)
        self.dy=np.array(dy,dtype=np.int)
        self.value=np.array(value,dtype=np.float)
        

        # force normalization
        self.value/=np.sum(self.value)
        

    def __call__(self,x,y):
        # a function to compute the Kernel
        return np.exp(-0.5*(x*x+y*y)/self.variance)/(2*np.pi*self.variance)

        
if __name__=='__main__':
    kern=GaussianKernel(1.0,5)
    
    for x,y,v in kern:
        print(x,y,v)
