import numpy as np
from shapely.geometry import Polygon
from astropy.convolution import convolve

from .h5tablebase import H5TableBase
from . import columns

class DDT(H5TableBase):
    MASK=False
    def __init__(self,segid,*args):
        self.segid=segid
        #self.beam=beam
        
        self.x=columns.X()
        self.y=columns.Y()
        self.wav=columns.WAV()
        self.val=columns.VAL()
        if len(args)==4:
            self.extend(*args)
            
    @property
    def name(self):
        return str(self.segid)

    def clear(self):
        self.x.clear()
        self.y.clear()
        self.wav.clear()
        self.val.clear()
            
    def __iter__(self):
        yield from zip(self.x,self.y,self.wav,self.val)

    def __len__(self):
        return len(self.x)
            
    def __imul__(self,a):
        self.val*=a
        #self.val=columns.VAL(self.val.to_numpy()*v)
        return self

    def __itruediv__(self,a):
        self.val/=a
        return self

    def extend_with_ddt(self,ddt):
        if len(ddt) != 0:
            self.extend(ddt.x.to_numpy(),ddt.y.to_numpy(),
                        ddt.wav.to_numpy(),ddt.val.to_numpy())
    
    def remove_pixels(self,xr,yr):        
        xy_remove=set(zip(xr,yr))         # pixels to remove

        # find values to keep
        keep=[(x,y,w,v) for (x,y,w,v) in self if (x,y) not in xy_remove]
        self.clear()

        # if have values to keep, then put them back in
        if len(keep):
            x,y,w,v=list(zip(*keep))
            self.extend(x,y,w,v)


            
    def threshold(self,v):
        g=np.where(self.val >= v)[0]       
        self.x=columns.X(self.x.to_numpy(g))
        self.y=columns.Y(self.y.to_numpy(g))
        self.wav=columns.WAV(self.wav.to_numpy(g))
        self.val=columns.VAL(self.val.to_numpy(g))
        
    
    def extend(self,x,y,wav,val):
        assert (len(x)==len(y)==len(wav)==len(val)),'Invalid quadruplet'
        self.x.extend(x)
        self.y.extend(y)
        self.wav.extend(wav)
        self.val.extend(val)

        
    def apply_mask(self,msk):
        if len(self)!=0:
            x=self.x.to_numpy()
            y=self.y.to_numpy()
            
            g=np.where(msk[y,x])[0]
            self.select(g)

        
    def select(self,g):
        if len(self)!=0 and len(g)!=0:
            x=self.x.to_numpy(g)
            y=self.y.to_numpy(g)
            wav=self.wav.to_numpy(g)
            val=self.val.to_numpy(g)

            self.clear()
            self.extend(x,y,wav,val)
    def bounding_box(self):
        xu=np.unique(self.x.to_numpy())
        x0,x1=np.amin(xu),np.amax(xu)
        
        yu=np.unique(self.y.to_numpy())
        y0,y1=np.amin(yu),np.amax(yu)
        
        return x0,x1,y0,y1
            

    def write_h5(self,h5,**kwargs):
        hd=self.write_data(h5,self.name,self.x,self.y,self.wav,
                           self.val,**kwargs)

    
        
    def convolve(self,kernel,border=10):
        wav=self.wav.to_numpy()

        newx,newy=[],[]
        neww,newv=[],[]
        for w in np.unique(wav):
            
            # get the table elements
            g=np.where(wav==w)
            x=self.x.to_numpy(g=g)
            y=self.y.to_numpy(g=g)
            val=self.val.to_numpy(g=g)

            # get a bounding box
            x0,x1=np.amin(x),np.amax(x)
            y0,y1=np.amin(y),np.amax(y)

            # fill an image
            shape=(y1-y0+2*border,x1-x0+2*border)
            img=np.zeros(shape,dtype=float)
            for xx,yy,vv in zip(x,y,val):
                img[yy-y0+border,xx-x0+border]+=vv

            # apply the convolution
            norm1=np.sum(img)
            new=convolve(img,kernel)
            norm2=np.sum(new)

            
            # get the new data
            gy,gx=np.where(new!=0)
            gv=new[gy,gx]
            gy+=(y0-border)
            gx+=(x0-border)
            gw=np.full_like(gx,w)

            # extend dummy arrays
            newx.extend(gx)
            newy.extend(gy)
            neww.extend(gw)
            newv.extend(gv)
            

            

            
            #vmax=np.amax(img)
            #import matplotlib.pyplot as plt
            #fig,(a1,a2)=plt.subplots(1,2)
            #a1.imshow(img,origin='lower',vmax=vmax)
            #a2.imshow(new,origin='lower',vmax=vmax)
            #plt.show()
            
        # clear the current table, and repopulate it
        self.clear()
        self.extend(newx,newy,neww,newv)
        


            
        

    @classmethod
    def load(cls,segid,h5):
        dat=cls.load_data(h5,str(segid))
        ddt=cls(segid,dat['x'],dat['y'],dat['wav'],dat['val'])
        return ddt

if __name__=='__main__':
    #tab=DDT(1)
    #tab.extend([1,2,3,4],[2,3,4,5],[5.,4.,3.,2.],[6.,5.,4.,1.])

    #print(tab)


    pass
