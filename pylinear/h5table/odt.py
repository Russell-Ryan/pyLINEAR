import numpy as np
import h5py

from .base import Base
from .pdt import PDT
from .ddt import DDT
from . import columns
from . import h5utils

class ODT(Base):
    DTYPE=np.uint64         # for internal integer arithmetic

    
    def __init__(self,segid,wav=[]):
        self.segid=segid

        
        self.wav=columns.WAV(wav)
        self.xyg=columns.XYG()
        self.lam=columns.LAM()
        self.val=columns.VAL()

        self.pix=[]          # FIX
        #self.count=[0]       # FIX

        self.x=columns.X()
        self.y=columns.Y()
        self.count=columns.Count([0])
        
    
    def extend(self,pdt):
        assert isinstance(pdt,PDT),'Wrong data type'
        
        self.pix.append(pdt.pixel)
        self.x.append(pdt.pixel[0])
        self.y.append(pdt.pixel[1])
        self.count.append(self.count[-1]+len(pdt))
        self.xyg.extend(pdt.xyg)
        self.lam.extend(pdt.lam)
        self.val.extend(pdt.val)


    def writeH5(self,grp,**kwargs):
        # original code
        #dset=self.writeData(grp,self.xyg,self.lam,self.val,\
        #                    wavelengths=self.wav,pixels=self.pix,\
        #                    count=self.count)

        # hack to work for Nor's big galaxies (explicitly typing the
        # internal variables with numpy dtypes to avoid the 64 kb limit
        # that is claimed to be present in HDF5)
        # https://stackoverflow.com/questions/16639503/unable-to-save-dataframe-to-hdf5-object-header-message-is-too-large

        # this hack didn't really work either, because the biggest of
        # sources overflow the 64kb limit using uint32.  the biggest
        # sources require uint8, but then their content would overflow
        # the numeric range of uint8        
        #dset=self.writeData(grp,self.xyg,self.lam,self.val,\
        #                    wavelengths=np.array(self.wav,dtype=np.float32),\
        #                    pixels=np.array(self.pix,dtype=np.uint16),\
        #                    count=np.array(self.count,dtype=np.uint32))

        # new attempt... create groups and write data to that -_-
        new=grp.create_group(self.name)
        for k,v in kwargs.items():
            h5utils.writeAttr(new,k,v)


        data=h5utils.writeData(new,self.ttype,self.xyg,self.lam,self.val)
        pixels=h5utils.writeData(new,'pix',self.x,self.y,\
                                 columns.Count(self.count[1:]))
        wave=h5utils.writeData(new,'wav',self.wav)


        
        return new


    
    def readH5(self,grp):
        if self.name in grp:
            new=grp[self.name]
            data=h5utils.loadData(new,self.ttype)
            self.xyg=columns.XYG(data['xyg'])
            self.lam=columns.LAM(data['lam'])
            self.val=columns.VAL(data['val'])
            
            pixels=h5utils.loadData(new,'pix')
            self.x=columns.X(pixels['x'])
            self.y=columns.Y(pixels['y'])
            self.pix=list(zip(self.x,self.y))
            self.count=columns.Count([0])
            self.count.extend(pixels['count'])
            self.wav=columns.WAV(h5utils.loadData(new,'wav'))
        else:
            self.notFound()
        

    def set(self):
        return set(self.xyg)

            
    @property
    def npix(self):
        return len(self.pix)
            
    @property
    def nwav(self):
        return len(self.wav)

    
    def decimate(self):
        ddt=DDT(self.segid)     # create empy DDT for output
        if len(self) != 0:
            ddt.pix=self.pix

            # make a one-d index
            #xyl=self.xyg.astype(dtype)+self.npix*self.lam.astype(dtype)
            xyl=self.DTYPE(self.nwav)*self.xyg.astype(self.DTYPE)+\
                 self.lam.astype(self.DTYPE)

            # find unique indices & compress
            xylu=np.unique(xyl)
            xylc=np.digitize(xyl,xylu)-1
            del xyl                # just save on memory usage

            # sum over repeated indices
            vald=np.bincount(xylc,weights=self.val.to_numpy)
            del xylc               # just save on memory usage
            
            # go back to 2d indices
            #xygu,lamu=divmod(xylu,self.npix)
            xygu,lamu=divmod(xylu,self.nwav)
            del xylu               # just save on memory usage
            
            # get the wavelengths
            wav=self.wav.to_numpy[lamu]
            del lamu               # just save on memory usage
            
            # update the output table            
            ddt.extend(xygu,wav,vald)

        return ddt

    #def __str__(self):
    #    return '{} for {}\n{} pixels and {} wavelengths'.format(self.ttype,self.segid,self.npix,self.nwav)
        
    def __getitem__(self,pix):
        if pix in self:
            i=self.pix.index(pix)

            i0,i1=self.count[i],self.count[i+1]

            pdt=PDT(x=pix[0],y=pix[1])
            
            pdt.extend(self.xyg[i0:i1],self.lam[i0:i1],self.val[i0:i1])
            return pdt
        else:
            return None

    def __contains__(self,pix):
        return pix in self.pix
        
    def __len__(self):
        return self.count[-1]
        
    @property
    def name(self):
        return '{}'.format(self.segid)


    
if __name__=='__main__':
    wav=np.array([7000,7100,7200,7300,7400,7500,7600],dtype=np.float)
    segid=1
    o=ODT(segid,wav=wav)


    pix=(1,2)
    x=PDT(pix)
    x.extend([1,2,3,4],[2,3,4,5],[1.,2.,3.,0.5])
#    o.extend(x)

    '''
    x=PDT((2,3))
    x.extend([11,21,31,4],[0,2,4,5],[11.,21.,31.,0.5])
    o.extend(x)

    x=PDT((4,5))
    x.extend([3,4,5,4],[1,2,3,5],[0.1,0.2,0.3,0.4])
    o.extend(x)
    '''


    with h5py.File('tester.h5','w') as h5:
        x.writeH5(h5)

    with h5py.File('tester.h5','r') as h5:
        x2=PDT(pix)
        x2.readH5(h5)

