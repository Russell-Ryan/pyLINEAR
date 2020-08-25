
import numpy as np
#import h5py
#from shapely.geometry import Polygon
#from scipy.spatial import ConvexHull

from ..utilities import convexhull,indices

from .h5tablebase import H5TableBase
from .pdt import PDT
from .ddt import DDT
from .ovt import OVT
from . import columns


class ODT(H5TableBase,dict):
    def __init__(self,segid,beam,wav):
        self.segid=segid
        self.beam=beam
        self.wav=wav

    def __imul__(self,a):
        for k in self.keys():
            self[k]*=a
        return self
        
    def __iter__(self):
        yield from self.values()

    def threshold(self,v):
        for pdt in self:
            pdt.threshold(v)

            

        
    @property
    def name(self):
        return str(self.segid)

    def extend(self,pdt):
        assert isinstance(pdt,PDT),'ODT can only extend a PDT'
        self[pdt.pixel]=pdt
  
    def write_h5(self,h5,**kwargs):
        hs=self.write_group(h5,self.name,**kwargs)        
        ht=self.write_group(hs,'odt')
        hf=self.write_group(ht,self.beam)
        self.write_attribute(hf,'wav0',self.wav[0])
        self.write_attribute(hf,'wav1',self.wav[-1])
        self.write_attribute(hf,'dwav',self.wav[1]-self.wav[0])
        self.write_attribute(hf,'npix',np.uint32(len(self)))
        
        for k,v in self.items():
            v.write_h5(hf)


    @classmethod
    def load(cls,segid,beam,h5):
        hf=h5[str(segid)+'/odt/'+str(beam)]
        wav0=cls.load_attribute(hf,'wav0')
        wav1=cls.load_attribute(hf,'wav1')
        dwav=cls.load_attribute(hf,'dwav')
        wav=np.arange(wav0,wav1+dwav,dwav)
        
        odt=cls(segid,beam,wav)
        for pix in hf.keys():
            pdt=PDT.load(pix,hf)
            odt.extend(pdt)
        return odt
        


    #def as_polygon(self):
    def compute_vertices(self):
        ovt=OVT(self.segid,self.beam)
        if len(self)!=0:

            
            # get all the (x,y) pairs
            x,y=[],[]
            for pdt in self:
                x.extend(pdt.x)
                y.extend(pdt.y)

            # only compute convex hull if there are points
            if len(x)>0:
                
                # make them np arrays
                x=np.array(x,dtype=np.uint64)
                y=np.array(y,dtype=np.uint64)
                
                # uniqify the pairs
                x,y=indices.unique_pairs(x,y)

                # compute the convex hull
                x,y=convexhull.vertices(x,y)
                
                # return a new table
                ovt.extend(x,y)
            '''
            
            # collect all the unique (x,y) pairs
            xy=[]
            for pdt in self:
                xy.extend(list(zip(pdt.x,pdt.y)))

            if len(xy)>0:
            
                xy=np.array(xy)
                
            
                # make the hull
                hull=ConvexHull(xy)
                
                # get the vertices
                #xyh=xy[hull.vertices]

                # make into a polygon
                #p=Polygon(xyh)

                # get the coordiantes
                xh=xy[hull.vertices][:,0]
                yh=xy[hull.vertices][:,1]
                
                ovt.extend(xh,yh)
            '''
        return ovt



    
    def decimate(self,nx,ny):
        if len(self)!=0:

            # get some values for quicker access
            npix=np.uint64(nx)*np.uint64(ny)

            # get the values to decimate
            xyl,val=[],[]

            for pdt in self:
                xy=pdt.x.astype(np.uint64)+nx*pdt.y.astype(np.uint64)
                xyl.extend(xy+npix*pdt.lam.astype(np.uint64))
                val.extend(pdt.val.astype(np.float64))
            if len(xyl)>0:
                xyl=np.array(xyl)
                val=np.array(val)
            
                # find unique indices & compress
                xylu=np.unique(xyl)
                xylc=np.digitize(xyl,xylu)-1
                
                # sum over repeated indices
                vu=np.bincount(xylc,weights=val)

                # go back to 1d indices
                lamu,xygu=np.divmod(xylu,npix)
                yu,xu=np.divmod(xygu,nx)
                
                # get the wavelengths
                wu=self.wav[lamu]

                # return the DDT            
                ddt=DDT(self.segid,xu,yu,wu,vu)
            else:
                # a null table
                ddt=DDT(self.segid)
        else:
            # a null table
            ddt=DDT(self.segid)

            
        return ddt
