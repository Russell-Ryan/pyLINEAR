import numpy as np


from .h5tablebase import H5TableBase
from . import columns



class PDT(H5TableBase):
    def __init__(self,pixel,*args):

        if isinstance(pixel,tuple):
            self.pixel=pixel
        elif isinstance(pixel,list):
            self.pixel=tuple(pixel)
        elif isinstance(pixel,str):
            pixel=pixel.strip()[1:-1].split(',')
            self.pixel=(int(pixel[0]),int(pixel[1]))
        else:
            raise NotImplementedError("Invalid data type for pixel.")

        self.x=columns.X()
        self.y=columns.Y()
        self.lam=columns.LAM()
        self.val=columns.VAL()
        
        if len(args)==4:
            self.extend(*args)

    def __iter__(self):
        yield from zip(self.x,self.y,self.lam,self.val)
    
            
    def extend(self,x,y,lam,val):
        assert (len(x)==len(y)==len(lam)==len(val)),'Invalid quadruplet'
        self.x.extend(x)
        self.y.extend(y)
        self.lam.extend(lam)
        self.val.extend(val)
        

    def __imul__(self,a):
        self.val*=a
        return self


    def __rmul__(self,a):
        self.val*=a
        return self


    def __mul__(self,a):
        self.val*=a
        return self


    def threshold(self,v):
        g=np.where(self.val >= v)[0]
        self.x=columns.X(self.x.to_numpy(g))
        self.y=columns.Y(self.y.to_numpy(g))
        self.lam=columns.LAM(self.lam.to_numpy(g))
        self.val=columns.VAL(self.val.to_numpy(g))
  


    
    @property
    def name(self):
        return '({},{})'.format(*self.pixel)

    
    def __str__(self):
        return 'pixel table: {}'.format(self.name)

    def __len__(self):
        return len(self.x)

    def write_h5(self,h5,**kwargs):
        hd=self.write_data(h5,self.name,self.x,self.y,self.lam,
                           self.val,**kwargs)


    

    @classmethod
    def load(cls,pixel,h5):
        pixel='({},{})'.format(*pixel)
        data=cls.load_data(h5,pixel)
        pdt=cls(pixel,data['x'],data['y'],data['lam'],data['val'])
        return pdt



    def convolve(self,kernel,device):
        dim=(device.npixel,1)   # the 1 here is just a dummy variable
        
        xyl=[]
        val=[]
        for x,y,l,v in self:

            # apply the kernel in real space
            xx=x+kernel.dx
            yy=y+kernel.dy
            vv=v*kernel.value
            
            # only get pixels that are within the image
            g=np.where((xx >= 0) & (xx < device.naxis1) and
                       (yy >= 0) & (yy < device.naxis2))[0]

            # only keep the good ones
            if len(g) > 0:
                # keep the good values
                xx,yy,vv=xx[g],yy[g],vv[g]
            
                # create a dummy wavelength array
                ll=np.full_like(xx,l)

                # join the (x,y) into a pixel index
                xy=indices.two2one(xx,yy,device.shape)

                # join pixel indices with wavelength into single triplet 
                cc=indices.two2one(xy,ll,dim)
                
                # save the results
                xyl.extend(cc)
                val.extend(vv)



        # clear and refill the data
        self.clear()

        # now refill the self if there is valid data
        if len(xyl)>0:

            # sum over the repeated indices.  This is the sum as part of
            # a numerical convolution
            val,xyl=indices.decimate(xyl,val)

            # decompose the positions back into (x,y,wavelength)
            xy,ll=indices.one2two(xyl,dim)
            xx,yy=indices.one2two(xy,device.shape)
            

            # refill the object with the appropriate data
            self.extend(xx,yy,ll,val)

            # or create a new PDT?
            #pdt=PDT(self.pixel,xx,yy,ll,val)
            
            
