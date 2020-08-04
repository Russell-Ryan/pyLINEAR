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
